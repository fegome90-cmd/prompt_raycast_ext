"""Synthetic examples package."""

from scripts.synthetic_examples.infrastructure import load_component_catalog
from scripts.synthetic_examples.generators.example_generator import ExampleGenerator
from scripts.synthetic_examples.dataset_builder import DSPyDatasetBuilder
from scripts.synthetic_examples.validator import ExampleValidator

__all__ = [
    "load_component_catalog",
    "ExampleGenerator",
    "DSPyDatasetBuilder",
    "ExampleValidator",
]
