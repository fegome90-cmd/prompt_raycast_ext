# Domain Layer Critical Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical and high-priority issues discovered in the hemdov/domain layer code review, focusing on silent failures, test coverage gaps, and error handling improvements.

**Architecture:** The domain layer follows hexagonal architecture with pure business logic. This plan addresses observability gaps (silent failures), test coverage voids in core services, and error handling refinements while maintaining domain purity (no IO/async in domain).

**Tech Stack:** Python 3.11+, Pydantic, pytest, DSPy

**Prerequisites:**
- Read `CLAUDE.md` for domain layer rules (no `except Exception:`, specific error types, degradation flags)
- Read `docs/api-error-handling.md` for error handling patterns
- Existing test infrastructure in `tests/`

---

## Task 1: Fix Silent Framework Default Assignment

**Issue:** Invalid framework strings silently default to `CHAIN_OF_THOUGHT` without logging in `metrics/evaluators.py:481-484`.

**Files:**
- Modify: `hemdov/domain/metrics/evaluators.py:481-484`
- Test: `tests/test_metrics_evaluators_exception_handling.py` (create new)

### Step 1: Write the failing test

Create test file with validation for framework parsing:

```python
# tests/test_metrics_evaluators_exception_handling.py

import pytest
from hemdov.domain.dto.nlac_models import FrameworkType
from hemdov.domain.metrics.evaluators import QualityEvaluator


def test_invalid_framework_logs_warning(caplog):
    """Test that invalid framework strings are logged before defaulting."""
    # Create a PromptObject with invalid framework
    from hemdov.domain.dto.nlac_models import PromptObject
    import uuid

    prompt = PromptObject(
        id=str(uuid.uuid4()),
        template="Test prompt",
        intent_type="debug",
        strategy_meta={},
        constraints={},
        framework="invalid-framework-value"  # Invalid value
    )

    # The evaluator should log a warning but not crash
    with caplog.at_level("WARNING"):
        result = QualityEvaluator.evaluate(prompt)

    # Verify warning was logged
    assert any(
        "Invalid framework" in record.message
        for record in caplog.records
    ), "Expected warning about invalid framework"

    # Verify it defaulted to CHAIN_OF_THOUGHT
    assert result.framework == FrameworkType.CHAIN_OF_THOUGHT


def test_valid_framework_parses_correctly():
    """Test that valid framework strings parse correctly."""
    from hemdov.domain.dto.nlac_models import PromptObject
    import uuid

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

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_metrics_evaluators_exception_handling.py::test_invalid_framework_logs_warning -v
```

Expected: FAIL - No warning is currently logged for invalid framework

**Step 3: Write minimal implementation**

Modify `hemdov/domain/metrics/evaluators.py` around line 481:

```python
# Find this section in the from_history_result method
# Parse framework
try:
    framework = FrameworkType(result.framework)
except ValueError:
    # ADD LOGGING HERE
    logger.warning(
        f"Invalid framework '{result.framework}' in prompt {result.prompt_id}, "
        f"defaulting to CHAIN_OF_THOUGHT. "
        f"Valid values: {[f.value for f in FrameworkType]}"
    )
    framework = FrameworkType.CHAIN_OF_THOUGHT
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_metrics_evaluators_exception_handling.py::test_invalid_framework_logs_warning -v
pytest tests/test_metrics_evaluators_exception_handling.py::test_valid_framework_parses_correctly -v
```

Expected: PASS for both tests

**Step 5: Commit**

```bash
git add tests/test_metrics_evaluators_exception_handling.py hemdov/domain/metrics/evaluators.py
git commit -m "fix(metrics): add logging for invalid framework default assignment

Silent failure found in code review - invalid framework strings were
defaulting without logging. Now logs WARNING with valid values.

Related: CM review findings 2026-01-15"
```

---

## Task 2: Fix Framework Validation Silent Mutation

**Issue:** `prompt_history.py` mutates frozen objects via `object.__setattr__` when framework is invalid.

**Files:**
- Modify: `hemdov/domain/entities/prompt_history.py:47-59`
- Test: `tests/test_prompt_history_validation.py` (create new)

### Step 1: Write the failing test

```python
# tests/test_prompt_history_validation.py

import pytest
from dataclasses import FrozenInstanceError
from hemdov.domain.entities.prompt_history import PromptHistory


def test_invalid_framework_raises_value_error():
    """Test that invalid framework raises ValueError instead of mutating."""
    with pytest.raises(ValueError) as exc_info:
        PromptHistory(
            original_idea="Test idea",
            improved_prompt="Improved prompt",
            framework="invalid-framework",  # Invalid value
            confidence=0.8,
            latency_ms=1000,
            guardrails=["guardrail1"]
        )

    assert "Invalid framework" in str(exc_info.value)
    assert "invalid-framework" in str(exc_info.value)


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

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_prompt_history_validation.py::test_invalid_framework_raises_value_error -v
```

