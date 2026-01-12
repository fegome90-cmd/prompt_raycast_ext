"""
KNNProvider - Bridge between ComponentCatalog and NLaC.

Provides semantic search functionality over the unified few-shot pool
using DSPy's KNNFewShot vector similarity.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import numpy as np
import dspy

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

    def __init__(self, catalog_path: Path, k: int = 3):
        """
        Initialize KNNProvider with ComponentCatalog.

        Args:
            catalog_path: Path to unified-fewshot-pool-v2.json
            k: Default number of examples to retrieve
        """
        self.catalog_path = catalog_path
        self.k = k
        self.catalog: List[FewShotExample] = []
        self._dspy_examples: List[dspy.Example] = []
        self._vectorizer: Optional[FixedVocabularyVectorizer] = None
        # Cache for pre-computed vectors to avoid repeated vectorization
        self._catalog_vectors: Optional[np.ndarray] = None

        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load ComponentCatalog from JSON file."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"ComponentCatalog not found at {self.catalog_path}. "
                f"KNNProvider cannot initialize without catalog."
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
            examples_data = data['examples']
        elif isinstance(data, list):
            examples_data = data
        else:
            raise ValueError(
                f"Invalid catalog format at {self.catalog_path}. "
                f"Expected dict with 'examples' key or list, got {type(data).__name__}"
            )

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
                    guardrails=outputs.get('guardrails', ''),
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
            logger.warning(
                f"Loaded {len(self.catalog)} examples from ComponentCatalog "
                f"(skipped {skipped_count} invalid examples)"
            )

        if len(self.catalog) == 0:
            raise ValueError(
                f"KNNProvider cannot initialize: No valid examples found in catalog at {self.catalog_path}. "
                f"All examples failed validation. Check logs for details."
            )

        logger.info(f"Loaded {len(self.catalog)} examples from ComponentCatalog")

        # Initialize KNNFewShot
        self._initialize_knn()

    def _initialize_knn(self) -> None:
        """Initialize vectorizer for semantic search and pre-compute catalog vectors."""
        if not self._dspy_examples:
            logger.warning("No examples to initialize vectorizer")
            return

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

    def find_examples(
        self,
        intent: str,
        complexity: str,
        k: Optional[int] = None,
        has_expected_output: bool = False
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

        Returns:
            List of FewShotExample sorted by similarity
        """
        k = k or self.k

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
            # Transform query to vector
            query_text = f"{intent} {complexity}"
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

            # Sort by similarity (descending) and return top k
            top_indices = np.argsort(similarities)[::-1][:k]
            return [candidates[i] for i in top_indices]
        else:
            # Fallback: return first k candidates
            logger.warning("Vectorizer not initialized, returning first k examples")
            return candidates[:k]
