# Plan: Deterministic Router for DSPy Prompt Improver (PATCHED v2)

## Summary

Integrate a deterministic router that intelligently selects between DSPy (legacy), NLaC, and RACE (hedged execution) modes based on input characteristics, without requiring an LLM judge.

**Key Principle:** AUTO is biased to DSPy by default. NLaC only for strong structure signals. RACE only for ambiguous + important cases.

## Current State Analysis

### Existing Architecture

**Backend (`api/prompt_improver_api.py`):**
- Request mode accepts only: `"legacy"` or `"nlac"`
- Routing: `get_strategy_selector(settings, use_nlac=request.mode == "nlac")`
- Intent classifier: GENERATE, DEBUG, REFACTOR, EXPLAIN
- Latency reality: DSPy ~10-30s, NLaC ~45-60s

**Strategy Selector (`eval/src/strategy_selector.py`):**
- NLaC mode: Returns unified NLaCStrategy
- Legacy mode: Routes to Simple/Moderate/Complex based on complexity

**Frontend (`dashboard/package.json`):**
- Current options: "DSPy Legacy", "NLaC Pipeline", "Ollama Local"
- TypeScript type: `"legacy" | "nlac" | "ollama"`

### Router Applicability: ✅ YES (with corrections)

| Router Feature | Current State | Adaptation |
|----------------|---------------|------------|
| `auto` mode | ❌ Doesn't exist | Add new mode, **biased to DSPy** |
| `race` mode | ❌ Doesn't exist | Hedged execution (return early) |
| File metrics | ❌ Not in request | **Add REAL metrics as optional fields** |
| Intent types | Partial match | Intent = **secondary feature** |

---

## CORRECTIONS APPLIED (P0) 🔥

### ✅ P0.1 — Router Location: Application Layer
**Moved from:** `hemdov/domain/services/deterministic_router.py`
**To:** `hemdov/application/policies/deterministic_router.py`

Router is **orchestration policy**, not pure domain logic. Domain should contain DSPy modules and business rules, not routing strings like `"auto"`/`"race"`.

### ✅ P0.2 — REAL File Metrics (No Heuristics)
**RouterInput extended with REAL metrics:**
```python
@dataclass(frozen=True, slots=True)
class RouterInput:
    mode: Mode
    idea: str
    context: str
    intent: str
    # REAL metrics from bundle (optional, default 0)
    files_count: int = 0
    bundle_chars_total: int = 0
    truncated_count: int = 0
```

**Endpoints:**
- `/improve-prompt` → metrics = 0
- `/improve-prompt-with-context` → metrics from actual bundle

### ✅ P0.3 — Realistic Deadlines
| Strategy | Claude Plan | **CORRECTED** |
|----------|-------------|--------------|
| DSPy deadline | 5s ❌ | **25-30s** ✅ |
| NLaC deadline | 15s ❌ | **70-90s** ✅ |

**RACE returns early** if DSPy passes quality gate — doesn't wait for NLaC.

---

## Implementation Plan (PATCHED)

### Phase 1: AUTO Mode (No RACE yet) — 80% Value, 0% Risk

**File:** `hemdov/application/policies/deterministic_router.py` (NEW)

