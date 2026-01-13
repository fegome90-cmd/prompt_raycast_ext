"""
KNNProvider - Bridge between ComponentCatalog and NLaC.

Provides semantic search functionality over the unified few-shot pool
using DSPy's KNNFewShot vector similarity.
"""

import logging
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import numpy as np
import dspy

if TYPE_CHECKING:
    from hemdov.infrastructure.repositories.catalog_repository import CatalogRepositoryInterface

logger = logging.getLogger(__name__)


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
        catalog_path: Optional[Path] = None,
        catalog_data: Optional[List[dict]] = None,
        repository: Optional['CatalogRepositoryInterface'] = None,
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
            from hemdov.infrastructure.repositories.catalog_repository import FileSystemCatalogRepository
            repo = FileSystemCatalogRepository(catalog_path)
            examples_data = repo.load_catalog()
            self.catalog_path = catalog_path
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
            except (TypeError, ValueError) as e:
                logger.exception(
                    f"Skipping example {idx} due to invalid data: {e}. "
                    f"Example data: {repr(str(ex)[:200])}"
                )
                skipped_count += 1
                continue

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
            raise RuntimeError(
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
    MIN_SIMILARITY_THRESHOLD = 0.1

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
        """
        k = k or self.k
        min_similarity = min_similarity if min_similarity is not None else self.MIN_SIMILARITY_THRESHOLD

        # Start with all examples
        candidates = self.catalog

        # Filter by expected_output if requested (CRITICAL for REFACTOR)
        if has_expected_output:
            candidates = [ex for ex in candidates if ex.expected_output is not None]

        if not candidates:
            logger.warning(f"No examples found (catalog empty or filtered out)")
            return []

        # If we have fewer candidates than k, return all
        if len(candidates) <= k:
            return candidates[:k]

        # Use KNN to find most similar by semantic search
        if self._vectorizer:
            # Transform query to vector - include user input for better semantic matching
            query_parts = [intent, complexity]
            if user_input and user_input.strip():  # Validate non-empty after stripping
                query_parts.append(user_input.strip())
            query_text = " ".join(query_parts)
            query_vector = self._vectorizer([query_text])[0]

            # Use cached vectors if available and no filtering, otherwise re-vectorize candidates
            if self._catalog_vectors is not None and candidates == self.catalog:
                candidate_vectors = self._catalog_vectors
            else:
                candidate_texts = [ex.input_idea for ex in candidates]
                candidate_vectors = self._vectorizer(candidate_texts)

            # Calculate cosine similarity using vectorized operations (7x faster)
            # Cosine similarity = (A . B) / (|A| * |B|)
            dot_products = np.dot(candidate_vectors, query_vector)
            query_norm = np.linalg.norm(query_vector)
            candidate_norms = np.linalg.norm(candidate_vectors, axis=1)
            similarities = dot_products / (query_norm * candidate_norms)
            # Handle division by zero
            similarities = np.where((query_norm > 0) & (candidate_norms > 0), similarities, 0)

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
            else:
                # Sort relevant examples by similarity (descending) and return top k
                relevant_similarities = similarities[relevant_indices]
                sorted_relevant_idx = np.argsort(relevant_similarities)[::-1][:k]
                top_indices = relevant_indices[sorted_relevant_idx]

                logger.debug(
                    f"KNN relevance filtering: {len(relevant_indices)}/{len(candidates)} examples "
                    f"met threshold {min_similarity:.2f}, returning top {len(top_indices)}"
                )

            return [candidates[i] for i in top_indices]
        else:
            # Vectorizer not initialized - this is a critical failure
            raise RuntimeError(
                "KNNProvider vectorizer not initialized. "
                "Cannot perform semantic search. Check logs for initialization errors."
            )


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
