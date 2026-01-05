#!/usr/bin/env python3
"""Merge all datasets into unified few-shot learning pool."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set
from hashlib import sha256
from datetime import datetime

# Import shared utilities to avoid code duplication
try:
    from .utils import load_dataset as _utils_load_dataset
except ImportError:
    from utils import load_dataset as _utils_load_dataset


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    """Load JSON dataset, returning empty list if file not found."""
    if not path.exists():
        print(f"  ⚠️  {path.name}: NOT FOUND (skipping)")
        return []
    return _utils_load_dataset(str(path))


def compute_io_hash(example: Dict[str, Any]) -> str:
    """Compute hash of (input, output) pair for deduplication."""
    # Handle both nested (inputs.original_idea) and flat (input) schemas
    if 'inputs' in example:
        input_text = example['inputs'].get('original_idea', '')
    else:
        input_text = example.get('input', '')

    if 'outputs' in example:
        output_text = example['outputs'].get('improved_prompt', '')
    else:
        output_text = example.get('output', '')

    combined = f"{input_text}|||{output_text}"
    return sha256(combined.encode()).hexdigest()


def normalize_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize example to nested schema {inputs, outputs, metadata}."""
    # Already has nested structure
    if 'inputs' in example and 'outputs' in example:
        return example

    # Flat schema (from sqlite-export.json) - needs normalization
    return {
        'inputs': {'original_idea': example.get('input', '')},
        'outputs': {
            'improved_prompt': example.get('output', ''),
            'framework': example.get('metadata', {}).get('framework', 'unknown')
        },
        'metadata': example.get('metadata', {})
    }


def merge_datasets(datasets: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merge multiple datasets with cross-source deduplication."""
    all_examples = []

    for source_name, examples in datasets.items():
        print(f"  Loading {source_name}: {len(examples)} examples")

        for ex in examples:
            # Normalize schema
            normalized = normalize_example(ex)

            # Add source metadata
            if 'metadata' not in normalized:
                normalized['metadata'] = {}
            normalized['metadata']['source_file'] = source_name

            all_examples.append(normalized)

    print(f"\n  Total examples before deduplication: {len(all_examples)}")

    # Deduplicate by I/O hash
    seen_hashes: Set[str] = set()
    deduped = []
    duplicates_removed = 0

    for example in all_examples:
        io_hash = compute_io_hash(example)

        if io_hash not in seen_hashes:
            seen_hashes.add(io_hash)
            example['metadata']['io_hash'] = io_hash
            example['metadata']['duplication_status'] = 'unique'
            deduped.append(example)
        else:
            duplicates_removed += 1

    print(f"  Total examples after deduplication: {len(deduped)}")
    print(f"  Duplicates removed: {duplicates_removed}")

    return deduped


def generate_statistics(pool: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics about the unified pool."""
    stats = {
        'total_examples': len(pool),
        'by_source': {},
        'by_framework': {}
    }

    for ex in pool:
        source = ex.get('metadata', {}).get('source_file', 'unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

        framework = ex.get('outputs', {}).get('framework', 'unknown')
        stats['by_framework'][framework] = stats['by_framework'].get(framework, 0) + 1

    return stats


def main() -> int:
    """Merge all datasets into unified pool."""
    base_path = Path(__file__).parent.parent.parent
    datasets_path = base_path / 'datasets/exports'
    output_path = base_path / 'datasets/exports/unified-fewshot-pool.json'

    print("=" * 70)
    print("CREATING UNIFIED FEWSHOT POOL")
    print("=" * 70)

    # Load all datasets
    print("\nLoading datasets:")
    datasets = {
        'merged-trainset-deduped.json': load_dataset(datasets_path / 'merged-trainset-deduped.json'),
        'fewshot-train.json': load_dataset(datasets_path / 'fewshot-train.json'),
        'sqlite-export.json': load_dataset(datasets_path / 'sqlite-export.json'),
    }

    # Merge and deduplicate
    print("\nMerging datasets:")
    unified_pool = merge_datasets(datasets)

    # Generate statistics
    print("\nGenerating statistics:")
    stats = generate_statistics(unified_pool)

    print(f"\n  By source:")
    for source, count in sorted(stats['by_source'].items()):
        print(f"    {source}: {count}")

    print(f"\n  By framework:")
    for framework, count in sorted(stats['by_framework'].items(), key=lambda x: -x[1])[:5]:
        print(f"    {framework}: {count}")

    # Save unified pool
    print(f"\nSaving unified pool to {output_path.name}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_examples': len(unified_pool),
                'sources': list(datasets.keys()),
                'created_at': str(datetime.now()),
                'statistics': stats
            },
            'examples': unified_pool
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Unified pool created successfully!")
    print(f"   Total examples: {len(unified_pool)}")
    print(f"   Output: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