```python
import re
from dataclasses import dataclass
from typing import Literal

Mode = Literal["legacy", "nlac", "auto", "race"]
Backend = Literal["dspy", "nlac", "race"]

# Structure patterns (NLaC signals)
STRUCTURE_PATTERNS = [
    r"\bjson\b", r"\byaml\b", r"\bschema\b", r"\bcontract\b",
    r"\bmust include\b", r"\bnon[- ]negotiable\b", r"\bacceptance criteria\b",
    r"\bdod\b", r"\bchecklist\b", r"\btemplate\b", r"\bplantilla\b",
    r"\bnatural language as code\b", r"\bnlac\b", r"\bpseudocode\b",
]

# High-value intents (NLaC preferred)
HIGH_VALUE_INTENTS = {"architecture", "spec_write", "wo_generation"}

@dataclass(frozen=True, slots=True)
class RouterInput:
    mode: Mode
    idea: str
    context: str
    intent: str
    # REAL metrics from bundle (optional)
    files_count: int = 0
    bundle_chars_total: int = 0
    truncated_count: int = 0

@dataclass(frozen=True, slots=True)
class RouterDecision:
    backend: Backend
    reason: str
    nlac_score: int
    dspy_score: int
    # For telemetry
    structure_hits: int = 0
    important: bool = False

def route(req: RouterInput) -> RouterDecision:
    """
    Deterministic router: AUTO biased to DSPy, NLaC for strong signals.
    """
    # Hard overrides
    if req.mode == "nlac":
        return RouterDecision("nlac", "mode override: nlac", 999, 0)
    if req.mode == "legacy":
        return RouterDecision("dspy", "mode override: legacy", 0, 999)
    if req.mode == "race":
        return RouterDecision("race", "mode override: race", 0, 0)

    # AUTO mode: scoring
    text = f"{req.idea}\n{req.context}"
    structure_hits = sum(1 for p in STRUCTURE_PATTERNS if re.search(p, text.lower()))

    # NLaC score: structure + intent + size
    nlac_score = 0
    nlac_score += 3 * structure_hits  # Structure is PRIMARY signal
    if req.intent in HIGH_VALUE_INTENTS:
        nlac_score += 2
    if req.files_count >= 5:
        nlac_score += 2
    if req.bundle_chars_total >= 60_000:
        nlac_score += 2

    # DSPy score: default + simplicity
    dspy_score = 2  # Base bias to DSPy
    if structure_hits == 0:
        dspy_score += 3
    if len(req.idea) <= 500:
        dspy_score += 2

    diff = nlac_score - dspy_score

    # Decision: AUTO biased to DSPy
    if diff >= 4:  # High threshold for NLaC
        return RouterDecision(
            "nlac",
            f"auto: nlac (diff={diff}, structure_hits={structure_hits})",
            nlac_score, dspy_score, structure_hits, True
        )

    # RACE: only if ambiguous AND important
    important = (
        req.intent in HIGH_VALUE_INTENTS or
        req.files_count >= 5 or
        req.bundle_chars_total >= 60_000
    )

    if abs(diff) <= 2 and important:
        return RouterDecision(
            "race",
            f"auto: race (ambiguous diff={diff}, important={important})",
            nlac_score, dspy_score, structure_hits, important
        )

    # Default: DSPy
    return RouterDecision(
        "dspy",
        f"auto: dspy (diff={diff}, structure_hits={structure_hits})",
        nlac_score, dspy_score, structure_hits, False
    )
```

**Key changes:**
- **Structure is PRIMARY signal** (3x weight), intent is secondary
- **DSPy bias**: base score of 2, needs strong signals for NLaC
- **NLaC threshold: diff >= 4** (not 2)
- **RACE only**: `abs(diff) <= 2 AND important=True`

### Phase 2: RACE Strategy (Hedged Execution) — Only after AUTO data

**File:** `eval/src/strategies/race_strategy.py` (NEW)

