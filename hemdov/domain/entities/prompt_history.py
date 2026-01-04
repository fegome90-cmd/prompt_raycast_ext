# hemdov/domain/entities/prompt_history.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    latency_ms: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        """Validate business invariants."""
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
            object.__setattr__(self, 'created_at', datetime.utcnow().isoformat())

    @property
    def quality_score(self) -> float:
        """Calculate composite quality score (0-1)."""
        conf_score = self.confidence or 0.5
        latency_penalty = min((self.latency_ms or 0) / 10000, 0.3)
        return max(0.0, min(1.0, conf_score - latency_penalty))
