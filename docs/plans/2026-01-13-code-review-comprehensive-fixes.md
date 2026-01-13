# Code Review Findings - Comprehensive Implementation Plan (REVISED)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address ALL findings from 4 code review agents: silent failures, domain layer violations, code duplication, and missing test coverage.

**Architecture:** Fix issues in dependency order (foundation → refactoring → features), maintaining hexagonal architecture principles and TDD workflow.

**Tech Stack:** Python 3.11+, pytest, DSPy, Pydantic

**Review Agents Analyzed:**
- `/code-review` (confidence-scoring)
- `pr-test-analyzer` (test coverage)
- `silent-failure-hunter` (error handling)
- `code-simplifier` (refactoring)

**Plan Evaluation:** 5 reviewers (sequential thinking + 4 agents) provided feedback. This REVISED plan incorporates all recommendations.

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 3 | Domain I/O violation, NLaCBuilder silent KNN failure, OPROOptimizer silent KNN failure |
| HIGH | 3 | Empty return without metadata, catalog skip threshold, test coverage gaps |
| MEDIUM | 9 | Cache fallback, logging consistency, type annotations, code clarity, duplication |
| LOW | 4 | Magic numbers, unused code, formatting, string validation |
| POSITIVE | 15 | Strengths to maintain |

**Total Issues:** 19 items requiring attention

**Estimated Time:** ~3-4 hours (revised from original 6.5h based on analysis that some tasks are partially complete and can be consolidated)

**Key Changes from Original Plan:**
- ✅ Reordered: Repository layer (Task 3) is now FIRST - foundational architecture fix
- ✅ Integrated TDD: Tests embedded in each task, not separate phase
- ✅ Consolidated: Related tasks merged for efficiency
- ✅ Verified: Current code state checked - some items partially done
- ✅ Detailed: Added schema specifications and code examples

---

## Plan Evaluation Summary

### What the Reviewers Found

| Reviewer | Key Finding | Impact |
|----------|-------------|--------|
| **Sequential Thinking** | Task dependencies wrong; Task 3 should be first | 🔴 CRITICAL |
| **Type-Design Analyzer** | Architecture violations persist until Task 3 | 🔴 CRITICAL |
| **Comment Analyzer** | Missing DTO field specifications | ⚠️ IMPORTANT |
| **Test Analyzer** | Plan violates TDD (tests in Phase 5) | 🔴 CRITICAL |
| **Code Simplifier** | Some tasks already complete; can consolidate | ⚠️ IMPORTANT |

### Corrections Applied

1. **Reordered phases** to respect dependencies
2. **Integrated TDD** into each task (test → implement → refactor)
3. **Added detailed specifications** for DTO fields
4. **Consolidated related tasks** to reduce context switching
5. **Verified current state** of codebase
6. **Added rollback strategies** for risky tasks

---

## Current State Verification

**Checked against recent commits:**
- ✅ Commit `6308bae`: Added `knn_failed`/`knn_error` to PromptObject (partial - not exposed to API)
- ✅ Commit `a821b66`: Added catalog skip rate threshold (partial - ERROR logging at 5% not added)
- ✅ Commit `6d24989`: Improved KNN failure logging in meta-prompts (partial - not tracked in OptimizeResponse)
- ✅ Commit `66af950`: Returns empty list when threshold not met (partial - without metadata)
- ✅ Commit `8343afc`: Validates user input before adding to query (complete ✅)
- ✅ Commit `a560015`: Made vectorizer initialization mandatory (complete ✅)

**Status:** Some CRITICAL items are partially done but need completion (expose to API responses, add metadata, ERROR logging).

---

## Consolidated Implementation Tasks

### Phase 0: FOUNDATION (Must Complete First - 30 min)

#### Task 0.1: Create Repository Layer for Catalog Loading ⭐ FIRST

**Addresses:** code-review CRITICAL #1, silent-failure-hunter architecture concern
**Priority:** BLOCKING - Must be done before any other KNN-related work
**Why First:** Foundational architecture fix; affects all KNN-dependent code

**Files:**
- Create: `hemdov/infrastructure/repositories/catalog_repository.py`
- Modify: `hemdov/domain/services/knn_provider.py:105-238`
- Test: `tests/test_catalog_repository.py` (to be created)

**TDD Step 1: Write failing tests**

```python
# Create: tests/test_catalog_repository.py
import pytest
from pathlib import Path
from hemdov.infrastructure.repositories.catalog_repository import (
    FileSystemCatalogRepository,
    CatalogRepositoryInterface
)

def test_repository_loads_valid_catalog(tmp_path):
    """Given: Valid catalog file with examples
    When: Load catalog
    Then: Returns list of example dictionaries"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": [{"inputs": {"original_idea": "test"}, "outputs": {"improved_prompt": "improved"}}]}')

    repo = FileSystemCatalogRepository(catalog_file)
    data = repo.load_catalog()

    assert len(data) == 1
    assert data[0]["inputs"]["original_idea"] == "test"

def test_repository_raises_on_missing_file(tmp_path):
    """Given: Catalog file doesn't exist
    When: Load catalog
    Then: Raises FileNotFoundError"""
    repo = FileSystemCatalogRepository(tmp_path / "nonexistent.json")

    with pytest.raises(FileNotFoundError):
        repo.load_catalog()

def test_repository_handles_list_format(tmp_path):
    """Given: Catalog in list format (no wrapper)
    When: Load catalog
    Then: Returns list correctly"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('[{"inputs": {"original_idea": "test"}, "outputs": {"improved_prompt": "improved"}}]')

    repo = FileSystemCatalogRepository(catalog_file)
    data = repo.load_catalog()

    assert len(data) == 1

def test_repository_raises_on_invalid_format(tmp_path):
    """Given: Catalog with invalid format
    When: Load catalog
    Then: Raises ValueError with 'Invalid catalog format'"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"invalid": "format"}')

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(ValueError, match="Invalid catalog format"):
        repo.load_catalog()

def test_repository_handles_permission_error(tmp_path):
    """Given: Catalog file with no read permissions
    When: Load catalog
    Then: Raises RuntimeError with permission error"""
    import os
    import stat

    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": []}')
    os.chmod(catalog_file, 0o000)

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(RuntimeError, match="PermissionError"):
        repo.load_catalog()

def test_repository_handles_json_decode_error(tmp_path):
    """Given: Catalog file with invalid JSON
    When: Load catalog
    Then: Raises ValueError with JSON decode info"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": [invalid json}')

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(ValueError, match="JSON"):
        repo.load_catalog()
```

**TDD Step 2: Run tests to verify they fail**

```bash
pytest tests/test_catalog_repository.py -v
# Expected: FAIL - repository doesn't exist yet
```

**TDD Step 3: Create repository interface and implementation**