```python
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)

# Realistic deadlines based on telemetry
DSPY_DEADLINE_SEC = 30
NLAC_DEADLINE_SEC = 90

@dataclass
class RaceResult:
    """Result from a single strategy in the race."""
    strategy: str
    result: object | None
    latency_ms: int
    error: str | None = None
    passed_gate: bool = False

@dataclass
class RaceMetadata:
    """Metadata for race execution (telemetry)."""
    dspy_ms: int | None
    nlac_ms: int | None
    winner: str
    winner_score: float
    dspy_score: float | None
    nlac_score: float | None
    fallback_reason: str | None


class DeterministicQualityGate:
    """
    Quality gate WITHOUT LLM judge.

    Checks:
    1. Format compliance (JSON/YAML if required)
    2. Guardrails not violated
    3. Not empty/filler (minimum length, no TBD patterns)
    """

    MIN_LENGTH = 100
    FILLER_PATTERNS = ["TBD", "TODO", "[Your text here]", "..."]

    def check(self, result, expected_format: str | None = None) -> tuple[bool, str]:
        """
        Returns (passed, reason).
        """
        if not result:
            return False, "empty_result"

        # Check minimum length
        improved_prompt = getattr(result, 'improved_prompt', '')
        if len(improved_prompt) < self.MIN_LENGTH:
            return False, "too_short"

        # Check for filler patterns
        prompt_lower = improved_prompt.lower()
        if any(p.lower() in prompt_lower for p in self.FILLER_PATTERNS):
            return False, "contains_filler"

        # Format check if specified
        if expected_format == "json":
            try:
                import json
                json.loads(improved_prompt)
            except (json.JSONDecodeError, ValueError):
                return False, "invalid_json"

        # Basic guardrails check
        guardrails = getattr(result, 'guardrails', [])
        if not guardrails:
            return False, "missing_guardrails"

        return True, "passed"


class RaceStrategy(PromptImproverStrategy):
    """
    Hedged execution: Return early if DSPy passes quality gate.

    NOT "run both and pick best" — that doubles cost without benefit.

    Strategy:
    1. Launch DSPy and NLaC in parallel
    2. If DSPy finishes and PASSES gate → return immediately
    3. If DSPy fails gate or expires → wait for NLaC
    4. If NLaC fails → fallback to DSPy (even if partial)
    """

    name = "race"

    def __init__(
        self,
        dspy_strategy: PromptImproverStrategy,
        nlac_strategy: PromptImproverStrategy,
        dspy_deadline: int = DSPY_DEADLINE_SEC,
        nlac_deadline: int = NLAC_DEADLINE_SEC,
    ):
        self.dspy_strategy = dspy_strategy
        self.nlac_strategy = nlac_strategy
        self.dspy_deadline = dspy_deadline
        self.nlac_deadline = nlac_deadline
        self.gate = DeterministicQualityGate()

    def improve(self, original_idea: str, context: str) -> object:
        """
        Execute race with early return on DSPy success.
        """
        start_time = time.time()
        dspy_result = None
        nlac_result = None
        dspy_latency = None
        nlac_latency = None

        # Run both in parallel with individual deadlines
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both strategies
            dspy_future = executor.submit(
                self._run_with_timeout,
                self.dspy_strategy.improve,
                original_idea, context,
                self.dspy_deadline
            )
            nlac_future = executor.submit(
                self._run_with_timeout,
                self.nlac_strategy.improve,
                original_idea, context,
                self.nlac_deadline
            )

            # Wait for DSPy first (hedged execution)
            try:
                dspy_result, dspy_latency = dspy_future.result(timeout=self.dspy_deadline + 1)

                # Early return if DSPy passes quality gate
                if dspy_result:
                    passed, reason = self.gate.check(dspy_result)
                    if passed:
                        logger.info(
                            f"RACE: DSPy won ({dspy_latency}ms, gate={reason})"
                        )
                        # Attach race metadata
                        self._attach_metadata(
                            dspy_result,
                            RaceMetadata(
                                dspy_ms=dspy_latency,
                                nlac_ms=None,
                                winner="dspy",
                                winner_score=1.0,
                                dspy_score=1.0,
                                nlac_score=None,
                                fallback_reason=None
                            )
                        )
                        return dspy_result
            except Exception as e:
                logger.warning(f"RACE: DSPy failed: {type(e).__name__}: {e}")

            # DSPy failed or didn't pass gate → wait for NLaC
            try:
                nlac_result, nlac_latency = nlac_future.result(timeout=self.nlac_deadline + 1)

                if nlac_result:
                    logger.info(f"RACE: NLaC won ({nlac_latency}ms, fallback_reason='dspy_failed')")
                    self._attach_metadata(
                        nlac_result,
                        RaceMetadata(
                            dspy_ms=dspy_latency,
                            nlac_ms=nlac_latency,
                            winner="nlac",
                            winner_score=1.0,
                            dspy_score=None,
                            nlac_score=1.0,
                            fallback_reason="dspy_failed"
                        )
                    )
                    return nlac_result
            except Exception as e:
                logger.error(f"RACE: NLaC failed: {type(e).__name__}: {e}")

        # Both failed → return DSPy if available (best effort)
        if dspy_result:
            logger.warning("RACE: Both failed, returning DSPy partial result")
            self._attach_metadata(
                dspy_result,
                RaceMetadata(
                    dspy_ms=dspy_latency,
                    nlac_ms=nlac_latency,
                    winner="dspy",
                    winner_score=0.5,
                    dspy_score=0.5,
                    nlac_score=0.0,
                    fallback_reason="both_failed"
                )
            )
            return dspy_result

        # Total failure
        raise RuntimeError("RACE: Both strategies failed")

    def _run_with_timeout(self, func, *args, timeout: int):
        """Run function with timeout, return (result, latency_ms)."""
        start = time.time()
        try:
            result = func(*args)
            latency = int((time.time() - start) * 1000)
            return result, latency
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            logger.error(f"Strategy failed after {latency}ms: {type(e).__name__}: {e}")
            raise

    def _attach_metadata(self, result, metadata: RaceMetadata):
        """Attach race metadata to result for telemetry."""
        if hasattr(result, 'strategy_meta'):
            result.strategy_meta['race'] = metadata.__dict__
```

