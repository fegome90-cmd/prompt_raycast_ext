"""DSPy optimizer for prompt optimization."""
from pathlib import Path
import json
from typing import List, Dict


class DatasetLoader:
    """Load Phase 2 datasets for DSPy optimization."""

    def load_datasets(self) -> tuple[List[Dict], List[Dict], List[Dict]]:
        """Load train/val/test datasets from Phase 2.

        Returns:
            Tuple of (train, val, test) lists of examples
        """
        data_dir = Path("datasets/exports/synthetic")

        with open(data_dir / "train.json") as f:
            train = json.load(f)['examples']

        with open(data_dir / "val.json") as f:
            val = json.load(f)['examples']

        with open(data_dir / "test.json") as f:
            test = json.load(f)['examples']

        return train, val, test