Expected: FAIL - Current code mutates instead of raising ValueError

**Step 3: Write minimal implementation**

Modify `hemdov/domain/entities/prompt_history.py` `__post_init__` method:

```python
def __post_init__(self):
    """Validate business invariants."""
    # Import here to avoid circular dependency
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

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_prompt_history_validation.py -v
```

Expected: PASS for all tests

**Step 5: Commit**

```bash
git add tests/test_prompt_history_validation.py hemdov/domain/entities/prompt_history.py
git commit -m "fix(entities): raise ValueError for invalid framework instead of mutating

Previous behavior used object.__setattr__ to mutate frozen objects,
violating the frozen=True contract. Now raises ValueError with
clear error message.

Related: CM review findings 2026-01-15"
```

---

## Task 3: Fix Broad Exception Catching in NLaCBuilder

**Issue:** Catches `KeyError`, `TypeError`, `RuntimeError` which indicate bugs, not transient failures.

**Files:**
- Modify: `hemdov/domain/services/nlac_builder.py:111-114`
- Test: `tests/test_nlac_builder_exception_handling.py` (create new)

### Step 1: Write the failing test

```python
# tests/test_nlac_builder_exception_handling.py

import pytest
from unittest.mock import Mock, patch
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest, ComplexityLevel


def test_transient_knn_failure_degrades_gracefully():
    """Test that ConnectionError/TimeoutError degrade gracefully."""
    builder = NLaCBuilder(
        knn_provider=Mock(),
        intent_classifier=Mock(),
        complexity_analyzer=Mock()
    )

    # Mock KNN to raise ConnectionError (transient failure)
    builder.knn_provider.find_examples.side_effect = ConnectionError("Network down")

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


def test_code_bug_keyerror_propagates():
    """Test that KeyError (code bug) propagates instead of being swallowed."""
    builder = NLaCBuilder(
        knn_provider=Mock(),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    # Mock to raise KeyError (indicates code bug, not transient failure)
    builder.knn_provider.find_examples.side_effect = KeyError("missing_key")

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
        knn_provider=Mock(),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    builder.knn_provider.find_examples.side_effect = TypeError("Wrong type")

    request = NLaCRequest(
        idea="Debug this error",
        mode="nlac",
        complexity="simple"
    )

    with pytest.raises(TypeError):
        builder.build(request)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_nlac_builder_exception_handling.py::test_code_bug_keyerror_propagates -v
```

Expected: FAIL - Current code swallows KeyError

**Step 3: Write minimal implementation**

Modify `hemdov/domain/services/nlac_builder.py` around line 111:

```python
# Find the KNN fetch section in build() method
# Replace the broad exception handler with:

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
    # These are expected transient failures - degrade gracefully
    knn_failed, knn_error = handle_knn_failure(
        logger, "NLaCBuilder.build", e
    )
    # Continue with empty examples list (zero-shot degradation)
except (RuntimeError, KeyError, TypeError) as e:
    # These are code bugs - should propagate to surface the issue
    logger.exception(
        f"Unexpected KNN error (code bug) in NLaCBuilder.build: {type(e).__name__}"
    )
    raise  # Re-raise to surface the bug
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_nlac_builder_exception_handling.py -v
```

Expected: PASS for all tests

**Step 5: Commit**

```bash
git add tests/test_nlac_builder_exception_handling.py hemdov/domain/services/nlac_builder.py
git commit -m "fix(nlac-builder): separate transient failures from code bugs

KeyError, TypeError, RuntimeError now propagate as they indicate
code bugs rather than transient failures. ConnectionError,
TimeoutError, KNNProviderError still degrade gracefully.

Related: CM review findings 2026-01-15"
```

---

## Task 4: Fix Broad Exception Catching in OPROOptimizer

**Issue:** Same as Task 3 but in `oprop_optimizer.py:264-278`. Also tracks failures.

**Files:**
- Modify: `hemdov/domain/services/oprop_optimizer.py:264-278`
- Test: `tests/test_oprop_optimizer_exception_handling.py` (create new)

### Step 1: Write the failing test

