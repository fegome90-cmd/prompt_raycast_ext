"""
DatasetLoader utility for loading test cases from JSONL files.

Provides a reusable way to load and filter test cases from integration
test datasets. Used by parameterized tests and test scripts.

Typical usage:
    from tests.dataset_loader import DatasetLoader

    # Load all test cases
    loader = DatasetLoader()
    all_cases = loader.load_all()

    # Filter by intent
    generate_cases = loader.load_by_intent("generate")

    # Filter by complexity
    simple_cases = loader.load_by_complexity("simple")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from typing import Any


@dataclass
class Assertions:
    """Assertions for a test case."""
    min_length: int
    contains_keywords: List[str]
    not_contains_keywords: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "Assertions":
        """Create Assertions from dictionary."""
        return cls(
            min_length=data["min_length"],
            contains_keywords=data.get("contains_keywords", []),
            not_contains_keywords=data.get("not_contains_keywords", [])
        )


@dataclass
class IntegrationTestCase:
    """A test case from the JSONL dataset."""
    test_id: str
    intent: str
    complexity: str
    idea: str
    context: str
    expected_quality_score: float
    assertions: Assertions

    @classmethod
    def from_dict(cls, data: dict) -> "IntegrationTestCase":
        """Create IntegrationTestCase from dictionary."""
        return cls(
            test_id=data["test_id"],
            intent=data["intent"],
            complexity=data["complexity"],
            idea=data["idea"],
            context=data.get("context", ""),
            expected_quality_score=data["expected_quality_score"],
            assertions=Assertions.from_dict(data["assertions"])
        )


class DatasetLoader:
    """
    Load and filter test cases from JSONL datasets.

    The default dataset path is datasets/integration-test-cases.jsonl
    relative to the project root.
    """

    DEFAULT_DATASET_PATH = "datasets/integration-test-cases.jsonl"

    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize DatasetLoader.

        Args:
            dataset_path: Path to JSONL file (relative to project root).
                         If None, uses DEFAULT_DATASET_PATH.
        """
        if dataset_path is None:
            dataset_path = self.DEFAULT_DATASET_PATH

        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent
        self.dataset_path = project_root / dataset_path
        self._cached_cases: Optional[List[IntegrationTestCase]] = None

    def load_all(self) -> List[IntegrationTestCase]:
        """
        Load all test cases from the dataset.

        Returns:
            List of IntegrationTestCase objects.

        Raises:
            FileNotFoundError: If dataset file does not exist.
            json.JSONDecodeError: If dataset file is not valid JSONL.
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        cases = []
        with open(self.dataset_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                try:
                    data = json.loads(line)
                    case = IntegrationTestCase.from_dict(data)
                    cases.append(case)
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Invalid JSON on line {line_num}: {e.msg}",
                        e.doc,
                        e.pos
                    )
                except KeyError as e:
                    raise ValueError(
                        f"Missing required field {e} on line {line_num}"
                    )

        self._cached_cases = cases
        return cases

    def load_by_intent(self, intent: str) -> List[IntegrationTestCase]:
        """
        Load test cases filtered by intent.

        Args:
            intent: Intent to filter by (e.g., "generate", "debug", "refactor").

        Returns:
            List of IntegrationTestCase objects matching the intent.
        """
        cases = self._get_cases()
        return [case for case in cases if case.intent == intent]

    def load_by_complexity(self, complexity: str) -> List[IntegrationTestCase]:
        """
        Load test cases filtered by complexity.

        Args:
            complexity: Complexity level to filter by
                       (e.g., "simple", "moderate", "complex").

        Returns:
            List of IntegrationTestCase objects matching the complexity.
        """
        cases = self._get_cases()
        return [case for case in cases if case.complexity == complexity]

    def _get_cases(self) -> List[IntegrationTestCase]:
        """
        Get cached cases or load them if not cached.

        Returns:
            List of IntegrationTestCase objects.
        """
        if self._cached_cases is None:
            return self.load_all()
        return self._cached_cases

    def get_unique_intents(self) -> List[str]:
        """
        Get list of unique intent values in the dataset.

        Returns:
            Sorted list of unique intent strings.
        """
        cases = self._get_cases()
        return sorted(set(case.intent for case in cases))

    def get_unique_complexities(self) -> List[str]:
        """
        Get list of unique complexity values in the dataset.

        Returns:
            Sorted list of unique complexity strings.
        """
        cases = self._get_cases()
        return sorted(set(case.complexity for case in cases))