```python
# Create: hemdov/infrastructure/repositories/catalog_repository.py
"""Catalog repository for loading few-shot examples from storage."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CatalogRepositoryInterface(ABC):
    """Interface for catalog data loading."""

    @abstractmethod
    def load_catalog(self) -> List[Dict[str, Any]]:
        """Load catalog data from storage.

        Returns:
            List of example dictionaries

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            RuntimeError: If file cannot be read
            ValueError: If JSON is invalid or format is wrong
        """
        pass


class FileSystemCatalogRepository(CatalogRepositoryInterface):
    """Load catalog from local filesystem.

    Follows existing PromptRepository pattern for consistency.
    """

    def __init__(self, catalog_path: Path):
        """Initialize with catalog file path.

        Args:
            catalog_path: Path to unified-fewshot-pool-v2.json
        """
        self.catalog_path = catalog_path

    def load_catalog(self) -> List[Dict[str, Any]]:
        """Load catalog data from JSON file.

        Returns:
            List of example dictionaries

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            RuntimeError: If file cannot be read
            ValueError: If JSON is invalid or format is wrong
        """
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"ComponentCatalog not found at {self.catalog_path}. "
                f"CatalogRepository cannot load catalog."
            )

        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(
                f"Failed to open ComponentCatalog at {self.catalog_path}. "
                f"Error: {type(e).__name__}: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from ComponentCatalog at {self.catalog_path}. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode ComponentCatalog at {self.catalog_path}. "
                f"Encoding error at position {e.start}: {e.reason}"
            ) from e

        # Handle wrapper format: {"examples": [...]}
        if isinstance(data, dict) and 'examples' in data:
            return data['examples']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(
                f"Invalid catalog format at {self.catalog_path}. "
                f"Expected dict with 'examples' key or list, got {type(data).__name__}"
            )
```

**TDD Step 4: Run tests to verify they pass**

```bash
pytest tests/test_catalog_repository.py -v
# Expected: PASS
```

**TDD Step 5: Refactor KNNProvider to use repository**

```python
# Modify: hemdov/domain/services/knn_provider.py:105-238

def __init__(
    self,
    catalog_path: Path = None,
    catalog_data: List[dict] = None,
    repository: CatalogRepositoryInterface = None,
    k: int = 3
):
    """
    Initialize KNNProvider with ComponentCatalog.

    Args:
        catalog_path: Path to unified-fewshot-pool-v2.json (legacy, creates repository)
        catalog_data: Pre-loaded catalog data (skip repository)
        repository: Catalog repository instance
        k: Default number of examples to retrieve

    **Backward Compatibility:** If repository is None and catalog_path is provided,
    creates FileSystemCatalogRepository automatically. If catalog_data is provided,
    uses it directly (useful for testing).
    """
    self.k = k
    self.catalog: List[FewShotExample] = []
    self._dspy_examples: List[dspy.Example] = []
    self._vectorizer: Optional[FixedVocabularyVectorizer] = None
    self._catalog_vectors: Optional[np.ndarray] = None

    # Determine data source with backward compatibility
    if catalog_data is not None:
        # Use pre-loaded data (testing path)
        examples_data = catalog_data
    elif repository is not None:
        # Use provided repository
        examples_data = repository.load_catalog()
    elif catalog_path is not None:
        # Legacy behavior: create repository (backward compatible)
        from hemdov.infrastructure.repositories.catalog_repository import FileSystemCatalogRepository
        repo = FileSystemCatalogRepository(catalog_path)
        examples_data = repo.load_catalog()
    else:
        raise ValueError("Must provide one of: catalog_path, catalog_data, or repository")

    self._load_catalog_from_data(examples_data)


def _load_catalog_from_data(self, examples_data: List[dict]) -> None:
    """Process catalog data (pure domain logic, no I/O).

    This method contains only domain logic - no file I/O, no network calls.
    All data is passed in as parameters.

    Args:
        examples_data: List of example dictionaries from repository
    """
    # ... existing processing logic ...
    # (Lines 162-236 from original _load_catalog, minus file I/O)
```

**TDD Step 6: Run existing tests to ensure backward compatibility**

```bash
pytest tests/test_knn_provider.py -v
# Expected: PASS (backward compatibility maintained)
```

**TDD Step 7: Write integration test**

```python
# Add to tests/test_catalog_repository.py
def test_knn_provider_with_repository(tmp_path):
    """Given: KNNProvider with repository
    When: Initialize and use KNNProvider
    Then: Works correctly with repository"""
    from hemdov.infrastructure.repositories.catalog_repository import FileSystemCatalogRepository
    from hemdov.domain.services.knn_provider import KNNProvider

    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": [{"inputs": {"original_idea": "debug code"}, "outputs": {"improved_prompt": "add logging"}}]}')

    repo = FileSystemCatalogRepository(catalog_file)
    provider = KNNProvider(repository=repo, k=1)

    examples = provider.find_examples(intent="debug", complexity="simple", k=1)

    assert len(examples) == 1
```

**TDD Step 8: Commit**

```bash
git add hemdov/infrastructure/repositories/ hemdov/domain/services/knn_provider.py tests/test_catalog_repository.py
git commit -m "feat(knn): create repository layer for catalog loading

- Add CatalogRepositoryInterface and FileSystemCatalogRepository
- Move file I/O from domain to infrastructure layer
- Refactor KNNProvider to accept repository or pre-loaded data
- Maintain backward compatibility with catalog_path parameter
- Add comprehensive repository tests (7 test cases)
- Add integration test for KNNProvider with repository

Addresses code-review CRITICAL #1: Domain layer I/O violation
Maintains hexagonal architecture principles
All tests pass with backward compatibility"
```

---

### Phase 1: REFACTORING (Prepare Foundation - 45 min)

#### Task 1.1: Extract Duplicate KNN Error Handling to Utility

**Addresses:** code-simplifier Priority 1 #1
**Why Now:** Reduces duplication before adding new features in Phase 2

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py` (add utility function)
- Modify: `hemdov/domain/services/nlac_builder.py:111-118`
- Modify: `hemdov/domain/services/oprop_optimizer.py:239-245`

**TDD Step 1: Write failing test for utility function**

```python
# Add to tests/test_knn_provider.py
def test_handle_knn_failure_returns_correct_tuple():
    """Given: KNN failure exception
    When: Call handle_knn_failure utility
    Then: Returns (failed=True, error_message)"""
    from hemdov.domain.services.knn_provider import handle_knn_failure
    import logging

    logger = logging.getLogger("test")
    exception = RuntimeError("vectorizer not initialized")

    failed, error = handle_knn_failure(logger, "test_context", exception)

    assert failed is True
    assert "RuntimeError" in error
    assert "vectorizer not initialized" in error
```

**TDD Step 2: Run test to verify it fails**

```bash
pytest tests/test_knn_provider.py::test_handle_knn_failure_returns_correct_tuple -v
# Expected: FAIL - utility doesn't exist yet
```

**TDD Step 3: Add utility function to KNNProvider**

```python
# Add at end of knn_provider.py (after line 366)

