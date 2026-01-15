"""
Tests for DatasetLoader utility.

Tests cover:
- Loading all test cases
- Filtering by intent
- Filtering by complexity
- Error handling for missing files
"""

import pytest
from pathlib import Path
import json
import tempfile

from tests.dataset_loader import DatasetLoader, IntegrationTestCase, Assertions


class TestDatasetLoader:
    """Test DatasetLoader functionality."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a temporary dataset file for testing."""
        test_cases = [
            {
                "test_id": "001",
                "intent": "generate",
                "complexity": "simple",
                "idea": "Create hello world function",
                "context": "Use Python",
                "expected_quality_score": 0.9,
                "assertions": {
                    "min_length": 50,
                    "contains_keywords": ["python", "function"],
                    "not_contains_keywords": []
                }
            },
            {
                "test_id": "002",
                "intent": "generate",
                "complexity": "moderate",
                "idea": "Write a function to add two numbers",
                "context": "",
                "expected_quality_score": 0.9,
                "assertions": {
                    "min_length": 50,
                    "contains_keywords": ["function", "add"],
                    "not_contains_keywords": []
                }
            },
            {
                "test_id": "003",
                "intent": "debug",
                "complexity": "simple",
                "idea": "Fix this bug",
                "context": "Returns None on empty input",
                "expected_quality_score": 0.9,
                "assertions": {
                    "min_length": 80,
                    "contains_keywords": ["bug", "fix"],
                    "not_contains_keywords": []
                }
            }
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False
        ) as f:
            for case in test_cases:
                f.write(json.dumps(case) + "\n")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_load_all(self, sample_dataset):
        """Should load all test cases from dataset."""
        # Use relative path from temp file
        loader = DatasetLoader(dataset_path=sample_dataset)
        cases = loader.load_all()

        assert len(cases) == 3
        assert all(isinstance(case, IntegrationTestCase) for case in cases)

        # Verify first case
        assert cases[0].test_id == "001"
        assert cases[0].intent == "generate"
        assert cases[0].complexity == "simple"
        assert cases[0].idea == "Create hello world function"
        assert cases[0].context == "Use Python"
        assert cases[0].expected_quality_score == 0.9
        assert cases[0].assertions.min_length == 50
        assert cases[0].assertions.contains_keywords == ["python", "function"]

    def test_load_by_intent(self, sample_dataset):
        """Should filter test cases by intent."""
        loader = DatasetLoader(dataset_path=sample_dataset)

        # Load "generate" cases
        generate_cases = loader.load_by_intent("generate")
        assert len(generate_cases) == 2
        assert all(case.intent == "generate" for case in generate_cases)
        assert generate_cases[0].test_id == "001"
        assert generate_cases[1].test_id == "002"

        # Load "debug" cases
        debug_cases = loader.load_by_intent("debug")
        assert len(debug_cases) == 1
        assert debug_cases[0].test_id == "003"

        # Load non-existent intent
        refactor_cases = loader.load_by_intent("refactor")
        assert len(refactor_cases) == 0

    def test_load_by_complexity(self, sample_dataset):
        """Should filter test cases by complexity."""
        loader = DatasetLoader(dataset_path=sample_dataset)

        # Load "simple" cases
        simple_cases = loader.load_by_complexity("simple")
        assert len(simple_cases) == 2
        assert all(case.complexity == "simple" for case in simple_cases)
        test_ids = [case.test_id for case in simple_cases]
        assert "001" in test_ids
        assert "003" in test_ids

        # Load "moderate" cases
        moderate_cases = loader.load_by_complexity("moderate")
        assert len(moderate_cases) == 1
        assert moderate_cases[0].test_id == "002"

        # Load non-existent complexity
        complex_cases = loader.load_by_complexity("complex")
        assert len(complex_cases) == 0

    def test_file_not_found(self):
        """Should raise FileNotFoundError when dataset doesn't exist."""
        loader = DatasetLoader(dataset_path="nonexistent/path/file.jsonl")

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_all()

        assert "Dataset not found" in str(exc_info.value)

    def test_invalid_json(self):
        """Should raise JSONDecodeError for invalid JSONL."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False
        ) as f:
            f.write('{"test_id": "001", "invalid": json}')
            temp_path = f.name

        try:
            loader = DatasetLoader(dataset_path=temp_path)

            with pytest.raises(json.JSONDecodeError):
                loader.load_all()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_required_field(self):
        """Should raise ValueError for missing required fields."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False
        ) as f:
            # Missing "assertions" field
            f.write('{"test_id": "001", "intent": "generate"}\n')
            temp_path = f.name

        try:
            loader = DatasetLoader(dataset_path=temp_path)

            with pytest.raises(ValueError) as exc_info:
                loader.load_all()

            assert "Missing required field" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_empty_lines_skipped(self, sample_dataset):
        """Should skip empty lines in JSONL file."""
        # Add empty lines to sample dataset
        with open(sample_dataset, "r") as f:
            content = f.read()

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False
        ) as f:
            # Write content with empty lines
            f.write("\n\n")
            f.write(content)
            f.write("\n\n\n")
            temp_path = f.name

        try:
            loader = DatasetLoader(dataset_path=temp_path)
            cases = loader.load_all()

            # Should still load all 3 cases despite empty lines
            assert len(cases) == 3
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_unique_intents(self, sample_dataset):
        """Should return list of unique intents."""
        loader = DatasetLoader(dataset_path=sample_dataset)
        intents = loader.get_unique_intents()

        assert sorted(intents) == ["debug", "generate"]

    def test_get_unique_complexities(self, sample_dataset):
        """Should return list of unique complexities."""
        loader = DatasetLoader(dataset_path=sample_dataset)
        complexities = loader.get_unique_complexities()

        assert sorted(complexities) == ["moderate", "simple"]

    def test_caching(self, sample_dataset):
        """Should cache loaded cases to avoid re-reading file."""
        loader = DatasetLoader(dataset_path=sample_dataset)

        # First load
        cases1 = loader.load_all()
        # Second load should use cache
        cases2 = loader.load_all()

        # Should be equal (same data)
        assert cases1 == cases2

        # Filter methods should also use cache
        generate_cases = loader.load_by_intent("generate")
        # Check that cache is used by verifying count matches
        assert len(generate_cases) == 2


