#!/usr/bin/env python3
"""
Validate DSPy Few-Shot Datasets

This script analyzes dataset quality by:
1. Validating DSPy Example structure (inputs/outputs fields)
2. Finding duplicate inputs
3. Checking output consistency for duplicate inputs

Usage:
    python3 scripts/data/validate_datasets.py
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List


def load_dataset(path: str) -> List[Dict[str, Any]]:
    """
    Load JSON dataset from file.

    Args:
        path: Path to JSON file

    Returns:
        List of examples

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_structure(data: List[Dict[str, Any]], name: str) -> bool:
    """
    Validate DSPy Example structure.

    Checks that each example has:
    - inputs field with original_idea
    - outputs field with improved_prompt

    Args:
        data: Dataset to validate
        name: Dataset name for error reporting

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, list):
        print(f"❌ {name}: Data is not a list")
        return False

    for i, example in enumerate(data):
        if not isinstance(example, dict):
            print(f"❌ {name}: Example {i} is not a dict")
            return False

        if "inputs" not in example:
            print(f"❌ {name}: Example {i} missing 'inputs' field")
            return False

        if "outputs" not in example:
            print(f"❌ {name}: Example {i} missing 'outputs' field")
            return False

        if "original_idea" not in example["inputs"]:
            print(f"❌ {name}: Example {i} missing 'original_idea' in inputs")
            return False

        if "improved_prompt" not in example["outputs"]:
            print(f"❌ {name}: Example {i} missing 'improved_prompt' in outputs")
            return False

    print(f"✅ {name}: Structure validation passed ({len(data)} examples)")
    return True


def analyze_duplicates(data: List[Dict[str, Any]], name: str) -> Dict[str, List[int]]:
    """
    Find duplicate inputs in dataset.

    Args:
        data: Dataset to analyze
        name: Dataset name for reporting

    Returns:
        Dictionary mapping input JSON string to list of indices where it appears
    """
    input_to_indices = defaultdict(list)

    for i, example in enumerate(data):
        # Create a canonical representation of the input
        input_key = json.dumps(example["inputs"], sort_keys=True)
        input_to_indices[input_key].append(i)

    # Filter to only duplicates (appears more than once)
    duplicates = {
        key: indices for key, indices in input_to_indices.items()
        if len(indices) > 1
    }

    total_duplicates = sum(len(indices) for indices in duplicates.values())
    unique_duplicates = len(duplicates)

    print(f"\n📊 {name} Duplication Analysis:")
    print(f"  Total examples: {len(data)}")
    print(f"  Unique inputs: {len(input_to_indices)}")
    print(f"  Duplicate inputs: {unique_duplicates}")
    print(f"  Total duplicate occurrences: {total_duplicates}")

    if len(data) > 0:
        dup_rate = (total_duplicates / len(data)) * 100
        print(f"  Duplication rate: {dup_rate:.1f}%")

    return duplicates


def check_output_consistency(
    data: List[Dict[str, Any]],
    duplicates: Dict[str, List[int]],
    name: str
) -> None:
    """
    Check if duplicate inputs have consistent or different outputs.

    Args:
        data: Dataset to check
        duplicates: Dictionary of duplicate inputs to indices
        name: Dataset name for reporting
    """
    if not duplicates:
        print(f"\n✅ {name}: No duplicates to check for consistency")
        return

    consistent = 0
    inconsistent = 0

    print(f"\n🔍 {name} Output Consistency Check:")

    for input_key, indices in duplicates.items():
        # Get all outputs for this input
        outputs = []
        for idx in indices:
            output_key = json.dumps(data[idx]["outputs"], sort_keys=True)
            outputs.append(output_key)

        # Check if all outputs are the same
        unique_outputs = set(outputs)
        if len(unique_outputs) == 1:
            consistent += 1
        else:
            inconsistent += 1
            # Show example of inconsistency
            if inconsistent <= 3:  # Show first 3
                print(f"\n  ⚠️  Inconsistent outputs for input:")
                # Pretty print the input (truncated)
                input_data = json.loads(input_key)
                idea = input_data.get("original_idea", "")[:60]
                print(f"     Input: {idea}...")
                print(f"     Found {len(unique_outputs)} different outputs across {len(indices)} examples")


def print_duplicate_examples(
    data: List[Dict[str, Any]],
    duplicates: Dict[str, List[int]],
    name: str,
    max_examples: int = 5
) -> None:
    """
    Print examples of duplicate inputs.

    Args:
        data: Dataset to analyze
        duplicates: Dictionary of duplicate inputs to indices
        name: Dataset name for reporting
        max_examples: Maximum examples to print
    """
    if not duplicates:
        return

    print(f"\n📝 {name} Sample Duplicates (showing first {min(max_examples, len(duplicates))}):")

    for i, (input_key, indices) in enumerate(list(duplicates.items())[:max_examples]):
        input_data = json.loads(input_key)
        idea = input_data.get("original_idea", "")

        print(f"\n  {i+1}. Input: {idea}")
        print(f"     Appears at indices: {indices}")
        print(f"     Count: {len(indices)} occurrences")


def main() -> int:
    """
    Main function to run validation on datasets.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Define datasets to validate
    datasets = {
        "merged-trainset.json": "datasets/exports/merged-trainset.json",
        "fewshot-train.json": "datasets/exports/fewshot-train.json",
    }

    base_path = Path("/Users/felipe_gonzalez/Developer/raycast_ext")

    all_valid = True

    for name, rel_path in datasets.items():
        print(f"\n{'='*70}")
        print(f"Validating: {name}")
        print(f"{'='*70}")

        path = base_path / rel_path

        if not path.exists():
            print(f"⚠️  File not found: {path}")
            all_valid = False
            continue

        try:
            # Load dataset
            data = load_dataset(str(path))

            # Validate structure
            if not validate_structure(data, name):
                all_valid = False
                continue

            # Analyze duplicates
            duplicates = analyze_duplicates(data, name)

            # Check output consistency
            check_output_consistency(data, duplicates, name)

            # Print sample duplicates
            print_duplicate_examples(data, duplicates, name)

        except json.JSONDecodeError as e:
            print(f"❌ {name}: Invalid JSON - {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {name}: Unexpected error - {e}")
            all_valid = False

    print(f"\n{'='*70}")
    if all_valid:
        print("✅ Validation complete")
    else:
        print("⚠️  Validation complete with errors")
    print(f"{'='*70}\n")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
