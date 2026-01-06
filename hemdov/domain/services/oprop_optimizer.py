"""
OPRO Optimizer - Optimization by PROmpting.

Iterative prompt optimization using meta-prompting with trajectory history.
Based on OPRO (Optimization by PROmpting) research.

Key features:
- Fixed iteration budget (max 3) for latency control
- Early stopping at quality threshold (1.0)
- Trajectory tracking for each iteration
- Returns best candidate from history
- KNN few-shot examples in meta-prompts for better guidance
"""

import logging
from typing import List, Optional
from datetime import datetime, UTC

from hemdov.domain.dto.nlac_models import (
    PromptObject,
    OPROIteration,
    OptimizeResponse,
)
from hemdov.domain.services.knn_provider import KNNProvider, FewShotExample

logger = logging.getLogger(__name__)


class OPOROptimizer:
    """
    Optimization by PROmpting (OPRO).

    Iteratively improves prompts using meta-prompting with trajectory history.
    Based on OPRO research papers.

    Enhanced with KNN few-shot examples from ComponentCatalog for
    better meta-prompt quality.
    """

    MAX_ITERATIONS = 3  # Fixed iterations (latency control per user decision: 5-10 LLM calls)
    QUALITY_THRESHOLD = 1.0  # Early stopping if 100% pass

    def __init__(self, llm_client=None, knn_provider: Optional[KNNProvider] = None):
        """
        Initialize optimizer.

        Args:
            llm_client: Optional LLM client for generating variations.
                      If None, uses mock evaluation for testing.
            knn_provider: Optional KNNProvider for few-shot examples in meta-prompts.
        """
        self.llm_client = llm_client
        self.knn_provider = knn_provider

    def run_loop(self, prompt_obj: PromptObject) -> OptimizeResponse:
        """
        Run OPRO optimization loop with early stopping.

        Process:
        1. Generate variation (meta-prompt + trajectory)
        2. Evaluate against constraints (IFEval-style)
        3. Early stopping if quality threshold reached
        4. Store trajectory entry
        5. Return best from history

        Args:
            prompt_obj: Initial PromptObject to optimize

        Returns:
            OptimizeResponse with final result and full trajectory
        """
        trajectory: List[OPROIteration] = []
        best_score = 0.0
        best_prompt = prompt_obj

        logger.info(
            f"Starting OPRO optimization | "
            f"intent={prompt_obj.intent_type} | "
            f"max_iterations={self.MAX_ITERATIONS}"
        )

        for i in range(1, self.MAX_ITERATIONS + 1):
            # Generate candidate variation
            if i == 1:
                # First iteration uses original prompt
                candidate = prompt_obj
            else:
                # Subsequent iterations generate variations
                candidate = self._generate_variation(prompt_obj, trajectory)

            # Evaluate candidate
            score, feedback = self._evaluate(candidate)

            logger.debug(
                f"Iteration {i}/{self.MAX_ITERATIONS} | "
                f"score={score:.2f} | "
                f"feedback={feedback}"
            )

            # Track best candidate
            if score > best_score:
                best_score = score
                best_prompt = candidate

            # Early stopping (quality threshold)
            if score >= self.QUALITY_THRESHOLD:
                logger.info(f"Early stopping at iteration {i} | score={score:.2f}")
                return self._build_response(
                    prompt_obj_id=prompt_obj.id,
                    final_instruction=best_prompt.template,
                    final_score=score,
                    iteration_count=i,
                    early_stopped=True,
                    trajectory=trajectory,
                )

            # Store trajectory entry
            trajectory.append(OPROIteration(
                iteration_number=i,
                meta_prompt_used=self._build_meta_prompt(candidate, trajectory),
                generated_instruction=candidate.template,
                score=score,
                feedback=feedback,
            ))

        # Return best from history
        logger.info(f"Completed {self.MAX_ITERATIONS} iterations | best_score={best_score:.2f}")

        return self._build_response(
            prompt_obj_id=prompt_obj.id,
            final_instruction=best_prompt.template,
            final_score=best_score,
            iteration_count=self.MAX_ITERATIONS,
            early_stopped=False,
            trajectory=trajectory,
        )

    def _generate_variation(self, original: PromptObject, trajectory: List[OPROIteration]) -> PromptObject:
        """
        Generate candidate variation using meta-prompt + trajectory.

        In production, this would call an LLM to generate an improved version.
        For now, returns a modified copy with template refinements.
        """
        if self.llm_client:
            # Production: Use LLM to generate variation
            improved_template = self._llm_generate_variation(original, trajectory)
        else:
            # Testing: Simple refinements without LLM
            improved_template = self._simple_refinement(original, trajectory)

        # Create new PromptObject with improved template
        return PromptObject(
            id=original.id,
            version=original.version,
            intent_type=original.intent_type,
            template=improved_template,
            strategy_meta=original.strategy_meta,
            constraints=original.constraints,
            is_active=original.is_active,
            created_at=original.created_at,
            updated_at=datetime.now(UTC).isoformat(),
        )

    def _simple_refinement(self, prompt_obj: PromptObject, trajectory: List[OPROIteration]) -> str:
        """
        Simple template refinement without LLM (for testing).

        Applies heuristic improvements based on trajectory feedback.
        """
        template = prompt_obj.template

        # If previous iteration had low score, add clarity
        if trajectory:
            last_feedback = trajectory[-1].feedback
            if "unclear" in last_feedback.lower() or "vague" in last_feedback.lower():
                template = "# Clarified Request\n\n" + template

            # If format issues, add formatting instructions
            if "format" in last_feedback.lower():
                if "code" in prompt_obj.constraints.get("format", "").lower():
                    template += "\n\n## Response Format\nProvide code in appropriate language."

        return template

    def _llm_generate_variation(self, prompt_obj: PromptObject, trajectory: List[OPROIteration]) -> str:
        """
        Generate variation using LLM (production implementation).

        This would call the LLM client with a meta-prompt that includes:
        - Original prompt
        - Trajectory history (what was tried and scores)
        - Request for improvement
        """
        # TODO: Integrate with actual LLM client
        # For now, delegate to simple refinement
        return self._simple_refinement(prompt_obj, trajectory)

    def _build_meta_prompt(self, candidate: PromptObject, trajectory: List[OPROIteration]) -> str:
        """
        Build meta-prompt for next iteration.

        Enhanced with KNN few-shot examples to guide the LLM toward
        better prompt variations.
        """
        # Build base meta-prompt
        if not trajectory:
            base_prompt = f"Improve this prompt: {candidate.template[:100]}..."
        else:
            history = "\n".join([
                f"Iteration {t.iteration_number}: score={t.score:.2f}, feedback={t.feedback}"
                for t in trajectory[-2:]  # Last 2 iterations
            ])
            base_prompt = f"Previous attempts:\n{history}\n\nGenerate improved version."

        # Add few-shot examples if KNNProvider available
        if self.knn_provider:
            # Fetch examples based on intent
            intent_str = candidate.strategy_meta.get("intent", "generate")
            complexity_str = candidate.strategy_meta.get("complexity", "moderate")

            fewshot_examples = self.knn_provider.find_examples(
                intent=intent_str,
                complexity=complexity_str,
                k=2  # Use 2 examples for meta-prompt (keep it concise)
            )

            if fewshot_examples:
                examples_section = "\n\n## Reference Examples\nThese examples show good prompt patterns:\n\n"
                for i, ex in enumerate(fewshot_examples, 1):
                    examples_section += f"### Example {i}\n"
                    examples_section += f"**Input:** {ex.input_idea}\n"
                    if ex.input_context:
                        examples_section += f"**Context:** {ex.input_context}\n"
                    examples_section += f"**Improved:** {ex.improved_prompt}\n\n"

                return base_prompt + examples_section

        return base_prompt

    def _evaluate(self, prompt_obj: PromptObject) -> tuple[float, str]:
        """
        Evaluate prompt against constraints (IFEval-style validation).

        Returns:
            (score, feedback) where score is 0.0-1.0
        """
        passed = 0
        total = 0
        warnings = []

        # Check template constraints
        constraints = prompt_obj.constraints

        # 1. Check max_tokens constraint
        max_tokens = constraints.get("max_tokens", 2000)
        template_length = len(prompt_obj.template)
        total += 1
        if template_length <= max_tokens:
            passed += 1
        else:
            warnings.append(f"Template too long: {template_length} > {max_tokens}")

        # 2. Check format constraints
        if "format" in constraints:
            total += 1
            format_req = constraints["format"]
            if "code" in format_req.lower():
                # Check if template contains code markers
                if "```" in prompt_obj.template or "def " in prompt_obj.template:
                    passed += 1
                else:
                    warnings.append("Missing code examples")
            else:
                passed += 1  # No specific format requirement

        # 3. Check include_examples constraint
        if constraints.get("include_examples", False):
            total += 1
            if "example" in prompt_obj.template.lower() or "```" in prompt_obj.template:
                passed += 1
            else:
                warnings.append("Missing examples as required")

        # 4. Check include_explanation constraint
        if constraints.get("include_explanation", False):
            total += 1
            if any(word in prompt_obj.template.lower() for word in ["explain", "reasoning", "because"]):
                passed += 1
            else:
                warnings.append("Missing explanation as required")

        # 5. Basic quality checks
        total += 1
        if len(prompt_obj.template) > 50:  # Minimum meaningful length
            passed += 1
        else:
            warnings.append("Template too short")

        # Calculate score
        score = passed / total if total > 0 else 0.0

        # Build feedback message
        if warnings:
            feedback = f"Issues: {', '.join(warnings)}"
        else:
            feedback = "All constraints passed"

        return score, feedback

    def _build_response(
        self,
        prompt_obj_id: str,
        final_instruction: str,
        final_score: float,
        iteration_count: int,
        early_stopped: bool,
        trajectory: List[OPROIteration],
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
            backend="nlac-opro",
            model="oprop-optimizer",
        )