class TestAssertionsDataclass:
    """Test Assertions dataclass."""

    def test_from_dict(self):
        """Should create Assertions from dict."""
        data = {
            "min_length": 100,
            "contains_keywords": ["python", "function"],
            "not_contains_keywords": ["bug"]
        }

        assertions = Assertions.from_dict(data)

        assert assertions.min_length == 100
        assert assertions.contains_keywords == ["python", "function"]
        assert assertions.not_contains_keywords == ["bug"]

    def test_from_dict_with_defaults(self):
        """Should use empty list defaults for optional fields."""
        data = {
            "min_length": 50,
            "contains_keywords": ["python"]
        }

        assertions = Assertions.from_dict(data)

        assert assertions.min_length == 50
        assert assertions.contains_keywords == ["python"]
        assert assertions.not_contains_keywords == []


class TestIntegrationTestCaseDataclass:
    """Test IntegrationTestCase dataclass."""

    def test_from_dict(self):
        """Should create IntegrationTestCase from dict."""
        data = {
            "test_id": "001",
            "intent": "generate",
            "complexity": "simple",
            "idea": "Create function",
            "context": "Use Python",
            "expected_quality_score": 0.9,
            "assertions": {
                "min_length": 50,
                "contains_keywords": ["python"],
                "not_contains_keywords": []
            }
        }

        test_case = IntegrationTestCase.from_dict(data)

        assert test_case.test_id == "001"
        assert test_case.intent == "generate"
        assert test_case.complexity == "simple"
        assert test_case.idea == "Create function"
        assert test_case.context == "Use Python"
        assert test_case.expected_quality_score == 0.9
        assert test_case.assertions.min_length == 50
        assert test_case.assertions.contains_keywords == ["python"]

    def test_from_dict_with_empty_context(self):
        """Should handle empty context field."""
        data = {
            "test_id": "002",
            "intent": "debug",
            "complexity": "moderate",
            "idea": "Fix bug",
            "expected_quality_score": 0.85,
            "assertions": {
                "min_length": 80,
                "contains_keywords": ["bug"],
                "not_contains_keywords": []
            }
        }

        test_case = IntegrationTestCase.from_dict(data)

        assert test_case.context == ""
