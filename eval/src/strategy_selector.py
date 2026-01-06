# eval/src/strategy_selector.py
from typing import Optional
from pathlib import Path
from .complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from .strategies.base import PromptImproverStrategy
from .strategies.simple_strategy import SimpleStrategy
from .strategies.moderate_strategy import ModerateStrategy
from .strategies.complex_strategy import ComplexStrategy
from .strategies.nlac_strategy import NLaCStrategy


class StrategySelector:
    """
    Selects appropriate prompt improvement strategy based on input complexity.

    Legacy mode (default):
    - SimpleStrategy (≤50 chars): Zero-shot, 800 char max
    - ModerateStrategy (≤150 chars): ChainOfThought, 2000 char max
    - ComplexStrategy (>150 chars): KNNFewShot, 5000 char max

    NLaC mode (use_nlac=True):
    - NLaCStrategy: Unified strategy handling all complexities with:
      - Intent classification (debug, refactor, generate, explain)
      - Role injection (MultiAIGCD)
      - RaR for complex inputs
      - OPRO optimization (3 iterations)
      - IFEval validation with autocorrection
      - SHA256-based caching
    """

    def __init__(
        self,
        trainset_path: Optional[str] = None,
        compiled_path: Optional[str] = None,
        fewshot_k: int = 3,
        use_nlac: bool = False,
        llm_client=None,
    ):
        """
        Initialize strategy selector.

        Args:
            trainset_path: Path to few-shot training set (for ComplexStrategy)
            compiled_path: Path to few-shot compilation metadata
            fewshot_k: Number of neighbors for KNNFewShot
            use_nlac: Whether to use NLaC strategy (default: False for backward compatibility)
            llm_client: Optional LLM client for NLaC advanced features

        Raises:
            RuntimeError: If ComplexStrategy initialization fails
        """
        self.analyzer = ComplexityAnalyzer()
        self._use_nlac = use_nlac

        # Initialize NLaC strategy if enabled
        if use_nlac:
            self.nlac_strategy = NLaCStrategy(llm_client=llm_client)
            logger = __import__("logging").getLogger(__name__)
            logger.info("NLaC strategy enabled - using unified NLaC pipeline")
            return  # Skip legacy strategy initialization

        # Initialize legacy DSPy strategies
        self.simple_strategy = SimpleStrategy(max_length=800)
        self.moderate_strategy = ModerateStrategy(max_length=2000)

        # ComplexStrategy may fail if trainset not available - log but continue
        try:
            self.complex_strategy = ComplexStrategy(
                max_length=5000,
                trainset_path=trainset_path,
                compiled_path=compiled_path,
                k=fewshot_k
            )
            self._complex_available = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"ComplexStrategy unavailable, will use ModerateStrategy fallback: {e}")
            self.complex_strategy = None
            self._complex_available = False

    def select(
        self,
        original_idea: str,
        context: str
    ) -> PromptImproverStrategy:
        """
        Select appropriate strategy based on mode and complexity.

        In NLaC mode: Always returns NLaCStrategy (handles all complexities internally)
        In legacy mode: Routes to Simple/Moderate/Complex based on complexity

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            Selected strategy instance

        Raises:
            ValueError: If inputs are None
            TypeError: If inputs are not strings
        """
        # Validate inputs
        if original_idea is None or context is None:
            raise ValueError("original_idea and context must be non-None strings")
        if not isinstance(original_idea, str) or not isinstance(context, str):
            raise TypeError("original_idea and context must be strings")

        # NLaC mode: return unified strategy
        if self._use_nlac:
            return self.nlac_strategy

        # Legacy mode: route based on complexity
        complexity = self.analyzer.analyze(original_idea, context)

        if complexity == ComplexityLevel.SIMPLE:
            return self.simple_strategy
        elif complexity == ComplexityLevel.MODERATE:
            return self.moderate_strategy
        else:  # COMPLEX
            # Fallback to moderate if complex strategy unavailable
            if self._complex_available:
                return self.complex_strategy
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("ComplexStrategy unavailable, using ModerateStrategy fallback")
                return self.moderate_strategy

    def get_complexity(self, original_idea: str, context: str) -> ComplexityLevel:
        """
        Get complexity level for logging/metrics.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            ComplexityLevel (SIMPLE, MODERATE, or COMPLEX)
        """
        return self.analyzer.analyze(original_idea, context)
