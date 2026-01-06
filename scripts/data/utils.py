#!/usr/bin/env python3
"""
Shared utility functions for data processing scripts.

This module provides common functionality for loading and manipulating
DSPy Few-Shot datasets across multiple scripts.
"""
import json
from typing import Any, Dict, List


def load_dataset(path: str) -> List[Dict[str, Any]]:
    """
    Load JSON dataset from file.

    Args:
        path: Path to JSON file

    Returns:
        List of examples

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_dataset(data: List[Dict[str, Any]], path: str) -> None:
    """
    Save dataset to JSON file.

    Args:
        data: Dataset to save
        path: Output file path
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