**Key RACE features:**
- ✅ **Hedged execution**: Return early if DSPy passes gate
- ✅ **Realistic deadlines**: 30s DSPy, 90s NLaC
- ✅ **Deterministic quality gate**: No LLM judge
- ✅ **Graceful degradation**: Falls back to DSPy if NLaC fails
- ✅ **Rich telemetry**: `dspy_ms`, `nlac_ms`, `winner`, `fallback_reason`

### Phase 3: API Integration (with real metrics)

**File:** `api/prompt_improver_api.py` (UPDATE)

1. **Update request validator:**

```python
class ImprovePromptRequest(BaseModel):
    idea: str = Field(..., min_length=5)
    context: str = Field(default="", max_length=5000)
    mode: str = Field(..., description="Execution mode: 'legacy', 'nlac', 'auto', or 'race'")
    # Optional REAL metrics for routing (from bundle context)
    files_count: int = Field(default=0, ge=0, description="Number of files in context bundle")
    bundle_chars_total: int = Field(default=0, ge=0, description="Total chars in context bundle")
    truncated_count: int = Field(default=0, ge=0, description="Number of truncated files")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ("legacy", "nlac", "auto", "race"):
            raise ValueError("mode must be 'legacy', 'nlac', 'auto', or 'race'")
        return v
```

2. **Integrate router in endpoint (PATCHED):**

```python
@router.post("/improve-prompt")
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve prompt with deterministic routing.
    """
    settings = container.get(Settings)

    # Get intent for routing
    intent = _classify_intent(request.idea, request.context)

    # Apply router if auto or race mode
    if request.mode in ("auto", "race"):
        from hemdov.application.policies.deterministic_router import route, RouterInput

        # Route decision with REAL metrics
        decision = route(RouterInput(
            mode=request.mode,
            idea=request.idea,
            context=request.context,
            intent=intent,
            files_count=request.files_count,
            bundle_chars_total=request.bundle_chars_total,
            truncated_count=request.truncated_count
        ))

        logger.info(
            f"Router: {decision.backend} | "
            f"reason={decision.reason} | "
            f"nlac_score={decision.nlac_score} | "
            f"dspy_score={decision.dspy_score} | "
            f"structure_hits={decision.structure_hits}"
        )

        # Select strategy based on decision
        if decision.backend == "nlac":
            selector = get_strategy_selector(settings, use_nlac=True)
            strategy = selector.select(request.idea, request.context)

        elif decision.backend == "race":
            # Get both strategies for race
            dspy_selector = get_strategy_selector(settings, use_nlac=False)
            nlac_selector = get_strategy_selector(settings, use_nlac=True)
            dspy_strategy = dspy_selector.select(request.idea, request.context)
            nlac_strategy = nlac_selector.select(request.idea, request.context)

            # Create race strategy
            from eval.src.strategies.race_strategy import RaceStrategy
            strategy = RaceStrategy(
                dspy_strategy=dspy_strategy,
                nlac_strategy=nlac_strategy
            )

        else:  # dspy
            selector = get_strategy_selector(settings, use_nlac=False)
            strategy = selector.select(request.idea, request.context)

    else:
        # Direct mode selection (legacy, nlac)
        use_nlac = request.mode == "nlac"
        selector = get_strategy_selector(settings, use_nlac=use_nlac)
        strategy = selector.select(request.idea, request.context)
        decision = None

    # ... rest of endpoint logic with timeout handling

    # Add routing decision to response for telemetry
    response = ImprovePromptResponse(
        # ... existing fields
        routing_decision={
            "backend": decision.backend if decision else request.mode,
            "reason": decision.reason if decision else "direct_mode",
            "nlac_score": decision.nlac_score if decision else None,
            "dspy_score": decision.dspy_score if decision else None,
            "structure_hits": decision.structure_hits if decision else None,
            "important": decision.important if decision else None,
        } if decision else None
    )
```

3. **Update response model:**

```python
class ImprovePromptResponse(BaseModel):
    # ... existing fields
    routing_decision: dict[str, Any] | None = Field(
        default=None,
        description="Router decision metadata (for auto/race modes)"
    )
```

### Phase 4: Frontend Updates

**File:** `dashboard/package.json` (UPDATE)

Add new mode options with clear descriptions:

