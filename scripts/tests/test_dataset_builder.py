"""Tests for DSPyDatasetBuilder."""

import pytest
import json
import tempfile
from pathlib import Path
from scripts.synthetic_examples.dataset_builder import (
    DSPyDatasetBuilder,
    DATASET_SCHEMA,
    TASK_TYPES,
)
from scripts.legacy_curation.models import Domain


def test_dspy_schema_invalid_format():
    """Should reject DSPy dataset with invalid schema"""
    builder = DSPyDatasetBuilder()

    invalid_examples = [
        {"question": "What is the answer?"},  # Missing metadata
        {"metadata": {"task_type": "role_definition"}},  # Missing question
        {
            "question": "What is AI?",
            "metadata": {"task_type": "invalid_type"},  # Invalid task_type
        },
    ]

    for invalid_example in invalid_examples:
        with pytest.raises((KeyError, ValueError)):
            builder.add_examples([invalid_example])


def test_dataset_builder_statistics():
    """Test that dataset builder calculates correct statistics"""
    builder = DSPyDatasetBuilder()

    examples = [
        {
            "question": "What is AI?",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test1.md",
                "variation": "base",
            },
        },
        {
            "question": "How to secure code?",
            "metadata": {
                "task_type": "directive_task",
                "domain": "security",
                "confidence": 0.8,
                "source_component_id": "test2.md",
                "variation": "expand",
            },
        },
        {
            "question": "What is AI?",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.85,
                "source_component_id": "test3.md",
                "variation": "simplify",
            },
        },
    ]

    builder.add_examples(examples)

    stats = builder.get_statistics()

    assert stats["total_examples"] == 3
    assert stats["by_task_type"]["role_definition"] == 2
    assert stats["by_task_type"]["directive_task"] == 1
    assert stats["by_domain"]["aiml"] == 2
    assert stats["by_domain"]["security"] == 1
    assert 0.84 < stats["avg_confidence"] < 0.86


def test_add_examples_valid():
    """Should add valid examples to dataset"""
    builder = DSPyDatasetBuilder()

    examples = [
        {
            "question": "What is machine learning?",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        }
    ]

    builder.add_examples(examples, task_type="role_definition")
    stats = builder.get_statistics()

    assert stats["total_examples"] == 1


def test_add_domain_specific_datasets():
    """Should add domain-specific examples"""
    builder = DSPyDatasetBuilder()

    components_by_domain = {
        Domain.SOFTDEV: [
            {
                "role": "Developer",
                "directive": "Write code",
                "framework": "TDD",
                "confidence": 0.9,
            }
        ],
        Domain.PRODUCTIVITY: [
            {
                "role": "Assistant",
                "directive": "Be productive",
                "framework": "CoT",
                "confidence": 0.8,
            }
        ],
    }

    builder.add_domain_specific_datasets(components_by_domain, examples_per_component=1)
    stats = builder.get_statistics()

    assert stats["total_examples"] == 2
    assert stats["by_domain"]["softdev"] == 1
    assert stats["by_domain"]["productivity"] == 1


def test_build_dataset_creates_valid_file():
    """Should create a valid DSPy-compatible dataset file"""
    builder = DSPyDatasetBuilder()

    examples = [
        {
            "question": "What is AI?",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        }
    ]

    builder.add_examples(examples)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_dataset.json"
        result_path = builder.build_dataset(str(output_path), split="train")

        assert result_path == str(output_path)
        assert output_path.exists()

        with open(output_path, "r") as f:
            dataset = json.load(f)

        assert "examples" in dataset
        assert len(dataset["examples"]) == 1
        assert dataset["examples"][0]["question"] == "What is AI?"


def test_dataset_builder_initialization():
    """Should initialize with default and custom dataset names"""
    builder_default = DSPyDatasetBuilder()
    assert builder_default.dataset_name == "synthetic_examples_v1"

    builder_custom = DSPyDatasetBuilder(dataset_name="custom_dataset")
    assert builder_custom.dataset_name == "custom_dataset"


def test_task_types_constant():
    """TASK_TYPES should contain all required task types"""
    required_types = [
        "role_definition",
        "directive_task",
        "framework_application",
        "guardrail_extraction",
        "combined_task",
    ]

    for task_type in required_types:
        assert task_type in TASK_TYPES


def test_dataset_schema_definition():
    """DATASET_SCHEMA should match expected structure"""
    assert "examples" in DATASET_SCHEMA
    assert isinstance(DATASET_SCHEMA["examples"], list)


def test_build_dataset_with_split():
    """Should build dataset with specified split"""
    builder = DSPyDatasetBuilder()

    examples = [
        {
            "question": "What is AI?",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        }
    ]

    builder.add_examples(examples)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "train_dataset.json"
        builder.build_dataset(str(output_path), split="train")

        with open(output_path, "r") as f:
            dataset = json.load(f)

        assert "split" in dataset
        assert dataset["split"] == "train"
        assert "dataset_name" in dataset


def test_empty_dataset_statistics():
    """Should return correct statistics for empty dataset"""
    builder = DSPyDatasetBuilder()

    stats = builder.get_statistics()

    assert stats["total_examples"] == 0
    assert stats["by_task_type"] == {}
    assert stats["by_domain"] == {}
    assert stats["avg_confidence"] == 0.0