```python
# tests/test_oprop_optimizer_exception_handling.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


def test_transient_failure_tracked_and_degraded():
    """Test that transient failures are tracked with metadata."""
    mock_llm = Mock()
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("Network timeout")

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    # Should not raise - should track and degrade
    result = optimizer.optimize(
        user_input="Write a function",
        intent="debug",
        complexity="simple"
    )

    # Verify failure was tracked
    assert len(optimizer._knn_failures) == 1
    failure = optimizer._knn_failures[0]
    assert failure["error_type"] == "ConnectionError"
    assert failure["is_transient"] is True


def test_code_bug_propagates_with_tracking():
    """Test that code bugs propagate after tracking."""
    mock_llm = Mock()
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyError("schema_drift")

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    # Should raise after tracking
    with pytest.raises(KeyError):
        optimizer.optimize(
            user_input="Write a function",
            intent="debug",
            complexity="simple"
        )

    # Verify bug was tracked
    assert len(optimizer._knn_failures) == 1
    failure = optimizer._knn_failures[0]
    assert failure["error_type"] == "KeyError"
    assert failure["is_bug"] is True
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_oprop_optimizer_exception_handling.py::test_code_bug_propagates_with_tracking -v
```

Expected: FAIL - Current code swallows all exceptions

**Step 3: Write minimal implementation**

Modify `hemdov/domain/services/oprop_optimizer.py` around line 264:

```python
# Find the KNN section in _build_meta_prompt method
# Replace the exception handler with:

try:
    fewshot_examples = self.knn_provider.find_examples(
        user_input=meta_user_input,
        intent=intent_str,
        complexity=complexity_str,
        k=knn_k
    )
except (KNNProviderError, ConnectionError, TimeoutError) as e:
    # Track transient failure with metadata
    self._knn_failures.append({
        "error_type": type(e).__name__,
        "error_message": str(e)[:200],
        "timestamp": datetime.now(UTC).isoformat(),
        "intent": intent_str,
        "complexity": complexity_str,
        "is_transient": True
    })

    # Use utility for consistent error handling
    handle_knn_failure(
        logger, "OPROOptimizer._build_meta_prompt", e
    )
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

    # Log and propagate the bug
    logger.exception(
        f"Unexpected KNN error (code bug) in OPROOptimizer: {type(e).__name__}"
    )
    raise
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_oprop_optimizer_exception_handling.py -v
```

Expected: PASS for all tests

**Step 5: Commit**

```bash
git add tests/test_oprop_optimizer_exception_handling.py hemdov/domain/services/oprop_optimizer.py
git commit -m "fix(oprop): separate transient failures from code bugs, improve tracking

KeyError, TypeError, ValueError, RuntimeError now propagate as bugs.
Transient failures (ConnectionError, TimeoutError) tracked with
is_transient flag. Code bugs tracked with is_bug flag.

Related: CM review findings 2026-01-15"
```

---

## Task 5: Add Missing Error Context in KNNProvider

**Issue:** KeyError logging lacks expected vs actual keys information.

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:290-295`
- Test: `tests/test_knn_provider_error_context.py` (create new)

### Step 1: Write the failing test

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

    assert len(keyerror_logs) > 0, "Expected KeyError to be logged"

    # Verify context is in the log message
    log_message = keyerror_logs[0].message
    # Should mention what was expected/available
    assert "key" in log_message.lower()
```

**Step 2: Run test to verify current state**

```bash
pytest tests/test_knn_provider_error_context.py -v
```

Note: This test might pass even with current code since KeyError is logged. The goal is to improve the log message quality.

**Step 3: Improve logging implementation**

Modify `hemdov/domain/services/knn_provider.py` around line 290:

```python
# In _load_catalog_from_data method, find the KeyError handler
# Replace with:

try:
    inputs = ex['inputs']
    outputs = ex['outputs']
    input_context = ex.get('context', '')
    role = outputs.get('role', 'Developer')
    directive = outputs.get('directive', '')
    framework = outputs.get('framework', 'chain-of-thought')
    guardrails = outputs.get('guardrails', [])

    # Validate required fields
    if not inputs or not isinstance(inputs, dict):
        raise ValueError(f"Invalid 'inputs' in example {idx}: {inputs}")

    example = FewShotExample(
        input_idea=inputs.get('idea', ''),
        input_context=input_context,
        improved_prompt=outputs['improved'],
        role=role,
        directive=directive,
        framework=framework,
        guardrails=guardrails or [],
        expected_output=outputs.get('expected_output')
    )

    self.catalog.append(example)
    self._dspy_examples.append(self._create_dspy_example(example))

except KeyError as e:
    # IMPROVED: Log full context for debugging
    logger.exception(
        f"Skipping example {idx} due to missing key: {e}. "
        f"Expected keys: inputs, outputs. "
        f"Available keys: {list(ex.keys()) if isinstance(ex, dict) else 'N/A (not a dict)'}. "
        f"Example data: {repr(ex)}"
    )
    skipped_count += 1
    continue
```

**Step 4: Run test to verify improvement**

```bash
pytest tests/test_knn_provider_error_context.py -v
```