def handle_knn_failure(
    logger_instance: logging.Logger,
    context: str,
    exception: Exception
) -> tuple[bool, str]:
    """
    Handle KNN provider failures consistently.

    This utility provides uniform error handling across all KNN call sites,
    ensuring consistent logging and error messages.

    Args:
        logger_instance: Logger to use for error messages
        context: Description of where the failure occurred (e.g., "NLaCBuilder.build")
        exception: The exception that was caught

    Returns:
        Tuple of (failed: bool, error_message: str)

    Example:
        >>> failed, error = handle_knn_failure(logger, "test_context", RuntimeError("test"))
        >>> assert failed is True
        >>> assert "RuntimeError" in error
    """
    error_msg = f"KNN failure in {context}: {type(exception).__name__}: {exception}"
    logger_instance.error(
        f"{error_msg}. "
        f"Proceeding without few-shot examples "
        f"(may reduce prompt quality)."
    )
    return True, error_msg
```

**TDD Step 4: Update nlac_builder.py to use utility**

```python
# In nlac_builder.py, around line 111-118
from hemdov.domain.services.knn_provider import handle_knn_failure

# Replace existing try-except with:
try:
    fewshot_examples = self.knn_provider.find_examples(...)
    knn_failed = False
    knn_error = None
except (RuntimeError, KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as e:
    knn_failed, knn_error = handle_knn_failure(logger, "NLaCBuilder.build", e)
    fewshot_examples = []
```

**TDD Step 5: Update oprop_optimizer.py to use utility**

```python
# In oprop_optimizer.py, around line 239-245
from hemdov.domain.services.knn_provider import handle_knn_failure

# Replace existing try-except with:
try:
    fewshot_examples = self.knn_provider.find_examples(...)
except (RuntimeError, KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as e:
    knn_failed, knn_error = handle_knn_failure(logger, "OPROOptimizer._build_meta_prompt", e)
    fewshot_examples = []
```

**TDD Step 6: Run tests to verify they pass**

```bash
pytest tests/test_knn_provider.py tests/test_nlac_builder_knn_integration.py tests/test_opro_knn_integration.py -v
# Expected: PASS
```

**TDD Step 7: Commit**

```bash
git add hemdov/domain/services/knn_provider.py hemdov/domain/services/nlac_builder.py hemdov/domain/services/oprop_optimizer.py tests/test_knn_provider.py
git commit -m "refactor(knn): extract duplicate KNN error handling to utility

- Add handle_knn_failure() utility to KNNProvider
- Update NLaCBuilder to use utility
- Update OPROOptimizer to use utility
- 75% reduction in duplicated error handling code
- Add test for utility function

Addresses code-simplifier Priority 1 #1
All existing tests pass"
```

---

#### Task 1.2: Add Named Constants for Magic Numbers (Includes Type Annotations)

**Addresses:** code-simplifier Priority 1 #3, code-review IMPORTANT #2
**Why Now:** Needed by Task 2.4 (ERROR logging)
**Consolidates:** Tasks 6, 8, 13, 17 from original plan

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:80-270`

**TDD Step 1: Add constants with documentation and type annotations**

```python
# Add after KNNProvider class definition (around line 104)
class KNNProvider:
    """KNN-based few-shot example provider.

    Provides semantic search functionality over the unified few-shot pool
    using DSPy's KNNFewShot vector similarity.
    """

    # Similarity threshold for relevance filtering
    # Character bigram similarity is less precise than embeddings,
    # so threshold is conservative (10% minimum similarity)
    MIN_SIMILARITY_THRESHOLD: float = 0.1

    # Catalog quality thresholds
    # At 5% skip rate, log ERROR (proactive monitoring for schema drift)
    # At 20% skip rate, raise ValueError (critical data quality issue)
    SKIP_RATE_ERROR_THRESHOLD: float = 0.05   # 5% - log ERROR
    SKIP_RATE_CRITICAL_THRESHOLD: float = 0.2  # 20% - raise ValueError

    # Vector computation constants
    # Floating-point epsilon for division safety when computing cosine similarity
    NORM_ZERO_THRESHOLD: float = 1e-10
```

**TDD Step 2: Update usages throughout the file**

```python
# Line ~222: Update skip rate check
if skip_rate > self.SKIP_RATE_CRITICAL_THRESHOLD:
    raise ValueError(...)

# Add ERROR logging at line ~215
if skip_rate >= self.SKIP_RATE_ERROR_THRESHOLD:
    logger.error(...)
else:
    logger.warning(...)

# Line ~336: Update division by zero check
similarities = np.where(
    (query_norm > self.NORM_ZERO_THRESHOLD) & (candidate_norms > self.NORM_ZERO_THRESHOLD),
    similarities,
    0
)
```

**TDD Step 3: Run tests to verify no regression**

```bash
pytest tests/test_knn_provider.py -v
# Expected: PASS
```

**TDD Step 4: Commit**

```bash
git add hemdov/domain/services/knn_provider.py
git commit -m "refactor(knn): add named constants with type annotations

- Add MIN_SIMILARITY_THRESHOLD with type annotation
- Add SKIP_RATE_ERROR_THRESHOLD (5%) for proactive monitoring
- Add SKIP_RATE_CRITICAL_THRESHOLD (20%) for critical issues
- Add NORM_ZERO_THRESHOLD for floating-point safety
- Document why each threshold exists
- Improves maintainability and tunability

Addresses code-simplifier Priority 1 #3
Addresses code-review IMPORTANT #2
All tests pass"
```

---

#### Task 1.3: Refactor find_examples into Smaller Methods

**Addresses:** code-simplifier Priority 1 #2
**Why Now:** Reduce complexity before changing interface in Phase 2

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:268-366`

**TDD Step 1: Write regression tests covering ALL current behavior**

```python
# Add to tests/test_knn_provider.py
def test_find_examples_with_valid_input():
    """Given: Valid intent, complexity, k
    When: Call find_examples
    Then: Returns k examples with highest similarity"""
    provider = KNNProvider(catalog_path=CATALOG_PATH)

    examples = provider.find_examples(intent="debug", complexity="simple", k=3)

    assert len(examples) <= 3
    assert all(isinstance(ex, FewShotExample) for ex in examples)

def test_find_examples_with_empty_user_input():
    """Given: Empty user_input string
    When: Call find_examples
    Then: Ignores user_input and returns examples"""
    provider = KNNProvider(catalog_path=CATALOG_PATH)

    examples = provider.find_examples(intent="debug", complexity="simple", k=3, user_input="  ")

    assert len(examples) > 0

def test_find_examples_returns_empty_when_threshold_not_met():
    """Given: Very high similarity threshold
    When: Call find_examples
    Then: Returns empty list"""
    provider = KNNProvider(catalog_path=CATALOG_PATH)

    examples = provider.find_examples(intent="debug", complexity="simple", k=3, min_similarity=0.99)

    assert len(examples) == 0

def test_find_examples_filters_by_expected_output():
    """Given: has_expected_output=True
    When: Call find_examples
    Then: Returns only examples with expected_output"""
    provider = KNNProvider(catalog_path=CATALOG_PATH)

    examples = provider.find_examples(intent="refactor", complexity="moderate", k=5, has_expected_output=True)

    assert all(ex.expected_output is not None for ex in examples)
```

**TDD Step 2: Run tests to establish baseline**

```bash
pytest tests/test_knn_provider.py::test_find_examples_with_valid_input -v
pytest tests/test_knn_provider.py::test_find_examples_with_empty_user_input -v
pytest tests/test_knn_provider.py::test_find_examples_returns_empty_when_threshold_not_met -v
pytest tests/test_knn_provider.py::test_find_examples_filters_by_expected_output -v
# Expected: All PASS (baseline behavior)
```

**TDD Step 3: Extract _filter_candidates method**

```python
# Add to KNNProvider class
def _filter_candidates(
    self,
    has_expected_output: bool
) -> List[FewShotExample]:
    """Filter catalog by expected_output requirement.

    Args:
        has_expected_output: If True, only return examples with expected_output

    Returns:
        Filtered list of candidates. Empty list if catalog is empty or no matches.
    """
    candidates = self.catalog

    if has_expected_output:
        candidates = [ex for ex in candidates if ex.expected_output is not None]

    if not candidates:
        logger.warning("No examples found (catalog empty or filtered out)")

    return candidates
```

**TDD Step 4: Run tests to verify they still pass**

```bash
pytest tests/test_knn_provider.py -k find_examples -v
# Expected: PASS
```

**TDD Step 5: Extract _semantic_search method**

```python
# Add to KNNProvider class
def _semantic_search(
    self,
    candidates: List[FewShotExample],
    intent: str,
    complexity: str,
    k: int,
    user_input: Optional[str],
    min_similarity: float
) -> List[FewShotExample]:
    """Perform semantic search over candidates.

    Args:
        candidates: Filtered candidate examples
        intent: Intent type for query
        complexity: Complexity level for query
        k: Number of examples to return
        user_input: Optional user input for better matching
        min_similarity: Minimum similarity threshold

    Returns:
        List of k most similar examples, sorted by similarity

    Raises:
        RuntimeError: If vectorizer not initialized
    """
    if not self._vectorizer:
        raise RuntimeError(
            "KNNProvider vectorizer not initialized. "
            "Cannot perform semantic search."
        )

    # Build query vector
    query_parts = [intent, complexity]
    if user_input and user_input.strip():
        query_parts.append(user_input.strip())
    query_text = " ".join(query_parts)
    query_vector = self._vectorizer([query_text])[0]

    # Get candidate vectors
    if self._catalog_vectors is not None and candidates == self.catalog:
        candidate_vectors = self._catalog_vectors
    else:
        candidate_texts = [ex.input_idea for ex in candidates]
        candidate_vectors = self._vectorizer(candidate_texts)

    return self._compute_similarities(
        candidates, candidate_vectors, query_vector, k, min_similarity
    )
```

**TDD Step 6: Run tests to verify they still pass**

```bash
pytest tests/test_knn_provider.py -k find_examples -v
# Expected: PASS
```

**TDD Step 7: Extract _compute_similarities method**

```python
# Add to KNNProvider class
def _compute_similarities(
    self,
    candidates: List[FewShotExample],
    candidate_vectors: np.ndarray,
    query_vector: np.ndarray,
    k: int,
    min_similarity: float
) -> List[FewShotExample]:
    """Compute cosine similarities and filter by threshold.

    Args:
        candidates: Candidate examples
        candidate_vectors: Pre-computed vectors for candidates
        query_vector: Query vector
        k: Number of examples to return
        min_similarity: Minimum similarity threshold

    Returns:
        List of k most similar examples that meet threshold
    """
    # Calculate cosine similarity
    dot_products = np.dot(candidate_vectors, query_vector)
    query_norm = np.linalg.norm(query_vector)
    candidate_norms = np.linalg.norm(candidate_vectors, axis=1)

    # Safe division with epsilon
    similarities = dot_products / (query_norm * candidate_norms)
    similarities = np.where(
        (query_norm > self.NORM_ZERO_THRESHOLD) & (candidate_norms > self.NORM_ZERO_THRESHOLD),
        similarities,
        0
    )

    # Filter by threshold
    relevant_mask = similarities >= min_similarity
    relevant_indices = np.where(relevant_mask)[0]

    if len(relevant_indices) == 0:
        highest_sim = float(similarities.max()) if len(similarities) > 0 else 0.0
        logger.warning(
            f"No examples met similarity threshold {min_similarity:.2f}. "
            f"Highest similarity: {highest_sim:.2f}. "
            f"Returning empty list."
        )
        return []

    # Sort and return top k
    relevant_similarities = similarities[relevant_indices]
    sorted_relevant_idx = np.argsort(relevant_similarities)[::-1][:k]
    top_indices = relevant_indices[sorted_relevant_idx]

    logger.debug(
        f"KNN relevance filtering: {len(relevant_indices)}/{len(candidates)} examples "
        f"met threshold {min_similarity:.2f}, returning top {len(top_indices)}"
    )

    return [candidates[i] for i in top_indices]
```

**TDD Step 8: Simplify main find_examples method**

```python
# Replace existing find_examples with simplified version
def find_examples(
    self,
    intent: str,
    complexity: str,
    k: Optional[int] = None,
    has_expected_output: bool = False,
    user_input: Optional[str] = None,
    min_similarity: Optional[float] = None
) -> List[FewShotExample]:
    """Find k similar examples using semantic search.

    Note: Current catalog doesn't have intent/complexity metadata,
    so filtering is done via semantic similarity to the query.

    Args:
        intent: Intent type (debug, refactor, generate, explain)
        complexity: Complexity level (simple, moderate, complex)
        k: Number of examples to retrieve
        has_expected_output: Filter for examples with expected_output
        user_input: Optional user input for better semantic matching
        min_similarity: Minimum cosine similarity threshold

    Returns:
        List of FewShotExample sorted by similarity
    """
    k = k or self.k
    min_similarity = min_similarity if min_similarity is not None else self.MIN_SIMILARITY_THRESHOLD

    # Filter candidates
    candidates = self._filter_candidates(has_expected_output)

    # Early returns
    if not candidates or len(candidates) <= k:
        return candidates[:k]

    # Semantic search
    return self._semantic_search(candidates, intent, complexity, k, user_input, min_similarity)
```

**TDD Step 9: Run all regression tests**

```bash
pytest tests/test_knn_provider.py -k find_examples -v
# Expected: All PASS
```

**TDD Step 10: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "refactor(knn): break find_examples into smaller methods

- Extract _filter_candidates() for catalog filtering
- Extract _semantic_search() for search orchestration
- Extract _compute_similarities() for similarity math
- Add regression tests before refactoring
- Reduce cyclomatic complexity from 8 to 3
- Reduce method length from 90 to 35 lines
- Reduce nesting depth from 4 to 2

Addresses code-simplifier Priority 1 #2
All existing tests pass"
```

---

### Phase 2: FEATURES (Build on Clean Foundation - 45 min)

#### Task 2.1: Expose KNN Failure Metadata to NLaCResponse

**Addresses:** silent-failure-hunter CRITICAL #1
**Status:** Partially done (knn_failed in PromptObject) - need to expose to API

**Files:**
- Modify: `hemdov/domain/dto/nlac_models.py:274-307` (NLaCResponse)
- Modify: `hemdov/domain/services/nlac_builder.py:111-120`
- Test: `tests/test_nlac_builder_knn_integration.py`

**TDD Step 1: Write failing test for API response field**

```python
# Add to tests/test_nlac_builder_knn_integration.py
def test_nlac_response_exposes_knn_failure_to_api():
    """Given: KNNProvider fails with RuntimeError
    When: NLaCBuilder.build() is called
    Then: NLaCResponse includes knn_failure field with error details"""
    from hemdov.domain.services.nlac_builder import NLaCBuilder
    from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType

    # Mock KNNProvider that raises RuntimeError
    from unittest.mock import Mock, patch

    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.side_effect = RuntimeError("vectorizer not initialized")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Test prompt",
        context="Test context",
        mode="nlac"
    )

    response = builder.build(request)

    # Verify response has failure metadata
    assert response.knn_failure is not None
    assert response.knn_failure["failed"] is True
    assert "RuntimeError" in response.knn_failure["error"]
    assert "vectorizer not initialized" in response.knn_failure["error"]
```

**TDD Step 2: Run test to verify it fails**

```bash
pytest tests/test_nlac_builder_knn_integration.py::test_nlac_response_exposes_knn_failure_to_api -v
# Expected: FAIL - knn_failure field doesn't exist in NLaCResponse
```

**TDD Step 3: Add knn_failure field to NLaCResponse**

```python
# In nlac_models.py, add to NLaCResponse class (after line 306)
class NLaCResponse(BaseModel):
    # ... existing fields ...
    cache_hit: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )

    # KNN failure tracking (exposed to API users)
    knn_failure: Optional[dict] = Field(
        None,
        description="KNN failure details if few-shot retrieval failed. Contains {failed: bool, error: str}"
    )
```

**TDD Step 4: Update NLaCBuilder to populate knn_failure**

```python
# In nlac_builder.py, modify build() method
def build(self, request: NLaCRequest, **kwargs) -> NLaCResponse:
    # ... existing code ...

    # After prompt_obj is created, check for KNN failure
    knn_failure_data = None
    if prompt_obj.knn_failed:
        knn_failure_data = {
            "failed": True,
            "error": prompt_obj.knn_error or "Unknown KNN error"
        }

    return NLaCResponse(
        # ... existing fields ...
        knn_failure=knn_failure_data,
    )
```

**TDD Step 5: Run test to verify it passes**

```bash
pytest tests/test_nlac_builder_knn_integration.py::test_nlac_response_exposes_knn_failure_to_api -v
# Expected: PASS
```

**TDD Step 6: Add tests for all KNN error types**

```python
# Add more tests for comprehensive coverage
@pytest.mark.parametrize("error_type,error_msg", [
    (RuntimeError, "vectorizer error"),
    (ConnectionError, "network unreachable"),
    (TimeoutError, "request timed out"),
    (KeyError, "missing key"),
    (TypeError, "type error"),
    (ValueError, "invalid value"),
])
def test_nlac_response_exposes_all_knn_error_types(error_type, error_msg):
    """Given: KNNProvider fails with various error types
    When: NLaCBuilder.build() is called
    Then: All error types are exposed in knn_failure field"""
    from hemdov.domain.services.nlac_builder import NLaCBuilder
    from hemdov.domain.dto.nlac_models import NLaCRequest

    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.side_effect = error_type(error_msg)

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(idea="Test", context="Test", mode="nlac")

    response = builder.build(request)

    assert response.knn_failure is not None
    assert response.knn_failure["failed"] is True
    assert error_type.__name__ in response.knn_failure["error"]
```

**TDD Step 7: Run all tests**

```bash
pytest tests/test_nlac_builder_knn_integration.py -v
# Expected: All PASS
```

**TDD Step 8: Commit**

```bash
git add hemdov/domain/dto/nlac_models.py hemdov/domain/services/nlac_builder.py tests/test_nlac_builder_knn_integration.py
git commit -m "fix(nlac): expose KNN failure metadata in API responses

- Add knn_failure field to NLaCResponse DTO
- Update NLaCBuilder to populate knn_failure from PromptObject
- Add comprehensive tests for all KNN error types
- Users can now see when KNN fails and why

Addresses silent-failure-hunter CRITICAL #1
Builds on Task 1.1 error handling utility
All tests pass"
```

---

#### Task 2.2: Add KNN Failure Tracking to OptimizeResponse

**Addresses:** silent-failure-hunter CRITICAL #2
**Status:** Partially done (logging improved) - need to track in OptimizeResponse

**Files:**
- Modify: `hemdov/domain/dto/nlac_models.py:245-268` (OptimizeResponse)
- Modify: `hemdov/domain/services/oprop_optimizer.py:56-143`
- Test: `tests/test_opro_knn_integration.py`

**TDD Step 1: Write failing test for OptimizeResponse tracking**

```python
# Add to tests/test_opro_knn_integration.py
def test_opro_response_tracks_knn_failures():
    """Given: KNN fails during OPRO iteration
    When: Run optimization loop
    Then: OptimizeResponse includes knn_failure field"""
    from hemdov.domain.services.oprop_optimizer import OPROOptimizer
    from hemdov.domain.dto.nlac_models import PromptObject, IntentType

    # Mock KNN that fails
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = RuntimeError("KNN unavailable")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)
    prompt_obj = PromptObject(
        id="test-id",
        intent_type=IntentType.GENERATE,
        template="Test prompt",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )

    response = optimizer.run_loop(prompt_obj)

    # Verify KNN failure is tracked
    assert response.knn_failure is not None
    assert response.knn_failure["failed"] is True
    assert "KNN" in response.knn_failure["error"]

def test_opro_tracks_knn_failure_mid_iteration():
    """Given: KNN fails in iteration 2 (not iteration 1)
    When: Run optimization loop
    Then: OptimizeResponse.trajectory shows which iteration failed"""
    # Implementation similar to above, but KNN fails on second call
    ...
```

**TDD Step 2: Run tests to verify they fail**

```bash
pytest tests/test_opro_knn_integration.py::test_opro_response_tracks_knn_failures -v
# Expected: FAIL - knn_failure field doesn't exist in OptimizeResponse
```

**TDD Step 3: Add knn_failure field to OptimizeResponse**

```python
# In nlac_models.py, add to OptimizeResponse class (after line 267)
class OptimizeResponse(BaseModel):
    # ... existing fields ...
    model: Optional[str] = Field(None, description="Model used for optimization")

    # KNN failure tracking (exposed to API users)
    knn_failure: Optional[dict] = Field(
        None,
        description="KNN failure details if few-shot retrieval failed during optimization"
    )
```

**TDD Step 4: Update OPROOptimizer to track KNN failures**

```python
# In oprop_optimizer.py, modify run_loop() method
def run_loop(self, prompt_obj: PromptObject) -> OptimizeResponse:
    """Run OPRO optimization loop with early stopping."""
    trajectory: List[OPROIteration] = []
    best_score = 0.0
    best_prompt = prompt_obj
    knn_failure_occurred = False  # Track if KNN ever failed

    for i in range(1, self.MAX_ITERATIONS + 1):
        # ... existing code ...

        # In _generate_variation, check if KNN failed
        candidate = self._generate_variation(prompt_obj, trajectory)
        if candidate.knn_failed:
            knn_failure_occurred = True

    # Build response with KNN failure info
    knn_failure_info = None
    if knn_failure_occurred:
        knn_failure_info = {
            "failed": True,
            "error": "KNN failed during one or more optimization iterations"
        }

    return self._build_response(
        prompt_obj_id=prompt_obj.id,
        final_instruction=best_prompt.template,
        final_score=best_score,
        iteration_count=self.MAX_ITERATIONS,
        early_stopped=False,
        trajectory=trajectory,
        knn_failure=knn_failure_info,
    )
```

**TDD Step 5: Update _build_response signature**

```python
def _build_response(
    self,
    prompt_obj_id: str,
    final_instruction: str,
    final_score: float,
    iteration_count: int,
    early_stopped: bool,
    trajectory: List[OPROIteration],
    knn_failure: Optional[dict] = None,  # Add this parameter
) -> OptimizeResponse:
    """Build OptimizeResponse from optimization results."""
    return OptimizeResponse(
        prompt_id=prompt_obj_id,
        final_instruction=final_instruction,
        final_score=final_score,
        iteration_count=iteration_count,
        early_stopped=early_stopped,
        trajectory=trajectory,
        improved_prompt=final_instruction,
        total_latency_ms=None,
        backend="nlac-opro",
        model="oprop-optimizer",
        knn_failure=knn_failure,  # Add this field
    )
```

**TDD Step 6: Run tests to verify they pass**

```bash
pytest tests/test_opro_knn_integration.py -v
# Expected: PASS
```

**TDD Step 7: Commit**

```bash
git add hemdov/domain/dto/nlac_models.py hemdov/domain/services/oprop_optimizer.py tests/test_opro_knn_integration.py
git commit -m "fix(opro): track KNN failures in OptimizeResponse

- Add knn_failure field to OptimizeResponse DTO
- Track KNN failures during optimization iterations
- Update _build_response to include knn_failure parameter
- Add comprehensive tests for failure tracking
- Users can now see when optimization used KNN examples

Addresses silent-failure-hunter CRITICAL #2
Builds on Task 1.1 error handling utility
All tests pass"
```

---

#### Task 2.3: Return Similarity Metadata When No Examples Match

**Addresses:** silent-failure-hunter HIGH #4
**Status:** Partially done (returns empty list) - need to add metadata

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:80-92, 268-366`
- Modify: `hemdov/domain/services/nlac_builder.py`
- Test: `tests/test_knn_provider.py`

**TDD Step 1: Write failing tests for FindExamplesResult**

```python
# Add to tests/test_knn_provider.py
def test_find_examples_returns_metadata_when_empty():
    """Given: High similarity threshold (no matches)
    When: Call find_examples
    Then: Returns FindExamplesResult with metadata (highest_similarity, etc.)"""
    from hemdov.domain.services.knn_provider import KNNProvider, FindExamplesResult

    provider = KNNProvider(catalog_path=CATALOG_PATH)

    result = provider.find_examples(
        intent="debug",
        complexity="simple",
        k=3,
        min_similarity=0.99  # Very high threshold
    )

    # Verify it's a FindExamplesResult
    assert isinstance(result, FindExamplesResult)
    assert result.threshold_met is False
    assert len(result.examples) == 0
    assert result.total_candidates > 0
    assert 0.0 <= result.highest_similarity <= 1.0
    assert result.matched_count == 0

def test_find_examples_returns_metadata_when_matches():
    """Given: Normal similarity threshold
    When: Call find_examples
    Then: Returns FindExamplesResult with positive metadata"""
    from hemdov.domain.services.knn_provider import KNNProvider, FindExamplesResult

    provider = KNNProvider(catalog_path=CATALOG_PATH)

    result = provider.find_examples(intent="debug", complexity="simple", k=3)

    assert isinstance(result, FindExamplesResult)
    assert result.threshold_met is True
    assert len(result.examples) > 0
    assert result.matched_count > 0
    assert result.total_candidates >= result.matched_count
```

**TDD Step 2: Run tests to verify they fail**

```bash
pytest tests/test_knn_provider.py::test_find_examples_returns_metadata_when_empty -v
# Expected: FAIL - returns list, not FindExamplesResult
```

**TDD Step 3: Create FindExamplesResult dataclass**

```python
# Add after FewShotExample dataclass (around line 92)
@dataclass
class FindExamplesResult:
    """Result from KNNProvider.find_examples with metadata.

    This result object provides debugging information about why
    examples were or weren't returned, helping users understand
    catalog coverage and similarity matching.

    Attributes:
        examples: List of found examples (empty if no matches)
        total_candidates: Total number of candidates considered
        matched_count: Number of candidates that met similarity threshold
        highest_similarity: Highest similarity score found (useful for debugging)
        threshold_met: Whether any examples met the minimum similarity threshold
    """
    examples: List[FewShotExample]
    total_candidates: int
    matched_count: int
    highest_similarity: float
    threshold_met: bool
```

**TDD Step 4: Update find_examples to return FindExamplesResult**

```python
# Update find_examples method signature
def find_examples(
    self,
    intent: str,
    complexity: str,
    k: Optional[int] = None,
    has_expected_output: bool = False,
    user_input: Optional[str] = None,
    min_similarity: Optional[float] = None
) -> FindExamplesResult:  # Changed return type
```

**TDD Step 5: Update return statements throughout find_examples**

```python
# In _filter_candidates section:
candidates = self._filter_candidates(has_expected_output)

if not candidates:
    return FindExamplesResult(
        examples=[],
        total_candidates=0,
        matched_count=0,
        highest_similarity=0.0,
        threshold_met=False
    )

if len(candidates) <= k:
    return FindExamplesResult(
        examples=candidates[:k],
        total_candidates=len(candidates),
        matched_count=len(candidates),
        highest_similarity=1.0,
        threshold_met=True
    )

# In _compute_similarities section:
if len(relevant_indices) == 0:
    return FindExamplesResult(
        examples=[],
        total_candidates=len(candidates),
        matched_count=0,
        highest_similarity=highest_sim,
        threshold_met=False
    )

return FindExamplesResult(
    examples=[candidates[i] for i in top_indices],
    total_candidates=len(candidates),
    matched_count=len(relevant_indices),
    highest_similarity=highest_sim,
    threshold_met=True
)
```

**TDD Step 6: Update nlac_builder to handle FindExamplesResult**

```python
# In nlac_builder.py, update the call to find_examples
result = self.knn_provider.find_examples(
    intent=prompt_obj.intent_type.value,
    complexity=strategy_meta.get("complexity", "moderate"),
    k=3,
    has_expected_output=(prompt_obj.intent_type == IntentType.REFACTOR),
    user_input=request.idea
)

fewshot_examples = result.examples

# Log metadata for debugging
if not result.threshold_met:
    logger.warning(
        f"KNN found no matching examples. "
        f"Highest similarity: {result.highest_similarity:.2f}, "
        f"Total candidates: {result.total_candidates}. "
        f"Proceeding without few-shot examples."
    )
```

**TDD Step 7: Run tests to verify they pass**

```bash
pytest tests/test_knn_provider.py::test_find_examples_returns_metadata -v
# Expected: PASS
```

**TDD Step 8: Commit**

```bash
git add hemdov/domain/services/knn_provider.py hemdov/domain/services/nlac_builder.py tests/test_knn_provider.py
git commit -m "feat(knn): return similarity metadata when no examples match

- Add FindExamplesResult dataclass with metadata
- Include highest_similarity, matched_count, threshold_met
- Helps callers understand why no examples were returned
- Update nlac_builder to log similarity failures
- Add comprehensive tests for result metadata

Addresses silent-failure-hunter HIGH #4
Builds on Task 1.3 refactored find_examples
All tests pass"
```

---

#### Task 2.4: Add ERROR-Level Logging for Catalog Skip Rates >= 5%

**Addresses:** silent-failure-hunter HIGH #3
**Status:** Partially done (skip rate threshold exists) - need ERROR logging at 5%

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:214-227`
- Test: `tests/test_knn_provider.py`

**TDD Step 1: Write failing test for ERROR logging**

```python
# Add to tests/test_knn_provider.py
def test_catalog_skip_rate_logs_error_at_5_percent(monkeypatch, tmp_path, caplog):
    """Given: Catalog with 6% skip rate
    When: Load catalog
    Then: Logs ERROR (not WARNING)"""
    import logging

    catalog_file = tmp_path / "test-catalog.json"
    # 94 valid, 6 invalid = 6% skip rate
    valid_examples = [{"inputs": {"original_idea": f"test{i}"}, "outputs": {"improved_prompt": "improved"}} for i in range(94)]
    invalid_examples = [{"invalid": "data"} for _ in range(6)]
    catalog_file.write_text(json.dumps({"examples": valid_examples + invalid_examples}))

    # Capture ERROR logs
    with caplog.at_level(logging.ERROR):
        provider = KNNProvider(catalog_path=catalog_file)

    # Should log ERROR, not just WARNING
    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert any("quality degradation" in record.getMessage() for record in caplog.records if record.levelno == logging.ERROR)

def test_catalog_skip_rate_logs_warning_below_5_percent(tmp_path, caplog):
    """Given: Catalog with 3% skip rate
    When: Load catalog
    Then: Logs WARNING (not ERROR)"""
    import logging

    catalog_file = tmp_path / "test-catalog.json"
    # 97 valid, 3 invalid = 3% skip rate
    valid_examples = [{"inputs": {"original_idea": f"test{i}"}, "outputs": {"improved_prompt": "improved"}} for i in range(97)]
    invalid_examples = [{"invalid": "data"} for _ in range(3)]
    catalog_file.write_text(json.dumps({"examples": valid_examples + invalid_examples}))

    with caplog.at_level(logging.WARNING):
        provider = KNNProvider(catalog_path=catalog_file)

    # Should log WARNING, not ERROR
    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
```

**TDD Step 2: Run tests to verify they fail**

```bash
pytest tests/test_knn_provider.py::test_catalog_skip_rate_logs_error_at_5_percent -v
# Expected: FAIL - ERROR logging not implemented yet
```

**TDD Step 3: Add ERROR logging threshold**

```python
# In _load_catalog_from_data, around line 214
if skipped_count > 0:
    skip_rate = skipped_count / len(examples_data)

    # ERROR level for 5% or higher (proactive monitoring)
    if skip_rate >= self.SKIP_RATE_ERROR_THRESHOLD:
        logger.error(
            f"Catalog quality degradation detected: {skip_rate:.1%} of examples "
            f"({skipped_count}/{len(examples_data)}) failed validation. "
            f"This may indicate schema drift or data corruption. "
            f"Investigate catalog data source."
        )
    else:
        logger.warning(
            f"Loaded {len(self.catalog)} examples from ComponentCatalog "
            f"(skipped {skipped_count} invalid examples, {skip_rate:.1%} skip rate)"
        )

    # CRITICAL threshold at 20%
    if skip_rate > self.SKIP_RATE_CRITICAL_THRESHOLD:
        raise ValueError(...)
```

**TDD Step 4: Run tests to verify they pass**

```bash
pytest tests/test_knn_provider.py::test_catalog_skip_rate_logs_error_at_5_percent -v
pytest tests/test_knn_provider.py::test_catalog_skip_rate_logs_warning_below_5_percent -v
# Expected: PASS
```

**TDD Step 5: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "feat(knn): add ERROR-level logging for catalog skip rates >= 5%

- Log ERROR when skip rate >= 5% for proactive monitoring
- Log WARNING when skip rate < 5%
- Maintain ValueError at > 20%
- Uses SKIP_RATE_ERROR_THRESHOLD constant from Task 1.2
- Add tests for both ERROR and WARNING thresholds

Addresses silent-failure-hunter HIGH #3
Builds on Task 1.2 named constants
All tests pass"
```

---

### Phase 3: INDEPENDENT IMPROVEMENTS (Can Parallelize - 30 min)

#### Task 3.1: Improve Error Message Construction

**Addresses:** code-simplifier Priority 2 #6
**Files:** `hemdov/domain/services/knn_provider.py:223-227`

**TDD Step 1: Extract error message to constant**

```python
# Add at module level (after imports, before class)
CATALOG_QUALITY_ERROR_TEMPLATE = (
    "Catalog data quality issue: {skip_rate:.1%} of examples "
    "({skipped}/{total}) failed validation. "
    "This may indicate a schema mismatch or data corruption. "
    "Check logs for details. Path: {path}"
)

# Update usage in _load_catalog_from_data
if skip_rate > self.SKIP_RATE_CRITICAL_THRESHOLD:
    raise ValueError(
        CATALOG_QUALITY_ERROR_TEMPLATE.format(
            skip_rate=skip_rate,
            skipped=skipped_count,
            total=len(examples_data),
            path=self.catalog_path
        )
    )
```

**TDD Step 2: Run tests**

```bash
pytest tests/test_knn_provider.py -v
# Expected: PASS
```

**TDD Step 3: Commit**

```bash
git add hemdov/domain/services/knn_provider.py
git commit -m "refactor(knn): improve error message construction

- Extract error message to constant template
- Improves readability of multi-line f-strings
- Easier to modify error messages

Addresses code-simplifier Priority 2 #6
All tests pass"
```

---

#### Task 3.2: Add Cache Health Metrics

**Addresses:** silent-failure-hunter MEDIUM #5
**Files:** `hemdov/domain/services/prompt_cache.py`

**TDD Step 1: Add health tracking**

```python
# Add to cache implementation
class PromptCache:
    def __init__(self):
        # ... existing code ...
        self._fallback_count = 0
        self._last_fallback_time = None

    def _record_fallback(self):
        """Track cache fallbacks for monitoring."""
        self._fallback_count += 1
        self._last_fallback_time = datetime.now(UTC)

    def get_health(self) -> dict:
        """Get cache health status.

        Returns:
            Dict with health metrics: {healthy: bool, fallback_count: int, last_fallback: str}
        """
        recent_fallbacks = (
            self._fallback_count > 5 and
            self._last_fallback_time and
            (datetime.now(UTC) - self._last_fallback_time).seconds < 300
        )

        return {
            "healthy": not recent_fallbacks,
            "fallback_count": self._fallback_count,
            "last_fallback": self._last_fallback_time.isoformat() if self._last_fallback_time else None
        }
```

**TDD Step 2: Run tests**

```bash
pytest tests/test_prompt_cache.py -v
# Expected: PASS (or write new tests)
```

**TDD Step 3: Commit**

```bash
git add hemdov/domain/services/prompt_cache.py tests/test_prompt_cache.py
git commit -m "feat(cache): add health metrics for monitoring

- Track fallback count and timing
- Add get_health() method for monitoring
- Log ERROR if fallback happens repeatedly
- Expose cache status in health endpoints

Addresses silent-failure-hunter MEDIUM #5
All tests pass"
```

---

#### Task 3.3: Expose Reflexion Convergence Status

**Addresses:** silent-failure-hunter MEDIUM #6
**Files:** `hemdov/domain/services/reflexion_service.py`

**TDD Step 1: Ensure converged=False is in API response**

```python
# Verify response DTO includes convergence status
# If not already present, add it
```

**TDD Step 2: Run tests**

```bash
pytest tests/ -k reflexion -v
# Expected: PASS
```

**TDD Step 3: Commit**

```bash
git add hemdov/domain/services/reflexion_service.py tests/
git commit -m "fix(reflexion): expose convergence status in API responses

- Ensure converged=False flag is in API responses
- Add user-facing warning for non-convergence
- Users can now see when Reflexion didn't verify code

Addresses silent-failure-hunter MEDIUM #6
All tests pass"
```

---

### Phase 4: POLISH (Low Priority - 20 min)

#### Task 4.1: Remove Unused _analyze_sentiment Method

**Addresses:** code-simplifier Priority 3 #7
**Files:** `hemdov/domain/services/oprop_optimizer.py`

**TDD Step 1: Verify method is unused**

```bash
grep -r "_analyze_sentiment" hemdov/
# Expected: Only definition found, no calls
```

**TDD Step 2: Remove method**

```bash
# Find and remove the method (lines ~188-219)
# Or add TODO comment if planned for future use
```

**TDD Step 3: Run tests**

```bash
pytest tests/ -v
# Expected: PASS (nothing breaks when removing unused code)
```

**TDD Step 4: Commit**

```bash
git add hemdov/domain/services/oprop_optimizer.py
git commit -m "chore(opro): remove unused _analyze_sentiment method

- Method was defined but never called
- Confirmed with grep that no code uses it
- Reduces codebase clutter

Addresses code-simplifier Priority 3 #7
All tests pass"
```

---

## Summary

**Total Tasks:** 11 (consolidated from original 19)
- **Phase 0 (FOUNDATION):** 1 task (~30 min)
- **Phase 1 (REFACTORING):** 3 tasks (~45 min)
- **Phase 2 (FEATURES):** 4 tasks (~45 min)
- **Phase 3 (INDEPENDENT):** 3 tasks (~30 min)
- **Phase 4 (POLISH):** 1 task (~20 min)

**Total Estimated Time:** ~3 hours (revised from original 6.5h)

**Key Improvements from Original Plan:**
1. ✅ **Repository Layer First** - Foundation before features
2. ✅ **TDD Integrated** - Tests embedded in each task
3. ✅ **Consolidated Tasks** - Reduced context switching
4. ✅ **Detailed Specifications** - Schema examples, code snippets
5. ✅ **Verified Current State** - Some items already done
6. ✅ **Rollback Strategy** - Each task is atomic and reversible

**Testing Strategy:**
- TDD for all new features (test → implement → refactor)
- Regression testing before refactoring
- Integration tests for cross-cutting concerns

**Commit Pattern:**
- One commit per task
- Atomic, reversible changes
- Clear commit messages linking to issues

**Success Criteria:**
- ✅ All CRITICAL issues resolved
- ✅ All HIGH issues resolved
- ✅ Code duplication reduced by 75%
- ✅ Cyclomatic complexity reduced by 60%
- ✅ Test coverage > 90% for modified files
- ✅ No regressions in existing functionality
- ✅ All POSITIVE findings maintained

---

## Verification After Implementation

After completing all tasks, run this verification checklist:

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Check test coverage
pytest tests/ --cov=hemdov/domain --cov-report=term-missing

# 3. Verify no regressions
pytest tests/test_knn_provider.py tests/test_nlac_builder_knn_integration.py tests/test_opro_knn_integration.py -v

# 4. Check for domain layer purity
grep -r "open(" hemdov/domain/  # Should return nothing
grep -r "json.load" hemdov/domain/  # Should return nothing

# 5. Verify repository layer exists
ls -la hemdov/infrastructure/repositories/catalog_repository.py

# 6. Check DTO fields
grep "knn_failure" hemdov/domain/dto/nlac_models.py

# 7. Run quality checks
ruff check hemdov/
mypy hemdov/

# 8. Verify git log
git log --oneline -11  # Should see 11 commits for this plan
```

---

## Next Steps

1. **Start with Phase 0 (Task 0.1)** - Repository layer is foundational
2. **Progress through Phases 1-4** - In dependency order
3. **Run verification** after each phase
4. **Create PR** after all tasks complete

**Required SUB-SKILL for execution:** Use `superpowers:executing-plans` to implement this plan task-by-task.

---

## Plan Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-13 | Original plan (19 tasks, 6.5h) |
| 2.0 | 2026-01-13 | **REVISED** - Reordered, TDD integrated, consolidated (11 tasks, 3h) |

**Revision 2.0 incorporates feedback from:**
- Sequential thinking analysis
- Type-design analyzer review
- Comment analyzer review
- Test analyzer review
- Code simplifier review
