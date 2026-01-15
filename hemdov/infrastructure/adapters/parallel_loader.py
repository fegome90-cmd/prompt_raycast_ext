"""
Parallel File Loader - Infrastructure Layer.
Implementation of the ContextLoader port using ThreadPoolExecutor.
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List
from shared.context_entities import ContextItem
from hemdov.domain.ports.context_loader import ContextLoader

logger = logging.getLogger(__name__)


class ParallelFileLoader(ContextLoader):
    """
    Infrastructure implementation of ContextLoader.
    Uses ThreadPoolExecutor to parallelize I/O operations.
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def _read_file(self, file_path: str) -> ContextItem:
        """Helper to read a single file and return a ContextItem."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple priority heuristic based on filename or content
            priority = 1
            category = "general"

            basename = os.path.basename(file_path).lower()
            if "instructions" in basename or "rule" in basename:
                priority = 5
                category = "instruction"
            elif "agent" in basename:
                priority = 4
                category = "agent"

            return ContextItem(
                source=file_path, content=content, priority=priority, category=category
            )
        except Exception as e:
            logger.error(f"Error reading context file {file_path}: {e}")
            return ContextItem(
                source=file_path,
                content=f"ERROR: Could not read file. {e}",
                priority=1,
                category="error",
            )

    def load_all(self, file_paths: List[str]) -> List[ContextItem]:
        """
        Loads multiple files in parallel using a thread pool.
        """
        if not file_paths:
            return []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # map returns results in the same order as file_paths
            items = list(executor.map(self._read_file, file_paths))

        return items
