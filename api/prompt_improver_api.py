"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
Supports both zero-shot and few-shot modes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import dspy

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings

router = APIRouter(prefix="/api/v1", tags=["prompts"])


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
    from hemdov.interfaces import container

    settings = container.get(Settings)

    # Use few-shot if enabled
    if settings.DSPY_FEWSHOT_ENABLED:
        improver = get_fewshot_improver(settings)
        backend = "few-shot"
    else:
        improver = get_prompt_improver(settings)
        backend = "zero-shot"

    # Improve prompt
    try:
        result = improver(original_idea=request.idea, context=request.context)

        return ImprovePromptResponse(
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

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prompt improvement failed: {str(e)}"
        )
