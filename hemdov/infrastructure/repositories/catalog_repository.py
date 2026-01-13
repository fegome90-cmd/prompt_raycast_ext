"""Catalog repository for loading few-shot examples from storage."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CatalogRepositoryInterface(ABC):
    """Interface for catalog data loading."""

    @abstractmethod
    def load_catalog(self) -> List[Dict[str, Any]]:
        """Load catalog data from storage.

        Returns:
            List of example dictionaries

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            RuntimeError: If file cannot be read
            ValueError: If JSON is invalid or format is wrong
        """
        pass


class FileSystemCatalogRepository(CatalogRepositoryInterface):
    """Load catalog from local filesystem.

    Follows existing PromptRepository pattern for consistency.
    """

    def __init__(self, catalog_path: Path):
        """Initialize with catalog file path.

        Args:
            catalog_path: Path to unified-fewshot-pool-v2.json
        """
        self.catalog_path = catalog_path

    def load_catalog(self) -> List[Dict[str, Any]]:
        """Load catalog data from JSON file.

        Returns:
            List of example dictionaries

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            PermissionError: If catalog file cannot be read due to permissions
            ValueError: If JSON is invalid or format is wrong
        """
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"ComponentCatalog not found at {self.catalog_path}. "
                f"CatalogRepository cannot load catalog."
            )

        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from ComponentCatalog at {self.catalog_path}. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode ComponentCatalog at {self.catalog_path}. "
                f"Encoding error at position {e.start}: {e.reason}"
            ) from e

        # Handle wrapper format: {"examples": [...]}
        if isinstance(data, dict) and 'examples' in data:
            return data['examples']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(
                f"Invalid catalog format at {self.catalog_path}. "
                f"Expected dict with 'examples' key or list, got {type(data).__name__}"
            )