Expected: PASS with improved log messages

**Step 5: Commit**

```bash
git add tests/test_knn_provider_error_context.py hemdov/domain/services/knn_provider.py
git commit -m "refactor(knn): improve KeyError logging with available keys

Error context now includes expected keys vs available keys for
faster debugging of catalog schema drift issues.

Related: CM review findings 2026-01-15"
```

---

## Task 6: Add Core Service Test Coverage - IntentClassifier

**Issue:** IntentClassifier has ZERO test coverage despite being critical for routing.

**Files:**
- Create: `tests/test_intent_classifier.py`
- Reference: `hemdov/domain/services/intent_classifier.py`

### Step 1: Write the test file

```python
# tests/test_intent_classifier.py

import pytest
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.dto.nlac_models import NLaCRequest, ComplexityLevel


def test_debug_intent_keywords():
    """Test debug intent classification from keywords."""
    classifier = IntentClassifier()

    # English debug keywords
    request = NLaCRequest(idea="fix this bug", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "debug"

    request = NLaCRequest(idea="help debug error", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "debug"

    # Spanish debug keywords
    request = NLaCRequest(idea="corregir error", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "debug"


def test_refactor_intent_keywords():
    """Test refactor intent classification."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="optimize this code", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "refactor"

    request = NLaCRequest(idea="mejorar rendimiento", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "refactor"


def test_explain_intent_keywords():
    """Test explain intent classification."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="how does this work", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "explain"

    request = NLuACRequest(idea="explain this function", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "explain"


def test_generate_intent_default():
    """Test that non-matching input defaults to generate."""
    classifier = IntentClassifier()

    request = NLaCRequest(idea="create a new feature", mode="nlac", complexity="simple")
    assert classifier.classify(request) == "generate"


def test_multiaigcd_scenarios():
    """Test MultiAIGCD scenarios where multiple intents match."""
    classifier = IntentClassifier()

    # Debug + Refactor (complex input)
    request = NLaCRequest(
        idea="optimize and fix the bug in the error handling",
        mode="nlac",
        complexity="complex"
    )
    intent = classifier.classify(request)
    # Should classify, exact behavior depends on implementation
    assert intent in ["debug", "refactor", "debug_refactor"]


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

    # Sub-types should map to base types
    assert classifier.get_intent_type("debug_runtime") == IntentType.DEBUG
    assert classifier.get_intent_type("debug_logic") == IntentType.DEBUG


def test_get_intent_type_invalid():
    """Test that invalid intents default to GENERATE."""
    classifier = IntentClassifier()

    assert classifier.get_intent_type("invalid") == IntentType.GENERATE
    assert classifier.get_intent_type("") == IntentType.GENERATE
```

### Step 2: Run tests (some may fail based on implementation)

```bash
pytest tests/test_intent_classifier.py -v
```

Note: Tests may reveal implementation details that need adjustment.

### Step 3: Fix any implementation issues discovered

If tests reveal bugs in IntentClassifier, fix them in `hemdov/domain/services/intent_classifier.py`.

### Step 4: Run tests to verify all pass

```bash
pytest tests/test_intent_classifier.py -v
```

Expected: PASS for all tests

### Step 5: Commit

```bash
git add tests/test_intent_classifier.py
git commit -m "test(intent-classifier): add comprehensive test coverage

Tests cover:
- Intent classification from keywords (EN/ES)
- MultiAIGCD scenarios
- IntentType enum mapping
- Sub-type handling
- Invalid intent defaults

Related: CM review findings - critical service untested"
```

---

## Task 7: Add Core Service Test Coverage - ComplexityAnalyzer

**Issue:** ComplexityAnalyzer has ZERO test coverage.

**Files:**
- Create: `tests/test_complexity_analyzer.py`
- Reference: `hemdov/domain/services/complexity_analyzer.py`

### Step 1: Write the test file

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

    long_idea = "debug this error " * 50  # >300 chars
    result = analyzer.analyze(long_idea, "")
    assert result == ComplexityLevel.COMPLEX


