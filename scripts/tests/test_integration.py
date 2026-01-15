"""Integration tests for synthetic examples pipeline."""

import json
import sys
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir))

from scripts.synthetic_examples.config import DEFAULT_OUTPUT_DIR
from scripts.synthetic_examples.dataset_builder import DSPyDatasetBuilder
from scripts.synthetic_examples.generators.example_generator import ExampleGenerator
from scripts.synthetic_examples.infrastructure import load_component_catalog
from scripts.synthetic_examples.validator import ExampleValidator


def test_full_pipeline_e2e():
    """Test end-to-end pipeline execution."""
    print("\n=== Integration Test: Full Pipeline E2E ===\n")

    # Step 1: Load components
    print("Step 1: Loading ComponentCatalog...")
    components = load_component_catalog()
    assert len(components) > 0, "Should load at least one component"
    print(f"  ✓ Loaded {len(components)} components")

    # Step 2: Generate examples
    print("\nStep 2: Generating synthetic examples...")
    generator = ExampleGenerator(seed=42)
    examples = generator.generate_batch(components, examples_per_component=2)
    assert len(examples) > 0, "Should generate at least one example"
    print(f"  ✓ Generated {len(examples)} examples")

    # Step 3: Validate examples
    print("\nStep 3: Validating examples...")
    validator = ExampleValidator()

    # Prepare validation examples
    validation_examples = []
    for example in examples:
        source_id = example['metadata']['source_component_id']
        domain = source_id.split(':')[-1]

        validation_examples.append({
            'question': example['example'],
            'metadata': {
                'task_type': 'combined_task',
                'domain': domain,
                'confidence': example['metadata']['confidence'],
                'source_component_id': source_id,
                'variation': example['metadata']['variation'],
            }
        })

    valid_examples, stats = validator.validate_batch(
        validation_examples,
        min_quality_score=0.5
    )

    assert stats['valid'] > 0, "Should have at least one valid example"
    print(f"  ✓ Valid: {stats['valid']}, Invalid: {stats['invalid']}")
    print(f"  ✓ Avg score: {stats['avg_score']:.3f}")

    # Step 4: Build dataset
    print("\nStep 4: Building DSPy dataset...")
    builder = DSPyDatasetBuilder()

    for example in valid_examples:
        source_id = example['metadata']['source_component_id']
        domain = source_id.split(':')[-1]

        dspy_example = {
            'question': example['question'],
            'metadata': {
                'task_type': 'combined_task',
                'domain': domain,
                'confidence': example['metadata']['confidence'],
                'source_component_id': source_id,
                'variation': example['metadata']['variation'],
            }
        }
        builder.add_examples([dspy_example])

    dataset_stats = builder.get_statistics()
    assert dataset_stats['total_examples'] > 0, "Dataset should have at least one example"
    print(f"  ✓ Dataset has {dataset_stats['total_examples']} examples")

    # Step 5: Export dataset
    print("\nStep 5: Exporting dataset...")
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = output_dir / "integration_test.json"
    builder.build_dataset(str(dataset_path), split="test")
    assert dataset_path.exists(), "Dataset file should exist"
    print(f"  ✓ Saved dataset: {dataset_path}")

    # Verify output format
    print("\nStep 6: Verifying output format...")
    with open(dataset_path) as f:
        dataset = json.load(f)

    assert 'dataset_name' in dataset, "Dataset should have dataset_name"
    assert 'split' in dataset, "Dataset should have split"
    assert 'examples' in dataset, "Dataset should have examples"
    assert 'total_examples' in dataset, "Dataset should have total_examples"

    for example in dataset['examples']:
        assert 'question' in example, "Example should have question"
        assert 'metadata' in example, "Example should have metadata"
        assert 'task_type' in example['metadata'], "Example should have task_type"
        assert 'domain' in example['metadata'], "Example should have domain"
        assert 'confidence' in example['metadata'], "Example should have confidence"

    print("  ✓ Output format is correct")

    # Verify example quality
    print("\nStep 7: Verifying example quality...")
    assert dataset['total_examples'] == len(valid_examples), "Total examples should match valid count"
    assert dataset['split'] == 'test', "Split should be 'test'"

    # Check domain distribution
    by_domain = dataset_stats['by_domain']
    assert len(by_domain) > 0, "Should have at least one domain"
    print(f"  ✓ Domain distribution: {by_domain}")

    # Check task type distribution
    by_task_type = dataset_stats['by_task_type']
    assert 'combined_task' in by_task_type, "Should have combined_task type"
    print(f"  ✓ Task type distribution: {by_task_type}")

    print("\n✅ Integration Test PASSED")


if __name__ == "__main__":
    test_full_pipeline_e2e()
