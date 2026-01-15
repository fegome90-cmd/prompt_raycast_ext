# eval/src/strategies/complex_strategy.py
import logging
from pathlib import Path

import dspy

from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)


class ComplexStrategy(PromptImproverStrategy):
    """
    Few-shot strategy for complex inputs with KNNFewShot.

    Uses KNNFewShot with k=3 to find the most relevant examples
    from the training set for high-quality prompt improvement.
    """

    def __init__(
        self,
        max_length: int = 5000,
        trainset_path: str | None = None,
        compiled_path: str | None = None,
        k: int = 3
    ):
        """
        Initialize complex strategy with few-shot learning.

        Args:
            max_length: Maximum output length in characters
            trainset_path: Path to few-shot training set (JSON)
            compiled_path: Path to save/load compilation metadata
            k: Number of neighbors for KNNFewShot
        """
        self._max_length = max_length
        self._trainset_path = trainset_path
        self._compiled_path = compiled_path
        self._k = k

        # Import few-shot module lazily
        from eval.src.dspy_prompt_improver_fewshot import (
            PromptImproverWithFewShot,
            load_trainset,
        )

        # Create few-shot improver
        self.improver = PromptImproverWithFewShot(
            compiled_path=compiled_path,
            k=k,
            fallback_to_zeroshot=False  # Require few-shot for complex inputs
        )

        # Compile if trainset is available
        if trainset_path and Path(trainset_path).exists():
            try:
                trainset = load_trainset(trainset_path)
                self.improver.compile(trainset, k=k)
                logger.info(f"ComplexStrategy compiled with k={k}, trainset size={len(trainset)}")
            except Exception as e:
                logger.error(f"Failed to compile ComplexStrategy: {e}")
                raise RuntimeError(f"Few-shot compilation failed: {e}") from e
        else:
            logger.warning(f"ComplexStrategy: trainset not found at {trainset_path}, using uncompiled mode")

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Generate high-quality prompt improvement with few-shot examples.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails

        Raises:
            ValueError: If DSPy Prediction validation fails
            TypeError: If inputs are not strings
            RuntimeError: If DSPy few-shot inference fails
        """
        # Input validation
        self._validate_inputs(original_idea, context)

        try:
            result = self.improver(original_idea=original_idea, context=context)
        except Exception as e:
            logger.error(f"DSPy KNNFewShot error in ComplexStrategy: {e}")
            raise RuntimeError(f"DSPy PromptImprover failed: {e}") from e

        # Validate Prediction structure
        self._validate_prediction(result)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(
                result.improved_prompt,
                self._max_length,
                add_suffix=False  # Complex prompts don't need "..."
            )

        return result

    @property
    def name(self) -> str:
        return "complex"