def test_technical_terms_increase_complexity():
    """Test that technical terms increase complexity score."""
    analyzer = ComplexityAnalyzer()

    # Without technical terms
    result1 = analyzer.analyze("help me with this problem", "")
    assert result1 == ComplexityLevel.SIMPLE

    # With technical terms
    result2 = analyzer.analyze(
        "help me debug this async race condition in the mutex",
        ""
    )
    # Technical terms should push toward higher complexity
    assert result2 in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_code_snippet_increases_complexity():
    """Test that code snippets increase complexity score."""
    analyzer = ComplexityAnalyzer()

    # Without code
    result1 = analyzer.analyze("fix function", "")
    assert result1 == ComplexityLevel.SIMPLE

    # With code snippet
    result2 = analyzer.analyze(
        "fix function",
        context="```python\ndef broken():\n    pass\n```"
    )
    assert result2 in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_punctuation_increases_complexity():
    """Test that structured punctuation increases complexity."""
    analyzer = ComplexityAnalyzer()

    # Simple idea
    result1 = analyzer.analyze("fix the bug", "")
    assert result1 == ComplexityLevel.SIMPLE

    # Structured idea with bullets/headers
    result2 = analyzer.analyze(
        "# Requirements\n- fix bug\n- add tests\n- update docs",
        ""
    )
    assert result2 in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_scoring_thresholds():
    """Test the specific score thresholds."""
    analyzer = ComplexityAnalyzer()

    # Score < 0.25 = SIMPLE
    # Score < 0.6 = MODERATE
    # Score >= 0.6 = COMPLEX

    # Can't directly test scores without modifying code,
    # but we can verify behavior at boundaries
    result_simple = analyzer.analyze("x", "")
    assert result_simple == ComplexityLevel.SIMPLE


def test_multilingual_technical_terms():
    """Test technical term detection in Spanish."""
    analyzer = ComplexityAnalyzer()

    # Spanish technical terms
    result = analyzer.analyze(
        "depurar este asíncrono condición de carrera",
        ""
    )
    # Should detect technical terms and increase complexity
    assert result in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_word_boundary_prevents_false_positives():
    """Test that 'class' doesn't match in 'classroom'."""
    analyzer = ComplexityAnalyzer()

    # 'class' is a technical term, but 'classroom' should not match
    result = analyzer.analyze("help with classroom management", "")
    # Should not trigger technical term detection
    assert result == ComplexityLevel.SIMPLE


def test_context_contributes_to_score():
    """Test that context is included in analysis."""
    analyzer = ComplexityAnalyzer()

    # Same idea, different context
    result1 = analyzer.analyze("fix it", "")
    result2 = analyzer.analyze("fix it", "with async mutex race condition")

    # More complex context should increase complexity
    assert result2.value >= result1.value


def test_invalid_input_raises():
    """Test that invalid inputs raise appropriate errors."""
    analyzer = ComplexityAnalyzer()

    with pytest.raises(ValueError):
        analyzer.analyze(None, "")  # None not allowed

    with pytest.raises(TypeError):
        analyzer.analyze(123, "")  # Must be string
```

### Step 2: Run tests

```bash
pytest tests/test_complexity_analyzer.py -v
```

### Step 3: Fix any implementation issues

### Step 4: Run tests to verify all pass

```bash
pytest tests/test_complexity_analyzer.py -v
```

### Step 5: Commit

```bash
git add tests/test_complexity_analyzer.py
git commit -m "test(complexity-analyzer): add comprehensive test coverage

Tests cover:
- Length-based classification
- Technical term detection (EN/ES)
- Code snippet detection
- Punctuation structure
- Word boundary matching
- Context contribution
- Input validation

Related: CM review findings - critical service untested"
```

---

## Task 8: Add Core Service Test Coverage - NLaCBuilder

**Issue:** NLaCBuilder has ZERO test coverage for template generation.

**Files:**
- Create: `tests/test_nlac_builder.py`
- Reference: `hemdov/domain/services/nlac_builder.py`

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

    # Verify result structure
    assert result.template
    assert result.intent_type == "debug"
    assert result.strategy_meta["strategy"]
    assert result.strategy_meta["intent"] == "debug"
    assert result.strategy_meta["complexity"] == "simple"


def test_simple_debug_template():
    """Test simple debug template generation."""
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

    # Verify template contains expected sections
    assert "# Role" in result.template
    assert "Code Debugger" in result.template
    assert "# Task" in result.template
    assert "Fix the null pointer" in result.template


def test_complex_refactor_template():
    """Test complex refactor template generation."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="refactor"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.COMPLEX)
    )

    request = NLaCRequest(
        idea="Optimize the database queries",
        mode="nlac",
        complexity="complex"
    )

    result = builder.build(request)

    # Complex refactor should use RaR
    assert result.strategy_meta["rar_used"] is True
    assert "# Role" in result.template


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
        context="This is a React component using hooks"
    )

    result = builder.build(request)

    # Context should be included
    assert "# Context" in result.template
    assert "React component" in result.template


def test_template_with_code_input():
    """Test template generation with code snippet input."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Fix this",
        mode="nlac",
        complexity="simple",
        inputs={
            "code_snippet": "def foo():\n    return bar",
            "error_log": "NameError: name 'bar' is not defined"
        }
    )

    result = builder.build(request)

    # Code and error should be included
    assert "# Code" in result.template
    assert "def foo():" in result.template
    assert "# Error" in result.template


def test_template_with_fewshot_examples():
    """Test template generation includes few-shot examples."""
    from hemdov.domain.services.knn_provider import FewShotExample

    mock_examples = [
        FewShotExample(
            input_idea="Fix bug",
            input_context="",
            improved_prompt="Debugged prompt",
            role="Debugger",
            directive="Find the bug",
            framework="chain-of-thought",
            guardrails=["Check edge cases"]
        )
    ]

    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: mock_examples),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Fix this error",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    # Few-shot examples should be included
    assert result.strategy_meta["fewshot_count"] == 1
    assert result.strategy_meta["knn_enabled"] is True


def test_strategy_selection_table():
    """Test that strategy is selected correctly."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.SIMPLE)
    )

    request = NLaCRequest(
        idea="Test",
        mode="nlac",
        complexity="simple"
    )

    result = builder.build(request)

    # Verify strategy was selected
    assert result.strategy_meta["strategy"] in [
        "simple_debug", "moderate_debug", "complex_debug",
        "simple_refactor", "complex_refactor",
        "explain"
    ]


def test_role_injection():
    """Test that roles are injected based on intent/complexity."""
    builder = NLaCBuilder(
        knn_provider=Mock(find_examples=lambda **_: []),
        intent_classifier=Mock(return_value="debug"),
        complexity_analyzer=Mock(return_value=ComplexityLevel.COMPLEX)
    )

    request = NLaCRequest(
        idea="Test",
        mode="nlac",
        complexity="complex"
    )

    result = builder.build(request)

    # Role should be in template
    assert "# Role" in result.template
    assert result.strategy_meta["role"]
```

