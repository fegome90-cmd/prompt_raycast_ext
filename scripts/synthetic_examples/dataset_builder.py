from typing import List, Dict, Optional
import json
from pathlib import Path
from scripts.legacy_curation.models import Domain


DATASET_SCHEMA = {
    "examples": [
        {
            "question": str,
            "metadata": {
                "task_type": str,
                "domain": str,
                "confidence": float,
                "source_component_id": str,
                "variation": str,
            },
        }
    ]
}


TASK_TYPES = [
    "role_definition",
    "directive_task",
    "framework_application",
    "guardrail_extraction",
    "combined_task",
]


class DSPyDatasetBuilder:
    """Builds DSPy-compatible datasets from synthetic examples."""

    def __init__(self, dataset_name: str = "synthetic_examples_v1"):
        """Initialize dataset builder.

        Args:
            dataset_name: Name of the dataset being built
        """
        self.dataset_name = dataset_name
        self.examples: List[Dict] = []

    def add_examples(self, examples: List[Dict], task_type: str = "combined_task"):
        """Add examples to dataset.

        Args:
            examples: List of example dictionaries
            task_type: Type of task for these examples

        Raises:
            KeyError: If example missing required fields
            ValueError: If task_type or other metadata is invalid
        """
        for example in examples:
            if "question" not in example:
                raise KeyError("Example missing 'question' field")
            if "metadata" not in example:
                raise KeyError("Example missing 'metadata' field")

            metadata = example["metadata"]

            required_metadata_fields = [
                "task_type",
                "domain",
                "confidence",
                "source_component_id",
                "variation",
            ]
            for field in required_metadata_fields:
                if field not in metadata:
                    raise KeyError(f"Example metadata missing '{field}' field")

            if metadata["task_type"] not in TASK_TYPES:
                raise ValueError(
                    f"Invalid task_type '{metadata['task_type']}'. "
                    f"Must be one of: {TASK_TYPES}"
                )

            if metadata["confidence"] < 0.0 or metadata["confidence"] > 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")

            validated_example = {
                "question": example["question"],
                "metadata": {
                    "task_type": metadata["task_type"],
                    "domain": metadata["domain"],
                    "confidence": float(metadata["confidence"]),
                    "source_component_id": metadata["source_component_id"],
                    "variation": metadata["variation"],
                },
            }

            self.examples.append(validated_example)

    def add_domain_specific_datasets(
        self,
        components_by_domain: Dict[Domain, List[Dict]],
        examples_per_component: int = 5,
    ):
        """Add domain-specific examples to dataset.

        Args:
            components_by_domain: Dictionary mapping Domain to list of component dicts
            examples_per_component: Number of examples to generate per component
        """
        for domain, components in components_by_domain.items():
            for component in components:
                for i in range(examples_per_component):
                    example = {
                        "question": f"{component.get('role', 'assistant')}. {component.get('directive', 'help')}.",
                        "metadata": {
                            "task_type": "combined_task",
                            "domain": domain.value,
                            "confidence": float(component.get("confidence", 0.8)),
                            "source_component_id": f"component_{len(self.examples)}_{i}",
                            "variation": "base",
                        },
                    }
                    self.examples.append(example)

    def build_dataset(self, output_path: str, split: str = "train") -> str:
        """Build and save DSPy-compatible dataset.

        Args:
            output_path: Path where to save the dataset JSON file
            split: Dataset split (e.g., 'train', 'validation', 'test')

        Returns:
            Path to the saved dataset file
        """
        dataset = {
            "dataset_name": self.dataset_name,
            "split": split,
            "total_examples": len(self.examples),
            "examples": self.examples,
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)

        return str(output_file)

    def get_statistics(self) -> Dict:
        """Calculate dataset statistics.

        Returns:
            Dictionary containing statistics about the dataset
        """
        total_examples = len(self.examples)

        by_task_type: Dict[str, int] = {}
        by_domain: Dict[str, int] = {}
        total_confidence = 0.0

        for example in self.examples:
            task_type = example["metadata"]["task_type"]
            domain = example["metadata"]["domain"]
            confidence = example["metadata"]["confidence"]

            by_task_type[task_type] = by_task_type.get(task_type, 0) + 1
            by_domain[domain] = by_domain.get(domain, 0) + 1
            total_confidence += confidence

        avg_confidence = (
            total_confidence / total_examples if total_examples > 0 else 0.0
        )

        return {
            "total_examples": total_examples,
            "by_task_type": by_task_type,
            "by_domain": by_domain,
            "avg_confidence": round(avg_confidence, 4),
        }