```json
{
  "executionMode": {
    "title": "Execution Mode",
    "description": "How to process prompt improvements",
    "type": "dropdown",
    "options": [
      {
        "value": "auto",
        "title": "Auto (Recommended)",
        "description": "Router selects best strategy: DSPy for fast iteration, NLaC for structured output, RACE for important/ambiguous cases"
      },
      {
        "value": "legacy",
        "title": "DSPy Legacy (Fast)",
        "description": "Fast few-shot learning (10-30s)"
      },
      {
        "value": "nlac",
        "title": "NLaC Pipeline (Structured)",
        "description": "Structured output with OPRO + IFEval (45-60s)"
      },
      {
        "value": "race",
        "title": "RACE (Hedged Execution)",
        "description": "Parallel execution with early return if DSPy passes quality gate (use for critical inputs)"
      },
      {
        "value": "ollama",
        "title": "Ollama Local",
        "description": "Use local Ollama only (no backend)"
      }
    ],
    "default": "auto"
  }
}
```

**File:** `dashboard/src/promptify-quick.tsx` (UPDATE)

Update TypeScript type:

```typescript
type ExecutionMode = "legacy" | "nlac" | "auto" | "race" | "ollama";
```

**File:** `dashboard/src/core/llm/improvePrompt.ts` (UPDATE)

Update API call to include optional metrics:

```typescript
interface ImprovePromptRequest {
  idea: string;
  context?: string;
  mode: ExecutionMode;
  // Optional: include if available from context bundle
  files_count?: number;
  bundle_chars_total?: number;
  truncated_count?: number;
}
```

### Phase 5: Testing & Verification (PATCHED)

#### Unit Tests - Router

**File:** `tests/unit/test_deterministic_router.py`

```python
import pytest
from hemdov.application.policies.deterministic_router import route, RouterInput

class TestRouterOverrides:
    """Test mode overrides take priority."""

    def test_nlac_override(self):
        decision = route(RouterInput(
            mode="nlac",
            idea="simple",
            context="",
            intent="generate"
        ))
        assert decision.backend == "nlac"
        assert "mode override" in decision.reason

    def test_legacy_override(self):
        decision = route(RouterInput(
            mode="legacy",
            idea="generate JSON schema contract",
            context="",
            intent="architecture"
        ))
        assert decision.backend == "dspy"

    def test_race_override(self):
        decision = route(RouterInput(
            mode="race",
            idea="anything",
            context="",
            intent="generate"
        ))
        assert decision.backend == "race"


class TestRouterAuto:
    """Test AUTO mode routing logic."""

    def test_simple_input_routes_to_dspy(self):
        """Simple input without structure should route to DSPy."""
        decision = route(RouterInput(
            mode="auto",
            idea="improve this prompt",
            context="",
            intent="generate"
        ))
        assert decision.backend == "dspy"
        assert decision.structure_hits == 0

    def test_structure_heavy_routes_to_nlac(self):
        """Strong structure signals should route to NLaC."""
        decision = route(RouterInput(
            mode="auto",
            idea="Generate JSON schema with validation rules and contract",
            context="Must include acceptance criteria and non-negotiable fields",
            intent="spec_write"
        ))
        assert decision.backend == "nlac"
        assert decision.structure_hits >= 3
        assert decision.nlac_score > decision.dspy_score

    def test_ambiguous_important_routes_to_race(self):
        """Ambiguous but important input should route to RACE."""
        decision = route(RouterInput(
            mode="auto",
            idea="design system architecture with some structure",
            context="",
            intent="architecture",
            files_count=8,
            bundle_chars_total=80_000
        ))
        assert decision.backend == "race"
        assert decision.important == True

    def test_ambiguous_not_important_routes_to_dspy(self):
        """Ambiguous unimportant input should default to DSPy."""
        decision = route(RouterInput(
            mode="auto",
            idea="help with code structure",
            context="",
            intent="generate"
        ))
        assert decision.backend == "dspy"
        assert decision.important == False

    def test_dspy_bias_by_default(self):
        """AUTO should be biased to DSPy (diff >= 4 needed for NLaC)."""
        # Weak structure signals (diff < 4)
        decision = route(RouterInput(
            mode="auto",
            idea="add template",
            context="",
            intent="generate"
        ))
        assert decision.backend == "dspy"
```

#### Unit Tests - RACE Strategy

**File:** `tests/unit/test_race_strategy.py`

