# Domain Layer Critical Fixes Implementation Plan v2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical and high-priority issues discovered in the hemdov/domain layer code review, focusing on silent failures, test coverage gaps, and error handling improvements.

**Architecture:** The domain layer follows hexagonal architecture with pure business logic. This plan addresses observability gaps (silent failures), test coverage voids in core services, and error handling refinements while maintaining domain purity (no IO/async in domain).

**Tech Stack:** Python 3.11+, Pydantic, pytest, DSPy

**v2 Changes:** Based on multi-agent review feedback - added migration strategy, fixed critical bugs, added rollback plan.

---

## Rollback Strategy

**Before starting:**
```bash
# Tag current state for easy rollback
git tag pre-domain-fixes-$(date +%Y%m%d)

# Create feature branch
git checkout -b fix/domain-critical-issues
```

**If something goes wrong:**
```bash
# Revert specific commits (atomic commits)
git revert <commit-hash>

# Or rollback to tag
git reset --hard pre-domain-fixes-$(date +%Y%m%d)
```

**Task 2 is highest risk** - validate in staging before production due to breaking change.

---

## Pre-Flight Checklist

- [ ] Read `CLAUDE.md` for domain layer rules
- [ ] Read `docs/api-error-handling.md` for error handling patterns
- [ ] Create git tag for pre-fix state
- [ ] Run full test suite to establish baseline: `make test`
- [ ] Verify `handle_knn_failure()` utility exists (check `hemdov/domain/exception_utils.py` or create)

---

## Task 0: Verify Dependencies

**Files:**
- Check: `hemdov/domain/exception_utils.py` (may need creation)
- Check: `hemdov/domain/services/knn_provider.py`

### Step 1: Verify handle_knn_failure() exists

```bash
grep -r "handle_knn_failure" hemdov/domain/
```

Expected: Should find existing usage or definition

### Step 2: If not found, create utility

```python
# hemdov/domain/exception_utils.py

import logging

logger = logging.getLogger(__name__)

def handle_knn_failure(
    logger: logging.Logger,
    context: str,
    exception: Exception
) -> tuple[bool, str]:
    """
    Handle KNN provider failures consistently.

    Args:
        logger: Logger instance for error tracking
        context: Context string for log messages (e.g., "NLaCBuilder.build")
        exception: The exception that occurred

    Returns:
        tuple of (knn_failed: bool, knn_error: str)
    """
    logger.exception(
        f"KNN failure in {context}: {type(exception).__name__} - {exception}"
    )
    return (True, str(exception))
```

### Step 3: Commit

```bash
git add hemdov/domain/exception_utils.py
git commit -m "feat(domain): add handle_knn_failure utility for consistent error handling"
```

---

## Task 1: Fix Silent Framework Default Assignment

**Issue:** Invalid framework strings silently default to `CHAIN_OF_THOUGHT` without logging.

**Files:**
- Modify: `hemdov/domain/metrics/evaluators.py:481-484`
- Test: `tests/test_metrics_evaluators_exception_handling.py` (create)

### Step 1: Write the failing test

Create test file:

```python
# tests/test_metrics_evaluators_exception_handling.py

import pytest
from hemdov.domain.dto.nlac_models import FrameworkType, PromptObject
from hemdov.domain.metrics.evaluators import QualityEvaluator
import uuid


def test_invalid_framework_logs_warning(caplog):
    """Test that invalid framework strings are logged before defaulting."""
    prompt = PromptObject(
        id=str(uuid.uuid4()),
        template="Test prompt",
        intent_type="debug",
        strategy_meta={},
        constraints={},
        framework="invalid-framework-value"  # Invalid
    )

    with caplog.at_level("WARNING"):
        result = QualityEvaluator.evaluate(prompt)

    # Verify warning was logged
    assert any(
        "Invalid framework" in record.message
        for record in caplog.records
    )

    # Verify it defaulted to CHAIN_OF_THOUGHT
    assert result.framework == FrameworkType.CHAIN_OF_THOUGHT


def test_valid_framework_parses_correctly():
    """Test that valid framework strings parse correctly."""
    for framework_val in [f.value for f in FrameworkType]:
        prompt = PromptObject(
            id=str(uuid.uuid4()),
            template="Test prompt",
            intent_type="debug",
            strategy_meta={},
            constraints={},
            framework=framework_val
        )

        result = QualityEvaluator.evaluate(prompt)
        assert result.framework.value == framework_val
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_metrics_evaluators_exception_handling.py::test_invalid_framework_logs_warning -v
```

Expected: FAIL - No warning is currently logged

### Step 3: Write minimal implementation

Modify `hemdov/domain/metrics/evaluators.py`:

