"""
KNNProvider - Bridge between ComponentCatalog and NLaC.

Provides semantic search functionality over the unified few-shot pool
using DSPy's KNNFewShot vector similarity.

ARCHITECTURE NOTE: Repository Pattern Integration
This service follows Hexagonal Architecture principles:
- Domain layer: Pure business logic, no I/O
- Infrastructure: FileSystemCatalogRepository handles file access

Migration Path (Legacy → Preferred):
- Legacy: KNNProvider(catalog_path=Path(...))  # Violates purity
- Preferred: KNNProvider(repository=repo)     # Clean separation

The catalog_path parameter is a legacy adapter maintained for backward compatibility.
New code should use the repository parameter.

Design Decisions:
- frozenset for VALID_INTENTS/VALID_COMPLEXITIES: Immutability prevents runtime modification
- TYPE_CHECKING for forward references: Avoids runtime import errors
- _find_examples_impl(): DRY principle - single implementation for both APIs
- Single Source of Truth: VALID_INTENTS/VALID_COMPLEXITIES derived from enums (IntentType, ComplexityLevel)
"""

import logging
import os
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import numpy as np
import dspy

if TYPE_CHECKING:
    from hemdov.infrastructure.repositories.catalog_repository import CatalogRepositoryInterface

# Import enums for type-safe validation
from hemdov.domain.dto.nlac_models import IntentType
from hemdov.domain.services.complexity_analyzer import ComplexityLevel

logger = logging.getLogger(__name__)


class KNNProviderError(RuntimeError):
    """Domain-specific exception for KNN provider errors.

    Provides consistent error type for all KNN-related failures,
    allowing callers to catch and handle KNN errors specifically.
    """
    pass


class FixedVocabularyVectorizer:
    """Vectorizer with fixed vocabulary for consistent dimensions.

    This vectorizer is both callable and has fit/transform methods
    to work with different DSPy versions.
    """

    def __init__(self, vocabulary: Optional[List[str]] = None):
        """Initialize with optional vocabulary.

        Args:
            vocabulary: Fixed list of ngrams to use as features
        """
        self.vocabulary = vocabulary or []

    def fit(self, texts: List[str]) -> 'FixedVocabularyVectorizer':
        """Build vocabulary from texts."""
        ngrams = set()
        for text in texts:
            text = text.lower()
            # Character bigrams
            for i in range(len(text) - 1):
                ngrams.add(text[i:i+2])
        self.vocabulary = list(ngrams)
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to feature vectors."""
        vectors = []
        for text in texts:
            text = text.lower()
            # Count character bigrams
            counts: dict[str, int] = {}
            for i in range(len(text) - 1):
                ngram = text[i:i+2]
                counts[ngram] = counts.get(ngram, 0) + 1
            # Create vector using fixed vocabulary
            vector = np.array([counts.get(ngram, 0) for ngram in self.vocabulary], dtype=np.float32)
            # Normalize
            total = vector.sum()
            if total > 0:
                vector = vector / total
            vectors.append(vector)

        return np.array(vectors)

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Fit and transform."""
        return self.fit(texts).transform(texts)

    def __call__(self, texts: List[str]) -> np.ndarray:
        """Make vectorizer callable.

        This allows it to work with DSPy's KNNFewShot.
        If vocabulary is not set, fit first.
        """
        if not self.vocabulary:
            return self.fit_transform(texts)
        return self.transform(texts)


@dataclass
class FewShotExample:
    """Single few-shot example from ComponentCatalog."""
    input_idea: str
    input_context: str
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: List[str]
    expected_output: Optional[str] = None  # CRITICAL for REFACTOR (MultiAIGCD Scenario III)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FindExamplesResult:
    """Result from find_examples with metadata for debugging.

    Provides similarity metadata when no examples match threshold,
    allowing callers to understand why no examples were returned.
    """
    examples: List[FewShotExample]
    highest_similarity: float
    threshold_used: float
    total_candidates: int
    met_threshold: bool

    def __post_init__(self):
        """Enforce invariants for FindExamplesResult.

        Raises:
            ValueError: If invariants are violated
        """
        # highest_similarity must be in valid cosine similarity range [-1, 1]
        if not (-1.0 <= self.highest_similarity <= 1.0):
            raise ValueError(
                f"highest_similarity must be in [-1, 1], got {self.highest_similarity}"
            )

        # total_candidates cannot be negative
        if self.total_candidates < 0:
            raise ValueError(
                f"total_candidates cannot be negative, got {self.total_candidates}"
            )

        # Consistency check: met_threshold=True requires non-empty examples
        if self.met_threshold and not self.examples:
            raise ValueError(
                f"met_threshold=True requires non-empty examples, got {len(self.examples)} examples"
            )

    @property
    def empty(self) -> bool:
        """Whether no examples met the similarity threshold."""
        return len(self.examples) == 0


