#!/usr/bin/env python3
"""
Generate few-shot training dataset for DSPy compilation.

Runs DSPy PromptImprover over training cases and saves input/output pairs
for use with KNNFewShot compilation.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict
import dspy

# Add parent dir to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_deepseek_adapter
from hemdov.interfaces import container


def load_training_cases(data_path: str) -> List[Dict]:
    """Load training cases from JSONL file."""
    cases = []
    with open(data_path, 'r') as f:
        for line in f:
            cases.append(json.loads(line))
    return cases


def generate_fewshot_examples(cases: List[Dict], improver: PromptImprover) -> List[Dict]:
    """Generate few-shot examples by running DSPy over training cases.

    Args:
        cases: List of training cases with 'id' and 'input'
        improver: DSPy PromptImprover instance

    Returns:
        List of examples with input (original_idea) and output fields
    """
    examples = []

    for case in cases:
        case_id = case.get('id', 'unknown')
        original_idea = case.get('input', '')

        if not original_idea:
            print(f"Skipping {case_id}: no input")
            continue

        try:
            # Run DSPy to generate improved prompt
            result = improver(original_idea=original_idea, context="")

            # Create example for DSPy KNNFewShot
            example = dspy.Example(
                original_idea=original_idea,
                context="",
                improved_prompt=result.improved_prompt,
                role=result.role,
                directive=result.directive,
                framework=result.framework,
                guardrails=result.guardrails,
                reasoning=getattr(result, 'reasoning', None),
                confidence=getattr(result, 'confidence', None),
            ).with_inputs('original_idea', 'context')

            examples.append(example)
            print(f"✓ Generated example for {case_id}")

            # Extract metadata for domain classification
            metadata = {
                'case_id': case_id,
                'domain': classify_domain(original_idea),
                'category': case.get('id', '').split('-')[0] if '-' in case.get('id', '') else 'unknown'
            }
            # Store metadata separately (not in DSPy example)
            example.metadata = metadata

        except Exception as e:
            print(f"✗ Failed {case_id}: {e}")
            continue

    return examples


def classify_domain(idea: str) -> str:
    """Classify the domain of a prompt idea.

    Simple heuristic classification:
    - 'documentation': documenta, escribe docs, JSDoc, comments
    - 'component': componente, UI, button, modal, form
    - 'hook': hook, React, useState, useEffect
    - 'function': función, helper, utility, method
    - 'api': API, endpoint, servicio, fetch, HTTP
    - 'data': datos, array, lista, estructura
    - 'other': anything else
    """
    idea_lower = idea.lower()

    if any(word in idea_lower for word in ['documenta', 'doc', 'jsdoc', 'comentarios', 'comentario']):
        return 'documentation'
    if any(word in idea_lower for word in ['componente', 'ui', 'button', 'modal', 'form', 'table']):
        return 'component'
    if any(word in idea_lower for word in ['hook', 'react', 'usestate', 'useeffect']):
        return 'hook'
    if any(word in idea_lower for word in ['función', 'function', 'helper', 'utility', 'method', 'método']):
        return 'function'
    if any(word in idea_lower for word in ['api', 'endpoint', 'servicio', 'fetch', 'http', 'wrapper']):
        return 'api'
    if any(word in idea_lower for word in ['dato', 'array', 'lista', 'estructura', 'ejemplo', 'fixture']):
        return 'data'
    if any(word in idea_lower for word in ['migración', 'database', 'db', 'up', 'down']):
        return 'database'

    return 'other'


def save_examples(examples: List, output_path: str) -> None:
    """Save examples to JSON file for DSPy KNNFewShot.

    Format: List of dicts with input fields and output fields.
    """
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

    print(f"\n✓ Saved {len(examples)} examples to {output_path}")


def main():
    """Generate few-shot training dataset."""
    # Configuration
    training_data = "/Users/felipe_gonzalez/Developer/raycast_ext/dashboard/testdata/cases.jsonl"
    output_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/fewshot-train.json"

    print("🔧 Initializing DSPy with DeepSeek...")

    # Initialize DSPy LM
    settings = container.get(Settings)
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.0,  # Deterministic for training
    )
    dspy.configure(lm=lm)

    # Initialize PromptImprover
    improver = PromptImprover()

    print("📂 Loading training cases...")
    cases = load_training_cases(training_data)
    print(f"   Loaded {len(cases)} cases")

    print("\n🔄 Generating few-shot examples...")
    examples = generate_fewshot_examples(cases, improver)

    print(f"\n✓ Generated {len(examples)} examples")

    print("\n💾 Saving to file...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    save_examples(examples, output_path)

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

    print(f"\n📊 Category distribution:")
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count}")


if __name__ == "__main__":
    main()