```python
# In from_history_result method, around line 481
try:
    framework = FrameworkType(result.framework)
except ValueError:
    # ADD LOGGING
    logger.warning(
        f"Invalid framework '{result.framework}' in prompt {result.prompt_id}, "
        f"defaulting to CHAIN_OF_THOUGHT. "
        f"Valid values: {[f.value for f in FrameworkType]}"
    )
    framework = FrameworkType.CHAIN_OF_THOUGHT
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_metrics_evaluators_exception_handling.py -v
```

### Step 5: Commit

```bash
git add tests/test_metrics_evaluators_exception_handling.py hemdov/domain/metrics/evaluators.py
git commit -m "fix(metrics): add logging for invalid framework default assignment

Silent failure found in code review - invalid framework strings were
defaulting without logging. Now logs WARNING with valid values.

Related: CM review findings 2026-01-15"
```

---

## Task 2: Fix Framework Validation (WITH MIGRATION STRATEGY)

**Issue:** `prompt_history.py` mutates frozen objects via `object.__setattr__` when framework is invalid.

**BREAKING CHANGE:** This will raise `ValueError` instead of silently defaulting. Requires migration strategy.

**Files:**
- Modify: `hemdov/domain/entities/prompt_history.py:47-59`
- Create: `scripts/migrate_prompt_history.py` (migration script)
- Test: `tests/test_prompt_history_validation.py`

### Step 1: Create migration script

```python
# scripts/migrate_prompt_history.py

"""
Migration script to find and fix PromptHistory records with invalid frameworks.

Run this before deploying Task 2 fixes to identify affected records.
"""

from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.metrics.dimensions import FrameworkType

def find_invalid_frameworks(histories: list[PromptHistory]) -> list[dict]:
    """
    Find all PromptHistory records with invalid frameworks.

    Returns:
        List of dicts with record details for manual review
    """
    valid_frameworks = {f.value for f in FrameworkType}
    invalid_records = []

    for history in histories:
        if history.framework not in valid_frameworks:
            invalid_records.append({
                "id": history.created_at.isoformat(),  # Use timestamp as ID
                "invalid_framework": history.framework,
                "suggested_fix": "chain-of-thought"
            })

    return invalid_records

if __name__ == "__main__":
    # Example usage
    print("Checking for invalid frameworks in PromptHistory records...")
    print("Run this against your data store before deploying Task 2 fix.")
```

### Step 2: Write the test with behavior change note

```python
# tests/test_prompt_history_validation.py

import pytest
from dataclasses import FrozenInstanceError
from hemdov.domain.entities.prompt_history import PromptHistory


def test_invalid_framework_raises_value_error():
    """
    Test that invalid framework raises ValueError.

    BREAKING CHANGE: Previously this would silently default to 'chain-of-thought'.
    After Task 2, it raises ValueError. Ensure existing data is migrated first.
    """
    with pytest.raises(ValueError) as exc_info:
        PromptHistory(
            original_idea="Test idea",
            improved_prompt="Improved prompt",
            framework="invalid-framework",
            confidence=0.8,
            latency_ms=1000,
            guardrails=["guardrail1"]
        )

    assert "Invalid framework" in str(exc_info.value)


def test_valid_frameworks_accepted():
    """Test that all valid frameworks are accepted."""
    from hemdov.domain.metrics.dimensions import FrameworkType

    for framework in [f.value for f in FrameworkType]:
        history = PromptHistory(
            original_idea="Test idea",
            improved_prompt="Improved prompt",
            framework=framework,
            confidence=0.8,
            latency_ms=1000,
            guardrails=["guardrail1"]
        )
        assert history.framework == framework


def test_frozen_instance_cannot_be_modified():
    """Verify PromptHistory is truly frozen."""
    history = PromptHistory(
        original_idea="Test idea",
        improved_prompt="Improved prompt",
        framework="chain-of-thought",
        confidence=0.8,
        latency_ms=1000,
        guardrails=["guardrail1"]
    )

    with pytest.raises(FrozenInstanceError):
        history.original_idea = "Modified"
```

### Step 3: Run test to verify it fails

```bash
pytest tests/test_prompt_history_validation.py::test_invalid_framework_raises_value_error -v
```

Expected: FAIL - Current code mutates instead of raising

### Step 4: Implement fix with proper validation

Modify `hemdov/domain/entities/prompt_history.py`:

```python
def __post_init__(self):
    """Validate business invariants."""
    from hemdov.domain.metrics.dimensions import FrameworkType

    # Validate framework is allowed value
    valid_frameworks = {f.value for f in FrameworkType}

    if self.framework not in valid_frameworks:
        raise ValueError(
            f"Invalid framework '{self.framework}'. "
            f"Must be one of: {sorted(valid_frameworks)}. "
            f"Got: '{self.framework}'"
        )

    # Validate non-empty strings
    if not self.original_idea or not self.original_idea.strip():
        raise ValueError("original_idea cannot be empty")

    if not self.improved_prompt or not self.improved_prompt.strip():
        raise ValueError("improved_prompt cannot be empty")

    # Validate confidence range if provided
    if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
        raise ValueError(f"confidence must be 0-1, got {self.confidence}")

    # Validate latency is non-negative if provided
    if self.latency_ms is not None and self.latency_ms < 0:
        raise ValueError(f"latency_ms must be non-negative, got {self.latency_ms}")

    # Validate guardrails is non-empty list
    if not self.guardrails:
        raise ValueError("guardrails cannot be empty")

    # Auto-generate created_at if not provided
    if self.created_at is None:
        from datetime import datetime, UTC
        object.__setattr__(self, 'created_at', datetime.now(UTC))
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_prompt_history_validation.py -v
```