class KNNProvider:
    """
    KNN-based few-shot example provider.

    Uses DSPy's KNNFewShot to find semantically similar examples
    from ComponentCatalog based on intent and complexity.

    This is the "memory" layer for NLaC - provides real-world
    curated examples instead of just templates.
    """

    def __init__(
        self,
        catalog_path: Optional[str | os.PathLike[str]] = None,
        catalog_data: Optional[List[dict]] = None,
        repository: Optional['CatalogRepositoryInterface'] = None,
        k: int = 3
    ):
        """
        Initialize KNNProvider with ComponentCatalog.

        Args:
            catalog_path: Path to unified-fewshot-pool-v2.json (legacy, creates repository).
                         NOTE: This parameter couples domain to filesystem concepts.
                         Prefer using 'repository' parameter for pure domain architecture.
            catalog_data: Pre-loaded catalog data (skip repository, useful for testing)
            repository: Catalog repository instance (recommended for production)
            k: Default number of examples to retrieve

        Raises:
            ValueError: If none of catalog_path, catalog_data, or repository are provided

        Architecture Note:
            The catalog_path parameter is a legacy adapter for backward compatibility.
            It violates hexagonal architecture purity by coupling the domain layer
            to filesystem concepts. New code should use the 'repository' parameter
            with dependency injection from the infrastructure layer.

        **Backward Compatibility:** If repository is None and catalog_path is provided,
        creates FileSystemCatalogRepository automatically. If catalog_data is provided,
        uses it directly (useful for testing).
        """
        self.k = k
        self.catalog: List[FewShotExample] = []
        self._dspy_examples: List[dspy.Example] = []
        self._vectorizer: Optional[FixedVocabularyVectorizer] = None
        # Cache for pre-computed vectors to avoid repeated vectorization
        self._catalog_vectors: Optional[np.ndarray] = None

        # Determine data source with backward compatibility
        if catalog_data is not None:
            # Use pre-loaded data (testing path)
            examples_data = catalog_data
            self.catalog_path = None
        elif repository is not None:
            # Use provided repository
            examples_data = repository.load_catalog()
            self.catalog_path = getattr(repository, 'catalog_path', None)
        elif catalog_path is not None:
            # Legacy behavior: create repository (backward compatible)
            # Import Path locally to avoid domain layer coupling
            from pathlib import Path
            from hemdov.infrastructure.repositories.catalog_repository import FileSystemCatalogRepository
            # Convert str/os.PathLike to Path for repository
            path_obj = Path(catalog_path) if not isinstance(catalog_path, Path) else catalog_path
            repo = FileSystemCatalogRepository(path_obj)
            examples_data = repo.load_catalog()
            self.catalog_path = str(path_obj)  # Store as string for domain purity
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
        # Convert to FewShotExample
        skipped_count = 0
        for idx, ex in enumerate(examples_data):
            try:
                inputs = ex['inputs']
                outputs = ex['outputs']
                metadata = ex.get('metadata', {})

                # Check if example has expected_output (CRITICAL for REFACTOR)
                # Metadata may contain 'has_expected_output' flag
                has_expected = metadata.get('has_expected_output', False)

                example = FewShotExample(
                    input_idea=inputs['original_idea'],
                    input_context=inputs.get('context', ''),
                    improved_prompt=outputs['improved_prompt'],
                    role=outputs.get('role', ''),
                    directive=outputs.get('directive', ''),
                    framework=outputs.get('framework', ''),
                    guardrails=outputs.get('guardrails', []),
                    expected_output=outputs.get('expected_output') if has_expected else None,
                    metadata=metadata
                )

                self.catalog.append(example)

                # Also create DSPy Example for KNNFewShot
                dspy_ex = dspy.Example(
                    original_idea=inputs['original_idea'],
                    context=inputs.get('context', ''),
                    improved_prompt=outputs['improved_prompt'],
                    role=outputs.get('role', ''),
                    directive=outputs.get('directive', ''),
                    framework=outputs.get('framework', ''),
                    guardrails=outputs.get('guardrails', []),
                ).with_inputs('original_idea', 'context')

                self._dspy_examples.append(dspy_ex)
            except KeyError as e:
                logger.exception(
                    f"Skipping example {idx} due to missing key: {e}. "
                    f"Example data: {repr(str(ex)[:200])}"
                )
                skipped_count += 1
                continue
            # NOTE: Broad exception catching is intentional here because:
            # - We process external JSON data (user-provided catalog)
            # - All exceptions are logged with full context for debugging
            # - Skip rate threshold (20%) catches systemic data issues
            # - Individual examples fail gracefully without crashing initialization
            except (TypeError, ValueError) as e:
                logger.exception(
                    f"Skipping example {idx} due to invalid data: {e}. "
                    f"Example data: {repr(str(ex)[:200])}"
                )
                skipped_count += 1
                continue

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
            if skip_rate >= self.SKIP_RATE_CRITICAL_THRESHOLD:
                raise ValueError(
                    f"Catalog data quality issue: {skip_rate:.1%} of examples ({skipped_count}/{len(examples_data)}) "
                    f"failed validation. This may indicate a schema mismatch or data corruption. "
                    f"Check logs for details."
                )

        if len(self.catalog) == 0:
            raise ValueError(
                f"KNNProvider cannot initialize: No valid examples found in catalog. "
                f"All examples failed validation. Check logs for details."
            )

        logger.info(f"Loaded {len(self.catalog)} examples from ComponentCatalog")

        # Initialize KNNFewShot
        self._initialize_knn()

    def _initialize_knn(self) -> None:
        """Initialize vectorizer for semantic search and pre-compute catalog vectors."""
        if not self._dspy_examples:
            raise KNNProviderError(
                "KNNProvider cannot initialize: No DSPy examples available. "
                "This indicates catalog loading failed or produced no valid examples. "
                f"Catalog path: {self.catalog_path}, examples loaded: {len(self.catalog)}"
            )

        # Create and fit vectorizer on all examples
        self._vectorizer = FixedVocabularyVectorizer()
        texts = [ex.original_idea for ex in self._dspy_examples]
        self._vectorizer.fit(texts)

        # Pre-compute and cache vectors for all catalog examples
        # This avoids repeated vectorization in find_examples calls
        catalog_texts = [ex.input_idea for ex in self.catalog]
        self._catalog_vectors = self._vectorizer(catalog_texts)

        logger.info(
            f"Vectorizer initialized with {len(self._vectorizer.vocabulary)} n-grams, "
            f"pre-computed {self._catalog_vectors.shape[0]} catalog vectors"
        )

    # Minimum cosine similarity threshold for relevance filtering
    # Character bigram similarity is less precise than embeddings, so threshold is conservative
    MIN_SIMILARITY_THRESHOLD: float = 0.1

    # Catalog quality thresholds
    # At 5% skip rate, log ERROR (proactive monitoring for schema drift)
    # At 20% skip rate, raise ValueError (critical data quality issue)
    SKIP_RATE_ERROR_THRESHOLD: float = 0.05   # 5% - log ERROR
    SKIP_RATE_CRITICAL_THRESHOLD: float = 0.2  # 20% - raise ValueError

    # Vector computation constants
    # Floating-point epsilon for division safety when computing cosine similarity
    NORM_ZERO_THRESHOLD: float = 1e-10

    # Valid intent values derived from IntentType enum (Single Source of Truth)
    # Used for validation in _build_query_text
    # frozenset ensures immutability - prevents runtime modification
    VALID_INTENTS: frozenset[str] = frozenset(e.value for e in IntentType)

    # Valid complexity values derived from ComplexityLevel enum (Single Source of Truth)
    # Used for validation in _build_query_text
    # frozenset ensures immutability - prevents runtime modification
    VALID_COMPLEXITIES: frozenset[str] = frozenset(e.value for e in ComplexityLevel)

    def _find_examples_impl(
        self,
        intent: str,
        complexity: str,
        k: Optional[int] = None,
        has_expected_output: bool = False,
        user_input: Optional[str] = None,
        min_similarity: Optional[float] = None,
        return_metadata: bool = False,
    ) -> List[FewShotExample] | FindExamplesResult:
        """
        Unified implementation for finding similar examples.

        This method consolidates the logic for both find_examples() and
        find_examples_with_metadata() to eliminate code duplication.

        Args:
            intent: Intent type (debug, refactor, generate, explain)
            complexity: Complexity level (simple, moderate, complex)
            k: Number of examples to retrieve (defaults to self.k)
            has_expected_output: Filter for examples with expected_output
            user_input: Optional user input for better semantic matching
            min_similarity: Minimum cosine similarity threshold
            return_metadata: If True, returns FindExamplesResult; otherwise returns List

        Returns:
            List[FewShotExample] or FindExamplesResult depending on return_metadata

        Raises:
            ValueError: If k <= 0, or min_similarity not in [-1, 1]
            KNNProviderError: If vectorizer is not initialized
            TypeError: If user_input is not str or None
        """
        k = self.k if k is None else k
        min_similarity = self.MIN_SIMILARITY_THRESHOLD if min_similarity is None else min_similarity

        # Validate parameters
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")

        if not (-1.0 <= min_similarity <= 1.0):
            raise ValueError(f"min_similarity must be in [-1, 1], got {min_similarity}")

        if user_input is not None and not isinstance(user_input, str):
            raise TypeError(f"user_input must be str or None, got {type(user_input).__name__}")

        # Filter candidates
        candidates = self._filter_candidates_by_expected_output(has_expected_output)

        if not candidates:
            logger.warning(
                f"No candidates found after filtering. "
                f"Intent='{intent}', Complexity='{complexity}', "
                f"has_expected_output={has_expected_output}. "
                f"Catalog may be missing examples for this combination."
            )
            if return_metadata:
                return FindExamplesResult(
                    examples=[],
                    highest_similarity=0.0,
                    threshold_used=min_similarity,
                    total_candidates=0,
                    met_threshold=False
                )
            return []

        # Early return if we have fewer candidates than k
        if len(candidates) <= k:
            if len(candidates) < k:
                logger.warning(
                    f"Returning {len(candidates)} examples (requested k={k}). "
                    f"Candidate pool exhausted - results may be lower quality than expected."
                )
            if return_metadata:
                return FindExamplesResult(
                    examples=candidates[:k],
                    highest_similarity=1.0,  # No filtering done, assume max
                    threshold_used=min_similarity,
                    total_candidates=len(candidates),
                    met_threshold=True
                )
            return candidates[:k]

        # Semantic search
        if not self._vectorizer:
            raise KNNProviderError(
                "KNNProvider vectorizer not initialized. "
                "Cannot perform semantic search. Check logs for initialization errors."
            )

        # Build query and compute similarities
        query_text = self._build_query_text(intent, complexity, user_input)
        candidate_vectors = self._get_candidate_vectors(candidates)
        query_vector = self._vectorizer([query_text])[0]
        similarities = self._compute_cosine_similarities(candidate_vectors, query_vector)

        # Filter and rank by similarity
        filtered, highest_sim, total_cands, met_threshold = self._filter_and_rank_by_similarity(
            candidates, similarities, k, min_similarity
        )

        if return_metadata:
            return FindExamplesResult(
                examples=filtered,
                highest_similarity=highest_sim,
                threshold_used=min_similarity,
                total_candidates=total_cands,
                met_threshold=met_threshold
            )
        return filtered

    def find_examples(
        self,
        intent: str,
        complexity: str,
        k: Optional[int] = None,
        has_expected_output: bool = False,
        user_input: Optional[str] = None,
        min_similarity: Optional[float] = None
    ) -> List[FewShotExample]:
        """
        Find k similar examples using semantic search.

        Note: Current catalog doesn't have intent/complexity metadata,
        so filtering is done via semantic similarity to the query.

        Args:
            intent: Intent type (debug, refactor, generate, explain) - used for query
            complexity: Complexity level (simple, moderate, complex) - used for query
            k: Number of examples to retrieve (defaults to self.k)
            has_expected_output: Filter for examples with expected_output
                              (CRITICAL for REFACTOR - MultiAIGCD Scenario III)
            user_input: Optional user input for better semantic matching
            min_similarity: Minimum cosine similarity threshold (defaults to MIN_SIMILARITY_THRESHOLD)

        Returns:
            List of FewShotExample sorted by similarity

        Raises:
            ValueError: If k <= 0, or min_similarity not in [-1, 1]
            KNNProviderError: If vectorizer is not initialized
            TypeError: If user_input is not str or None
        """
        result = self._find_examples_impl(
            intent=intent,
            complexity=complexity,
            k=k,
            has_expected_output=has_expected_output,
            user_input=user_input,
            min_similarity=min_similarity,
            return_metadata=False,
        )
        # Type narrowing: we know result is List when return_metadata=False
        assert isinstance(result, list)
        return result

    def find_examples_with_metadata(
        self,
        intent: str,
        complexity: str,
        k: Optional[int] = None,
        has_expected_output: bool = False,
        user_input: Optional[str] = None,
        min_similarity: Optional[float] = None
    ) -> FindExamplesResult:
        """
        Find k similar examples using semantic search with metadata.

        This is the recommended API for production use as it provides
        diagnostic metadata about the search results.

        Args:
            intent: Intent type (debug, refactor, generate, explain)
            complexity: Complexity level (simple, moderate, complex)
            k: Number of examples to retrieve (defaults to self.k)
            has_expected_output: Filter for examples with expected_output
            user_input: Optional user input for better semantic matching
            min_similarity: Minimum cosine similarity threshold

        Returns:
            FindExamplesResult with examples and diagnostic metadata

        Raises:
            ValueError: If k <= 0, or min_similarity not in [-1, 1]
            KNNProviderError: If vectorizer is not initialized
            TypeError: If user_input is not str or None

        Example:
            >>> result = provider.find_examples_with_metadata("debug", "simple", k=3)
            >>> if result.empty:
            ...     print(f"No examples met threshold. Highest similarity: {result.highest_similarity}")
        """
        result = self._find_examples_impl(
            intent=intent,
            complexity=complexity,
            k=k,
            has_expected_output=has_expected_output,
            user_input=user_input,
            min_similarity=min_similarity,
            return_metadata=True,
        )
        # Type narrowing: we know result is FindExamplesResult when return_metadata=True
        assert isinstance(result, FindExamplesResult)
        return result

    def _filter_candidates_by_expected_output(self, has_expected_output: bool) -> List[FewShotExample]:
        """Filter catalog by expected_output flag."""
        if not has_expected_output:
            return self.catalog

        filtered = [ex for ex in self.catalog if ex.expected_output is not None]
        if not filtered:
            logger.warning("No examples found (filtered by expected_output)")
        return filtered

    def _build_query_text(self, intent: str, complexity: str, user_input: Optional[str]) -> str:
        """Build search query from intent, complexity, and optional user input.

        Args:
            intent: Intent type (must be one of VALID_INTENTS)
            complexity: Complexity level (must be one of VALID_COMPLEXITIES)
            user_input: Optional user input for better semantic matching

        Returns:
            Search query string

        Raises:
            ValueError: If intent or complexity are not valid values
        """
        # Validate inputs (defense in depth - IntentClassifier already validates)
        if intent not in self.VALID_INTENTS:
            raise ValueError(
                f"Invalid intent '{intent}'. Must be one of: {', '.join(sorted(self.VALID_INTENTS))}"
            )
        if complexity not in self.VALID_COMPLEXITIES:
            raise ValueError(
                f"Invalid complexity '{complexity}'. Must be one of: {', '.join(sorted(self.VALID_COMPLEXITIES))}"
            )

        query_parts = [intent, complexity]
        if user_input and user_input.strip():
            query_parts.append(user_input.strip())
        return " ".join(query_parts)

    def _get_candidate_vectors(self, candidates: List[FewShotExample]) -> np.ndarray:
        """Get cached or compute candidate vectors.

        Uses cached vectors if no filtering was applied (candidates is same object as catalog).
        Re-vectorizes when candidates are a subset of the catalog.

        Returns:
            Candidate vectors for similarity computation
        """
        # Use cached vectors if available and no filtering was applied
        # Use 'is' for identity comparison (O(1)) instead of '==' (O(n) list equality)
        if self._catalog_vectors is not None and candidates is self.catalog:
            logger.debug("Using pre-computed catalog vectors (cache hit)")
            return self._catalog_vectors

        # Re-vectorize candidates (filtering was applied or cache not available)
        logger.debug(f"Re-vectorizing {len(candidates)} candidates (cache miss)")
        candidate_texts = [ex.input_idea for ex in candidates]
        return self._vectorizer(candidate_texts)

    def _compute_cosine_similarities(
        self,
        candidate_vectors: np.ndarray,
        query_vector: np.ndarray
    ) -> np.ndarray:
        """Calculate cosine similarities using vectorized operations (7x faster).

        Raises:
            KNNProviderError: If vectors contain NaN or infinite values
        """
        # Validate inputs for NaN/inf
        if not np.all(np.isfinite(candidate_vectors)):
            raise KNNProviderError(
                f"Candidate vectors contain NaN or infinite values. "
                f"This may indicate corrupted data or invalid vectorization."
            )
        if not np.all(np.isfinite(query_vector)):
            raise KNNProviderError(
                f"Query vector contains NaN or infinite values. "
                f"This may indicate corrupted input data."
            )

        # Cosine similarity = (A . B) / (|A| * |B|)
        dot_products = np.dot(candidate_vectors, query_vector)
        query_norm = np.linalg.norm(query_vector)
        candidate_norms = np.linalg.norm(candidate_vectors, axis=1)

        # Handle division by zero using np.divide with 'where' parameter
        # This avoids computing NaN/Inf values before the check
        result = np.divide(
            dot_products,
            query_norm * candidate_norms,
            out=np.zeros_like(dot_products),
            where=(query_norm > self.NORM_ZERO_THRESHOLD) & (candidate_norms > self.NORM_ZERO_THRESHOLD)
        )

        # Log when zero-norm vectors are detected (silent failure prevention)
        zero_norm_count = np.sum(result == 0)
        if zero_norm_count > 0:
            zero_norm_pct = (zero_norm_count / len(candidate_vectors)) * 100
            logger.warning(
                f"Zero-norm vectors detected in {zero_norm_count}/{len(candidate_vectors)} "
                f"candidates ({zero_norm_pct:.1f}%). These vectors have no semantic content "
                f"and will have 0 similarity. Consider reviewing catalog data quality."
            )

        return result

    def _filter_and_rank_by_similarity(
        self,
        candidates: List[FewShotExample],
        similarities: np.ndarray,
        k: int,
        min_similarity: float
    ) -> tuple[List[FewShotExample], float, int, bool]:
        """
        Filter by threshold and return top-k examples with metadata.

        Returns:
            Tuple of (examples, highest_similarity, total_candidates, met_threshold)
        """
        # Filter by minimum similarity threshold (relevance filtering)
        relevant_mask = similarities >= min_similarity
        relevant_indices = np.where(relevant_mask)[0]

        highest_similarity = float(similarities.max()) if len(similarities) > 0 else 0.0
        met_threshold = len(relevant_indices) > 0

        if not met_threshold:
            logger.warning(
                f"No examples met similarity threshold {min_similarity:.2f}. "
                f"Highest similarity: {highest_similarity:.2f}. "
                f"Returning empty - user input does not match any catalog examples."
            )
            return [], highest_similarity, len(candidates), False

        # Sort relevant examples by similarity (descending) and return top k
        relevant_similarities = similarities[relevant_indices]
        sorted_relevant_idx = np.argsort(relevant_similarities)[::-1][:k]
        top_indices = relevant_indices[sorted_relevant_idx]

        logger.debug(
            f"KNN relevance filtering: {len(relevant_indices)}/{len(candidates)} examples "
            f"met threshold {min_similarity:.2f}, returning top {len(top_indices)}"
        )

        filtered_examples = [candidates[i] for i in top_indices]
        return filtered_examples, highest_similarity, len(candidates), True


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
        >>> import logging
        >>> logger = logging.getLogger(__name__)
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
