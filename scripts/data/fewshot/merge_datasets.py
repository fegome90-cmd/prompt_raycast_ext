#!/usr/bin/env python3
"""
Merge ComponentCatalog and cases.jsonl datasets for DSPy training.

Combines:
- normalized-components.json (847 components)
- fewshot-train.json (30 cases with DSPy outputs)

Result: Combined dataset for KNNFewShot compilation.
"""

import json
from pathlib import Path
from typing import List, Dict


def load_dataset(path: str) -> List[Dict]:
    """Load dataset from JSON file.

    Args:
        path: Path to JSON file

    Returns:
        List of examples
    """
    with open(path, 'r') as f:
        return json.load(f)


def merge_datasets(
    components_path: str,
    cases_path: str,
    output_path: str,
    max_components: int = None
) -> None:
    """Merge ComponentCatalog and cases datasets.

    Args:
        components_path: Path to normalized-components.json
        cases_path: Path to fewshot-train.json
        output_path: Path to save merged dataset
        max_components: Optional limit on components (for testing)
    """
    print(f"📂 Loading components from {components_path}...")
    components = load_dataset(components_path)
    print(f"   Loaded {len(components)} components")

    print(f"\n📂 Loading cases from {cases_path}...")
    cases = load_dataset(cases_path)
    print(f"   Loaded {len(cases)} cases")

    # Optional: limit components for faster testing
    if max_components:
        components = components[:max_components]
        print(f"\n⚠️  Limited to {max_components} components for testing")

    # Merge datasets
    print(f"\n🔄 Merging datasets...")
    merged = components + cases
    print(f"   Merged: {len(components)} + {len(cases)} = {len(merged)} examples")

    # Analyze domain distribution
    domains = {}
    categories = {}
    sources = {}

    for ex in merged:
        metadata = ex.get('metadata', {})
        domain = metadata.get('domain', 'unknown')
        category = metadata.get('category', 'unknown')
        source = metadata.get('source', 'unknown')

        domains[domain] = domains.get(domain, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        sources[source] = sources.get(source, 0) + 1

    print(f"\n📊 Source distribution:")
    for source, count in sorted(sources.items()):
        print(f"   {source}: {count}")

    print(f"\n📊 Domain distribution:")
    for domain, count in sorted(domains.items()):
        print(f"   {domain}: {count}")

    print(f"\n📊 Top 10 categories:")
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories[:10]:
        print(f"   {category}: {count}")

    # Save merged dataset
    print(f"\n💾 Saving to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)

    print(f"✓ Saved {len(merged)} examples to {output_path}")

    # Validation: check all examples have required fields
    print(f"\n✓ Validating dataset format...")
    invalid = 0
    for i, ex in enumerate(merged):
        if 'inputs' not in ex or 'outputs' not in ex:
            print(f"   ✗ Example {i}: missing inputs or outputs")
            invalid += 1
        if 'original_idea' not in ex['inputs']:
            print(f"   ✗ Example {i}: missing original_idea in inputs")
            invalid += 1
        if 'improved_prompt' not in ex['outputs']:
            print(f"   ✗ Example {i}: missing improved_prompt in outputs")
            invalid += 1

    if invalid == 0:
        print(f"   ✓ All {len(merged)} examples have valid format")
    else:
        print(f"   ✗ Found {invalid} invalid examples")


def main():
    """Merge datasets for DSPy few-shot training."""
    # Configuration
    components_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/normalized-components.json"
    cases_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/fewshot-train.json"
    output_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/merged-trainset.json"

    # Optional: limit components for faster testing
    # Comment out for full dataset
    max_components = None  # None = use all 847 components

    merge_datasets(
        components_path=components_path,
        cases_path=cases_path,
        output_path=output_path,
        max_components=max_components
    )


if __name__ == "__main__":
    main()
