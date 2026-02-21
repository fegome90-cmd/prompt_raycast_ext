"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
Supports both zero-shot and few-shot modes.
"""

import asyncio
import hashlib
import logging
import time
import uuid
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from api.circuit_breaker import CircuitBreaker
from api.quality_gates import GateReport, evaluate_output, get_template_summary
from eval.src.dspy_prompt_improver import PromptImprover
from eval.src.strategy_selector import StrategySelector
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.metrics.evaluators import (
    ImpactData,
    PromptMetricsCalculator,
)
from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from hemdov.interfaces import container

logger = logging.getLogger(__name__)


class DegradationFlag(str, Enum):
    """Well-defined degradation flags to prevent typos."""
    METRICS_FAILED = "metrics_failed"
    KNN_DISABLED = "knn_disabled"
    COMPLEX_STRATEGY_DISABLED = "complex_strategy_disabled"
    PERSISTENCE_FAILED = "persistence_failed"


# Custom exceptions for better error handling
class QualityGateEvaluationError(Exception):
    """Raised when gate evaluation fails."""
    pass


# Helper functions for code quality
def _normalize_guardrails(guardrails: str | list[str]) -> list[str]:
    """Convert guardrails to normalized list format.

    Args:
        guardrails: Either newline-separated string or list of strings

    Returns:
        List of guardrail strings with whitespace trimmed
    """
    if isinstance(guardrails, str):
        return [g.strip() for g in guardrails.split('\n') if g.strip()]
    return guardrails


def _extract_confidence(result: Any) -> float | None:
    """Extract confidence score from DSPy result.

    Args:
        result: DSPy output (may have .confidence attribute or dict access)

    Returns:
        Confidence as float 0-1, or None if not available
    """
    if hasattr(result, 'confidence'):
        conf = result.confidence
        if conf is not None:
            try:
                return float(conf)
            except (ValueError, TypeError):
                return None
        return None
    if isinstance(result, dict) and 'confidence' in result:
        conf = result['confidence']
        if conf is not None:
            try:
                return float(conf)
            except (ValueError, TypeError):
                return None
        return None
    return None


def normalize_framework_for_history(framework_raw: str) -> tuple[str, bool]:
    """Normalize model framework output to PromptHistory-allowed enum values.

    Returns:
        tuple[framework, used_fallback]:
            - framework: normalized enum value for PromptHistory
            - used_fallback: True when heuristic matching failed and safe default was used
    """
    normalized = framework_raw.strip().lower()
    valid_frameworks = {
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing",
    }

    if normalized in valid_frameworks:
        return normalized, False

    if "decomp" in normalized:
        return "decomposition", False
    if "chain" in normalized or "cot" in normalized:
        return "chain-of-thought", False
    if "tree" in normalized or "tot" in normalized:
        return "tree-of-thoughts", False
    if "role" in normalized:
        return "role-playing", False

    # Safe default that preserves write path stability for unknown framework variants.
    return "decomposition", True


router = APIRouter(prefix="/api/v1", tags=["prompts"])

# Circuit breaker instance
_circuit_breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)


def _classify_intent(idea: str, context: str) -> str:
    """
    Classify intent based on keyword matching.

    Simple heuristic for test compatibility.
    Returns uppercase intent string (DEBUG, REFACTOR, GENERATE, EXPLAIN).
    """
    combined = f"{idea} {context}".lower()

    # Priority order for keyword matching
    if any(kw in combined for kw in ["bug", "fix", "debug", "error", "issue", "fail"]):
        return "DEBUG"
    elif any(kw in combined for kw in ["refactor", "rewrite", "clean", "improve code"]):
        return "REFACTOR"
    elif any(kw in combined for kw in ["explain", "how does", "describe", "what is"]):
        return "EXPLAIN"
    else:
        return "GENERATE"


def _generate_stable_prompt_id(idea: str, context: str, mode: str) -> str:
    """
    Generate stable prompt ID from request hash.

    Identical requests produce the same ID for cache compatibility.
    """
    content = f"{idea}|{context}|{mode}"
    hash_obj = hashlib.sha256(content.encode())
    return str(uuid.UUID(bytes=hash_obj.digest()[:16]))

# Metrics calculator
_metrics_calculator = PromptMetricsCalculator()

# Repository getter with circuit breaker
async def get_repository(settings: Settings) -> PromptRepository | None:
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
    idea: str = Field(..., min_length=5, description="User's raw idea (min 5 characters)")
    context: str = Field(default="", max_length=5000, description="Additional context")
    mode: str = Field(
        default="legacy",
        description="Execution mode: 'legacy' (DSPy) or 'nlac' (NLaC pipeline)"
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        """Validate mode is either 'legacy' or 'nlac'."""
        if v not in ("legacy", "nlac"):
            raise ValueError("mode must be 'legacy' or 'nlac'")
        return v


class ImprovePromptResponse(BaseModel):
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: str | None = None
    confidence: float | None = None
    backend: str | None = None  # "zero-shot" or "few-shot"
    # Additional fields for test compatibility
    prompt_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique prompt identifier"
    )
    strategy: str = Field(default="simple", description="Strategy used for improvement")
    intent: str = Field(
        default="generate",
        description="Intent classification (debug, refactor, generate, explain)"
    )
    strategy_meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional strategy metadata"
    )
    # Degradation and warning fields
    metrics_warning: str | None = Field(
        default=None,
        description="Warning message if metrics calculation failed"
    )
    degradation_flags: dict[str, bool] = Field(
        default_factory=dict,
        description="Degradation flags indicating optional feature failures"
    )

    @field_validator("degradation_flags")
    @classmethod
    def validate_degradation_flags(cls, v: dict[str, bool]) -> dict[str, bool]:
        """Validate that degradation_flags only contains valid keys."""
        valid_keys = {flag.value for flag in DegradationFlag}
        invalid_keys = set(v.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid degradation flags: {invalid_keys}. Valid keys: {valid_keys}")
        return v


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
            create_fewshot_improver,
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


# Initialize strategy selector (lazy loading)
# Dict mapping mode ("legacy"/"nlac") to StrategySelector instance
_strategy_selector: dict[str, StrategySelector] = {}
_strategy_selector_lock = asyncio.Lock()


async def get_strategy_selector(settings: Settings, use_nlac: bool = False) -> StrategySelector:
    """
    Get or initialize StrategySelector with all three strategies.

    Args:
        settings: Application settings
        use_nlac: Whether to use NLaC strategy (default: False)
    """
    global _strategy_selector

    # Create separate selectors for legacy and NLaC modes
    selector_key = "nlac" if use_nlac else "legacy"

    # Use lock to prevent race condition during lazy initialization
    async with _strategy_selector_lock:
        if selector_key not in _strategy_selector:
            # Create selector with appropriate mode
            selector = StrategySelector(
                trainset_path=settings.DSPY_FEWSHOT_TRAINSET_PATH,
                compiled_path=settings.DSPY_FEWSHOT_COMPILED_PATH,
                fewshot_k=settings.DSPY_FEWSHOT_K,
                use_nlac=use_nlac
            )
            _strategy_selector[selector_key] = selector
            mode_name = "NLaC" if use_nlac else "legacy DSPy"
            logger.info(f"StrategySelector initialized with {mode_name} mode")

    return _strategy_selector[selector_key]


@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest, http_request: Request):
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
    # Get settings
    # Note: Pydantic validators automatically handle:
    # - idea min_length validation (422 error)
    # - mode required validation (422 error)
    settings = container.get(Settings)

    # Use StrategySelector for intelligent strategy routing
    # NLaC mode is enabled when request.mode == "nlac"
    use_nlac = request.mode == "nlac"
    selector = await get_strategy_selector(settings, use_nlac=use_nlac)
    strategy = selector.select(request.idea, request.context)
    complexity = selector.get_complexity(request.idea, request.context)

    # Log strategy selection for observability
    logger.info(
        f"Mode: {request.mode} | Strategy: {strategy.name} | "
        f"Complexity: {complexity.value} | Idea: {len(request.idea)} chars"
    )

    # Start timer for latency
    start_time = time.time()

    # Improve prompt using selected strategy with timeout
    # 🔴 CRITICAL: Must match frontend timeout (120s) to prevent AbortError
    # See: dashboard/src/core/config/defaults.ts:58-80 for three-layer sync invariant
    STRATEGY_TIMEOUT_SECONDS = 120

    try:
        # Run synchronous strategy.improve in thread with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                strategy.improve,
                original_idea=request.idea,
                context=request.context
            ),
            timeout=STRATEGY_TIMEOUT_SECONDS
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Track metrics warnings for response metadata
        metrics_warnings = []

        # Calculate comprehensive metrics
        try:
            # Extract model and provider from settings
            model = settings.LLM_MODEL
            provider = settings.LLM_PROVIDER

            # Convert guardrails to list if it's a string
            guardrails_list = _normalize_guardrails(result.guardrails)

            # Extract confidence
            confidence_value = _extract_confidence(result)

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
                backend=strategy.name,  # Use strategy name instead of backend
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
                f"Metrics ({metrics_duration_ms}ms): "
                f"overall={metrics.overall_score:.2f} ({metrics.grade}), "
                f"quality={metrics.quality.composite_score:.2f}, "
                f"perf={metrics.performance.performance_score:.2f}"
            )

            # Store metrics if SQLite is enabled
            if settings.SQLITE_ENABLED:
                try:
                    metrics_repo = await get_repository(settings)
                    if metrics_repo and hasattr(metrics_repo, 'save'):
                        # Note: We need a metrics repository, not prompt repo
                        # For now, just log that we would save it
                        logger.debug(
                            "Metrics calculated (persistence to be implemented)"
                        )
                except (ConnectionError, OSError) as e:
                    metrics_warnings.append(f"Metrics persistence failed: {type(e).__name__}")
                    logger.error(f"Failed to save metrics: {type(e).__name__}: {e}")
                except (AttributeError, KeyError) as e:
                    metrics_warnings.append(f"Metrics data issue: {type(e).__name__}")
                    logger.warning(f"Metrics data structure issue: {type(e).__name__}: {e}")
        except (ValueError, TypeError, AttributeError) as e:
            # Expected errors from metrics calculation (invalid data types, missing attributes)
            metrics_warnings.append(f"Metrics calculation skipped: {type(e).__name__}")
            logger.warning(
                f"Metrics calculation skipped due to data issue: {type(e).__name__}: {e}"
            )
        except (ConnectionError, OSError) as e:
            # Connection/IO errors during metrics calculation
            metrics_warnings.append(f"Metrics calculation failed: {type(e).__name__}")
            logger.error(
                f"Metrics calculation failed: {type(e).__name__}: {e} | "
                f"strategy={strategy.name} | model={model}",
                exc_info=True
            )
        except (RuntimeError, MemoryError) as e:
            # Unexpected but recoverable errors
            metrics_warnings.append(f"Metrics calculation failed: {type(e).__name__}")
            logger.error(
                f"Metrics calculation failed: {type(e).__name__}: {e} | "
                f"strategy={strategy.name} | model={model}",
                exc_info=True
            )

        # Build response
        # Classify intent for response (used by tests)
        intent = _classify_intent(request.idea, request.context)

        prompt_id = _generate_stable_prompt_id(
            request.idea, request.context, request.mode
        )
        request_id = (
            getattr(http_request.state, "request_id", None)
            or prompt_id
        )
        persistence_failed = False

        history_task_coro = _save_history_async(
            settings=settings,
            original_idea=request.idea,
            context=request.context,
            result=result,
            backend=strategy.name,  # Use strategy name instead of backend
            latency_ms=latency_ms,
            mode=request.mode,
            request_id=request_id,
        )
        try:
            # Fire-and-forget persistence, never block request completion.
            asyncio.create_task(history_task_coro)
        except RuntimeError as e:
            # If scheduling fails, close coroutine to avoid unawaited warnings.
            history_task_coro.close()
            persistence_failed = True
            logger.warning(
                "event=persistence_failed reason=schedule_failed error_type=%s "
                "request_id=%s backend=%s mode=%s latency_ms=%s",
                type(e).__name__,
                request_id,
                strategy.name,
                request.mode,
                latency_ms,
            )

        response = ImprovePromptResponse(
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=_normalize_guardrails(result.guardrails),
            reasoning=getattr(result, "reasoning", None),
            confidence=_extract_confidence(result),
            backend=strategy.name,  # Use strategy name instead of backend
            prompt_id=prompt_id,
            strategy=strategy.name,
            intent=intent,
            strategy_meta={
                "complexity": complexity.value,
                "mode": request.mode,
                "strategy": strategy.name,
            },
            metrics_warning=metrics_warnings[0] if metrics_warnings else None,
            degradation_flags={
                DegradationFlag.METRICS_FAILED.value: len(metrics_warnings) > 0,
                DegradationFlag.KNN_DISABLED.value: selector.get_degradation_flags().get(
                    DegradationFlag.KNN_DISABLED.value, False
                ),
                DegradationFlag.COMPLEX_STRATEGY_DISABLED.value: (
                    selector.get_degradation_flags().get(
                        DegradationFlag.COMPLEX_STRATEGY_DISABLED.value, False
                    )
                ),
                DegradationFlag.PERSISTENCE_FAILED.value: persistence_failed,
            },
        )

        return response

    except asyncio.TimeoutError:
        logger.critical(
            f"Strategy {strategy.name} timed out after {STRATEGY_TIMEOUT_SECONDS}s | "
            f"idea_length: {len(request.idea)}"
        )
        raise HTTPException(
            status_code=504,  # Gateway Timeout
            detail="Prompt improvement took too long. Please try with a shorter prompt."
        ) from None
    except (ConnectionError, OSError) as e:
        logger.error(f"Connection/IO error during prompt improvement: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail="Service temporarily unavailable. Please try again."
        ) from None
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Invalid input or data error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=400,  # Bad Request
            detail=f"Invalid request: {type(e).__name__}"
        ) from None


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
        description=(
            "Template ID to use for evaluation. "
            "Must be one of: json, procedure_md, checklist_md, example_md."
        )
    )
    template_spec: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional template specification override. "
            "If not provided, uses DEFAULT_TEMPLATES."
        )
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
    overall_pass: bool = Field(
        description="Overall pass (v0.1 must pass AND v0.2 must have 0 FAILs)."
    )
    overall_status: str = Field(description="Overall status: PASS, WARN, or FAIL.")
    summary: str = Field(description="Human-readable summary of evaluation results.")
    gates: dict[str, dict[str, Any]] = Field(
        description="Complete gate results with details for each gate."
    )


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
        raise  # Global handler will convert to 500

    except KeyError as e:
        # Missing keys in output data - include the specific key name
        missing_key = str(e) if e else "unknown"
        logger.warning(
            f"Quality gate key error: KeyError | "
            f"template_id={request.template_id} | "
            f"missing_key={missing_key} | "
            f"output_length={len(request.output)}"
        )
        raise  # Global handler will convert to 400

    except (RuntimeError, MemoryError, AttributeError) as e:
        # Internal quality gate errors
        logger.error(
            f"Internal quality gate error: {type(e).__name__}: {e} | "
            f"template_id={request.template_id}",
            exc_info=True
        )
        raise  # Global handler will convert to 500

    # Let all other exceptions propagate (KeyboardInterrupt, SystemExit, etc.)


async def _save_history_async(
    settings: Settings,
    original_idea: str,
    context: str,
    result,
    backend: str,
    latency_ms: int,
    mode: str = "legacy",
    request_id: str | None = None,
):
    """
    Save prompt improvement history to SQLite with circuit breaker protection.

    Non-blocking async function that logs errors without failing the request.
    """
    repo = None
    success = False

    try:
        if not settings.SQLITE_ENABLED:
            logger.debug("Persistence disabled by configuration")
            return

        # Get repository with circuit breaker
        repo = await get_repository(settings)
        if repo is None:
            logger.warning(
                "event=persistence_failed reason=circuit_breaker_open "
                "request_id=%s backend=%s mode=%s latency_ms=%s",
                request_id or "unknown",
                backend,
                mode,
                latency_ms,
            )
            return

        # Extract model and provider from settings
        model = settings.LLM_MODEL
        provider = settings.LLM_PROVIDER

        # Convert guardrails to list if it's a string
        guardrails_list = _normalize_guardrails(result.guardrails)

        # Extract confidence score
        confidence_value = _extract_confidence(result)

        # Create PromptHistory entity
        framework_for_history, used_framework_fallback = normalize_framework_for_history(result.framework)
        if used_framework_fallback:
            logger.warning(
                "event=framework_normalization_fallback framework_raw=%r framework_normalized=%s",
                result.framework,
                framework_for_history,
            )
        history = PromptHistory(
            original_idea=original_idea,
            context=context,
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=framework_for_history,
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

    except (ConnectionError, OSError, TimeoutError) as e:
        # Record failure on circuit breaker
        await _circuit_breaker.record_failure()
        logger.error(
            "event=persistence_failed error_type=%s request_id=%s backend=%s mode=%s "
            "latency_ms=%s error=%s",
            type(e).__name__,
            request_id or "unknown",
            backend,
            mode,
            latency_ms,
            str(e),
        )
    except (ValueError, KeyError, TypeError) as e:
        # Record failure on circuit breaker
        await _circuit_breaker.record_failure()
        logger.warning(
            "event=persistence_failed error_type=%s request_id=%s backend=%s mode=%s "
            "latency_ms=%s error=%s",
            type(e).__name__,
            request_id or "unknown",
            backend,
            mode,
            latency_ms,
            str(e),
        )
    # Let unexpected errors propagate - don't silently swallow them

    finally:
        # Record success OUTSIDE try-except to prevent paradox
        if success:
            await _circuit_breaker.record_success()