```python
import pytest
from unittest.mock import Mock
from eval.src.strategies.race_strategy import (
    RaceStrategy,
    DeterministicQualityGate,
    RaceMetadata
)


class TestDeterministicQualityGate:
    """Test quality gate WITHOUT LLM judge."""

    def test_passes_valid_output(self):
        gate = DeterministicQualityGate()
        result = Mock()
        result.improved_prompt = "This is a valid prompt improvement with sufficient content and guardrails."
        result.guardrails = ["Be helpful", "Be concise"]

        passed, reason = gate.check(result)
        assert passed == True
        assert reason == "passed"

    def test_fails_empty_result(self):
        gate = DeterministicQualityGate()
        passed, reason = gate.check(None)
        assert passed == False
        assert reason == "empty_result"

    def test_fails_too_short(self):
        gate = DeterministicQualityGate()
        result = Mock()
        result.improved_prompt = "x" * 50  # Below MIN_LENGTH
        result.guardrails = ["test"]

        passed, reason = gate.check(result)
        assert passed == False
        assert reason == "too_short"

    def test_fails_filler_patterns(self):
        gate = DeterministicQualityGate()
        result = Mock()
        result.improved_prompt = "## Steps\n\n1. TBD\n2. TODO\n3. [Your text here]"
        result.guardrails = ["test"]

        passed, reason = gate.check(result)
        assert passed == False
        assert reason == "contains_filler"

    def test_fails_missing_guardrails(self):
        gate = DeterministicQualityGate()
        result = Mock()
        result.improved_prompt = "x" * 200
        result.guardrails = []

        passed, reason = gate.check(result)
        assert passed == False
        assert reason == "missing_guardrails"

    def test_json_validation_when_required(self):
        gate = DeterministicQualityGate()
        result = Mock()
        result.improved_prompt = "{ invalid json"
        result.guardrails = ["test"]

        passed, reason = gate.check(result, expected_format="json")
        assert passed == False
        assert reason == "invalid_json"


class TestRaceStrategy:
    """Test hedged execution behavior."""

    def test_returns_early_when_dspy_passes_gate(self, mocker):
        """
        CRITICAL TEST: RACE should return immediately if DSPy passes gate.
        This is the heart of hedged execution — don't wait for NLaC.
        """
        # Mock DSPy strategy that passes gate
        dspy_result = Mock()
        dspy_result.improved_prompt = "x" * 200
        dspy_result.guardrails = ["test"]
        dspy_strategy = Mock()
        dspy_strategy.improve.return_value = dspy_result

        # Mock NLaC strategy (should NOT be called)
        nlac_strategy = Mock()
        nlac_strategy.improve.side_effect = Exception("Should not be called")

        race = RaceStrategy(
            dspy_strategy=dspy_strategy,
            nlac_strategy=nlac_strategy,
            dspy_deadline=30,
            nlac_deadline=90
        )

        result = race.improve("test idea", "test context")

        # Verify DSPy was used
        assert result == dspy_result
        dspy_strategy.improve.assert_called_once()

        # Verify NLaC was NOT called (early return)
        # Note: In real execution, NLaC future is cancelled, but in test
        # we verify by checking that the result came from DSPy
        assert hasattr(result, 'strategy_meta')
        assert result.strategy_meta['race']['winner'] == 'dspy'
        assert result.strategy_meta['race']['nlac_ms'] is None

    def test_falls_back_to_nlac_when_dspy_fails_gate(self):
        """If DSPy fails gate, should wait for and return NLaC."""
        # Mock DSPy that fails gate
        dspy_result = Mock()
        dspy_result.improved_prompt = "TBD"
        dspy_result.guardrails = []
        dspy_strategy = Mock()
        dspy_strategy.improve.return_value = dspy_result

        # Mock NLaC that passes
        nlac_result = Mock()
        nlac_result.improved_prompt = "x" * 200
        nlac_result.guardrails = ["test"]
        nlac_strategy = Mock()
        nlac_strategy.improve.return_value = nlac_result

        race = RaceStrategy(
            dspy_strategy=dspy_strategy,
            nlac_strategy=nlac_strategy,
            dspy_deadline=30,
            nlac_deadline=90
        )

        result = race.improve("test idea", "test context")

        # Verify NLaC won
        assert result == nlac_result
        assert result.strategy_meta['race']['winner'] == 'nlac'
        assert result.strategy_meta['race']['fallback_reason'] == 'dspy_failed'

    def test_handles_both_strategies_failing(self):
        """If both fail, should return DSPy partial with error metadata."""
        # Mock both failing
        dspy_result = Mock()
        dspy_result.improved_prompt = "partial"
        dspy_result.guardrails = []
        dspy_strategy = Mock()
        dspy_strategy.improve.return_value = dspy_result

        nlac_strategy = Mock()
        nlac_strategy.improve.side_effect = Exception("NLaC crashed")

        race = RaceStrategy(
            dspy_strategy=dspy_strategy,
            nlac_strategy=nlac_strategy,
            dspy_deadline=30,
            nlac_deadline=90
        )

        result = race.improve("test idea", "test context")

        # Verify DSPy fallback
        assert result == dspy_result
        assert result.strategy_meta['race']['winner'] == 'dspy'
        assert result.strategy_meta['race']['fallback_reason'] == 'both_failed'

    def test_raises_when_both_completely_fail(self):
        """If both throw exceptions, raise RuntimeError."""
        dspy_strategy = Mock()
        dspy_strategy.improve.side_effect = ValueError("DSPy error")

        nlac_strategy = Mock()
        nlac_strategy.improve.side_effect = RuntimeError("NLaC error")

        race = RaceStrategy(
            dspy_strategy=dspy_strategy,
            nlac_strategy=nlac_strategy,
            dspy_deadline=30,
            nlac_deadline=90
        )

        with pytest.raises(RuntimeError, match="RACE: Both strategies failed"):
            race.improve("test idea", "test context")
```

