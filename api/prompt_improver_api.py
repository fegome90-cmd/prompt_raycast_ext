"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
Supports both zero-shot and few-shot modes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import dspy
import time
import logging
import asyncio
from typing import Optional

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.interfaces import container
from hemdov.infrastructure.config import Settings
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from api.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prompts"])

# Circuit breaker instance
_circuit_breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

# Repository getter with circuit breaker
async def get_repository(settings: Settings) -> Optional[PromptRepository]:
    """Get repository instance with circuit breaker protection."""
    if not settings.SQLITE_ENABLED:
        return None

    if not await _circuit_breaker.should_attempt():
        return None

    # Get or create repository from container
    try:
        return container.get(PromptRepository)
    except ValueError:
        # Not registered, register it now
        repo = SQLitePromptRepository(settings)
        container.register(PromptRepository, repo)

        # Register cleanup hook
        async def cleanup():
            await repo.close()

        container._cleanup_hooks.append(cleanup)

        return repo



class ImprovePromptRequest(BaseModel):
    idea: str
    context: str = ""


class ImprovePromptResponse(BaseModel):
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: str | None = None
    confidence: float | None = None
    backend: str | None = None  # "zero-shot" or "few-shot"


# Initialize modules (lazy loading)
_prompt_improver: PromptImprover | None = None
_fewshot_improver = None  # Will be PromptImproverWithFewShot


def get_prompt_improver(settings: Settings) -> PromptImprover:
    """Get or initialize zero-shot PromptImprover module."""
    global _prompt_improver

    if _prompt_improver is None:
        # Initialize module
        improver = PromptImprover()
        _prompt_improver = improver

    return _prompt_improver


def get_fewshot_improver(settings: Settings):
    """Get or initialize few-shot PromptImprover module."""
    global _fewshot_improver

    if _fewshot_improver is None:
        from eval.src.dspy_prompt_improver_fewshot import (
            PromptImproverWithFewShot,
            load_trainset,
            create_fewshot_improver
        )

        if settings.DSPY_FEWSHOT_TRAINSET_PATH:
            # Load and compile with training set
            improver = create_fewshot_improver(
                trainset_path=settings.DSPY_FEWSHOT_TRAINSET_PATH,
                compiled_path=settings.DSPY_FEWSHOT_COMPILED_PATH,
                k=settings.DSPY_FEWSHOT_K
            )
        else:
            # Create uncompiled few-shot improver
            improver = PromptImproverWithFewShot(k=settings.DSPY_FEWSHOT_K)

        _fewshot_improver = improver

    return _fewshot_improver


@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    Uses zero-shot or few-shot mode based on DSPY_FEWSHOT_ENABLED setting.

    POST /api/v1/improve-prompt
    {
        "idea": "Design ADR process",
        "context": "Software architecture team"
    }

    Response:
    {
        "improved_prompt": "**[ROLE & PERSONA]**\\nYou are...",
        "role": "World-Class Software Architect...",
        "directive": "To design and detail...",
        "framework": "chain-of-thought",
        "guardrails": ["Avoid jargon", "Prioritize pragmatism", ...],
        "reasoning": "Selected role for expertise...",
        "confidence": 0.87,
        "backend": "few-shot"  # or "zero-shot"
    }
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400, detail="Idea must be at least 5 characters"
        )

    # Get module
    settings = container.get(Settings)

    # Use few-shot if enabled
    if settings.DSPY_FEWSHOT_ENABLED:
        improver = get_fewshot_improver(settings)
        backend = "few-shot"
    else:
        improver = get_prompt_improver(settings)
        backend = "zero-shot"

    # Start timer for latency
    start_time = time.time()

    # Improve prompt
    try:
        result = improver(original_idea=request.idea, context=request.context)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Build response
        response = ImprovePromptResponse(
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails,
            reasoning=getattr(result, "reasoning", None),
            confidence=getattr(result, "confidence", None),
            backend=backend,
        )

        # Save history asynchronously (non-blocking)
        asyncio.create_task(_save_history_async(
            settings=settings,
            original_idea=request.idea,
            context=request.context,
            result=result,
            backend=backend,
            latency_ms=latency_ms
        ))

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prompt improvement failed: {str(e)}"
        )


async def _save_history_async(
    settings: Settings,
    original_idea: str,
    context: str,
    result,
    backend: str,
    latency_ms: int
):
    """
    Save prompt improvement history to SQLite with circuit breaker protection.

    Non-blocking async function that logs errors without failing the request.
    """
    repo = None
    success = False

    try:
        # Get repository with circuit breaker
        repo = await get_repository(settings)
        if repo is None:
            logger.debug("Persistence disabled or circuit breaker open")
            return

        # Extract model and provider from settings
        model = settings.LLM_MODEL
        provider = settings.LLM_PROVIDER

        # Convert guardrails to list if it's a string
        guardrails_list = (
            result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails
        )

        # Extract and convert confidence to float if it's a string
        confidence_value = getattr(result, "confidence", None)
        if confidence_value is not None:
            try:
                confidence_value = float(confidence_value)
            except (ValueError, TypeError):
                confidence_value = None

        # Create PromptHistory entity
        history = PromptHistory(
            original_idea=original_idea,
            context=context,
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=guardrails_list,
            backend=backend,
            model=model,
            provider=provider,
            reasoning=getattr(result, "reasoning", None),
            confidence=confidence_value,
            latency_ms=latency_ms
        )

        # Save to database
        await repo.save(history)
        success = True
        logger.info(f"Saved prompt history to database (latency: {latency_ms}ms)")

    except Exception as e:
        # Record failure on circuit breaker
        await _circuit_breaker.record_failure()
        logger.error(f"Failed to save prompt history: {e}", exc_info=True)

    finally:
        # Record success OUTSIDE try-except to prevent paradox
        if success:
            await _circuit_breaker.record_success()

