"""
NLaC (Natural Language as Code) API Models.

Pydantic models for the NLaC feature - treating prompts as structured
executable objects rather than plain strings.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Dict, Any, NotRequired, TypedDict
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class IntentType(str, Enum):
    """Intent classification for prompt routing."""
    GENERATE = "generate"
    DEBUG = "debug"
    REFACTOR = "refactor"
    EXPLAIN = "explain"


class TestType(str, Enum):
    """Test case types."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"


# ============================================================================
# TypedDict Definitions (Type-safe dictionaries)
# ============================================================================

class StrategyMetadata(TypedDict):
    """
    Type-safe dictionary for strategy metadata.

    Expected keys:
        strategy: str - Selected strategy name (simple_debug, moderate_debug, etc.)
        intent: str - Intent classification (debug, refactor, generate, explain)
        complexity: str - Complexity level (simple, moderate, complex)
        knn_enabled: bool - Whether KNN few-shot was used
        fewshot_count: int - Number of few-shot examples injected
        rar_used: bool - Whether RaR (Rephrase and Respond) was used
        role: str - Role assigned to the AI
        directive: NotRequired[str] - Primary directive/instruction (optional)
        framework: NotRequired[str] - Framework or methodology used (optional)
        guardrails: NotRequired[list[str]] - Guardrails/constraints (optional)
    """
    strategy: str
    intent: str
    complexity: str
    knn_enabled: bool
    fewshot_count: int
    rar_used: bool
    role: str
    directive: NotRequired[str]
    framework: NotRequired[str]
    guardrails: NotRequired[list[str]]


class PromptConstraints(TypedDict):
    """
    Type-safe dictionary for prompt constraints.

    Expected keys:
        max_tokens: Maximum tokens in response
        format: Required output format (e.g., "code in Python")
        include_examples: Whether to include examples in response
        include_explanation: Whether to include explanation
    """
    max_tokens: int
    format: NotRequired[str]
    include_examples: NotRequired[bool]
    include_explanation: NotRequired[bool]


# ============================================================================
# Input Models
# ============================================================================

class NLaCInputs(BaseModel):
    """
    Optional structured inputs for intent classification and routing.

    All fields are optional to maintain backward compatibility with
    simple text-based prompts.
    """
    code_snippet: Optional[str] = Field(
        None,
        description="Code snippet for debugging/refactoring"
    )
    error_log: Optional[str] = Field(
        None,
        description="Error message or stack trace"
    )
    target_language: Optional[str] = Field(
        None,
        description="Target programming language"
    )
    target_framework: Optional[str] = Field(
        None,
        description="Target framework (e.g., React, FastAPI)"
    )
    context_files: Optional[list[str]] = Field(
        default_factory=list,
        description="Related file paths for context"
    )

    @field_validator("context_files", mode="before")
    @classmethod
    def validate_context_files(cls, v):
        """Ensure non-empty strings in context_files, filter None and empty values."""
        if v is None:
            return []
        return [f for f in v if isinstance(f, str) and f and f.strip()]


class NLaCRequest(BaseModel):
    """
    Main request model for NLaC API.

    Extends the existing prompt improvement API with:
    - Structured inputs for intent classification
    - Mode selector (legacy vs NLaC)
    - Optional optimization settings
    """
    idea: str = Field(..., description="User's raw idea or prompt text")
    context: str = Field(
        default="",
        max_length=5000,
        description="Additional context or requirements (max 5000 chars)"
    )
    inputs: Optional[NLaCInputs] = Field(
        default=None,
        description="Structured inputs for intent classification"
    )
    mode: Literal["legacy", "nlac"] = Field(
        default="legacy",
        description="API mode: legacy (Strategy Pattern) or nlac (NLaC optimization)"
    )

    # OPRO optimization settings (only used in nlac mode)
    enable_optimization: bool = Field(
        default=False,
        description="Enable OPRO iterative optimization"
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Max OPRO iterations (1-5)"
    )
    target_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Target quality score (0-1), stops early if reached"
    )

    @field_validator("idea")
    @classmethod
    def validate_idea(cls, v):
        """Ensure idea is not empty."""
        if not v or not v.strip():
            raise ValueError("idea cannot be empty")
        return v.strip()

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v):
        """Limit max iterations to prevent excessive LLM calls."""
        if v > 5:
            raise ValueError("max_iterations cannot exceed 5 (budget limit)")
        return v