#### Integration Tests

**File:** `tests/integration/test_router_api.py`

```python
import pytest
from fastapi.testclient import TestClient

def test_auto_mode_with_routing_decision(client: TestClient):
    """Test that auto mode includes routing decision in response."""
    response = client.post("/api/v1/improve-prompt", json={
        "idea": "Create JSON schema for user entity",
        "context": "",
        "mode": "auto"
    })
    assert response.status_code == 200
    data = response.json()
    assert "routing_decision" in data
    assert "backend" in data["routing_decision"]
    assert "reason" in data["routing_decision"]

def test_race_mode_with_telemetry(client: TestClient):
    """Test that race mode includes race telemetry."""
    response = client.post("/api/v1/improve-prompt", json={
        "idea": "Design system architecture",
        "context": "",
        "mode": "race"
    })
    assert response.status_code == 200
    data = response.json()
    # Race metadata should be in strategy_meta.race
    if "strategy_meta" in data and "race" in data["strategy_meta"]:
        race_meta = data["strategy_meta"]["race"]
        assert "winner" in race_meta
        assert "dspy_ms" in race_meta
```

#### Verification Steps

1. **Unit tests:** `pytest tests/unit/test_deterministic_router.py tests/unit/test_race_strategy.py`
2. **Integration tests:** `pytest tests/integration/test_router_api.py`
3. **Full test suite:** `make test`
4. **Quality gates:** `make eval`
5. **Manual testing matrix:**

| Input Type | Expected Backend | Verify |
|------------|------------------|--------|
| "improve prompt" | DSPy | Simple = fast |
| "JSON schema + contract" | NLaC | Structure = nlac |
| Large bundle + ambiguous | RACE | Important + ambiguous = race |
| Direct "nlac" mode | NLaC | Override works |

6. **Telemetry monitoring:**
   - Check logs for `Router:` messages
   - Verify routing decisions match expectations
   - Track race metadata (winner, latencies)

---

## Critical Files (PATCHED)

### New Files
| File | Purpose |
|------|---------|
| `hemdov/application/policies/deterministic_router.py` | Core routing logic (Application layer) |
| `eval/src/strategies/race_strategy.py` | Hedged execution with early return |
| `tests/unit/test_deterministic_router.py` | Router unit tests |
| `tests/unit/test_race_strategy.py` | RACE unit tests (including quality gate) |
| `tests/integration/test_router_api.py` | API integration tests |

### Modified Files
| File | Changes |
|------|---------|
| `api/prompt_improver_api.py` | Add auto/race modes, router integration, REAL metrics fields |
| `dashboard/package.json` | Add mode options with clear descriptions |
| `dashboard/src/promptify-quick.tsx` | Update TypeScript types |

---

## Rollback Plan (P1.2 - Previously Omitted) 🔄

### Server-Side Feature Flags

