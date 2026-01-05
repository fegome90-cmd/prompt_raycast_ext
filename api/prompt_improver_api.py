"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
Supports both zero-shot and few-shot modes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ValidationError
import dspy
import time
import logging
import asyncio
from typing import Optional, Dict, Any

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.interfaces import container
from hemdov.infrastructure.config import Settings
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from api.circuit_breaker import CircuitBreaker
from hemdov.domain.metrics.evaluators import (
    PromptMetricsCalculator,
    ImpactData,
)
from api.quality_gates import evaluate_output, GateReport, get_template_summary

logger = logging.getLogger(__name__)

# Custom exceptions for better error handling
class QualityGateEvaluationError(Exception):
    """Raised when gate evaluation fails."""
    pass


router = APIRouter(prefix="/api/v1", tags=["prompts"])

# Circuit breaker instance
_circuit_breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

# Metrics calculator
_metrics_calculator = PromptMetricsCalculator()

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

        # Calculate comprehensive metrics
        try:
            # Extract model and provider from settings
            model = settings.LLM_MODEL
            provider = settings.LLM_PROVIDER

            # Convert guardrails to list if it's a string
            guardrails_list = (
                result.guardrails.split("\n")
                if isinstance(result.guardrails, str)
                else result.guardrails
            )

            # Extract confidence
            confidence_value = getattr(result, "confidence", None)

            # Calculate metrics using calculate_from_history with timing
            metrics_start = time.time()
            metrics = _metrics_calculator.calculate_from_history(
                original_idea=request.idea,
                context=request.context,
                improved_prompt=result.improved_prompt,
                role=result.role,
                directive=result.directive,
                framework=result.framework,
                guardrails=guardrails_list,
                backend=backend,
                model=model,
                provider=provider,
                latency_ms=latency_ms,
                confidence=confidence_value,
                impact_data=ImpactData(),  # TODO: Track user interactions
            )
            metrics_duration_ms = int((time.time() - metrics_start) * 1000)

            # Warn if too slow
            if metrics_duration_ms > 10:
                logger.warning(f"Metrics calculation took {metrics_duration_ms}ms (target: <10ms)")

            # Log metrics for monitoring
            logger.info(
                f"Metrics calculated in {metrics_duration_ms}ms: "
                f"overall={metrics.overall_score:.2f} ({metrics.grade}), "
                f"quality={metrics.quality.composite_score:.2f}, "
                f"performance={metrics.performance.performance_score:.2f}, "
                f"latency={metrics.performance.latency_ms}ms"
            )

            # Store metrics if SQLite is enabled
            if settings.SQLITE_ENABLED:
                try:
                    metrics_repo = await get_repository(settings)
                    if metrics_repo and hasattr(metrics_repo, 'save'):
                        # Note: We need a metrics repository, not prompt repository
                        # For now, just log that we would save it
                        logger.debug("Metrics calculated successfully (persistence to be implemented)")
                except Exception as e:
                    logger.error(f"Failed to save metrics: {e}")
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}", exc_info=True)
            # Don't fail the request if metrics fail

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


