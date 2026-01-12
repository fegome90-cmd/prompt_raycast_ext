# hemdov/infrastructure/persistence/metrics_repository.py
"""
SQLite repository for persisting prompt metrics.

Provides async operations for storing and retrieving PromptMetrics
using aiosqlite with WAL mode for optimal concurrency.
"""

import aiosqlite
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from hemdov.domain.metrics.dimensions import (
    PromptMetrics,
    QualityMetrics,
    PerformanceMetrics,
    ImpactMetrics,
    FrameworkType,
)

logger = logging.getLogger(__name__)


class SQLiteMetricsRepository:
    """
    SQLite repository for prompt metrics.

    Features:
    - Async operations via aiosqlite
    - Connection pooling (single connection for WAL mode)
    - JSON serialization for complex metrics
    - Graceful error handling
    """

    def __init__(self, db_path: str):
        """
        Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file (or ":memory:" for in-memory)
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """
        Initialize database connection and schema.

        Creates connection, configures WAL mode, and creates tables if needed.
        Should be called after construction before any other operations.
        """
        if self._connection is None:
            # Create parent directory if using file-based database
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            try:
                self._connection = await aiosqlite.connect(self.db_path)
                self._connection.row_factory = aiosqlite.Row
                await self._configure_connection(self._connection)
            except (aiosqlite.Error, OSError, PermissionError):
                # Clean up connection if initialization fails
                if self._connection:
                    await self._connection.close()
                    self._connection = None
                raise

    async def _configure_connection(self, conn: aiosqlite.Connection):
        """
        Configure connection with optimal settings.

        Args:
            conn: aiosqlite connection to configure
        """
        # WAL mode for better concurrency
        await conn.execute("PRAGMA journal_mode=WAL")

        # Performance optimizations
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=-64000")  # 64MB
        await conn.execute("PRAGMA temp_store=MEMORY")

        # Create metrics table
        await self._create_schema(conn)

        logger.info(f"SQLite metrics repository initialized: {self.db_path}")

    async def _create_schema(self, conn: aiosqlite.Connection):
        """
        Create database schema for metrics storage.

        Args:
            conn: aiosqlite connection to use for schema creation
        """
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT NOT NULL UNIQUE,
                original_idea TEXT NOT NULL,
                improved_prompt TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                measured_at TEXT NOT NULL,
                framework TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                backend TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create indexes for common queries
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompt_id ON prompt_metrics(prompt_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_measured_at ON prompt_metrics(measured_at DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_framework ON prompt_metrics(framework)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_provider ON prompt_metrics(provider)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_backend ON prompt_metrics(backend)"
        )

        await conn.commit()

    async def save(self, metrics: PromptMetrics) -> int:
        """
        Save metrics to database.

        Args:
            metrics: PromptMetrics instance to save

        Returns:
            Row ID of inserted record

        Raises:
            Exception: If database operation fails
        """
        async with self._lock:
            conn = self._connection
            if conn is None:
                raise RuntimeError("Repository not initialized. Call initialize() first.")

            # Serialize metrics to JSON
            metrics_json = json.dumps(metrics.to_dict())

            cursor = await conn.execute(
                """
                INSERT INTO prompt_metrics (
                    prompt_id, original_idea, improved_prompt, metrics_json,
                    measured_at, framework, provider, model, backend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(prompt_id) DO UPDATE SET
                    original_idea = excluded.original_idea,
                    improved_prompt = excluded.improved_prompt,
                    metrics_json = excluded.metrics_json,
                    measured_at = excluded.measured_at,
                    framework = excluded.framework,
                    provider = excluded.provider,
                    model = excluded.model,
                    backend = excluded.backend
                """,
                (
                    metrics.prompt_id,
                    metrics.original_idea,
                    metrics.improved_prompt,
                    metrics_json,
                    metrics.measured_at.isoformat(),
                    metrics.framework.value,
                    metrics.provider,
                    metrics.model,
                    metrics.backend,
                ),
            )
            await conn.commit()

            logger.debug(f"Saved metrics for prompt_id={metrics.prompt_id} (id={cursor.lastrowid})")
            return cursor.lastrowid

    async def get_by_id(self, prompt_id: str) -> Optional[PromptMetrics]:
        """
        Retrieve metrics by prompt ID.

        Args:
            prompt_id: Unique prompt identifier

        Returns:
            PromptMetrics instance if found, None otherwise
        """
        async with self._lock:
            conn = self._connection
            if conn is None:
                raise RuntimeError("Repository not initialized. Call initialize() first.")

            async with conn.execute(
                "SELECT * FROM prompt_metrics WHERE prompt_id = ?",
                (prompt_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_metrics(row)
                return None

    async def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PromptMetrics]:
        """
        Retrieve all metrics with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of PromptMetrics instances
        """
        async with self._lock:
            conn = self._connection
            if conn is None:
                raise RuntimeError("Repository not initialized. Call initialize() first.")

            async with conn.execute(
                """
                SELECT * FROM prompt_metrics
                ORDER BY measured_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_metrics(row) for row in rows]

    async def close(self):
        """Close database connection."""
        async with self._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("SQLite metrics repository connection closed")

    def _row_to_metrics(self, row) -> PromptMetrics:
        """
        Convert database row to PromptMetrics entity.

        Args:
            row: Database row with metrics data

        Returns:
            PromptMetrics instance

        Raises:
            ValueError: If required keys are missing or JSON is invalid
        """
        # Deserialize JSON metrics
        try:
            metrics_dict = json.loads(row["metrics_json"])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to deserialize metrics JSON for prompt_id={row['prompt_id']}: {e}")
            raise ValueError(f"Invalid metrics JSON: {e}") from e

        # Validate and extract metadata
        metadata = metrics_dict.get("metadata", {})
        if not metadata:
            raise ValueError("Missing 'metadata' in metrics JSON")

        measured_at_str = metadata.get("measured_at")
        if not measured_at_str:
            raise ValueError("Missing 'measured_at' in metadata")

        framework_str = metadata.get("framework")
        if not framework_str:
            raise ValueError("Missing 'framework' in metadata")

        # Parse datetime
        measured_at = datetime.fromisoformat(measured_at_str)

        # Parse framework enum
        framework = FrameworkType(framework_str)

        # Reconstruct quality metrics
        quality_data = metrics_dict["quality"]
        quality = QualityMetrics(
            coherence_score=quality_data["coherence"],
            relevance_score=quality_data["relevance"],
            completeness_score=quality_data["completeness"],
            clarity_score=quality_data["clarity"],
            guardrails_count=quality_data["guardrails_count"],
            has_required_structure=quality_data["has_structure"],
        )

        # Reconstruct performance metrics
        perf_data = metrics_dict["performance"]
        performance = PerformanceMetrics(
            latency_ms=perf_data["latency_ms"],
            total_tokens=perf_data["total_tokens"],
            cost_usd=perf_data["cost_usd"],
            provider=perf_data["provider"],
            model=perf_data["model"],
            backend=perf_data["backend"],
        )

        # Reconstruct impact metrics
        impact_data = metrics_dict["impact"]
        impact = ImpactMetrics(
            copy_count=impact_data["copy_count"],
            regeneration_count=impact_data["regeneration_count"],
            feedback_score=impact_data["feedback_score"],
            reuse_count=impact_data["reuse_count"],
        )

        # Reconstruct full metrics
        return PromptMetrics(
            prompt_id=row["prompt_id"],
            original_idea=row["original_idea"],
            improved_prompt=row["improved_prompt"],
            quality=quality,
            performance=performance,
            impact=impact,
            measured_at=measured_at,
            framework=framework,
            provider=metadata["provider"],
            model=metadata["model"],
            backend=metadata["backend"],
        )
