from typing import List, Dict, Optional
import random
from scripts.legacy_curation.models import Component, Domain


class ExampleGenerator:
    """Generates synthetic prompt examples from components."""

    TEMPLATES = {
        Domain.SOFTDEV: [
            "You are an expert {role}.",
            "As a {role}, your task is to {directive}.",
            "You specialize in {role} with expertise in {domain_lower}.",
        ],
        Domain.PRODUCTIVITY: [
            "You are a {role} focused on efficiency.",
            "Your primary goal is {directive}.",
        ],
        Domain.AIML: [
            "You are a {role} with deep understanding of {domain_lower}.",
            "As a {role}, help with {directive}.",
        ],
        Domain.SECURITY: [
            "You are a security-focused {role}.",
            "Apply {framework} to {directive}.",
        ],
        Domain.OTHER: [
            "You are a {role}.",
            "Your task is to {directive}.",
        ],
    }

    VARIATIONS = [
        "add_context",
        "simplify",
        "expand",
        "restructure",
    ]

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)

    def generate_single_example(
        self, component: Component, variation: Optional[str] = None
    ) -> Dict:
        """
        Generate a single synthetic example from a component.

        Args:
            component: Source component with role, directive, framework, guardrails
            variation: Optional variation to apply

        Returns:
            Dictionary with example data
        """
        # Clean role (remove trailing dots and whitespace)
        role = component.role.strip().rstrip(".")
        if not role:
            role = "assistant"

        # Clean directive (handle empty directive)
        directive = component.directive.strip().rstrip(".")
        if not directive:
            # Generate a default directive based on domain
            default_directives = {
                Domain.SOFTDEV: "assist with software development tasks",
                Domain.PRODUCTIVITY: "improve productivity and efficiency",
                Domain.AIML: "help with AI and machine learning",
                Domain.SECURITY: "provide security guidance",
                Domain.OTHER: "assist with the task",
            }
            directive = default_directives.get(component.domain, "assist with the task")

        component_with_defaults = Component(
            source_file=component.source_file,
            domain=component.domain,
            role=role,
            directive=directive,
            framework=component.framework,
            guardrails=component.guardrails,
            confidence=component.confidence,
        )

        domain_templates = self.TEMPLATES.get(
            component.domain, self.TEMPLATES[Domain.OTHER]
        )

        # Select template and apply variation
        template = random.choice(domain_templates)
        if variation:
            template = self._apply_variation(
                template, variation, component_with_defaults
            )

        # Fill template and clean up
        example = self._fill_template(template, component_with_defaults)

        # Post-process to ensure minimum length
        if len(example) < 50 and variation:
            # If variation applied but still too short, add more context
            example += f" Provide detailed explanations, step-by-step reasoning, and practical examples."

        # Ensure example ends with proper punctuation
        if not example.endswith((".", "!", "?")):
            example += "."

        example_dict = {
            "role": role,
            "directive": directive,
            "example": example,
            "metadata": {
                "source_component_id": f"{component.source_file}:{component.domain}",
                "variation": variation or "base",
                "generated_at": "2026-01-01T21:00:00Z",
                "confidence": component.confidence,
            },
        }

        return example_dict

    def generate_batch(
        self,
        components: List[Component],
        examples_per_component: int = 3,
        variation: Optional[str] = None,
    ) -> List[Dict]:
        """
        Generate multiple examples per component.

        Args:
            components: List of components to generate examples from
            examples_per_component: Number of examples per component
            variation: Optional variation to apply to all

        Returns:
            List of generated examples
        """
        examples = []
        for component in components:
            for _ in range(examples_per_component):
                example = self.generate_single_example(component, variation)
                examples.append(example)

        return examples

    def _apply_variation(
        self, template: str, variation: str, component: Component
    ) -> str:
        """Apply a variation to a template."""
        if variation == "simplify":
            parts = template.split(".")
            if len(parts) > 1:
                return parts[0] + "."
            return template
        elif variation == "expand":
            # Expand by adding more descriptive language
            if "You are a" in template:
                return template.replace(
                    "You are a", "You act as a highly experienced and knowledgeable"
                )
            elif "You are an" in template:
                return template.replace(
                    "You are an", "You act as a highly experienced and knowledgeable"
                )
            elif "You are" in template:
                return template.replace(
                    "You are", "You act as a highly experienced and knowledgeable"
                )
            elif "As a" in template:
                return template.replace(
                    "As a", "As an exceptionally skilled and experienced"
                )
            elif "You specialize" in template:
                return template.replace(
                    "You specialize", "You are a recognized expert who specializes"
                )
            else:
                return f"{template} You have extensive expertise and deep knowledge in your field."
        elif variation == "add_context":
            return f"{template} Provide detailed explanations with step-by-step reasoning, include practical examples when relevant, and avoid unnecessary technical jargon."
        elif variation == "restructure":
            parts = template.split(".")
            if len(parts) > 1:
                clean_parts = [p.strip() for p in parts if p.strip()]
                if len(clean_parts) > 1:
                    return f"{clean_parts[1]}. {clean_parts[0]}."
            return template
        return template

    def _fill_template(self, template: str, component: Component) -> str:
        """Fill template with component data."""
        try:
            example = template.replace("{role}", component.role)
            example = example.replace("{directive}", component.directive)
            example = example.replace("{domain_lower}", component.domain.value.lower())
            example = example.replace("{framework}", component.framework)

            # Clean up double dots and formatting issues
            example = example.replace("..", ".").replace("  ", " ").strip()

            return example
        except Exception:
            return f"{component.role}. {component.directive}."
