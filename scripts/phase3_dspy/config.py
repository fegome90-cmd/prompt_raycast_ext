"""Configuration for DSPy optimizer."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DSPOptimizerConfig:
    """Configuration for DSPy prompt optimizer."""

    # Dataset paths
    data_dir: str = "datasets/exports/synthetic"

    # DSPy optimization settings
    max_bootstrapped_demos: int = 5
    max_labeled_demos: int = 3

    # Validation settings
    val_size: float = 0.2