### Step 2: Run tests

```bash
pytest tests/test_nlac_builder.py -v
```

### Step 3: Fix any implementation issues

### Step 4: Run tests to verify all pass

```bash
pytest tests/test_nlac_builder.py -v
```

### Step 5: Commit

```bash
git add tests/test_nlac_builder.py
git commit -m "test(nlac-builder): add comprehensive template generation tests

Tests cover:
- PromptObject creation
- Simple/complex template generation
- Context inclusion
- Code snippet handling
- Few-shot example integration
- Strategy selection
- Role injection

Related: CM review findings - critical service untested"
```

---

## Task 9: Add Core Service Test Coverage - ReflexionService

**Issue:** ReflexionService has ZERO test coverage.

**Files:**
- Create: `tests/test_reflexion_service.py`
- Reference: `hemdov/domain/services/reflexion_service.py`

### Step 1: Write the test file

```python
# tests/test_reflexion_service.py

import pytest
from unittest.mock import Mock
from hemdov.domain.services.reflexion_service import ReflexionService, ReflexionResult


def test_refine_returns_result():
    """Test that refine() returns a ReflexionResult."""
    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="fixed code")),
        executor=Mock(execute=Mock(return_value=(True, None)))
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
        (False, "still broken"),  # First attempt fails
        (True, None)  # Second attempt succeeds
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
    executor = Mock()
    executor.execute.return_value = (False, "always fails")

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
    assert len(result.error_history) == 3


def test_refine_without_executor():
    """Test that refinement works without executor (code generation only)."""
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

    # Without executor, always succeeds
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
            prompt=None,  # None not allowed
            error_type="RuntimeError",
            error_message="error"
        )

    with pytest.raises(TypeError):
        service.refine(
            prompt=123,  # Must be string
            error_type="RuntimeError",
            error_message="error"
        )

    with pytest.raises(ValueError):
        service.refine(
            prompt="code",
            error_type="RuntimeError",
            error_message="error",
            max_iterations=0  # Must be >= 1
        )

    with pytest.raises(ValueError):
        service.refine(
            prompt="code",
            error_type="RuntimeError",
            error_message="error",
            max_iterations=6  # Must be <= 5
        )


def test_refine_tracks_error_history():
    """Test that errors are tracked in history."""
    executor = Mock()
    executor.execute.return_value = (False, "error message")

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
    assert "error message" in result.error_history


def test_refine_handles_llm_failure():
    """Test that LLM failures are handled gracefully."""
    from hemdov.domain.exception_utils import LLMProviderError

    service = ReflexionService(
        llm_client=Mock(generate=Mock(side_effect=ConnectionError("LLM down"))),
        executor=Mock()
    )

    result = service.refine(
        prompt="code",
        error_type="RuntimeError",
        error_message="error",
        max_iterations=2
    )

    # Should handle LLM failure and return unsuccessful result
    assert result.success is False
    assert result.iteration_count == 1


def test_refine_builds_feedback_prompt():
    """Test that feedback prompt includes error context."""
    executor = Mock()
    executor.execute.return_value = (False, "NameError: name 'x' is not defined")

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="fixed code")),
        executor=executor
    )

    result = service.refine(
        prompt="def foo():\n    return x",
        error_type="NameError",
        error_message="name 'x' is not defined",
        max_iterations=2
    )

    # Verify executor was called with refined prompt
    assert executor.execute.call_count == 2


def test_refine_with_initial_context():
    """Test that initial context is included in first prompt."""
    executor = Mock()
    executor.execute.return_value = (True, None)

    service = ReflexionService(
        llm_client=Mock(generate=Mock(return_value="code")),
        executor=executor
    )

    initial_context = "This is a Python function using numpy"

    result = service.refine(
        prompt="optimize this",
        error_type="PerformanceWarning",
        error_message="slow loop",
        initial_context=initial_context,
        max_iterations=1
    )

    assert result.success is True
```

