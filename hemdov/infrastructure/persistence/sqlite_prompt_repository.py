# hemdov/infrastructure/persistence/sqlite_prompt_repository.py
import aiosqlite
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.persistence.migrations import run_migrations

logger = logging.getLogger(__name__)


class SQLitePromptRepository(PromptRepository):
    """
    SQLite implementation of PromptRepository.

    Features:
    - Async operations via aiosqlite
    - Connection pooling (single connection for WAL mode)
    - Automatic schema migrations
    - Graceful error handling
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_path = Path(settings.SQLITE_DB_PATH)
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create connection with lazy initialization."""
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = await aiosqlite.connect(self.db_path)
            # Set row_factory to access columns by name
            self._connection.row_factory = aiosqlite.Row
            await self._configure_connection(self._connection)
        return self._connection

    async def _configure_connection(self, conn: aiosqlite.Connection):
        """Configure connection with optimal settings."""
        # WAL mode for better concurrency
        if self.settings.SQLITE_WAL_MODE:
            await conn.execute("PRAGMA journal_mode=WAL")

        # Performance optimizations
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=-64000")  # 64MB
        await conn.execute("PRAGMA temp_store=MEMORY")

        # Run migrations
        await run_migrations(conn)

        logger.info(f"SQLite repository initialized: {self.db_path}")

    async def save(self, history: PromptHistory) -> int:
        """Save a prompt history record."""
        async with self._lock:
            conn = await self._get_connection()

            cursor = await conn.execute(
                """
                INSERT INTO prompt_history (
                    created_at, original_idea, context, improved_prompt,
                    role, directive, framework, guardrails, reasoning,
                    confidence, backend, model, provider, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history.created_at,
                    history.original_idea,
                    history.context,
                    history.improved_prompt,
                    history.role,
                    history.directive,
                    history.framework,
                    json.dumps(history.guardrails),
                    history.reasoning,
                    history.confidence,
                    history.backend,
                    history.model,
                    history.provider,
                    history.latency_ms,
                ),
            )
            await conn.commit()

            logger.debug(f"Saved prompt history (id={cursor.lastrowid})")
            return cursor.lastrowid

    async def find_by_id(self, history_id: int) -> Optional[PromptHistory]:
        """Find a prompt history by ID."""
        async with self._lock:
            conn = await self._get_connection()

            async with conn.execute(
                "SELECT * FROM prompt_history WHERE id = ?",
                (history_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_entity(row)
                return None

    async def find_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        provider: Optional[str] = None,
        backend: Optional[str] = None,
    ) -> List[PromptHistory]:
        """Find recent prompts with optional filters."""
        async with self._lock:
            conn = await self._get_connection()

            # Build query
            query = "SELECT * FROM prompt_history WHERE 1=1"
            params = []

            if provider:
                query += " AND provider = ?"
                params.append(provider)

            if backend:
                query += " AND backend = ?"
                params.append(backend)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_entity(row) for row in rows]

    async def search(self, query: str, limit: int = 20) -> List[PromptHistory]:
        """Search prompts by text content."""
        async with self._lock:
            conn = await self._get_connection()

            pattern = f"%{query}%"
            async with conn.execute(
                """
                SELECT * FROM prompt_history
                WHERE original_idea LIKE ? OR improved_prompt LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_entity(row) for row in rows]

    async def delete_old_records(self, days: int) -> int:
        """Delete records older than specified days."""
        async with self._lock:
            conn = await self._get_connection()

            cursor = await conn.execute(
                "DELETE FROM prompt_history WHERE created_at < datetime('now', '-' || ? || ' days')",
                (days,),
            )
            await conn.commit()

            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"Deleted {deleted} old prompt history records")

            return deleted

    async def get_statistics(self) -> dict:
        """Get usage statistics."""
        async with self._lock:
            conn = await self._get_connection()

            async with conn.execute(
                "SELECT COUNT(*) as total FROM prompt_history"
            ) as cursor:
                total = (await cursor.fetchone())["total"]

            async with conn.execute(
                "SELECT AVG(confidence) as avg_conf, AVG(latency_ms) as avg_lat FROM prompt_history"
            ) as cursor:
                row = await cursor.fetchone()
                avg_confidence = row["avg_conf"] or 0
                avg_latency = row["avg_lat"] or 0

            async with conn.execute(
                "SELECT backend, COUNT(*) as count FROM prompt_history GROUP BY backend"
            ) as cursor:
                backend_dist = {row["backend"]: row["count"] for row in await cursor.fetchall()}

            return {
                "total_count": total,
                "average_confidence": round(avg_confidence, 3),
                "average_latency_ms": round(avg_latency, 1),
                "backend_distribution": backend_dist,
            }

    async def close(self):
        """Close database connection."""
        async with self._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("SQLite repository connection closed")

    def _row_to_entity(self, row) -> PromptHistory:
        """Convert database row to PromptHistory entity."""
        # Safely parse JSON, fallback to safe default on corruption
        try:
            guardrails = json.loads(row["guardrails"])
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid JSON in guardrails for record {row['id']}, using fallback value")
            # Use fallback that won't trigger validation error but indicates data issue
            guardrails = ["[data corrupted - unavailable]"]

        return PromptHistory(
            original_idea=row["original_idea"],
            context=row["context"] or "",
            improved_prompt=row["improved_prompt"],
            role=row["role"],
            directive=row["directive"],
            framework=row["framework"],
            guardrails=guardrails,
            reasoning=row["reasoning"],
            confidence=row["confidence"],
            backend=row["backend"],
            model=row["model"],
            provider=row["provider"],
            latency_ms=row["latency_ms"],
            created_at=row["created_at"],
        )
