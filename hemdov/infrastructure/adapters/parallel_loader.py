"""
Parallel File Loader - Infrastructure Layer.
Implementation of the ContextLoader port using ThreadPoolExecutor.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hemdov.domain.ports.context_loader import ContextLoader
from hemdov.domain.ports.priority_classifier import PriorityClassifier
from hemdov.domain.services.keyword_classifier import KeywordBasedClassifier
from shared.context_entities import ContextItem

logger = logging.getLogger(__name__)


class ParallelFileLoader(ContextLoader):
    """
    Infrastructure implementation of ContextLoader.
    Uses ThreadPoolExecutor to parallelize I/O operations.
    """

    def __init__(self, max_workers: int = 5, classifier: PriorityClassifier | None = None):
        if max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {max_workers}")
        if max_workers > 100:
            raise ValueError(f"max_workers too high ({max_workers}), max is 100")

        self.max_workers = max_workers
        self.classifier = classifier or KeywordBasedClassifier()

    def _read_file(self, file_path: str) -> ContextItem:
        """
        Read a single file and return a ContextItem.

        Args:
            file_path: Path to the file to read

        Returns:
            ContextItem with file content or error message
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            priority, category = self.classifier.classify(Path(file_path).name)

            return ContextItem(
                source=file_path, content=content, priority=priority, category=category
            )
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return ContextItem(
                source=file_path,
                content=f"ERROR: File not found - {file_path}",
                priority=1,
                category="error",
            )
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            return ContextItem(
                source=file_path,
                content=f"ERROR: Permission denied - {file_path}",
                priority=1,
                category="error",
            )
        except UnicodeDecodeError:
            logger.error(f"Invalid UTF-8 encoding: {file_path}")
            return ContextItem(
                source=file_path,
                content=f"ERROR: Invalid file encoding - {file_path}",
                priority=1,
                category="error",
            )

    def load_all(self, file_paths: list[str]) -> list[ContextItem]:
        """
        Loads multiple files in parallel using a thread pool.
        """
        if not file_paths:
            return []

        logger.debug(
            f"Starting parallel load of {len(file_paths)} files with {self.max_workers} workers"
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # map returns results in the same order as file_paths
            items = list(executor.map(self._read_file, file_paths))

        valid_count = sum(1 for item in items if item.category != "error")
        error_count = len(items) - valid_count

        logger.debug(f"Completed loading: {valid_count} valid, {error_count} errors")

        return items
