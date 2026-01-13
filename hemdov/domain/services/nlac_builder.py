"""
NLaC Builder - Compiles structured PromptObjects.

The "Compiler" for NLaC - builds structured prompts using:
- Role Injection (MultiAIGCD)
- RaR (Rephrase and Respond) for complex inputs
- Context Injection for SQL schemas
- Strategy selection based on complexity + intent
- KNN few-shot examples from ComponentCatalog
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Optional, List

from hemdov.domain.dto.nlac_models import (
    NLaCRequest,
    PromptObject,
    IntentType,
)
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.knn_provider import KNNProvider, FewShotExample
from hemdov.domain.services.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel

logger = logging.getLogger(__name__)


class NLaCBuilder:
    """
    Compiles prompts using Role + RaR + Context Injection.

    Based on:
    - DSPy compiler pattern (prompt optimization)
    - MultiAIGCD techniques (role injection, RaR)
    - KNN few-shot learning (ComponentCatalog)
    """

    def __init__(self, knn_provider: Optional[KNNProvider] = None):
        """
        Initialize builder with dependencies.

        Args:
            knn_provider: Optional KNNProvider for few-shot examples
        """
        self.complexity_analyzer = ComplexityAnalyzer()
        self.intent_classifier = IntentClassifier()
        self.knn_provider = knn_provider

    def build(self, request: NLaCRequest) -> PromptObject:
        """
        Construct a structured PromptObject from NLaCRequest.

        Pipeline:
        1. Classify intent
        2. Analyze complexity
        3. Select strategy
        4. Inject role
        5. Fetch KNN examples (if KNNProvider available)
        6. Build template (with RaR if complex, with few-shot examples)
        7. Compile metadata

        Args:
            request: NLaCRequest with idea, context, inputs

        Returns:
            PromptObject with structured template and metadata
        """
        # Step 1: Classify intent
        intent_str = self.intent_classifier.classify(request)
        intent_type = self.intent_classifier.get_intent_type(intent_str)

        logger.debug(
            f"Building PromptObject | intent={intent_type} | "
            f"idea_length={len(request.idea)}"
        )

        # Step 2: Analyze complexity
        complexity = self.complexity_analyzer.analyze(
            request.idea,
            request.context
        )

        # Step 3: Select strategy
        strategy = self._select_strategy(complexity, intent_str)

        # Step 4: Inject role
        role = self._inject_role(intent_str, complexity)

        # Step 5: Fetch KNN examples
        knn_failed = False
        knn_error = None
        fewshot_examples: List[FewShotExample] = []

        if self.knn_provider:
            # Determine k based on complexity (k=3 for simple/moderate, k=5 for complex)
            k = 5 if complexity == ComplexityLevel.COMPLEX else 3

            # For REFACTOR, filter by expected_output (CRITICAL for MultiAIGCD Scenario III)
            has_expected_output = intent_str.startswith("refactor")

            try:
                fewshot_examples = self.knn_provider.find_examples(
                    intent=intent_str,
                    complexity=complexity.value,
                    k=k,
                    has_expected_output=has_expected_output,
                    user_input=request.idea
                )
                logger.info(f"Fetched {len(fewshot_examples)} KNN examples for {intent_str}/{complexity.value}")
            except (RuntimeError, KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as e:
                logger.exception(
                    f"Failed to fetch KNN examples for {intent_str}/{complexity.value}. "
                    f"Continuing without few-shot guidance. Error: {type(e).__name__}"
                )
                knn_failed = True
                knn_error = f"{type(e).__name__}: {str(e)[:100]}"
                # Continue with empty examples list

        # Step 6: Build template
        if complexity == ComplexityLevel.COMPLEX:
            template = self._build_rar_template(request, role, fewshot_examples)
        else:
            template = self._build_simple_template(request, role, fewshot_examples)

        # Step 7: Build strategy metadata
        strategy_meta = {
            "strategy": strategy,
            "complexity": complexity.value,
            "intent": intent_str,
            "role": role,
            "rar_used": complexity == ComplexityLevel.COMPLEX,
            "fewshot_count": len(fewshot_examples),  # Track KNN examples
            "knn_enabled": self.knn_provider is not None,
        }

        # Step 8: Build constraints
        constraints = self._build_constraints(request, complexity)

        return PromptObject(
            id=str(uuid.uuid4()),
            version="1.0.0",
            intent_type=intent_type,
            template=template,
            strategy_meta=strategy_meta,
            constraints=constraints,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
            knn_failed=knn_failed,
            knn_error=knn_error,
        )

    def _select_strategy(self, complexity: ComplexityLevel, intent: str) -> str:
        """Select strategy based on complexity + intent."""
        # Debug intent always uses debug-focused strategy
        if intent.startswith("debug"):
            if complexity == ComplexityLevel.SIMPLE:
                return "simple_debug"
            elif complexity == ComplexityLevel.MODERATE:
                return "moderate_debug"
            else:
                return "complex_debug"

        # Refactor intent
        elif intent.startswith("refactor"):
            if complexity == ComplexityLevel.SIMPLE:
                return "simple_refactor"
            else:
                return "complex_refactor"

        # Explain intent
        elif intent == "explain":
            return "explain"

        # Generate/Default
        else:
            return complexity.value  # "simple", "moderate", "complex"

    def _inject_role(self, intent: str, complexity: ComplexityLevel) -> str:
        """
        Inject expert role (activates latent subspaces).

        Role selection based on intent + complexity hierarchy.
        """
        # Debug roles ( escalate with complexity)
        if intent.startswith("debug"):
            if complexity == ComplexityLevel.SIMPLE:
                return "Code Debugger"
            elif complexity == ComplexityLevel.MODERATE:
                return "Senior Debugging Specialist"
            else:
                return "Expert Systems Diagnostics Engineer"

        # Refactor roles
        elif intent.startswith("refactor"):
            if complexity == ComplexityLevel.SIMPLE:
                return "Code Reviewer"
            else:
                return "Software Architect"

        # Explain roles
        elif intent == "explain":
            return "Technical Educator"

        # Generate roles ( escalate with complexity)
        else:
            if complexity == ComplexityLevel.SIMPLE:
                return "Developer"
            elif complexity == ComplexityLevel.MODERATE:
                return "Senior Developer"
            else:
                return "Software Engineer"

    def _build_simple_template(self, request: NLaCRequest, role: str, fewshot_examples: Optional[List[FewShotExample]] = None) -> str:
        """Build simple template without RaR, optionally with few-shot examples."""
        template_parts = [
            f"# Role\nYou are a {role}.",
            "",
            "# Task",
        ]

        # Add the core idea
        template_parts.append(request.idea)

        # Add context if provided
        if request.context and request.context.strip():
            template_parts.extend([
                "",
                "# Context",
                request.context,
            ])

        # Add structured inputs (code snippet, error log)
        if request.inputs:
            if request.inputs.code_snippet:
                template_parts.extend([
                    "",
                    "# Code",
                    "```",
                    request.inputs.code_snippet,
                    "```",
                ])

            if request.inputs.error_log:
                template_parts.extend([
                    "",
                    "# Error",
                    request.inputs.error_log,
                ])

            if request.inputs.target_language:
                template_parts.extend([
                    "",
                    f"# Target Language: {request.inputs.target_language}",
                ])

        # Add few-shot examples if available
        if fewshot_examples:
            template_parts.extend([
                "",
                "# Examples",
                "Here are some similar examples to guide you:",
                "",
            ])
            for i, ex in enumerate(fewshot_examples, 1):
                template_parts.extend([
                    f"## Example {i}",
                    f"**Input:** {ex.input_idea}",
                ])
                if ex.input_context:
                    template_parts.append(f"**Context:** {ex.input_context}")
                template_parts.extend([
                    f"**Output:** {ex.improved_prompt}",
                    "",
                ])

        return "\n".join(template_parts)

    def _build_rar_template(self, request: NLaCRequest, role: str, fewshot_examples: Optional[List[FewShotExample]] = None) -> str:
        """
        Build template with RaR (Rephrase and Respond) and few-shot examples.

        For complex inputs, we first rephrase the request to:
        1. Clarify ambiguity
        2. Expand implicit requirements
        3. Structure the problem space

        Few-shot examples are added after RaR for guidance.
        """
        template_parts = [
            f"# Role",
            f"You are a {role}.",
            "",
            "# Understanding the Request",
            "First, let me rephrase the request to ensure clarity:",
            "",
        ]

        # Rephrase section (RaR)
        rephrase = self._rephrase_request(request)
        template_parts.append(f"**Original Request:** {request.idea}")
        template_parts.append(f"**Rephrased Understanding:** {rephrase}")

        # Add the structured response section
        template_parts.extend([
            "",
            "# Task",
            "Based on the above understanding, please:",
        ])

        # Add context if provided
        if request.context and request.context.strip():
            template_parts.extend([
                "",
                "## Additional Context",
                request.context,
            ])

        # Add structured inputs
        if request.inputs:
            if request.inputs.code_snippet:
                template_parts.extend([
                    "",
                    "## Code to Work With",
                    "```",
                    request.inputs.code_snippet,
                    "```",
                ])

            if request.inputs.error_log:
                template_parts.extend([
                    "",
                    "## Error Information",
                    request.inputs.error_log,
                ])

            if request.inputs.target_framework:
                template_parts.append(f"\n**Framework:** {request.inputs.target_framework}")

        # Add few-shot examples if available
        if fewshot_examples:
            template_parts.extend([
                "",
                "## Reference Examples",
                "These examples may help guide your approach:",
                "",
            ])
            for i, ex in enumerate(fewshot_examples[:3], 1):  # Limit to 3 for RAR
                template_parts.extend([
                    f"### Example {i}",
                    f"**Request:** {ex.input_idea}",
                ])
                if ex.input_context:
                    template_parts.append(f"**Context:** {ex.input_context}")
                template_parts.extend([
                    f"**Response:** {ex.improved_prompt}",
                    "",
                ])

        # Add requirements
        template_parts.extend([
            "",
            "## Requirements",
            "- Provide a clear, well-structured response",
            "- Include code examples where applicable",
            "- Explain your reasoning",
        ])

        return "\n".join(template_parts)

    def _rephrase_request(self, request: NLaCRequest) -> str:
        """Rephrase complex request for clarity (RaR technique)."""
        # This is a simplified rephrasing - in production could use LLM
        idea = request.idea

        # Detect key elements
        has_code = request.inputs and request.inputs.code_snippet
        has_error = request.inputs and request.inputs.error_log

        # Build rephrased version
        rephrase_parts = []

        if has_error:
            rephrase_parts.append("debug and fix the error")
        elif "optimizar" in idea.lower() or "refactor" in idea.lower():
            rephrase_parts.append("optimize the code for better performance and maintainability")
        else:
            rephrase_parts.append("implement the requested functionality")

        if request.context:
            rephrase_parts.append("considering the provided context and requirements")

        if has_code:
            rephrase_parts.append("for the given code snippet")

        # Capitalize and join
        result = " ".join(rephrase_parts)
        return result[0].upper() + result[1:] if result else "Process the request"

    def _build_constraints(self, request: NLaCRequest, complexity: ComplexityLevel) -> dict[str, object]:
        """Build constraints dict for the prompt."""
        constraints: dict[str, object] = {}

        # Length constraint based on complexity
        if complexity == ComplexityLevel.SIMPLE:
            constraints["max_tokens"] = 500
        elif complexity == ComplexityLevel.MODERATE:
            constraints["max_tokens"] = 1000
        else:
            constraints["max_tokens"] = 2000

        # Format constraints
        if request.inputs and request.inputs.target_language:
            constraints["format"] = f"code in {request.inputs.target_language}"

        # Quality constraints
        constraints["include_examples"] = complexity != ComplexityLevel.SIMPLE
        constraints["include_explanation"] = complexity == ComplexityLevel.COMPLEX

        return constraints
