"""
Prompt History Entity - Domain entity for prompt improvement events.

Immutable value object following Domain-Driven Design principles.
Represents a single prompt improvement event with full audit trail.
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PromptHistory:
    """
    Domain entity representing a prompt improvement event.

    Immutable value object following Domain-Driven Design principles.
    All validation happens in __post_init__ to enforce business invariants.
    """

    # Input fields
    original_idea: str
    context: str

    # Output fields
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]

    # Metadata
    backend: str  # "zero-shot" | "few-shot"
    model: str
    provider: str

    # Optional fields with defaults
    reasoning: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    created_at: str | None = None

    def __post_init__(self):
        """Validate business invariants."""
        # Validate framework is allowed value (with fallback)
        allowed_frameworks = {
            "chain-of-thought",
            "tree-of-thoughts",
            "decomposition",
            "role-playing"
        }
        if self.framework not in allowed_frameworks:
            logger.warning(
                f"Unknown framework '{self.framework}', "
                f"defaulting to 'chain-of-thought'"
            )
            object.__setattr__(self, 'framework', 'chain-of-thought')

        # Validate confidence range
        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

        # Validate latency is non-negative
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError(f"Latency must be >= 0, got {self.latency_ms}")

        # Validate non-empty inputs
        if not self.original_idea or not self.original_idea.strip():
            raise ValueError("original_idea cannot be empty")

        if not self.improved_prompt or not self.improved_prompt.strip():
            raise ValueError("improved_prompt cannot be empty")

        # Validate guardrails is not empty
        if not self.guardrails:
            raise ValueError("guardrails cannot be empty")

        # Set created_at if not provided
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.now(UTC).isoformat())

    @property
    def quality_score(self) -> float:
        """Calculate composite quality score (0-1)."""
        conf_score = self.confidence or 0.5
        latency_penalty = min((self.latency_ms or 0) / 10000, 0.3)
        return max(0.0, min(1.0, conf_score - latency_penalty))
