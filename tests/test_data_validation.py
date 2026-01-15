"""
Tests for dataset validation and deduplication scripts.

Following TDD approach: tests are written first, then implementation.
"""
import json
import os
from pathlib import Path

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestValidationScriptsExist:
    """Test that validation scripts exist and are executable."""

    def test_validate_datasets_script_exists(self):
        """Check that validate_datasets.py exists and is executable."""
        script_path = PROJECT_ROOT / "scripts/data/validate_datasets.py"
        assert script_path.exists(), "validate_datasets.py should exist"
        assert os.access(script_path, os.X_OK), "validate_datasets.py should be executable"

    def test_deduplicate_dataset_script_exists(self):
        """Check that deduplicate_dataset.py exists and is executable."""
        script_path = PROJECT_ROOT / "scripts/data/deduplicate_dataset.py"
        assert script_path.exists(), "deduplicate_dataset.py should exist"
        assert os.access(script_path, os.X_OK), "deduplicate_dataset.py should be executable"


class TestDeduplicationLogic:
    """Test deduplication logic with sample data."""

    def test_deduplicate_removes_duplicate_inputs(self):
        """Test that deduplication keeps first occurrence of each unique input."""
        # Sample data with duplicate inputs
        sample_data = [
            {
                "inputs": {"original_idea": "create a function", "context": ""},
                "outputs": {"improved_prompt": "Prompt 1", "role": "role1"},
                "metadata": {"source": "test1"}
            },
            {
                "inputs": {"original_idea": "create a function", "context": ""},
                "outputs": {"improved_prompt": "Prompt 2", "role": "role2"},
                "metadata": {"source": "test2"}
            },
            {
                "inputs": {"original_idea": "write a component", "context": ""},
                "outputs": {"improved_prompt": "Prompt 3", "role": "role3"},
                "metadata": {"source": "test3"}
            },
        ]

        # Import and use deduplication function
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts/data"))
        from deduplicate_dataset import deduplicate_by_input

        result = deduplicate_by_input(sample_data)

        # Should have 2 unique inputs (first "create a function" and "write a component")
        assert len(result) == 2, f"Expected 2 unique inputs, got {len(result)}"

        # First occurrence should be kept
        assert result[0]["outputs"]["improved_prompt"] == "Prompt 1", "Should keep first occurrence"
        assert result[0]["metadata"]["source"] == "test1", "Should preserve metadata"

        # Second unique input should be present
        assert result[1]["inputs"]["original_idea"] == "write a component"

    def test_deduplicate_preserves_all_fields(self):
        """Test that deduplication preserves all fields of the kept example."""
        sample_data = [
            {
                "inputs": {"original_idea": "test", "context": "some context"},
                "outputs": {
                    "improved_prompt": "Full prompt",
                    "role": "Test Role",
                    "directive": "Test Directive",
                    "framework": "test-framework",
                    "guardrails": "test-guardrails"
                },
                "metadata": {
                    "source": "test-source",
                    "domain": "test-domain",
                    "category": "test-category"
                }
            },
            {
                # Same input (including context) - should be deduplicated
                "inputs": {"original_idea": "test", "context": "some context"},
                "outputs": {"improved_prompt": "Duplicate"},
                "metadata": {"source": "duplicate"}
            }
        ]

        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts/data"))
        from deduplicate_dataset import deduplicate_by_input

        result = deduplicate_by_input(sample_data)

        assert len(result) == 1
        assert result[0]["inputs"]["context"] == "some context"
        assert result[0]["outputs"]["role"] == "Test Role"
        assert result[0]["metadata"]["domain"] == "test-domain"


class TestDeduplicatedDataset:
    """Test the actual deduplicated dataset file."""

    def test_deduped_dataset_was_created(self):
        """Verify that deduped file exists and has no duplicate inputs."""
        deduped_path = PROJECT_ROOT / "datasets/exports/merged-trainset-deduped.json"

        assert deduped_path.exists(), "Deduplicated dataset should exist"

        with open(deduped_path) as f:
            data = json.load(f)

        # Check structure
        assert isinstance(data, list), "Dataset should be a list"

        # Extract all inputs
        inputs_set = set()
        duplicate_count = 0
        for item in data:
            input_key = json.dumps(item["inputs"], sort_keys=True)
            if input_key in inputs_set:
                duplicate_count += 1
            inputs_set.add(input_key)

        assert duplicate_count == 0, f"Found {duplicate_count} duplicate inputs in deduplicated dataset"

        # Verify significant reduction from original
        # Original has 877 examples, expected ~39 unique
        assert len(data) < 100, f"Deduplicated dataset should have < 100 examples, got {len(data)}"
        assert len(data) >= 30, f"Deduplicated dataset should have at least 30 examples, got {len(data)}"

    def test_deduped_dataset_structure_valid(self):
        """Verify that deduplicated examples have valid DSPy structure."""
        deduped_path = PROJECT_ROOT / "datasets/exports/merged-trainset-deduped.json"

        with open(deduped_path) as f:
            data = json.load(f)

        for i, item in enumerate(data):
            # Check required fields
            assert "inputs" in item, f"Example {i} missing 'inputs' field"
            assert "outputs" in item, f"Example {i} missing 'outputs' field"

            # Check inputs structure
            assert "original_idea" in item["inputs"], f"Example {i} missing 'original_idea' in inputs"

            # Check outputs has at least improved_prompt
            assert "improved_prompt" in item["outputs"], f"Example {i} missing 'improved_prompt' in outputs"


class TestValidationScriptFunctions:
    """Test individual functions from validation script."""

    def test_validate_structure(self):
        """Test validate_structure function."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts/data"))
        from validate_datasets import validate_structure

        # Valid data
        valid_data = [
            {
                "inputs": {"original_idea": "test", "context": ""},
                "outputs": {"improved_prompt": "prompt"},
                "metadata": {}
            }
        ]
        assert validate_structure(valid_data, "test") is True

        # Invalid data - missing inputs
        invalid_data = [{"outputs": {"improved_prompt": "prompt"}}]
        assert validate_structure(invalid_data, "test") is False

    def test_analyze_duplicates(self):
        """Test analyze_duplicates function."""
        import json
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts/data"))
        from validate_datasets import analyze_duplicates

        data = [
            {"inputs": {"original_idea": "test1", "context": ""}},
            {"inputs": {"original_idea": "test1", "context": ""}},
            {"inputs": {"original_idea": "test2", "context": ""}},
        ]

        duplicates = analyze_duplicates(data, "test")
        assert len(duplicates) == 1, "Should find 1 duplicate input"

        # The key is the JSON representation of the input
        expected_key = json.dumps({"original_idea": "test1", "context": ""}, sort_keys=True)
        assert expected_key in duplicates, "Should identify 'test1' input as duplicate"
        assert len(duplicates[expected_key]) == 2, "Should have 2 occurrences of 'test1'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
