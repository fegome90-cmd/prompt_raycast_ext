#!/usr/bin/env python3
"""
Normalize ComponentCatalog to DSPy Example format.

ComponentCatalog has 847 components with structure (role, directive, framework, guardrails)
but lacks original input. This script generates synthetic inputs and creates DSPy Examples.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Callable
import dspy

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_deepseek_adapter
from hemdov.interfaces import container


def generate_component_input(component: dict) -> str:
    """Generate synthetic input for component.

    Uses domain, category, and framework to create
    realistic input that would produce this component.

    Args:
        component: Component dict with domain, category, framework

    Returns:
        Synthetic input string
    """
    domain = component.get("domain", "")
    category = component.get("category", "")
    framework = component.get("framework", "")
    source_file = component.get("source_file", "")

    # Domain-specific templates
    templates = {
        "softdev": [
            "Crea un prompt para {category} usando {framework}",
            "Genera un prompt de {category} con framework {framework}",
            "Desarrolla prompt para {category}",
        ],
        "data": [
            "Crea estructura de datos para {category}",
            "Genera dataset de {category}",
            "Define formato de {category}",
        ],
        "default": [
            "Genera prompt de {category}",
            "Crea {category}",
            "Desarrolla {category}",
        ]
    }

    # Select template based on domain
    domain_templates = templates.get(domain, templates["default"])

    # Use first template by default, could randomize
    template = domain_templates[0]

    # Generate input
    if framework and framework != "N/A":
        input_text = template.format(category=category, framework=framework)
    else:
        # Fallback template without framework
        input_text = f"Genera prompt de {category}"

    return input_text


def load_component_catalog(path: str) -> List[Dict]:
    """Load ComponentCatalog from JSON file.

    Args:
        path: Path to ComponentCatalog.json

    Returns:
        List of components
    """
    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both array and object formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "components" in data:
        return data["components"]
    else:
        raise ValueError(f"Unexpected ComponentCatalog format at {path}")


def normalize_component(
    component: dict,
    input_generator: Callable[[dict], str]
) -> dspy.Example:
    """Normalize a single component to DSPy Example format.

    Args:
        component: Component dict
        input_generator: Function to generate synthetic input

    Returns:
        dspy.Example with inputs() and outputs()
    """
    # Generate synthetic input
    original_idea = input_generator(component)

    # Extract outputs from component
    role = component.get("role", "")
    directive = component.get("directive", "")
    framework = component.get("framework", "")
    guardrails = component.get("guardrails", [])

    # Handle guardrails as list or string
    if isinstance(guardrails, list):
        guardrails_str = "\n".join(guardrails) if guardrails else ""
    else:
        guardrails_str = guardrails

    # Create improved_prompt from component structure
    # This mirrors the DSPy output format
    improved_prompt_parts = []
    if role:
        improved_prompt_parts.append(f"## Role\n{role}")
    if directive:
        improved_prompt_parts.append(f"## Directive\n{directive}")
    if framework:
        improved_prompt_parts.append(f"## Framework\n{framework}")
    if guardrails_str:
        improved_prompt_parts.append(f"## Guardrails\n{guardrails_str}")

    improved_prompt = "\n\n".join(improved_prompt_parts)

    # Create DSPy Example
    example = dspy.Example(
        original_idea=original_idea,
        context="",
        improved_prompt=improved_prompt,
        role=role,
        directive=directive,
        framework=framework,
        guardrails=guardrails_str,
    ).with_inputs('original_idea', 'context')

    # Add metadata
    metadata = {
        'source': 'ComponentCatalog',
        'domain': component.get('domain', 'unknown'),
        'category': component.get('category', 'unknown'),
        'source_file': component.get('source_file', ''),
    }
    example.metadata = metadata

    return example


def normalize_component_catalog(
    input_path: str,
    output_path: str,
    input_generator: Callable[[dict], str] = generate_component_input
) -> None:
    """Normalize ComponentCatalog to DSPy format.

    For each component:
    1. Extract role, directive, framework, guardrails
    2. Generate synthetic input using input_generator
    3. Save as DSPy Example with inputs() + outputs()

    Args:
        input_path: Path to ComponentCatalog.json
        output_path: Path to save normalized dataset
        input_generator: Function to generate synthetic inputs
    """
    print(f"📂 Loading ComponentCatalog from {input_path}...")
    components = load_component_catalog(input_path)
    print(f"   Loaded {len(components)} components")

    print(f"\n🔄 Normalizing components to DSPy format...")
    examples = []

    for i, component in enumerate(components, 1):
        try:
            example = normalize_component(component, input_generator)
            examples.append(example)

            if i % 100 == 0:
                print(f"   Processed {i}/{len(components)} components")

        except Exception as e:
            print(f"   ✗ Failed to normalize component {i}: {e}")
            continue

    print(f"\n✓ Normalized {len(examples)} components")

    # Save to JSON
    print(f"\n💾 Saving to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert DSPy Examples to dicts for JSON serialization
    data = []
    for ex in examples:
        item = {
            'inputs': {
                'original_idea': ex.original_idea,
                'context': ex.context,
            },
            'outputs': {
                'improved_prompt': ex.improved_prompt,
                'role': ex.role,
                'directive': ex.directive,
                'framework': ex.framework,
                'guardrails': ex.guardrails,
            }
        }
        if hasattr(ex, 'metadata'):
            item['metadata'] = ex.metadata
        data.append(item)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved {len(examples)} examples to {output_path}")

    # Statistics
    domains = {}
    categories = {}
    for ex in examples:
        if hasattr(ex, 'metadata'):
            domain = ex.metadata.get('domain', 'unknown')
            category = ex.metadata.get('category', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1
            categories[category] = categories.get(category, 0) + 1

    print(f"\n📊 Domain distribution:")
    for domain, count in sorted(domains.items()):
        print(f"   {domain}: {count}")

    print(f"\n📊 Top 10 categories:")
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories[:10]:
        print(f"   {category}: {count}")


def main():
    """Normalize ComponentCatalog for DSPy few-shot training."""
    # Configuration
    component_catalog_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/ComponentCatalog.json"
    output_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/normalized-components.json"

    normalize_component_catalog(
        input_path=component_catalog_path,
        output_path=output_path,
        input_generator=generate_component_input
    )


if __name__ == "__main__":
    main()
