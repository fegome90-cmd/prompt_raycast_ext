"""
NLaC Strategy - Natural Language as Code integration.

Adapts NLaC services to the PromptImproverStrategy interface.
Maintains backward compatibility with existing DSPy-based strategies.
"""

import dspy
import logging
from typing import Optional

from hemdov.domain.dto.nlac_models import (
    NLaCRequest,
    PromptObject,
    IntentType,
    NLaCInputs,
)
from hemdov.domain.services import (
    NLaCBuilder,
    OPOROptimizer,
    PromptValidator,
    PromptCache,
)
from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)


class NLaCStrategy(PromptImproverStrategy):
    """
    NLaC Strategy - Treats prompts as structured executable objects.

    Integrates:
    - Intent classification (debug, refactor, generate, explain)
    - Complexity analysis (simple, moderate, complex)
    - Role injection (MultiAIGCD)
    - RaR (Rephrase and Respond) for complex inputs
    - OPRO optimization (3 iterations with early stopping)
    - IFEval-style validation with autocorrection
    - SHA256-based caching

    Maintains backward compatibility by returning dspy.Prediction.
    """

    def __init__(
        self,
        llm_client=None,
        enable_cache: bool = True,
        enable_optimization: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize NLaC strategy with all services.

        Args:
            llm_client: Optional LLM client for advanced features
            enable_cache: Whether to use prompt caching
            enable_optimization: Whether to run OPRO optimization
            enable_validation: Whether to run IFEval validation
        """
        self.builder = NLaCBuilder()
        self.optimizer = OPOROptimizer(llm_client=llm_client)
        self.validator = PromptValidator(llm_client=llm_client)
        self.cache = PromptCache(repository=None) if enable_cache else None
        self._enable_optimization = enable_optimization
        self._enable_validation = enable_validation
        self._llm_client = llm_client

    @property
    def name(self) -> str:
        """Strategy name for logging."""
        return "nlac"

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Improve prompt using NLaC pipeline.

        Pipeline:
        1. Check cache (if enabled)
        2. Build PromptObject (intent + complexity + role injection)
        3. Optimize with OPRO (if enabled)
        4. Validate with IFEval (if enabled)
        5. Cache result (if enabled)
        6. Convert to dspy.Prediction for compatibility

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails
        """
        # Input validation
        self._validate_inputs(original_idea, context)

        # Create NLaC request
        request = NLaCRequest(
            idea=original_idea,
            context=context,
            mode="nlac"
        )

        # Check cache
        if self.cache:
            cached = self._check_cache(request)
            if cached:
                logger.info(f"Cache hit for request: {original_idea[:50]}...")
                return self._to_prediction(cached)

        # Build PromptObject
        logger.info(f"Building NLaC prompt for: {original_idea[:50]}...")
        prompt_obj = self.builder.build(request)

        # Optimize with OPRO
        if self._enable_optimization:
            logger.info("Running OPRO optimization...")
            opt_response = self.optimizer.run_loop(prompt_obj)
            # Update template with optimized version
            prompt_obj.template = opt_response.final_instruction
            from datetime import datetime, UTC
            prompt_obj.updated_at = datetime.now(UTC).isoformat()

        # Validate with IFEval
        if self._enable_validation:
            logger.info("Running IFEval validation...")
            passed, warnings = self.validator.validate(prompt_obj)
            if not passed:
                logger.warning(f"Validation failed with {len(warnings)} warnings: {warnings}")

        # Cache result
        if self.cache:
            self._update_cache(request, prompt_obj)

        # Convert to dspy.Prediction for compatibility
        return self._to_prediction(prompt_obj)

    def _check_cache(self, request: NLaCRequest) -> Optional[PromptObject]:
        """Check cache for existing prompt."""
        # Synchronous wrapper for async cache
        import asyncio
        return asyncio.run(self.cache.get(request))

    def _update_cache(self, request: NLaCRequest, prompt_obj: PromptObject) -> None:
        """Update cache with new prompt."""
        # Synchronous wrapper for async cache
        import asyncio
        asyncio.run(self.cache.put(request, prompt_obj))

    def _to_prediction(self, prompt_obj: PromptObject) -> dspy.Prediction:
        """
        Convert PromptObject to dspy.Prediction for compatibility.

        Maps NLaC fields to legacy DSPy format:
        - template → improved_prompt
        - strategy_meta.role → role
        - strategy_meta → directive (metadata)
        - framework (default: chain-of-thought)
        - guardrails (from constraints)
        """
        # Extract metadata
        strategy_meta = prompt_obj.strategy_meta or {}
        constraints = prompt_obj.constraints or {}

        # Build guardrails from constraints
        guardrails = []
        if constraints.get("max_tokens"):
            guardrails.append(f"Max length: {constraints['max_tokens']} tokens")
        if constraints.get("include_examples"):
            guardrails.append("Include examples")
        if constraints.get("include_explanation"):
            guardrails.append("Include explanation")
        if constraints.get("format"):
            guardrails.append(f"Format: {constraints['format']}")

        # Build directive from strategy metadata
        directive_parts = [
            f"Strategy: {strategy_meta.get('strategy', 'unknown')}",
            f"Intent: {strategy_meta.get('intent', 'unknown')}",
            f"Complexity: {strategy_meta.get('complexity', 'unknown')}",
        ]
        directive = " | ".join(directive_parts)

        # Determine framework from complexity
        complexity = strategy_meta.get("complexity", "simple")
        if complexity == "complex":
            framework = "tree-of-thoughts"
        elif complexity == "moderate":
            framework = "decomposition"
        else:
            framework = "chain-of-thought"

        return dspy.Prediction(
            improved_prompt=prompt_obj.template,
            role=strategy_meta.get("role", "Developer"),
            directive=directive,
            framework=framework,
            guardrails=guardrails,
        )