### Step 2: Run tests

```bash
pytest tests/test_reflexion_service.py -v
```

### Step 3: Fix any implementation issues

### Step 4: Run tests to verify all pass

```bash
pytest tests/test_reflexion_service.py -v
```

### Step 5: Commit

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
- LLM failure handling
- Feedback prompt building
- Initial context inclusion

Related: CM review findings - critical service untested"
```

---

## Task 10: Add Core Service Test Coverage - OPROOptimizer

**Issue:** OPROOptimizer has ZERO test coverage.

**Files:**
- Create: `tests/test_oprop_optimizer.py`
- Reference: `hemdov/domain/services/oprop_optimizer.py`

### Step 1: Write the test file

```python
# tests/test_oprop_optimizer.py

import pytest
from unittest.mock import Mock, MagicMock
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


def test_optimize_returns_prompt_object():
    """Test that optimize() returns a PromptObject."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Optimized prompt"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    result = optimizer.optimize(
        user_input="Write a function to sort a list",
        intent="generate",
        complexity="simple"
    )

    # Verify result structure
    assert result.template
    assert result.intent_type == "generate"


def test_optimize_uses_fewshot_examples():
    """Test that few-shot examples are fetched and used."""
    from hemdov.domain.services.knn_provider import FewShotExample

    mock_examples = [
        FewShotExample(
            input_idea="Create a function",
            input_context="",
            improved_prompt="Write a Python function that...",
            role="Developer",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Include type hints"]
        )
    ]

    mock_llm = Mock()
    mock_llm.generate.return_value = "Optimized prompt"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = mock_examples

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=2
    )

    result = optimizer.optimize(
        user_input="Create a sorting function",
        intent="generate",
        complexity="simple"
    )

    # Verify KNN was called
    mock_knn.find_examples.assert_called_once()
    assert result.strategy_meta["knn_enabled"] is True
    assert result.strategy_meta["fewshot_count"] >= 0


def test_optimize_runs_multiple_iterations():
    """Test that optimization runs for specified iterations."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Prompt v{iteration}"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=3
    )

    result = optimizer.optimize(
        user_input="Optimize this",
        intent="refactor",
        complexity="moderate"
    )

    # LLM should be called max_iterations times
    assert mock_llm.generate.call_count == 3


def test_optimize_tracks_failures():
    """Test that KNN failures are tracked."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Prompt"

    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("KNN down")

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=1
    )

    result = optimizer.optimize(
        user_input="Test",
        intent="debug",
        complexity="simple"
    )

    # Failure should be tracked
    assert len(optimizer._knn_failures) == 1
    assert optimizer._knn_failures[0]["error_type"] == "ConnectionError"


def test_optimize_validates_inputs():
    """Test that optimize() validates inputs."""
    optimizer = OPROOptimizer(
        llm_client=Mock(),
        knn_provider=Mock(),
        max_iterations=2
    )

    with pytest.raises(ValueError):
        optimizer.optimize(
            user_input="",  # Empty not allowed
            intent="generate",
            complexity="simple"
        )

    with pytest.raises(ValueError):
        optimizer.optimize(
            user_input="Test",
            intent="invalid",  # Invalid intent
            complexity="simple"
        )

    with pytest.raises(ValueError):
        optimizer.optimize(
            user_input="Test",
            intent="generate",
            complexity="invalid"  # Invalid complexity
        )


def test_optimize_without_llm():
    """Test behavior when LLM client is None."""
    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    optimizer = OPROOptimizer(
        llm_client=None,
        knn_provider=mock_knn,
        max_iterations=1
    )

    result = optimizer.optimize(
        user_input="Test",
        intent="generate",
        complexity="simple"
    )

    # Should still return a result (maybe default template)
    assert result.template


def test_optimize_meta_prompt_structure():
    """Test that meta-prompt includes required sections."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Optimized"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=1
    )

    result = optimizer.optimize(
        user_input="Write a sorting function",
        intent="generate",
        complexity="simple"
    )

    # LLM should have been called with a meta-prompt
    assert mock_llm.generate.call_count == 1
    call_args = mock_llm.generate.call_args[0][0]
    # Meta-prompt should contain user input
    assert "sorting function" in call_args.lower()


