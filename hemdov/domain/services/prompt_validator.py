"""
Prompt Validator - IFEval-style validation with autocorrection.

Validates prompts against constraints using IFEval-inspired checks.
Implements Reflexion loop (1 retry) for autocorrection.
"""

import logging
from typing import List, Tuple
from datetime import datetime, UTC

from hemdov.domain.dto.nlac_models import PromptObject

logger = logging.getLogger(__name__)


class PromptValidator:
    """
    Linter de prompts basado en IFEval + Reflexion loop.

    Features:
    - Constraint validation (format, length, structure)
    - Autocorrection with 1 retry (Reflexion pattern)
    - Permissive fallback if autocorrection fails
    """

    MAX_RETRIES = 1  # Reflexion loop: 1 retry attempt

    def validate(self, prompt_obj: PromptObject) -> Tuple[bool, List[str]]:
        """
        Validate prompt against constraints.

        Process:
        1. Check all constraints
        2. If warnings found, attempt autocorrection
        3. Re-validate after correction
        4. Return result (permissive fallback)

        Args:
            prompt_obj: PromptObject to validate

        Returns:
            (passed, warnings) where passed is True if all constraints satisfied
        """
        warnings = self._check_constraints(prompt_obj)

        if not warnings:
            # All constraints passed
            logger.debug("Prompt validation: all constraints passed")
            return True, []

        # Attempt autocorrection (Reflexion loop)
        logger.info(f"Validation found {len(warnings)} issues, attempting autocorrection")

        if self._autocorrect(prompt_obj, warnings):
            # Re-validate after correction
            return self.validate(prompt_obj)

        # Autocorrection failed or MAX_RETRIES exceeded
        logger.warning(f"Autocorrection failed, returning warnings: {warnings}")
        return False, warnings

    def _check_constraints(self, prompt_obj: PromptObject) -> List[str]:
        """Check all constraints and return list of warnings."""
        warnings = []
        template = prompt_obj.template
        constraints = prompt_obj.constraints

        # 1. Check max_tokens constraint
        max_tokens = constraints.get("max_tokens")
        if max_tokens is not None:
            template_length = len(template)
            if template_length > max_tokens:
                warnings.append(
                    f"Template exceeds max_tokens: {template_length} > {max_tokens}"
                )

        # 2. Check format constraints
        format_req = constraints.get("format", "")
        if "json_only" in format_req.lower():
            if not self._is_json_ready(template):
                warnings.append("Template is not valid JSON")

        # Check for markdown constraint (but not if no_markdown is set)
        if "markdown" in format_req.lower() and "no_markdown" not in format_req.lower():
            if "```" not in template:
                warnings.append("Template missing markdown formatting (required)")

        if "no_markdown" in format_req.lower():
            if "```" in template:
                warnings.append("Template contains markdown code blocks (prohibited)")

        # 3. Check include_examples constraint
        if constraints.get("include_examples", False):
            if not self._has_examples(template):
                warnings.append("Template missing examples (required by constraint)")

        # 4. Check include_explanation constraint
        if constraints.get("include_explanation", False):
            if not self._has_explanation(template):
                warnings.append("Template missing explanation (required by constraint)")

        # 5. Basic quality checks
        if len(template.strip()) < 20:
            warnings.append("Template too short (minimum 20 characters)")

        # 6. Check for role/directive presence
        if not any(keyword in template.lower() for keyword in ["role", "task", "you are"]):
            warnings.append("Template missing role or task definition")

        return warnings

    def _is_json_ready(self, template: str) -> bool:
        """Check if template is valid JSON or produces JSON output."""
        import json

        template = template.strip()

        # Check if template itself is valid JSON
        try:
            json.loads(template)
            return True
        except json.JSONDecodeError:
            pass

        # Check if template asks for JSON output
        json_indicators = ["json", "{", "return {", "output.json"]
        return any(indicator in template.lower() for indicator in json_indicators)

    def _has_examples(self, template: str) -> bool:
        """Check if template contains examples."""
        example_indicators = [
            "example", "for instance", "e.g.", "such as",
            "ejemplo", "por ejemplo", "por ejemplo:"
        ]
        template_lower = template.lower()
        return any(indicator in template_lower for indicator in example_indicators)

    def _has_explanation(self, template: str) -> bool:
        """Check if template includes explanation/reasoning."""
        explanation_indicators = [
            "explain", "because", "reason", "why", "how",
            "explica", "porque", "razón", "cómo"
        ]
        template_lower = template.lower()
        return any(indicator in template_lower for indicator in explanation_indicators)

    def _autocorrect(self, prompt_obj: PromptObject, warnings: List[str]) -> bool:
        """
        Attempt autocorrection (Reflexion loop).

        Args:
            prompt_obj: PromptObject to correct (modified in-place)
            warnings: List of validation warnings

        Returns:
            True if correction succeeded, False otherwise
        """
        if not self.llm_client:
            # No LLM client, perform simple autocorrections
            return self._simple_autocorrect(prompt_obj, warnings)

        # Production: Use LLM for autocorrection
        correction_prompt = self._build_correction_prompt(prompt_obj, warnings)
        try:
            corrected = self.llm_client.correct(prompt_obj.template, correction_prompt)
            if corrected and corrected != prompt_obj.template:
                # Update prompt object with corrected template
                object.__setattr__(prompt_obj, 'template', corrected)
                object.__setattr__(prompt_obj, 'updated_at', datetime.now(UTC).isoformat())
                logger.info("Autocorrection successful")
                return True
        except Exception as e:
            logger.error(f"Autocorrection failed: {e}")

        return False

    def _simple_autocorrect(self, prompt_obj: PromptObject, warnings: List[str]) -> bool:
        """
        Simple autocorrection without LLM (testing fallback).

        Applies basic fixes for common issues.
        """
        template = prompt_obj.template
        original_template = template
        corrected = False

        # Fix 1: Add missing role if missing
        if any("missing role" in w.lower() for w in warnings):
            if "role" not in template.lower() and "you are" not in template.lower():
                template = "# Role\nYou are an expert assistant.\n\n" + template
                corrected = True

        # Fix 2: Add code block markers if format requires markdown
        if any("markdown" in w.lower() and "missing" in w.lower() for w in warnings):
            if "def " in template or "function " in template:
                # Add code blocks around function definitions
                lines = template.split('\n')
                in_code_block = False
                new_lines = []
                for line in lines:
                    if line.strip().startswith(('def ', 'function ', 'class ')):
                        if not in_code_block:
                            new_lines.append('```python')
                            in_code_block = True
                    new_lines.append(line)
                if in_code_block:
                    new_lines.append('```')
                template = '\n'.join(new_lines)
                corrected = True

        # Fix 3: Remove code blocks if markdown is prohibited
        if any("markdown" in w.lower() and "prohibited" in w.lower() for w in warnings):
            # Remove markdown code blocks
            template = template.replace('```', '')
            template = template.replace('`', '"')
            corrected = True

        # Apply corrections if any were made
        if corrected and template != original_template:
            object.__setattr__(prompt_obj, 'template', template)
            object.__setattr__(prompt_obj, 'updated_at', datetime.now(UTC).isoformat())
            logger.info("Simple autocorrection applied")
            return True

        return False

    def _build_correction_prompt(self, prompt_obj: PromptObject, warnings: List[str]) -> str:
        """Build correction prompt for LLM."""
        issues = '\n'.join(f'- {w}' for w in warnings)

        return f"""Your previous response had issues:
{issues}

Please correct the prompt to address these issues.
Respond only with the corrected prompt template."""

    def __init__(self, llm_client=None):
        """Initialize validator with optional LLM client."""
        self.llm_client = llm_client
