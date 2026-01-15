#!/usr/bin/env python3
"""Script to generate synthetic example datasets."""

import sys
from pathlib import Path

# Add raycast_ext to path for imports
project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir))

import json

from scripts.synthetic_examples.config import DEFAULT_OUTPUT_DIR
from scripts.synthetic_examples.dataset_builder import DSPyDatasetBuilder
from scripts.synthetic_examples.generators.example_generator import ExampleGenerator
from scripts.synthetic_examples.infrastructure import load_component_catalog
from scripts.synthetic_examples.validator import ExampleValidator


def generate_synthetic_datasets():
    """Generate train/val/test synthetic example datasets."""
    print("=== Synthetic Dataset Generation Pipeline ===\n")

    # 1. Load components
    print("Step 1: Loading ComponentCatalog...")
    components = load_component_catalog()
    print(f"  ✓ Loaded {len(components)} components with confidence >= 0.2\n")

    # 2. Generate synthetic examples
    print("Step 2: Generating synthetic examples...")
    generator = ExampleGenerator(seed=42)
    examples = generator.generate_batch(
        components,
        examples_per_component=3,
    )
    print(f"  ✓ Generated {len(examples)} synthetic examples\n")

    # 3. Validate examples
    print("Step 3: Validating examples...")
    validator = ExampleValidator()

    # Prepare validation examples
    validation_examples = []
    for example in examples:
        source_id = example["metadata"]["source_component_id"]
        domain = source_id.split(":")[-1]

        validation_examples.append(
            {
                "question": example["example"],
                "metadata": {
                    "task_type": "combined_task",
                    "domain": domain,
                    "confidence": example["metadata"]["confidence"],
                    "source_component_id": source_id,
                    "variation": example["metadata"]["variation"],
                },
            }
        )

    valid_examples, stats = validator.validate_batch(
        validation_examples, min_quality_score=0.5
    )

    print(f"  ✓ Valid: {stats['valid']}, Invalid: {stats['invalid']}")
    print(f"  ✓ Avg score: {stats['avg_score']:.3f}")
    print(f"  ✓ Min score: {stats['min_score']:.3f}")
    print(f"  ✓ Max score: {stats['max_score']:.3f}\n")

    # 4. Build datasets
    print("Step 4: Building DSPy datasets...")
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert valid examples to DSPy format
    builder = DSPyDatasetBuilder()

    for i, example in enumerate(valid_examples):
        source_id = example["metadata"]["source_component_id"]
        domain = source_id.split(":")[-1]

        dspy_example = {
            "question": example["question"],
            "metadata": {
                "task_type": "combined_task",
                "domain": domain,
                "confidence": example["metadata"]["confidence"],
                "source_component_id": source_id,
                "variation": example["metadata"]["variation"],
            },
        }
        builder.add_examples([dspy_example])

    # Split into train/val/test (70/15/15)
    all_examples = builder.examples
    total = len(all_examples)
    train_count = int(total * 0.70)
    val_count = int(total * 0.15)
    test_count = total - train_count - val_count

    print(f"  ✓ Total examples: {total}")
    print(f"  ✓ Train: {train_count}, Val: {val_count}, Test: {test_count}\n")

    # Train dataset
    builder_train = DSPyDatasetBuilder(dataset_name="synthetic_examples_train")
    builder_train.examples = all_examples[:train_count]
    train_path = output_dir / "train.json"
    builder_train.build_dataset(str(train_path), split="train")
    print(f"  ✓ Saved train dataset: {train_path}")

    # Val dataset
    builder_val = DSPyDatasetBuilder(dataset_name="synthetic_examples_val")
    builder_val.examples = all_examples[train_count : train_count + val_count]
    val_path = output_dir / "val.json"
    builder_val.build_dataset(str(val_path), split="validation")
    print(f"  ✓ Saved val dataset: {val_path}")

    # Test dataset
    builder_test = DSPyDatasetBuilder(dataset_name="synthetic_examples_test")
    builder_test.examples = all_examples[train_count + val_count :]
    test_path = output_dir / "test.json"
    builder_test.build_dataset(str(test_path), split="test")
    print(f"  ✓ Saved test dataset: {test_path}\n")

    # 5. Print statistics
    print("Step 5: Dataset Statistics")
    stats = builder.get_statistics()
    print(f"  Total examples: {stats['total_examples']}")
    print(f"  By task_type: {stats['by_task_type']}")
    print(f"  By domain: {stats['by_domain']}")
    print(f"  Avg confidence: {stats['avg_confidence']:.3f}\n")

    print("=== Pipeline Completed Successfully ===\n")

    # Save summary
    summary = {
        "pipeline_stats": stats,
        "validation_stats": stats,
        "splits": {"train": train_count, "val": val_count, "test": test_count},
        "total_components": len(components),
        "total_examples_generated": len(examples),
        "total_valid_examples": len(valid_examples),
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ Saved summary: {summary_path}")


if __name__ == "__main__":
    generate_synthetic_datasets()