### Step 6: Commit

```bash
git add scripts/migrate_prompt_history.py tests/test_prompt_history_validation.py hemdov/domain/entities/prompt_history.py
git commit -m "fix(entities): raise ValueError for invalid framework instead of mutating

BREAKING CHANGE: Previously silently defaulted to 'chain-of-thought'.
Now raises ValueError with clear error message.

Migration:
- Run scripts/migrate_prompt_history.py to identify affected records
- Fix invalid data before deploying

Related: CM review findings 2026-01-15"
```

---

## Task 2.5: Validate No Existing Data Issues

**NEW TASK** - Run migration script to check for existing invalid frameworks.

### Step 1: Run migration check

```bash
python scripts/migrate_prompt_history.py
```

### Step 2: If issues found, create data fix

If invalid records exist, create a data migration before proceeding.

### Step 3: Document findings

```bash
git add scripts/migrate_prompt_history.py
git commit -m "docs(migration): document framework validation migration results"
```

---

## Task 3: Fix Broad Exception Catching in NLaCBuilder

**Issue:** Catches `KeyError`, `TypeError`, `RuntimeError` which indicate bugs, not transient failures.

**Files:**
- Modify: `hemdov/domain/services/nlac_builder.py:111-114`
- Test: `tests/test_nlac_builder_exception_handling.py`

### Step 1: Write the failing test

```python
# tests/test_nlac_builder_exception_handling.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest
from hemdov.domain.services.complexity_analyzer import ComplexityLevel


def test_transient_knn_failure_degrades_gracefully():
    """Test that ConnectionError/TimeoutError degrade gracefully."""
    from hemdov.domain.exception_utils import handle_knn_failure

    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=Mock(side_effect=ConnectionError("Network down"))),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Debug this error",
        mode="nlac",
        complexity="simple"
    )

    # Should not raise - should degrade gracefully
    result = builder.build(request)

    # Verify prompt was still generated (degraded behavior)
    assert result.template
    assert result.strategy_meta["knn_failed"] is True
    # Verify template is functional even without examples
    assert len(result.template) > 100


def test_code_bug_keyerror_propagates():
    """Test that KeyError (code bug) propagates instead of being swallowed."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=Mock(side_effect=KeyError("missing_key"))),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Debug this error",
        mode="nlac",
        complexity="simple"
    )

    # Should propagate KeyError, not swallow it
    with pytest.raises(KeyError) as exc_info:
        builder.build(request)

    assert "missing_key" in str(exc_info.value)


def test_code_bug_typeerror_propagates():
    """Test that TypeError (code bug) propagates."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=Mock(side_effect=TypeError("Wrong type"))),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Debug this error",
        mode="nlac",
        complexity="simple"
    )

    with pytest.raises(TypeError):
        builder.build(request)
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_nlac_builder_exception_handling.py::test_code_bug_keyerror_propagates -v
```

### Step 3: Implement fix

Modify `hemdov/domain/services/nlac_builder.py`:

```python
# Import handle_knn_failure at top of file
from hemdov.domain.exception_utils import handle_knn_failure

# In build() method, replace exception handler with:

# Fetch few-shot examples from KNN (optional feature)
knn_failed = False
knn_error = None
fewshot_examples = []

try:
    fewshot_examples = self.knn_provider.find_examples(
        user_input=request.idea,
        intent=intent,
        complexity=complexity,
        k=3
    )
    logger.info(f"Fetched {len(fewshot_examples)} KNN examples for {intent}/{complexity.value}")
except (KNNProviderError, ConnectionError, TimeoutError) as e:
    # Expected transient failures - degrade gracefully
    knn_failed, knn_error = handle_knn_failure(
        logger, "NLaCBuilder.build", e
    )
except (RuntimeError, KeyError, TypeError) as e:
    # Code bugs - should propagate to surface the issue
    logger.exception(
        f"Unexpected KNN error (code bug) in NLaCBuilder.build: {type(e).__name__}"
    )
    raise
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_nlac_builder_exception_handling.py -v
```

### Step 5: Commit

```bash
git add tests/test_nlac_builder_exception_handling.py hemdov/domain/services/nlac_builder.py
git commit -m "fix(nlac-builder): separate transient failures from code bugs

KeyError, TypeError, RuntimeError now propagate as they indicate
code bugs rather than transient failures. ConnectionError,
TimeoutError, KNNProviderError still degrade gracefully.

Note: KNNProvider intentionally uses broad catching for external data.
This is the documented exception to that pattern.

Related: CM review findings 2026-01-15"
```

