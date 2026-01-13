# Fix KNN Silent Failures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix silent fallback behaviors in KNN provider that cause degraded prompt quality without user awareness

**Architecture:** The KNNProvider currently has three silent failure modes that return poor-quality results: (1) fallback to first-k examples when vectorizer uninitialized, (2) fallback to top-k below similarity threshold, (3) empty examples when KNN fails but logged and continued. Fix by making these failures explicit with error propagation and metadata.

**Tech Stack:** Python 3.14, pytest, numpy, DSPy KNNFewShot

---

## Task 1: Make Vectorizer Initialization Mandatory

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:231-250`
- Test: `tests/test_knn_provider.py`

**Context:** Currently when `_initialize_knn()` has no examples, it logs a warning and leaves `_vectorizer = None`. This causes silent fallback in `find_examples()` to return random first-k examples.

**Step 1: Write failing test for empty vectorizer**

```python
# Add to tests/test_knn_provider.py

def test_knn_provider_raises_when_no_examples():
    """KNNProvider should raise RuntimeError when catalog has no valid examples."""
    import tempfile
    import json
    from pathlib import Path

    # Create temporary catalog with no valid examples
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        empty_catalog = {
            "examples": [
                {
                    "inputs": {"original_idea": "test"},
                    "outputs": {"improved_prompt": "test"}
                    # Missing required fields - will be skipped
                }
            ]
        }
        json.dump(empty_catalog, f)
        catalog_path = Path(f.name)

    try:
        # Should raise RuntimeError, not return with None vectorizer
        with pytest.raises(RuntimeError, match="No valid examples"):
            from hemdov.domain.services.knn_provider import KNNProvider
            KNNProvider(catalog_path=catalog_path)
    finally:
        catalog_path.unlink()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_knn_provider.py::test_knn_provider_raises_when_no_examples -v`

Expected: FAIL (currently returns with warning instead of raising)

**Step 3: Implement raise in _initialize_knn**

Modify `hemdov/domain/services/knn_provider.py:234-235`:

```python
def _initialize_knn(self) -> None:
    """Initialize vectorizer for semantic search and pre-compute catalog vectors."""
    if not self._dspy_examples:
        raise RuntimeError(
            "KNNProvider cannot initialize: No DSPy examples available. "
            "This indicates catalog loading failed or produced no valid examples. "
            f"Catalog path: {self.catalog_path}, examples loaded: {len(self.catalog)}"
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_knn_provider.py::test_knn_provider_raises_when_no_examples -v`

Expected: PASS

**Step 5: Add test for vectorizer failure in find_examples**

```python
# Add to tests/test_knn_provider.py

def test_find_examples_raises_when_vectorizer_none(monkeypatch):
    """find_examples should raise RuntimeError when vectorizer is None."""
    from hemdov.domain.services.knn_provider import KNNProvider

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Mock vectorizer to None to simulate initialization failure
    monkeypatch.setattr(provider, '_vectorizer', None)

    # Should raise RuntimeError, not return first-k examples
    with pytest.raises(RuntimeError, match="vectorizer not initialized"):
        provider.find_examples(intent="explain", complexity="moderate", k=3)
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_raises_when_vectorizer_none -v`

Expected: FAIL (currently returns first-k with warning)

**Step 7: Implement raise in find_examples fallback**

Modify `hemdov/domain/services/knn_provider.py:349-352`:

```python
else:
    # Vectorizer not initialized - this is a critical failure
    raise RuntimeError(
        "KNNProvider vectorizer not initialized. "
        "Cannot perform semantic search. Check logs for initialization errors."
    )
```

**Step 8: Run test to verify it passes**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_raises_when_vectorizer_none -v`

Expected: PASS

**Step 9: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "fix(knn): make vectorizer initialization mandatory

- Raise RuntimeError when catalog has no valid examples
- Raise RuntimeError when vectorizer not initialized in find_examples
- Prevents silent fallback to random first-k examples

Fixes silent-failure-hunter issue #2"
```

---

## Task 2: Return Empty List When Similarity Threshold Not Met

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:326-348`
- Test: `tests/test_knn_provider.py`

**Context:** Currently when no examples meet the similarity threshold, the code returns top-k anyway with a warning. This hides the fact that semantic search failed.

**Step 1: Write failing test for threshold behavior**

```python
# Add to tests/test_knn_provider.py

def test_find_examples_returns_empty_when_threshold_not_met(monkeypatch):
    """find_examples should return empty list when no examples meet similarity threshold."""
    from hemdov.domain.services.knn_provider import KNNProvider
    from unittest.mock import patch
    import numpy as np

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Mock similarity calculation to return all zeros (no matches)
    with patch.object(np, 'dot', return_value=np.array([0.0, 0.0, 0.0])):
        result = provider.find_examples(
            intent="explain",
            complexity="moderate",
            k=3,
            min_similarity=0.5  # High threshold that won't be met
        )

    # Should return empty list, not fallback to top-k
    assert result == []
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_returns_empty_when_threshold_not_met -v`

Expected: FAIL (currently returns top-k below threshold)

**Step 4: Implement empty list return**

Modify `hemdov/domain/services/knn_provider.py:330-336`:

```python
# Filter by minimum similarity threshold (relevance filtering)
relevant_mask = similarities >= min_similarity
relevant_indices = np.where(relevant_mask)[0]

if len(relevant_indices) == 0:
    logger.warning(
        f"No examples met similarity threshold {min_similarity:.2f}. "
        f"Highest similarity: {similarities.max():.2f}. "
        f"Returning empty list - user input does not match any catalog examples."
    )
    return []  # Let caller decide how to handle no examples
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_returns_empty_when_threshold_not_met -v`

Expected: PASS

**Step 6: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "fix(knn): return empty list when similarity threshold not met

- Prevents returning irrelevant examples below threshold
- Caller can decide how to handle empty results
- Logs highest similarity achieved for debugging

Fixes silent-failure-hunter issue #1"
```

---

## Task 3: Add KNN Failure Metadata to PromptObject

**Files:**
- Modify: `hemdov/domain/dto/nlac_models.py`
- Modify: `hemdov/domain/services/nlac_builder.py:99-112`
- Test: `tests/test_nlac_builder_knn_integration.py`

**Context:** When KNN fails in NLaC Builder, we log and continue with empty examples. The caller can't distinguish this from "KNN ran but found no examples." Add metadata to track failures.

**Step 1: Add knn_failed field to PromptObject**

Read `hemdov/domain/dto/nlac_models.py` to find PromptObject class definition.

**Step 2: Add knn_failed field**

Add to PromptObject dataclass (after existing fields):

```python
@dataclass
class PromptObject:
    # ... existing fields ...
    updated_at: str
    knn_failed: bool = False  # Tracks if KNN provider failed to fetch examples
    knn_error: Optional[str] = None  # Error message if KNN failed
```

**Step 3: Write test for KNN failure metadata**

```python
# Add to tests/test_nlac_builder_knn_integration.py

def test_nlac_builder_includes_knn_failure_metadata():
    """NLaC Builder should include KNN failure metadata in PromptObject."""
    from hemdov.domain.dto.nlac_models import NLaCRequest
    from hemdov.domain.services.nlac_builder import NLaCBuilder
    from unittest.mock import Mock, patch
    from hemdov.domain.dto.nlac_models import IntentType

    # Create mock KNN provider that raises error
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("KNN backend unavailable")

    builder = NLaCBuilder(knn_provider=mock_knn)

    request = NLaCRequest(
        idea="test prompt",
        context="test context"
    )

    result = builder.build(request)

    # Should have metadata indicating KNN failed
    assert result.knn_failed is True
    assert "KNN backend unavailable" in result.knn_error or result.knn_error is not None
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_nlac_builder_knn_integration.py::test_nlac_builder_includes_knn_failure_metadata -v`

Expected: FAIL (fields don't exist yet)

**Step 5: Update NLaC Builder to track KNN failures**

Modify `hemdov/domain/services/nlac_builder.py:99-120`:

```python
# Step 5: Fetch KNN examples
knn_failed = False
knn_error = None
fewshot_examples: List[FewShotExample] = []

if self.knn_provider:
    k = 5 if complexity == ComplexityLevel.COMPLEX else 3
    has_expected_output = intent_str.startswith("refactor")

    try:
        fewshot_examples = self.knn_provider.find_examples(
            intent=intent_str,
            complexity=complexity.value,
            k=k,
            has_expected_output=has_expected_output,
            user_input=request.idea
        )
        logger.info(f"Fetched {len(fewshot_examples)} KNN examples for {intent_str}/{complexity.value}")
    except (RuntimeError, KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as e:
        logger.error(
            f"KNN provider failed for {intent_str}/{complexity.value}: {type(e).__name__}: {e}"
        )
        knn_failed = True
        knn_error = f"{type(e).__name__}: {str(e)[:100]}"
        # Continue with empty examples list
```

**Step 6: Add metadata to PromptObject creation**

Find where PromptObject is created (around line 135-150) and add the new fields:

```python
prompt_obj = PromptObject(
    # ... existing fields ...
    updated_at=datetime.now(UTC).isoformat(),
    knn_failed=knn_failed,
    knn_error=knn_error,
)
```

**Step 7: Run test to verify it passes**

Run: `uv run pytest tests/test_nlac_builder_knn_integration.py::test_nlac_builder_includes_knn_failure_metadata -v`

Expected: PASS

**Step 8: Commit**

```bash
git add hemdov/domain/dto/nlac_models.py hemdov/domain/services/nlac_builder.py tests/test_nlac_builder_knn_integration.py
git commit -m "feat(nlac): add KNN failure metadata to PromptObject

- Add knn_failed and knn_error fields to track KNN issues
- Enables monitoring and debugging of KNN reliability
- Caller can distinguish \"no examples\" from \"KNN failed\"

Fixes silent-failure-hunter issue #4"
```

---

## Task 4: Add KNN Failure Handling to OPRO Optimizer

**Files:**
- Modify: `hemdov/domain/services/oprop_optimizer.py:230-242`

**Context:** OPRO has the same silent failure issue as NLaC Builder. Since it's used for meta-prompts, KNN failures are especially impactful.

**Step 1: Write test for OPRO KNN failure handling**

```python
# Add to tests/test_opro_knn_integration.py (create if doesn't exist)

def test_oprop_handles_knn_failure_gracefully():
    """OPRO should handle KNN failures without crashing."""
    from hemdov.domain.dto.nlac_models import PromptObject
    from hemdov.domain.services.oprop_optimizer import OPROOptimizer
    from unittest.mock import Mock
    from datetime import datetime, UTC

    # Create mock KNN that fails
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("KNN unavailable")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    prompt_obj = PromptObject(
        id="test-1",
        version=1,
        intent_type="explain",
        template="Test prompt",
        strategy_meta={"intent": "explain", "complexity": "moderate"},
        constraints={},
        is_active=True,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )

    # Should not raise, should complete without few-shot examples
    result = optimizer.run_loop(prompt_obj)

    assert result is not None
    assert result.trajectory is not None
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_opro_knn_integration.py::test_oprop_handles_knn_failure_gracefully -v`

Expected: PASS (already handles gracefully with log + continue)

**Step 3: Improve OPRO error logging**

Modify `hemdov/domain/services/oprop_optimizer.py:236-242`:

```python
except (RuntimeError, KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as e:
    logger.error(
        f"KNN failed for OPRO meta-prompt: {type(e).__name__}: {e}. "
        f"Meta-prompt will proceed without few-shot examples "
        f"(may reduce optimization quality)."
    )
    fewshot_examples = []
```

**Step 4: Commit**

```bash
git add hemdov/domain/services/oprop_optimizer.py tests/test_opro_knn_integration.py
git commit -m "fix(opro): improve KNN failure logging in meta-prompts

- Clarify that meta-prompts without examples may have lower quality
- Already handles failures gracefully, just improved logging

Addresses silent-failure-hunter issue #5"
```

---

## Task 5: Add Catalog Skip Rate Threshold

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:214-224`

**Context:** When catalog examples fail validation, they're silently skipped. Add a threshold to raise error if too many fail.

**Step 1: Write test for high skip rate**

```python
# Add to tests/test_knn_provider.py

def test_knn_raises_when_skip_rate_high(monkeypatch, tmp_path):
    """KNNProvider should raise when >20% of catalog examples fail validation."""
    import json

    # Create catalog with mostly invalid examples
    catalog_path = tmp_path / "bad_catalog.json"

    bad_examples = []
    for i in range(10):
        # Only 2 valid examples, 8 invalid
        if i < 2:
            bad_examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            # Missing required fields
            bad_examples.append({"inputs": {}})

    with open(catalog_path, 'w') as f:
        json.dump({"examples": bad_examples}, f)

    # Should raise due to 80% skip rate
    with pytest.raises(RuntimeError, match="skip rate"):
        from hemdov.domain.services.knn_provider import KNNProvider
        KNNProvider(catalog_path=catalog_path)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_knn_provider.py::test_knn_raises_when_skip_rate_high -v`

Expected: FAIL (doesn't raise currently)

**Step 3: Implement skip rate check**

Modify `hemdov/domain/services/knn_provider.py:214-224`:

```python
if skipped_count > 0:
    skip_rate = skipped_count / len(examples_data)
    logger.warning(
        f"Loaded {len(self.catalog)} examples from ComponentCatalog "
        f"(skipped {skipped_count} invalid examples, {skip_rate:.1%} skip rate)"
    )

    # If more than 20% of examples are invalid, this is likely a schema issue
    if skip_rate > 0.2:
        raise ValueError(
            f"Catalog data quality issue: {skip_rate:.1%} of examples ({skipped_count}/{len(examples_data)}) "
            f"failed validation. This may indicate a schema mismatch or data corruption. "
            f"Check logs for details. Path: {self.catalog_path}"
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_knn_provider.py::test_knn_raises_when_skip_rate_high -v`

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "feat(knn): add catalog skip rate threshold

- Raises ValueError when >20% of examples fail validation
- Prevents silent data quality issues
- Helps catch schema mismatches early

Fixes silent-failure-hunter issue #3"
```

---

## Task 6: Validate User Input Before Use

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:296-300`

**Context:** Empty or whitespace-only user_input should be validated before adding to query.

**Step 1: Write test for empty user input**

```python
# Add to tests/test_knn_provider.py

def test_find_examples_ignores_empty_user_input():
    """find_examples should ignore empty or whitespace-only user_input."""
    from hemdov.domain.services.knn_provider import KNNProvider

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Empty string should be ignored
    result1 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        user_input="",
        k=2
    )

    # Whitespace-only should be ignored
    result2 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        user_input="   ",
        k=2
    )

    # Both should return same results as no user_input
    result3 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        k=2
    )

    # Results should be identical (same examples selected)
    assert len(result1) == len(result2) == len(result3)
```

**Step 2: Run test to verify behavior**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_ignores_empty_user_input -v`

Expected: May pass or fail depending on current behavior

**Step 3: Implement user input validation**

Modify `hemdov/domain/services/knn_provider.py:296-300`:

```python
# Transform query to vector - include user input for better semantic matching
query_parts = [intent, complexity]
if user_input and user_input.strip():  # Validate non-empty after stripping
    query_parts.append(user_input.strip())
query_text = " ".join(query_parts)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_knn_provider.py::test_find_examples_ignores_empty_user_input -v`

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "fix(knn): validate user input before adding to query

- Strips and validates user_input is non-empty
- Prevents empty strings from degrading semantic search

Addresses silent-failure-hunter issue #8"
```

---

## Summary

This plan addresses 6 critical/high-priority silent failure issues:

1. **Vectorizer mandatory** - Raises error when not initialized
2. **Threshold enforcement** - Returns empty list instead of below-threshold results
3. **NLaC metadata** - Tracks KNN failures in PromptObject
4. **OPRO logging** - Improved failure messages
5. **Catalog quality** - Raises when >20% skip rate
6. **Input validation** - Strips and validates user_input

All changes follow TDD with tests written first, maintain backward compatibility where possible, and include proper error propagation instead of silent fallbacks.

**Total estimated time:** 2-3 hours
**Test coverage:** Adds 7 new tests
**Risk level:** Low (all changes are additive or make failures explicit)