# ============================================================================
# Domain Models
# ============================================================================

class PromptObject(BaseModel):
    """
    Structured prompt representation (NLaC core concept).

    A PromptObject is a structured, executable representation of a prompt
    with metadata, constraints, and versioning - not just a string.
    """
    id: str = Field(..., description="UUID v4 identifier")
    version: str = Field(default="1.0.0", description="Semantic version")
    intent_type: IntentType = Field(..., description="Classified intent")

    # Core template (the actual prompt template)
    template: str = Field(..., description="Prompt template with placeholders")

    # Strategy metadata (should conform to StrategyMetadata TypedDict)
    strategy_meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy used, complexity, routing decisions. Expected to conform to StrategyMetadata TypedDict."
    )

    # Constraints (should conform to PromptConstraints TypedDict)
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Constraints like max_tokens, format requirements, etc. Expected to conform to PromptConstraints TypedDict."
    )

    # Metadata
    is_active: bool = Field(default=True, description="Whether this version is active")
    created_at: str = Field(..., description="ISO timestamp")
    updated_at: str = Field(..., description="ISO timestamp")

    # KNN failure tracking (for monitoring and debugging)
    knn_failed: bool = Field(default=False, description="Whether KNN provider failed to fetch examples")
    knn_error: Optional[str] = Field(None, description="Error message if KNN failed")

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Ensure template is not empty."""
        if not v or not v.strip():
            raise ValueError("template cannot be empty")
        return v

    @field_validator("strategy_meta", "constraints", mode="before")
    @classmethod
    def validate_metadata(cls, v):
        """Ensure metadata is a dict, convert None to {}."""
        if v is None:
            return {}
        return v


class OPROIteration(BaseModel):
    """Single OPRO optimization iteration result."""
    iteration_number: int = Field(..., ge=1, description="Iteration number (1-indexed)")
    meta_prompt_used: str = Field(..., description="Meta-prompt template used")
    generated_instruction: str = Field(..., description="Generated instruction")
    score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0-1)")
    feedback: Optional[str] = Field(None, description="Feedback for next iteration")


class OptimizeResponse(BaseModel):
    """
    Response model for OPRO optimization process.

    Contains the final optimized prompt and full trajectory history.
    """
    prompt_id: str = Field(..., description="PromptObject UUID")
    final_instruction: str = Field(..., description="Final optimized instruction")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final quality score")
    iteration_count: int = Field(..., ge=1, description="Total iterations executed")
    early_stopped: bool = Field(default=False, description="Stopped early due to target score")
    trajectory: list[OPROIteration] = Field(
        default_factory=list,
        description="Full optimization trajectory"
    )

    # Optional improved prompt (full rendered result)
    improved_prompt: Optional[str] = Field(None, description="Rendered improved prompt")

    # Timing and metadata
    total_latency_ms: Optional[int] = Field(None, description="Total optimization time")
    backend: str = Field(default="nlac", description="Backend identifier")
    model: Optional[str] = Field(None, description="Model used for optimization")


# ============================================================================
# Response Models (Extended)
# ============================================================================

class NLaCResponse(BaseModel):
    """
    Complete response for NLaC API requests.

    Extends the legacy ImprovePromptResponse with NLaC-specific fields.
    """
    # Core fields (compatible with legacy)
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    backend: str = "nlac"

    # NLaC-specific fields
    prompt_object: Optional[PromptObject] = Field(
        None,
        description="Structured PromptObject (only in nlac mode)"
    )
    optimization_result: Optional[OptimizeResponse] = Field(
        None,
        description="OPRO optimization result (if enable_optimization=True)"
    )
    intent_type: Optional[IntentType] = Field(
        None,
        description="Classified intent (only in nlac mode)"
    )
    cache_hit: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )

    # KNN failure tracking
    knn_failure: Optional[Dict[str, Any]] = Field(
        None,
        description="KNN failure metadata if few-shot examples were unavailable"
    )