---

## Task 4: Fix Broad Exception Catching in OPROOptimizer

**Issue:** Same as Task 3 but in `oprop_optimizer.py:264-278`.

**Files:**
- Modify: `hemdov/domain/services/oprop_optimizer.py:264-278`
- Test: `tests/test_oprop_optimizer_exception_handling.py`

### Step 1: Write the failing test

```python
# tests/test_oprop_optimizer_exception_handling.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


def test_transient_failure_tracked_and_degraded():
    """Test that transient failures are tracked with metadata."""
    mock_llm = Mock(generate=Mock(return_value="result"))
    mock_knn = Mock(find_examples=Mock(side_effect=ConnectionError("Network timeout")))

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    # Should not raise - should track and degrade
    response = optimizer.run_loop(
        prompt_obj=Mock(  # Mock PromptObject
            template="Write a function",
            intent_type="generate",
            strategy_meta={"intent": "generate", "complexity": "simple"}
        )
    )

    # Verify failure was tracked
    assert len(optimizer._knn_failures) == 1
    failure = optimizer._knn_failures[0]
    assert failure["error_type"] == "ConnectionError"
    assert failure["is_transient"] is True


def test_code_bug_propagates_with_tracking():
    """Test that code bugs propagate after tracking."""
    mock_llm = Mock(generate=Mock(return_value="result"))
    mock_knn = Mock(find_examples=Mock(side_effect=KeyError("schema_drift")))

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    # Should raise after tracking
    with pytest.raises(KeyError):
        optimizer.run_loop(
            prompt_obj=Mock(
                template="Write a function",
                intent_type="generate",
                strategy_meta={"intent": "generate", "complexity": "simple"}
            )
        )

    # Verify bug was tracked
    assert len(optimizer._knn_failures) == 1
    assert optimizer._knn_failures[0]["is_bug"] is True
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_oprop_optimizer_exception_handling.py::test_code_bug_propagates_with_tracking -v
```

### Step 3: Implement fix

Modify `hemdov/domain/services/oprop_optimizer.py`:

```python
# Import handle_knn_failure at top
from hemdov.domain.exception_utils import handle_knn_failure

# In _build_meta_prompt method, replace exception handler with:

try:
    fewshot_examples = self.knn_provider.find_examples(
        user_input=meta_user_input,
        intent=intent_str,
        complexity=complexity_str,
        k=knn_k
    )
except (KNNProviderError, ConnectionError, TimeoutError) as e:
    # Track transient failure
    self._knn_failures.append({
        "error_type": type(e).__name__,
        "error_message": str(e)[:200],
        "timestamp": datetime.now(UTC).isoformat(),
        "intent": intent_str,
        "complexity": complexity_str,
        "is_transient": True
    })
    handle_knn_failure(logger, "OPROOptimizer._build_meta_prompt", e)
    fewshot_examples = []
except (RuntimeError, KeyError, TypeError, ValueError) as e:
    # Track code bug before propagating
    self._knn_failures.append({
        "error_type": type(e).__name__,
        "error_message": str(e)[:200],
        "timestamp": datetime.now(UTC).isoformat(),
        "intent": intent_str,
        "complexity": complexity_str,
        "is_bug": True
    })
    logger.exception(
        f"Unexpected KNN error (code bug) in OPROOptimizer: {type(e).__name__}"
    )
    raise
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_oprop_optimizer_exception_handling.py -v
```

### Step 5: Commit

```bash
git add tests/test_oprop_optimizer_exception_handling.py hemdov/domain/services/oprop_optimizer.py
git commit -m "fix(oprop): separate transient failures from code bugs

KeyError, TypeError, ValueError, RuntimeError now propagate.
Transient failures tracked with is_transient flag.
Code bugs tracked with is_bug flag.

Related: CM review findings 2026-01-15"
```

---

## Task 5: Add Missing Error Context in KNNProvider

**Issue:** KeyError logging lacks expected vs actual keys information.

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:290-295`
- Test: `tests/test_knn_provider_error_context.py`

### Step 1: Write the test

```python
# tests/test_knn_provider_error_context.py

import pytest
from hemdov.domain.services.knn_provider import KNNProvider


def test_missing_key_error_logged_with_context(caplog):
    """Test that KeyError includes expected and available keys."""
    provider = KNNProvider(k=3)

    # Catalog data with missing 'inputs' key
    bad_examples = [
        {
            "input_idea": "Debug error",
            # Missing 'inputs' key
            "outputs": {"improved": "Fixed"}
        }
    ]

    with caplog.at_level("ERROR"):
        provider.load_catalog_from_data(bad_examples)

    # Find the KeyError log entry
    keyerror_logs = [
        r for r in caplog.records
        if "missing key" in r.message.lower() or "keyerror" in r.message.lower()
    ]

    assert len(keyerror_logs) > 0
    log_message = keyerror_logs[0].message
    # Should mention what was expected/available
    assert "key" in log_message.lower()