class EvaluateQualityRequest(BaseModel):
    """Request model for quality gate evaluation.

    Raises:
        ValueError: If output is empty/whitespace or exceeds size limit.
        ValueError: If template_id is not supported.
    """
    output: str = Field(
        ...,
        description="The output text to evaluate against quality gates.",
        min_length=1,
        max_length=100000  # 100KB limit
    )
    template_id: str = Field(
        default="json",
        description="Template ID to use for evaluation. Must be one of: json, procedure_md, checklist_md, example_md."
    )
    template_spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional template specification override. If not provided, uses DEFAULT_TEMPLATES."
    )

    @field_validator("output")
    @classmethod
    def output_must_not_be_whitespace(cls, v: str) -> str:
        """Validate output is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Output cannot be empty or whitespace only")
        return v

    @field_validator("template_id")
    @classmethod
    def template_id_must_be_valid(cls, v: str) -> str:
        """Validate template_id is supported."""
        from api.quality_gates import DEFAULT_TEMPLATES
        valid_templates = set(DEFAULT_TEMPLATES.keys())
        if v not in valid_templates:
            raise ValueError(
                f"Invalid template_id '{v}'. Must be one of: {', '.join(sorted(valid_templates))}"
            )
        return v


class EvaluateQualityResponse(BaseModel):
    """Response model for quality gate evaluation.

    Contains complete gate evaluation results including v0.1 (format+completeness)
    and v0.2 (anti-trampa heuristics) gate results.
    """
    template_id: str = Field(description="The template ID used for evaluation.")
    output_length: int = Field(description="Character length of the evaluated output.")
    v0_1_pass: bool = Field(description="Whether all v0.1 gates (format+completeness) passed.")
    v0_2_fail_count: int = Field(description="Number of v0.2 gates that FAILED.")
    v0_2_warn_count: int = Field(description="Number of v0.2 gates that WARNED.")
    overall_pass: bool = Field(description="Overall pass status (v0.1 must pass AND v0.2 must have 0 FAILs).")
    overall_status: str = Field(description="Overall status: PASS, WARN, or FAIL.")
    summary: str = Field(description="Human-readable summary of evaluation results.")
    gates: Dict[str, Dict[str, Any]] = Field(description="Complete gate results with details for each gate.")


@router.post("/evaluate-quality", response_model=EvaluateQualityResponse)
async def evaluate_quality(request: EvaluateQualityRequest):
    """
    Evaluate output quality against v0.1 + v0.2 gates.

    POST /api/v1/evaluate-quality
    {
        "output": "## Objetivo\\n\\n## Pasos\\n\\n1. TBD",
        "template_id": "procedure_md"
    }

    Response:
    {
        "template_id": "procedure_md",
        "output_length": 45,
        "v0.1_pass": false,
        "v0.2_fail_count": 1,
        "v0.2_warn_count": 0,
        "overall_pass": false,
        "overall_status": "FAIL",
        "summary": "Pasos genéricos o vacíos",
        "gates": {
            "v0.1_gates": {...},
            "v0.2_gates": {...}
        }
    }

    Error Responses:
    - 400: Validation error (empty output, invalid template_id)
    - 500: Evaluation error (internal gate failure)
    """
    # Note: Pydantic validators handle input validation automatically
    # Custom validators check for:
    # - Empty/whitespace output
    # - Invalid template_id
    # - Output size limits (min 1, max 100000 chars)

    try:
        # Run quality gates
        report: GateReport = evaluate_output(
            output_text=request.output,
            template_id=request.template_id,
            template_spec=request.template_spec
        )

        # Build gates dict for response (only v0.1 and v0.2 gates)
        gates_dict = {
            "v0_1_gates": {
                k: v.to_dict() for k, v in report.v0_1_gates.items()
            },
            "v0_2_gates": {
                k: v.to_dict() for k, v in report.v0_2_gates.items()
            }
        }

        # Convert to response format
        return EvaluateQualityResponse(
            template_id=report.template_id,
            output_length=report.output_length,
            v0_1_pass=report.v0_1_pass,
            v0_2_fail_count=report.v0_2_fail_count,
            v0_2_warn_count=report.v0_2_warn_count,
            overall_pass=report.overall_pass,
            overall_status=report._get_overall_status(),
            summary=get_template_summary(report),
            gates=gates_dict
        )

    except QualityGateEvaluationError as e:
        # Custom business logic errors
        logger.error(
            f"Quality gate error: {type(e).__name__} | "
            f"template_id={request.template_id} | "
            f"message={str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Quality gate evaluation failed. Please try again later."
        )
    except KeyError as e:
        # Missing keys in output data - include the specific key name
        missing_key = str(e) if e else "unknown"
        logger.warning(
            f"Quality gate key error: KeyError | "
            f"template_id={request.template_id} | "
            f"missing_key={missing_key} | "
            f"output_length={len(request.output)}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: missing required key '{missing_key}'"
        )
    except Exception as e:
        # Unexpected errors - log with full context, hide internals from client
        # Note: ValidationError from Pydantic is handled before reaching this code
        logger.error(
            f"Unexpected error in quality gate evaluation: {type(e).__name__} | "
            f"template_id={request.template_id} | "
            f"output_length={len(request.output)} | "
            f"error={str(e)}",
            exc_info=True
        )
        # Generate error ID for tracking (timestamp + template_id)
        error_id = f"QE-{int(time.time())}-{request.template_id}"
        logger.error(f"Error ID for tracking: {error_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal evaluation error. Reference ID: {error_id}"
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

