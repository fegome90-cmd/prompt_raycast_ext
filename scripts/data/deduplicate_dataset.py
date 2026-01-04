#!/usr/bin/env python3
"""
Deduplicate DSPy Few-Shot Dataset by Input

This script removes duplicate examples from a dataset by keeping only the
first occurrence of each unique input. This prevents GIGO (Garbage In, Garbage Out)
in DSPy KNNFewShot learning where duplicate inputs with different outputs
can confuse the few-shot selector.

Usage:
    python3 scripts/data/deduplicate_dataset.py
"""
import sys
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# Handle both module import and direct execution
try:
    from .utils import load_dataset, save_dataset
except ImportError:
    from utils import load_dataset, save_dataset


def deduplicate_by_input(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate dataset by keeping first occurrence of each unique input.

    Args:
        data: Dataset to deduplicate

    Returns:
        Deduplicated dataset with unique inputs only
    """
    import json
    seen_inputs = set()
    deduplicated = []

    for example in data:
        # Create canonical representation of input
        input_key = json.dumps(example["inputs"], sort_keys=True)

        if input_key not in seen_inputs:
            # First occurrence - keep it
            seen_inputs.add(input_key)
            deduplicated.append(example)

    return deduplicated


def add_metadata(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add deduplication metadata to dataset.

    Args:
        data: Deduplicated dataset

    Returns:
        Dataset with added metadata
    """
    for example in data:
        if "metadata" not in example:
            example["metadata"] = {}
        example["metadata"]["deduplicated"] = True
        example["metadata"]["deduplication_date"] = datetime.now().isoformat()

    return data


def main() -> int:
    """
    Main function to deduplicate merged-trainset.json.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Use relative path from script location
    script_dir = Path(__file__).parent.parent.parent
    base_path = script_dir
    input_file = base_path / "datasets/exports/merged-trainset.json"
    output_file = base_path / "datasets/exports/merged-trainset-deduped.json"

    print(f"Loading dataset from: {input_file}")

    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return 1

    try:
        # Load dataset
        data = load_dataset(str(input_file))
        original_count = len(data)
        print(f"Loaded {original_count} examples")

        # Deduplicate
        print("Deduplicating by input...")
        deduplicated = deduplicate_by_input(data)
        deduplicated_count = len(deduplicated)

        # Add metadata
        deduplicated = add_metadata(deduplicated)

        # Save
        print(f"Saving deduplicated dataset to: {output_file}")
        save_dataset(deduplicated, str(output_file))

        # Report
        removed_count = original_count - deduplicated_count
        removal_rate = (removed_count / original_count) * 100 if original_count > 0 else 0

        print(f"\n{'='*60}")
        print(f"✅ Deduplication Complete!")
        print(f"{'='*60}")
        print(f"Original examples:     {original_count}")
        print(f"Unique examples:       {deduplicated_count}")
        print(f"Removed duplicates:    {removed_count}")
        print(f"Reduction rate:        {removal_rate:.1f}%")
        print(f"Output file:           {output_file}")
        print(f"{'='*60}\n")

        return 0

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file - {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