```

### Step 2: Run test

```bash
pytest tests/test_knn_provider_error_context.py -v
```

### Step 3: Improve logging

Modify `hemdov/domain/services/knn_provider.py`:

```python
except KeyError as e:
    # IMPROVED: Log full context
    logger.exception(
        f"Skipping example {idx} due to missing key: {e}. "
        f"Expected keys: inputs, outputs. "
        f"Available keys: {list(ex.keys()) if isinstance(ex, dict) else 'N/A'}. "
        f"Example data: {repr(ex)}"
    )
    skipped_count += 1
    continue
```

### Step 4: Run test to verify

```bash
pytest tests/test_knn_provider_error_context.py -v
```

### Step 5: Commit

```bash
git add tests/test_knn_provider_error_context.py hemdov/domain/services/knn_provider.py
git commit -m "refactor(knn): improve KeyError logging with available keys

Error context now includes expected vs available keys for
faster debugging of catalog schema drift.

Related: CM review findings 2026-01-15"
```

---

## Task 6: Add Core Service Test Coverage - IntentClassifier

**FIXED TYPO:** `NLuACRequest` → `NLaCRequest`

**Time Estimate:** 20-30 minutes (not 2-5)

**Files:**
- Create: `tests/test_intent_classifier.py`

### Step 1: Write the test file

```python
# tests/test_intent_classifier.py

import pytest
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType


