"""
DSPy PromptImprover with few-shot compilation.

Extends PromptImprover with KNNFewShot compilation for better quality.
"""

import json
from pathlib import Path
from typing import List, Optional, Callable
import numpy as np
import dspy

# Import base PromptImprover
from .dspy_prompt_improver import PromptImprover, PromptImproverSignature


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
            counts = {}
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


def create_vectorizer():
    """Create vectorizer for KNNFewShot.

    Returns a sklearn-like vectorizer with fit/transform methods.
    """
    return FixedVocabularyVectorizer()


class PromptImproverWithFewShot(dspy.Module):
    """DSPy PromptImprover with few-shot compilation.

    Wraps the base PromptImprover and adds KNNFewShot compilation
    for improved quality using example-based learning.
    """

    def __init__(
        self,
        compiled_path: Optional[str] = None,
        k: int = 3,
        fallback_to_zeroshot: bool = True
    ):
        """Initialize few-shot enabled improver.

        Args:
            compiled_path: Path to load/save compiled module
            k: Number of neighbors for KNNFewShot
            fallback_to_zeroshot: Allow zero-shot if compilation fails
        """
        super().__init__()
        self.base_improver = PromptImprover()
        self.compiled_path = compiled_path
        self.k = k
        self.fallback_to_zeroshot = fallback_to_zeroshot
        self._compiled = False
        self.compiled_improver = None

        # Try to load existing compiled module
        if compiled_path and Path(compiled_path).exists():
            self._load_compiled()

    def _load_compiled(self) -> None:
        """Load compiled module from disk.

        DSPy doesn't have native serialization, so we track
        compilation state separately and recompile if needed.
        """
        # Check if compilation metadata exists
        metadata_path = Path(self.compiled_path).with_suffix('.metadata.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self._compiled = metadata.get('compiled', False)
            # Note: Actual compiled module needs to be recreated
            # by recompiling with the same trainset

    def _save_compiled_metadata(self, trainset_size: int) -> None:
        """Save compilation metadata.

        Args:
            trainset_size: Size of training set used for compilation
        """
        if self.compiled_path:
            metadata_path = Path(self.compiled_path).with_suffix('.metadata.json')
            metadata = {
                'compiled': True,
                'k': self.k,
                'trainset_size': trainset_size,
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

    def compile(
        self,
        trainset: List[dspy.Example],
        k: Optional[int] = None
    ) -> None:
        """Compile with KNNFewShot.

        Args:
            trainset: Training examples with inputs() and outputs()
            k: Number of neighbors (overrides init k if provided)

        Raises:
            CompilationError: If compilation fails and fallback is disabled
        """
        k = k or self.k

        try:
            print(f"🔧 Compiling PromptImprover with KNNFewShot (k={k})...")
            print(f"   Training set size: {len(trainset)}")

            # Extract texts from trainset for vocabulary building
            trainset_texts = [ex.original_idea for ex in trainset]

            # Create and fit vectorizer on trainset
            vectorizer = create_vectorizer()
            vectorizer.fit(trainset_texts)

            # Create KNNFewShot with trainset and vectorizer
            knn_fewshot = dspy.KNNFewShot(k=k, trainset=trainset, vectorizer=vectorizer)

            # Compile the base improver
            self.compiled_improver = knn_fewshot.compile(self.base_improver)

            self._compiled = True
            print(f"✓ Compilation complete")

            # Save metadata
            if self.compiled_path:
                self._save_compiled_metadata(len(trainset))
                print(f"✓ Saved compilation metadata")

        except Exception as e:
            print(f"✗ Compilation failed: {e}")
            if self.fallback_to_zeroshot:
                print(f"⚠️  Falling back to zero-shot mode")
                self._compiled = False
                self.compiled_improver = None
            else:
                raise CompilationError(f"Few-shot compilation failed: {e}")

    def forward(
        self,
        original_idea: str,
        context: str = ""
    ) -> dspy.Prediction:
        """Generate improved prompt with few-shot examples.

        If compiled, uses KNNFewShot to select relevant examples.
        Otherwise falls back to zero-shot.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, etc.
        """
        if self._compiled and self.compiled_improver:
            # Use compiled module with few-shot examples
            return self.compiled_improver.forward(
                original_idea=original_idea,
                context=context
            )
        else:
            # Fallback to zero-shot
            return self.base_improver.forward(
                original_idea=original_idea,
                context=context
            )


class CompilationError(Exception):
    """Raised when few-shot compilation fails."""
    pass


def load_trainset(path: str) -> List[dspy.Example]:
    """Load training set from JSON file.

    Args:
        path: Path to merged-trainset.json

    Returns:
        List of dspy.Example with inputs() and outputs()
    """
    with open(path, 'r') as f:
        data = json.load(f)

    trainset = []
    for item in data:
        inputs = item['inputs']
        outputs = item['outputs']

        example = dspy.Example(
            original_idea=inputs['original_idea'],
            context=inputs.get('context', ''),
            improved_prompt=outputs['improved_prompt'],
            role=outputs.get('role', ''),
            directive=outputs.get('directive', ''),
            framework=outputs.get('framework', ''),
            guardrails=outputs.get('guardrails', ''),
        ).with_inputs('original_idea', 'context')

        trainset.append(example)

    return trainset


def create_fewshot_improver(
    trainset_path: str,
    compiled_path: Optional[str] = None,
    k: int = 3,
    force_recompile: bool = False
) -> PromptImproverWithFewShot:
    """Create and compile few-shot improver.

    Args:
        trainset_path: Path to merged-trainset.json
        compiled_path: Path for compilation metadata
        k: Number of neighbors for KNNFewShot
        force_recompile: Force recompilation even if compiled module exists

    Returns:
        Compiled PromptImproverWithFewShot
    """
    # Create improver
    improver = PromptImproverWithFewShot(
        compiled_path=compiled_path,
        k=k
    )

    # Check if already compiled
    if improver._compiled and not force_recompile:
        print(f"✓ Using existing compiled module")
        # Recompile to restore (DSPy doesn't serialize compiled modules)
        trainset = load_trainset(trainset_path)
        improver.compile(trainset, k=k)
    else:
        # Compile from scratch
        trainset = load_trainset(trainset_path)
        improver.compile(trainset, k=k)

    return improver