def test_optimize_with_different_intents():
    """Test optimization with different intents."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Prompt"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=1
    )

    for intent in ["debug", "refactor", "explain", "generate"]:
        result = optimizer.optimize(
            user_input=f"Test {intent}",
            intent=intent,
            complexity="simple"
        )
        assert result.intent_type == intent


def test_optimize_iteration_limit():
    """Test that max_iterations is respected (1-5)."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Prompt"

    mock_knn = Mock()
    mock_knn.find_examples.return_value = []

    # Test minimum
    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=1
    )
    optimizer.optimize("Test", "generate", "simple")
    assert mock_llm.generate.call_count == 1

    # Test maximum
    mock_llm.reset_mock()
    optimizer = OPROOptimizer(
        llm_client=mock_llm,
        knn_provider=mock_knn,
        max_iterations=5
    )
    optimizer.optimize("Test", "generate", "simple")
    assert mock_llm.generate.call_count == 5
```

### Step 2: Run tests

```bash
pytest tests/test_oprop_optimizer.py -v
```

### Step 3: Fix any implementation issues

### Step 4: Run tests to verify all pass

```bash
pytest tests/test_oprop_optimizer.py -v
```

### Step 5: Commit

```bash
git add tests/test_oprop_optimizer.py
git commit -m "test(oprop): add comprehensive meta-optimization tests

Tests cover:
- Basic optimization flow
- Few-shot example integration
- Multiple iteration handling
- KNN failure tracking
- Input validation
- No-LLM mode
- Meta-prompt structure
- Different intent types
- Iteration limits (1-5)

Related: CM review findings - critical service untested"
```

---

## Task 11: Run Full Test Suite and Verify Coverage

**Files:**
- Run: All tests
- Verify: Coverage metrics

### Step 1: Run full test suite

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

### Step 2: Run coverage report

```bash
pytest tests/ --cov=hemdov/domain --cov-report=term-missing
```

Expected: Coverage for domain services should be significantly higher

### Step 3: Review coverage report

Check that previously untested services now have coverage:
- `services/intent_classifier.py`
- `services/complexity_analyzer.py`
- `services/nlac_builder.py`
- `services/reflexion_service.py`
- `services/oprop_optimizer.py`

### Step 4: Document coverage improvements

```bash
git add tests/
git commit -m "test(docs): document coverage improvements from domain layer fixes

Added comprehensive test coverage for 5 core services that previously
had ZERO tests:
- IntentClassifier (routing logic)
- ComplexityAnalyzer (classification)
- NLaCBuilder (template generation)
- ReflexionService (iterative refinement)
- OPROOptimizer (meta-optimization)

All tests follow TDD principles with descriptive names and
edge case coverage.

Related: CM review findings 2026-01-15"
```

---

## Task 12: Update Documentation and CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (if needed)
- Modify: `docs/api-error-handling.md` (if needed)

### Step 1: Review if any documentation needs updates

Check if the fixes reveal any patterns that should be documented.

### Step 2: Update docs if needed

If new error handling patterns emerged, document them in `docs/api-error-handling.md`.

### Step 3: Commit any doc updates

```bash
git add CLAUDE.md docs/api-error-handling.md
git commit -m "docs: update error handling patterns from domain fixes

Documented patterns discovered during critical fixes:
- Distinguish transient failures from code bugs
- Log before defaulting values
- Don't mutate frozen objects

Related: CM review findings 2026-01-15"
```

---

## Completion Checklist

After all tasks complete:

```bash
# Run full test suite
make test

# Run quality gates
make eval

# Verify git history
git log --oneline -10

# Check coverage
pytest tests/ --cov=hemdov/domain --cov-report=term-missing
```

**Success Criteria:**
- [ ] All 12 tasks completed
- [ ] All tests pass
- [ ] Coverage increased for core services
- [ ] No silent failures remain
- [ ] Error handling follows CLAUDE.md rules
- [ ] Commits are clean with descriptive messages

---

## Related Skills

- `superpowers:executing-plans` - For executing this plan
- `superpowers:receiving-code-review` - For processing review feedback
- `superpowers:test-driven-development` - For TDD workflow
- `superpowers:systematic-debugging` - If tests reveal bugs

---

**Plan complete and saved to `docs/plans/2026-01-15-domain-layer-critical-fixes.md`**