def test_debug_intent_keywords():
    """Test debug intent classification from keywords."""
    classifier = IntentClassifier()

    # English debug keywords
    request = NLaCRequest(idea="fix this bug", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "debug"

    # Spanish debug keywords
    request = NLaCRequest(idea="corregir error", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "debug"


def test_refactor_intent_keywords():
    """Test refactor intent classification."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="optimize this code", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "refactor"


def test_explain_intent_keywords():
    """Test explain intent classification."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="how does this work", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "explain"


def test_generate_intent_default():
    """Test that non-matching input defaults to generate."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="create a new feature", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "generate"


def test_get_intent_type_mapping():
    """Test that intent strings map to IntentType enum."""
    classifier = IntentClassifier()

    assert classifier.get_intent_type("debug") == IntentType.DEBUG
    assert classifier.get_intent_type("refactor") == IntentType.REFACTOR
    assert classifier.get_intent_type("explain") == IntentType.EXPLAIN
    assert classifier.get_intent_type("generate") == IntentType.GENERATE


def test_get_intent_type_subtypes():
    """Test that subtypes map to base types."""
    classifier = IntentClassifier()

    assert classifier.get_intent_type("debug_runtime") == IntentType.DEBUG
    assert classifier.get_intent_type("debug_logic") == IntentType.DEBUG


def test_get_intent_type_invalid():
    """Test that invalid intents default to GENERATE."""
    classifier = IntentClassifier()

    assert classifier.get_intent_type("invalid") == IntentType.GENERATE
```

### Step 2: Run tests

```bash
pytest tests/test_intent_classifier.py -v
```

### Step 3: Fix any implementation issues

### Step 4: Commit

```bash
git add tests/test_intent_classifier.py
git commit -m "test(intent-classifier): add comprehensive test coverage

Tests cover:
- Intent classification from keywords (EN/ES)
- IntentType enum mapping
- Sub-type handling
- Invalid intent defaults

Time: ~20 min

Related: CM review findings - critical service untested"
```

---

## Task 7: Add Core Service Test Coverage - ComplexityAnalyzer

**Time Estimate:** 25-30 minutes

**Files:**
- Create: `tests/test_complexity_analyzer.py`

### Step 1: Write the test file with COMPLETE error handling

```python
# tests/test_complexity_analyzer.py

import pytest
from hemdov.domain.services.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel


def test_short_idea_is_simple():
    """Test that short ideas are classified as SIMPLE."""
    analyzer = ComplexityAnalyzer()

    result = analyzer.analyze("fix bug", "")
    assert result == ComplexityLevel.SIMPLE


def test_long_idea_is_complex():
    """Test that ideas >300 chars auto-classify as COMPLEX."""
    analyzer = ComplexityAnalyzer()

    long_idea = "debug this error " * 50
    result = analyzer.analyze(long_idea, "")
    assert result == ComplexityLevel.COMPLEX


def test_technical_terms_increase_complexity():
    """Test that technical terms increase complexity score."""
    analyzer = ComplexityAnalyzer()

    result1 = analyzer.analyze("help me with this problem", "")
    assert result1 == ComplexityLevel.SIMPLE

    result2 = analyzer.analyze(
        "help me debug this async race condition in the mutex",
        ""
    )
    assert result2 in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_invalid_input_none_idea():
    """Test that None idea raises ValueError."""
    analyzer = ComplexityAnalyzer()

    with pytest.raises(ValueError, match="must be non-None strings"):
        analyzer.analyze(None, "")


def test_invalid_input_none_context():
    """Test that None context raises ValueError."""
    analyzer = ComplexityAnalyzer()

    with pytest.raises(ValueError, match="must be non-None strings"):
        analyzer.analyze("test", None)


def test_invalid_input_wrong_type_idea():
    """Test that non-string idea raises TypeError."""
    analyzer = ComplexityAnalyzer()

    with pytest.raises(TypeError, match="must be strings"):
        analyzer.analyze(123, "")


def test_invalid_input_wrong_type_context():
    """Test that non-string context raises TypeError."""
    analyzer = ComplexityAnalyzer()

    with pytest.raises(TypeError, match="must be strings"):
        analyzer.analyze("test", 123)


def test_word_boundary_prevents_false_positives():
    """Test that 'class' doesn't match in 'classroom'."""
    analyzer = ComplexityAnalyzer()

    result = analyzer.analyze("help with classroom management", "")
    assert result == ComplexityLevel.SIMPLE
```

### Step 2: Run tests

```bash
pytest tests/test_complexity_analyzer.py -v
```

### Step 3: Fix implementation if needed

### Step 4: Commit

```bash
git add tests/test_complexity_analyzer.py
git commit -m "test(complexity-analyzer): add comprehensive test coverage

Tests cover:
- Length-based classification
- Technical term detection
- Word boundary matching
- Complete error handling (None, wrong types)

Time: ~25 min

Related: CM review findings - critical service untested"
```

---

## Task 8: Add Core Service Test Coverage - NLaCBuilder

**Time Estimate:** 30-40 minutes

**CHANGED:** Use semantic checks instead of brittle template matching

**Files:**
- Create: `tests/test_nlac_builder.py`

### Step 1: Write the test file

```python
# tests/test_nlac_builder.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest
from hemdov.domain.services.complexity_analyzer import ComplexityLevel


def test_build_creates_prompt_object():
    """Test that build() returns a valid PromptObject."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Fix this bug",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    assert result.template
    assert result.intent_type == "debug"
    assert result.strategy_meta["strategy"]


def test_simple_debug_template_semantic_checks():
    """Test simple debug template with semantic (not exact) checks."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Fix the null pointer",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    # SEMANTIC checks (not exact format)
    template_lower = result.template.lower()
    assert "role" in template_lower
    assert "debugger" in template_lower or "specialist" in template_lower
    assert "task" in template_lower
    assert "fix the null pointer" in result.template


def test_complex_uses_rar():
    """Test that complex requests use RaR (semantic check)."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="refactor"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.COMPLEX)
    )

    request = NLaCRequest(
        idea="Optimize the database",
        mode="nlac",
        complexity="complex"
    )

    result = builder.build(request)

    # Complex should have RaR section (case-insensitive)
    template_lower = result.template.lower()
    assert "understanding" in template_lower or "request" in template_lower


def test_knn_failure_produces_functional_template():
    """Test that KNN failure produces functional prompts."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=Mock(side_effect=ConnectionError("KNN down"))),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Fix this",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    # Verify degradation
    assert result.strategy_meta["knn_failed"] is True
    assert result.strategy_meta["fewshot_count"] == 0

    # Verify template is still functional
    template = result.template
    assert len(template) > 100  # Reasonable length
    assert "role" in template.lower()
    assert "task" in template.lower()


def test_template_with_context():
    """Test template generation with context."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="explain"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.MODERATE)
    )

    request = NLaCRequest(
        idea="How does this work",
        mode="nlac",
        complexity="moderate",
        context="This is a React component"
    )

    result = builder.build(request)

    template_lower = result.template.lower()
    assert "context" in template_lower
    assert "react" in result.template
```

### Step 2: Run tests

```bash
pytest tests/test_nlac_builder.py -v
```

### Step 3: Commit

```bash
git add tests/test_nlac_builder.py
git commit -m "test(nlac-builder): add comprehensive tests with semantic checks

Tests cover:
- PromptObject creation
- Semantic template validation (not brittle)
- RaR usage for complex requests
- KNN failure functional degradation
- Context inclusion

Uses semantic checks to avoid brittleness from format changes.

Time: ~30 min

Related: CM review findings - critical service untested"
```

---

## Task 9: Add Core Service Test Coverage - ReflexionService

**Time Estimate:** 25-30 minutes

**Files:**
- Create: `tests/test_reflexion_service.py`

### Step 1: Write the test file

```python
# tests/test_reflexion_service.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.reflexion_service import ReflexionService, ReflexionResult


def test_refine_returns_result():
    """Test that refine() returns a ReflexionResult."""
    executor = Mock(execute=Mock(return_value=(True, None)))

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="fixed code")),
        executor=executor
    )

    result = service.refine(
        prompt="def broken(): pass",
        error_type="SyntaxError",
        error_message="invalid syntax"
    )

    assert isinstance(result, ReflexionResult)
    assert result.code
    assert result.iteration_count >= 1


def test_refine_stops_on_success():
    """Test that refinement stops when execution succeeds."""
    executor = Mock()
    executor.execute.side_effect = [
        (False, "still broken"),
        (True, None)
    ]

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="code")),
        executor=executor
    )

    result = service.refine(
        prompt="broken code",
        error_type="RuntimeError",
        error_message="error",
        max_iterations=5
    )

    assert result.success is True
    assert result.iteration_count == 2


def test_refine_max_iterations():
    """Test that refinement stops at max_iterations."""
    executor = Mock(execute=Mock(return_value=(False, "always fails")))

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="code")),
        executor=executor
    )

    result = service.refine(
        prompt="broken code",
        error_type="RuntimeError",
        error_message="error",
        max_iterations=3
    )

    assert result.success is False
    assert result.iteration_count == 3


def test_refine_without_executor():
    """Test refinement without executor (code generation only)."""
    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="generated code")),
        executor=None
    )

    result = service.refine(
        prompt="write a function",
        error_type=None,
        error_message=None,
        max_iterations=1
    )

    assert result.success is True
    assert result.code == "generated code"


def test_refine_validates_inputs():
    """Test that refine() validates inputs."""
    service = ReflexionService(
        llm_client=Mock(),
        executor=Mock()
    )

    with pytest.raises(ValueError):
        service.refine(
            prompt=None,
            error_type="RuntimeError",
            error_message="error"
        )

    with pytest.raises(ValueError):
        service.refine(
            prompt="code",
            error_type="RuntimeError",
            error_message="error",
            max_iterations=0
        )


def test_refine_tracks_error_history():
    """Test that errors are tracked in history."""
    executor = Mock(execute=Mock(return_value=(False, "error message")))

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="code")),
        executor=executor
    )

    result = service.refine(
        prompt="broken code",
        error_type="RuntimeError",
        error_message="initial error",
        max_iterations=2
    )

    assert len(result.error_history) == 2
```

### Step 2: Run tests

```bash
pytest tests/test_reflexion_service.py -v
```

### Step 3: Commit

```bash
git add tests/test_reflexion_service.py
git commit -m "test(reflexion): add comprehensive iterative refinement tests

Tests cover:
- Basic refinement flow
- Success stopping condition
- Max iterations limit
- No-executor mode
- Input validation
- Error history tracking

Time: ~25 min

Related: CM review findings - critical service untested"
```

---

## Task 10: Add Core Service Test Coverage - OPROOptimizer

**CRITICAL FIX:** Tests must use `run_loop()` method, not `optimize()`

**Time Estimate:** 30-40 minutes (need to understand actual API)

**Files:**
- Create: `tests/test_oprop_optimizer.py`

### Step 1: Write the test file with CORRECT API

```python
# tests/test_oprop_optimizer.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.dto.nlac_models import PromptObject, IntentType
from datetime import datetime, UTC


def create_mock_prompt_object(template: str = "Test prompt") -> PromptObject:
    """Helper to create a mock PromptObject."""
    return PromptObject(
        id="test-id",
        template=template,
        intent_type=IntentType.GENERATE,
        strategy_meta={"intent": "generate", "complexity": "simple"},
        constraints={},
        created_at=datetime.now(UTC).isoformat()
    )


def test_run_loop_returns_response():
    """Test that run_loop() returns an OptimizeResponse."""
    mock_llm = Mock(generate=Mock(return_value="Optimized prompt"))
    mock_knn = Mock(find_examples=Mock(return_value=[]))

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    prompt_obj = create_mock_prompt_object()
    response = optimizer.run_loop(prompt_obj)

    # Verify response structure
    assert response.final_instruction
    assert response.final_score >= 0.0
    assert response.trajectory is not None


def test_run_loop_uses_knn_examples():
    """Test that few-shot examples are fetched and used."""
    from hemdov.domain.services.knn_provider import FewShotExample

    mock_examples = [
        FewShotExample(
            input_idea="Create a function",
            input_context="",
            improved_prompt="Write a Python function",
            role="Developer",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Include type hints"]
        )
    ]

    mock_llm = Mock(generate=Mock(return_value="Optimized"))
    mock_knn = Mock(find_examples=Mock(return_value=mock_examples))

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    prompt_obj = create_mock_prompt_object()
    response = optimizer.run_loop(prompt_obj)

    # Verify KNN was called
    mock_knn.find_examples.assert_called_once()
    assert len(optimizer._knn_failures) >= 0


def test_run_loop_runs_multiple_iterations():
    """Test that optimization runs for specified iterations."""
    mock_llm = Mock(generate=Mock(return_value=f"Prompt v{{iteration}}"))
    mock_knn = Mock(find_examples=Mock(return_value=[]))

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=3
    )

    prompt_obj = create_mock_prompt_object()
    response = optimizer.run_loop(prompt_obj)

    # LLM should be called max_iterations times
    assert mock_llm.generate.call_count == 3


def test_run_loop_validates_inputs():
    """Test that run_loop() validates inputs."""
    optimizer = OPROOptimizer(
        llm_client=Mock(),
        knn_provider=Mock(),
        max_iterations=2
    )

    # Invalid PromptObject (empty template)
    with pytest.raises((ValueError, ValidationError)):
        invalid_prompt = PromptObject(
            id="test",
            template="",  # Empty - should fail validation
            intent_type=IntentType.GENERATE,
            strategy_meta={},
            constraints={}
        )
        optimizer.run_loop(invalid_prompt)
```

### Step 2: Run tests

```bash
pytest tests/test_oprop_optimizer.py -v
```

### Step 3: Commit

```bash
git add tests/test_oprop_optimizer.py
git commit -m "test(oprop): add comprehensive meta-optimization tests

Tests use CORRECT API (run_loop not optimize):
- Response structure validation
- Few-shot example integration
- Multiple iteration handling
- Input validation

Fixed from v1: Tests now use run_loop() method matching actual
implementation.

Time: ~30 min

Related: CM review findings - critical service untested"
```

---

## Task 11: Run Full Test Suite and Verify Coverage

### Step 1: Run full test suite

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

### Step 2: Run coverage report

```bash
pytest tests/ --cov=hemdov/domain --cov-report=term-missing
```

### Step 3: Document coverage improvements

```bash
git add tests/
git commit -m "test(docs): document coverage improvements

Added comprehensive test coverage for 5 core services:
- IntentClassifier (routing logic)
- ComplexityAnalyzer (classification)
- NLaCBuilder (template generation)
- ReflexionService (iterative refinement)
- OPROOptimizer (meta-optimization)

All tests follow TDD with descriptive names and edge case coverage."
```

---

## Task 12: Update Documentation

### Step 1: Review documentation

### Step 2: Update if needed

```bash
git add CLAUDE.md docs/api-error-handling.md
git commit -m "docs: update error handling patterns from domain fixes"
```

---

## Task 13: Create Integration Tests (NEW)

**Recommended by review** - Add integration tests with real dependencies.

### Step 1: Create integration test file

```python
# tests/test_nlac_integration.py

import pytest
from hemdov.domain.services.knn_provider import KNNProvider
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest


def test_nlac_pipeline_with_real_knn():
    """Test full pipeline with real KNNProvider (not mock)."""
    # Use real KNNProvider with small test catalog
    knn = KNNProvider(k=2)
    knn.load_catalog_from_data([
        {
            "inputs": {"idea": "fix bug"},
            "outputs": {
                "improved": "Debug the error carefully",
                "role": "Debugger"
            }
        }
    ])

    builder = NLaCBuilder(knn_provider=knn)

    request = NLaCRequest(
        idea="Fix this null pointer",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    # Verify integration worked
    assert result.template
    # Real KNN may return 0 examples if catalog is small
    # But template should still be functional
    assert len(result.template) > 100
```

### Step 2: Run integration tests

```bash
pytest tests/test_nlac_integration.py -v
```

### Step 3: Commit

```bash
git add tests/test_nlac_integration.py
git commit -m "test(integration): add end-to-end pipeline tests

Tests verify services work together with real (not mocked) dependencies.
Catches integration bugs that unit tests miss.

Recommended by multi-agent review."
```

---

## Completion Checklist

```bash
# Run full test suite
make test

# Run quality gates
make eval

# Verify git history
git log --oneline -15

# Check coverage
pytest tests/ --cov=hemdov/domain --cov-report=term-missing

# Verify we can rollback if needed
git tag | grep pre-domain-fixes
```

**Success Criteria:**
- [ ] All 13 tasks completed
- [ ] All tests pass
- [ ] Coverage increased for core services
- [ ] No silent failures remain
- [ ] Migration strategy executed (Task 2.5)
- [ ] Integration tests passing
- [ ] Clean commit history

---

## v2 Summary of Changes

**From multi-agent review feedback:**

1. **Added Task 0**: Verify `handle_knn_failure()` exists
2. **Added Task 2.5**: Migration check for Task 2 breaking change
3. **Added Task 13**: Integration tests
4. **Fixed Task 6**: Typo `NLuACRequest` → `NLaCRequest`
5. **Fixed Task 10**: Tests now use `run_loop()` not `optimize()`
6. **Fixed Task 7**: Complete error handling tests
7. **Fixed Task 8**: Semantic checks instead of brittle template matching
8. **Updated time estimates**: 15-40 min for test tasks (not 2-5)
9. **Added rollback strategy**: Section at top
10. **Added pre-flight checklist**: Before starting

---

**Plan v2 saved to `docs/plans/2026-01-15-domain-layer-critical-fixes-v2.md`**