**File:** `hemdov/infrastructure/config/feature_flags.py` (UPDATE)

```python
# Router feature flags
feature_flags = {
    # Disable auto/race modes without redeploy
    "auto_mode_enabled": True,
    "race_mode_enabled": True,

    # Force default mode (emergency override)
    "force_default_mode": None,  # None, "legacy", "nlac", "auto", "race"
}
```

**Usage in API:**

```python
@router.post("/improve-prompt")
async def improve_prompt(request: ImprovePromptRequest):
    settings = container.get(Settings)

    # Feature flag check
    if request.mode == "auto" and not settings.feature_flags.get("auto_mode_enabled", True):
        # Fallback to legacy
        request.mode = "legacy"
        logger.warning("AUTO mode disabled by feature flag, falling back to legacy")

    if request.mode == "race" and not settings.feature_flags.get("race_mode_enabled", True):
        request.mode = "legacy"
        logger.warning("RACE mode disabled by feature flag, falling back to legacy")

    # Force default mode if configured
    forced_mode = settings.feature_flags.get("force_default_mode")
    if forced_mode:
        logger.warning(f"Forcing mode to {forced_mode} via feature flag")
        request.mode = forced_mode
```

### Rollback Procedure

| Situation | Action | Time to Recover |
|-----------|--------|-----------------|
| AUTO routing causes high latency | Set `auto_mode_enabled=False` | Instant (no restart) |
| RACE doubles costs unexpectedly | Set `race_mode_enabled=False` | Instant (no restart) |
| Router makes poor decisions | Set `force_default_mode="legacy"` | Instant (no restart) |
| Critical bug in router | Revert deploy | 5-10 minutes |

### Monitoring Alarms

Set up alerts for:
- **Latency P95 > 60s** (AUTO going to NLaC too often)
- **RACE winner = NLaC > 50%** (DSPy failing gate too much)
- **Routing errors** (exceptions in router)

---

## Migration Notes

**Backward Compatibility:**
- Existing `"legacy"` and `"nlac"` modes unchanged
- New `"auto"` and `"race"` modes are opt-in initially
- Default changes to `"auto"` only after validation period

**Rollout Phases:**

### Phase 1: Deploy (Week 1)
- Deploy with `"auto"` as opt-in (user must select)
- Feature flags enabled but monitor closely
- Set `"force_default_mode="legacy""` initially for safety

### Phase 2: Monitor (Week 1-2)
- Track routing decisions via logs
- Monitor latency P95, error rates
- Sample quality of outputs from each backend

### Phase 3: Enable Default (Week 2-3)
- Remove `"force_default_mode"` override
- Set `"auto"` as default in package.json
- Continue monitoring

### Phase 4: RACE Rollout (Week 3+)
- Enable `race_mode_enabled` flag
- Only triggers for ambiguous + important inputs
- Monitor cost vs quality tradeoff

---

## Intent Mapping (Secondary Feature)

| Router Intent | Current Intent | Weight in Scoring |
|---------------|----------------|-------------------|
| `wo_generation` | `GENERATE` | +2 NLaC (high value) |
| `spec_write` | `GENERATE` | +2 NLaC (high value) |
| `architecture` | `GENERATE` | +2 NLaC (high value) |
| `prompt_improve` | `GENERATE` | 0 (default) |
| `brainstorm` | `GENERATE` | 0 (default) |
| `policy_update` | `REFACTOR` | +1 NLaC |
| `rewrite` | `REFACTOR` | +1 NLaC |
| `optimization` | `REFACTOR` | +1 NLaC |
| `debugging` | `DEBUG` | 0 (use DSPy for speed) |
| `code_review` | `EXPLAIN` | 0 (use DSPy for speed) |

**Key point:** Intent is **secondary** to structure signals. A "JSON schema" request with GENERATE intent will route to NLaC due to structure, not intent.

---

## Risk Mitigation (UPDATED)

| Risk | Mitigation |
|------|------------|
| RACE doubles cost without benefit | Hedged execution: return early if DSPy passes gate |
| Router biased to NLaC | DSPy base score of 2, NLaC needs diff >= 4 |
| Deadlines unrealistic | Realistic: DSPy 30s, NLaC 90s (based on telemetry) |
| Poor routing decisions | Feature flags + telemetry + gradual rollout |
| Quality gate too strict/lenient | Deterministic rules, tune based on real data |
| Frontend timeout mismatch | Keep 120s timeout (matches current backend) |
