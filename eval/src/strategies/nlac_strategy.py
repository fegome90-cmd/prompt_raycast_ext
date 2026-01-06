"""
NLaC Strategy - Unified prompt improvement pipeline.

Integrates:
- NLaCBuilder (Role injection + RaR + KNN examples)
- ReflexionService (for DEBUG scenario - MultiAIGCD Scenario II)
- OPROOptimizer (for non-DEBUG scenarios)
- IFEval validation (optional)

Pipeline:
1. Build PromptObject (intent + complexity + role + KNN examples)
2. For DEBUG: Use Reflexion (not OPRO)
3. For non-DEBUG: Optimize with OPRO (if enabled)
4. Validate with IFEval (if enabled)
5. Return dspy.Prediction for compatibility
"""
import logging
import dspy
from datetime import datetime, UTC
from typing import Optional

from hemdov.domain.dto.nlac_models import NLaCRequest, PromptObject
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.oprop_optimizer import OPOROptimizer
from hemdov.domain.services.reflexion_service import ReflexionService
from hemdov.domain.services.knn_provider import KNNProvider

from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)


class NLaCStrategy(PromptImproverStrategy):
    """
    Unified NLaC + KNN pipeline for prompt improvement.

    Implements MultiAIGCD refinements:
    - DEBUG → Reflexion (Scenario II) - 1-2 iterations vs 3 for OPRO
    - REFACTOR → KNN with expected_output filter (Scenario III)
    - GENERATE → RaR for complex inputs + KNN examples
    """

    def __init__(
        self,
        llm_client=None,
        enable_cache: bool = True,
        enable_optimization: bool = True,
        enable_validation: bool = False,
        knn_provider: Optional[KNNProvider] = None,
    ):
        """
        Initialize NLaC strategy with all services.

        Args:
            llm_client: Optional LLM client for advanced features
            enable_cache: Whether to use prompt caching (reserved, not yet implemented)
            enable_optimization: Whether to run OPRO optimization
            enable_validation: Whether to run IFEval validation (reserved, not yet implemented)
            knn_provider: Optional KNNProvider for few-shot examples
        """
        self.builder = NLaCBuilder(knn_provider=knn_provider)
        self.optimizer = OPOROptimizer(llm_client=llm_client, knn_provider=knn_provider)
        self.reflexion = ReflexionService(llm_client=llm_client) if llm_client else None
        self._enable_optimization = enable_optimization
        self._enable_validation = enable_validation
        self._llm_client = llm_client
        self._knn_provider = knn_provider

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Improve prompt using NLaC pipeline.

        Pipeline:
        1. Build PromptObject (intent + complexity + role injection + KNN examples)
        2. For DEBUG: Use Reflexion (not OPRO)
        3. For non-DEBUG: Optimize with OPRO (if enabled)
        4. Validate with IFEval (if enabled)
        5. Convert to dspy.Prediction for compatibility

        Args:
            original_idea: User's original prompt idea
            context: Additional context

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails
        """
        # Input validation
        self._validate_inputs(original_idea, context)

        # Create NLaC request
        request = NLaCRequest(
            idea=original_idea,
            context=context,
        )

        # Build PromptObject (with KNN examples if available)
        logger.info(f"Building NLaC prompt for: {original_idea[:50]}...")
        prompt_obj = self.builder.build(request)

        # Extract intent for routing
        intent = prompt_obj.strategy_meta.get("intent", "").lower()

        # Route to appropriate optimizer
        if intent.startswith("debug") and self.reflexion:
            # DEBUG uses Reflexion (MultiAIGCD Scenario II)
            logger.info("Using Reflexion for DEBUG scenario")
            refined_result = self.reflexion.refine(
                prompt=prompt_obj.template,
                error_type=self._extract_error_type(context),
                error_message=context,
                max_iterations=2
            )

            if refined_result.success:
                prompt_obj.template = refined_result.code
                logger.info(f"Reflexion converged in {refined_result.iteration_count} iterations")
            else:
                logger.warning(f"Reflexion did not converge, using initial template")

        elif self._enable_optimization:
            # Non-DEBUG uses OPRO with KNN examples
            logger.info("Running OPRO optimization...")
            opt_response = self.optimizer.run_loop(prompt_obj)
            prompt_obj.template = opt_response.final_instruction
            prompt_obj.updated_at = datetime.now(UTC).isoformat()

        # Validation (reserved for future IFEval integration)
        if self._enable_validation:
            logger.info("Validation requested but not yet implemented")
            # TODO: Integrate IFEval validator

        # Convert to dspy.Prediction for compatibility
        return self._to_prediction(prompt_obj)

    def _extract_error_type(self, context: str) -> str:
        """
        Extract error type from context for Reflexion.

        Args:
            context: Context string that may contain error information

        Returns:
            Extracted error type or "Error" fallback
        """
        error_keywords = [
            "ZeroDivisionError", "NameError", "TypeError",
            "ValueError", "AttributeError", "KeyError",
            "IndexError", "ImportError", "RuntimeError",
            "AssertionError", "MemoryError", "IOError"
        ]

        context_lower = context.lower()
        for error in error_keywords:
            if error.lower() in context_lower:
                return error

        return "Error"  # Fallback

    def _validate_inputs(self, original_idea: str, context: str) -> None:
        """
        Validate input parameters for NLaC strategy.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Raises:
            ValueError: If inputs are None or empty
            TypeError: If inputs are not strings
        """
        if original_idea is None or context is None:
            raise ValueError("original_idea and context must be non-None strings")
        if not isinstance(original_idea, str) or not isinstance(context, str):
            raise TypeError("original_idea and context must be strings")
        if not original_idea.strip():
            raise ValueError("original_idea cannot be empty or whitespace only")

    def _to_prediction(self, prompt_obj: PromptObject) -> dspy.Prediction:
        """
        Convert PromptObject to dspy.Prediction for compatibility.

        Args:
            prompt_obj: PromptObject to convert

        Returns:
            dspy.Prediction with standard fields
        """
        return dspy.Prediction(
            improved_prompt=prompt_obj.template,
            role=prompt_obj.strategy_meta.get("role", "Assistant"),
            directive=prompt_obj.strategy_meta.get("directive", "Help with the request"),
            framework=prompt_obj.strategy_meta.get("framework", "General"),
            guardrails=prompt_obj.guardrails if prompt_obj.guardrails else [],
        )

    @property
    def name(self) -> str:
        """Strategy name for logging."""
        return "nlac"
