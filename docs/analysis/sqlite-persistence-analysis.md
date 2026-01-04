# SQLite Persistence Design Analysis for DSPy Prompt Improver

**Date:** 2026-01-04
**Project:** /Users/felipe_gonzalez/Developer/raycast_ext
**Architecture:** HemDov (Hexagonal) with Domain/Infrastructure/Interfaces layers

---

## Executive Summary

This analysis evaluates a proposed SQLite persistence layer for the DSPy Prompt Improver project. The current implementation has **NO persistence** - every prompt improvement is lost after execution. The proposed design introduces domain entities, repository interfaces, and SQLite implementation following Hexagonal Architecture principles.

**Critical Finding:** The proposed design needs significant improvements to properly integrate with the existing HemDov architecture, handle errors gracefully, and support production requirements like performance monitoring and graceful degradation.

---

## 1. Architecture Compliance Analysis

### Current HemDov Structure

```
hemdov/
├── domain/
│   ├── __init__.py
│   └── dspy_modules/
│       ├── __init__.py
│       └── prompt_improver.py
├── infrastructure/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── litellm_dspy_adapter.py
│   │   └── litellm_dspy_adapter_prompt.py
│   └── config/
│       └── __init__.py (Settings with pydantic-settings)
└── interfaces.py (Container for dependency injection)
```

### Proposed Components

#### ✅ **Component 1: Domain Entity** (PromptHistory)
**Location:** `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/prompt_history.py`

**Design Compliance:** PARTIAL ✅

**Strengths:**
- Pure dataclass aligns with domain layer principles
- No infrastructure dependencies (SQLAlchemy, sqlite3, etc.)
- Contains business logic (latency calculation, quality score)

**Weaknesses:**
- Missing from proposed location: Should be in `hemdov/domain/entities/` (directory doesn't exist yet)
- Should use `frozen=True` for immutability (domain entities should be value objects)
- Missing validation for business invariants (e.g., confidence must be 0-1, latency_ms >= 0)

**Recommended Implementation:**
```python
# hemdov/domain/entities/prompt_history.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class BackendType(str, Enum):
    ZERO_SHOT = "zero-shot"
    FEW_SHOT = "few-shot"

@dataclass(frozen=True)  # Immutable value object
class PromptHistory:
    """Domain entity representing a prompt improvement event."""

    # Core identifiers
    id: Optional[int]  # None for new entities, set after persistence
    timestamp: datetime

    # Input
    original_idea: str
    context: str

    # Output
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]

    # Metadata
    backend: BackendType
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    latency_ms: Optional[int] = None
    model_version: Optional[str] = None

    def __post_init__(self):
        """Validate business invariants."""
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0-1, got {self.confidence}")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError(f"Latency must be >= 0, got {self.latency_ms}")
        if not self.original_idea.strip():
            raise ValueError("original_idea cannot be empty")

    @property
    def quality_score(self) -> float:
        """Calculate composite quality score."""
        conf_score = self.confidence or 0.5
        latency_penalty = min(self.latency_ms or 0 / 10000, 0.3)  # Max 30% penalty
        return max(0.0, min(1.0, conf_score - latency_penalty))
```

---

#### ✅ **Component 2: Repository Interface** (PromptRepository)
**Location:** `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/repositories/prompt_repository.py`

**Design Compliance:** GOOD ✅

**Strengths:**
- Abstract base class follows Interface Segregation Principle
- Located in domain layer (depends on domain entities only)
- No infrastructure leakage

**Weaknesses:**
- Missing repository directory structure
- No async support (FastAPI is async-first)
- Missing pagination for large datasets
- No query methods for analytics (e.g., `find_by_backend`, `find_by_quality_threshold`)

**Recommended Implementation:**
```python
# hemdov/domain/repositories/prompt_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from hemdov.domain.entities.prompt_history import PromptHistory, BackendType

class PromptRepository(ABC):
    """Repository interface for prompt history persistence."""

    @abstractmethod
    async def save(self, history: PromptHistory) -> PromptHistory:
        """
        Save a prompt history record.

        Args:
            history: PromptHistory entity to save

        Returns:
            PromptHistory with assigned ID

        Raises:
            RepositoryError: If save fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, history_id: int) -> Optional[PromptHistory]:
        """Find a prompt history by ID."""
        pass

    @abstractmethod
    async def find_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        backend: Optional[BackendType] = None
    ) -> List[PromptHistory]:
        """Find recent prompt histories with optional filtering."""
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[PromptHistory]:
        """Find histories within a date range."""
        pass

    @abstractmethod
    async def get_statistics(self) -> dict:
        """Get usage statistics (total count, avg confidence, avg latency)."""
        pass

    @abstractmethod
    async def delete_old(self, days: int) -> int:
        """Delete histories older than specified days. Returns count deleted."""
        pass


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class RepositoryConnectionError(RepositoryError):
    """Raised when repository cannot connect to storage."""
    pass


class RepositoryConstraintError(RepositoryError):
    """Raised when a constraint violation occurs."""
    pass
```

---

#### ⚠️ **Component 3: SQLite Implementation** (SQLitePromptRepository)
**Location:** `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/sqlite_prompt_repository.py`

**Design Compliance:** NEEDS IMPROVEMENT ⚠️

**Critical Issues:**

1. **Missing Dependency Injection via Container**
   - Current HemDov Container in `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/interfaces.py` only registers Settings
   - Repository should be registered in container and injected into API layer

2. **No Async Support**
   - Uses synchronous `sqlite3` instead of `aiosqlite`
   - Blocks FastAPI event loop

3. **Poor Error Handling**
   - Bare `except Exception` catches everything
   - No distinction between connection errors vs constraint errors
   - No logging for debugging

4. **No Connection Pooling**
   - Creates new connection per operation
   - SQLite has limits on concurrent writes

5. **Missing Schema Migrations**
   - No versioning of schema
   - No upgrade path if schema changes

6. **No Configuration**
   - Hardcoded database path
   - Not in Settings

**Recommended Implementation:**

```python
# hemdov/infrastructure/persistence/sqlite_prompt_repository.py
import logging
import aiosqlite
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from hemdov.domain.entities.prompt_history import PromptHistory, BackendType
from hemdov.domain.repositories.prompt_repository import (
    PromptRepository,
    RepositoryError,
    RepositoryConnectionError,
    RepositoryConstraintError
)
from hemdov.infrastructure.config import Settings

logger = logging.getLogger(__name__)

class SQLitePromptRepository(PromptRepository):
    """SQLite implementation of PromptRepository."""

    SCHEMA_VERSION = 1

    def __init__(self, settings: Settings):
        """Initialize repository with settings."""
        self.db_path = Path(settings.SQLITE_DB_PATH)
        self._connection_pool_size = settings.SQLITE_POOL_SIZE
        logger.info(f"SQLitePromptRepository initialized with db={self.db_path}")

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection with proper configuration."""
        try:
            conn = await aiosqlite.connect(
                self.db_path,
                check_same_thread=False  # Allow cross-thread access
            )
            # Enable WAL mode for better concurrency
            await conn.execute("PRAGMA journal_mode=WAL")
            # Optimize for performance
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            await conn.execute("PRAGMA temp_store=MEMORY")
            return conn
        except aiosqlite.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise RepositoryConnectionError(f"Cannot connect to database: {e}")

    async def _initialize_schema(self, conn: aiosqlite.Connection):
        """Initialize database schema if not exists."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_idea TEXT NOT NULL,
                context TEXT,
                improved_prompt TEXT NOT NULL,
                role TEXT NOT NULL,
                directive TEXT NOT NULL,
                framework TEXT NOT NULL,
                guardrails TEXT NOT NULL,
                backend TEXT NOT NULL,
                confidence REAL,
                reasoning TEXT,
                latency_ms INTEGER,
                model_version TEXT,
                CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
                CHECK(latency_ms IS NULL OR latency_ms >= 0)
            )
        """)

        # Create indexes for common queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON prompt_history(timestamp DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_backend
            ON prompt_history(backend)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality
            ON prompt_history(confidence, latency_ms)
        """)

        # Create metadata table for schema versioning
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Set schema version
        await conn.execute("""
            INSERT OR REPLACE INTO schema_metadata (key, value)
            VALUES ('schema_version', ?)
        """, (self.SCHEMA_VERSION,))

        await conn.commit()
        logger.info("Database schema initialized")

    async def save(self, history: PromptHistory) -> PromptHistory:
        """Save a prompt history record."""
        conn = None
        try:
            conn = await self._get_connection()
            await self._initialize_schema(conn)

            cursor = await conn.execute(
                """
                INSERT INTO prompt_history (
                    timestamp, original_idea, context, improved_prompt,
                    role, directive, framework, guardrails, backend,
                    confidence, reasoning, latency_ms, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history.timestamp or datetime.utcnow(),
                    history.original_idea,
                    history.context,
                    history.improved_prompt,
                    history.role,
                    history.directive,
                    history.framework,
                    "\n".join(history.guardrails),
                    history.backend.value,
                    history.confidence,
                    history.reasoning,
                    history.latency_ms,
                    history.model_version
                )
            )

            await conn.commit()
            history_id = cursor.lastrowid

            # Return new instance with ID
            from dataclasses import replace
            return replace(history, id=history_id)

        except aiosqlite.IntegrityError as e:
            logger.error(f"Integrity error saving prompt history: {e}")
            raise RepositoryConstraintError(f"Constraint violation: {e}")
        except aiosqlite.Error as e:
            logger.error(f"Database error saving prompt history: {e}")
            raise RepositoryError(f"Failed to save prompt history: {e}")
        finally:
            if conn:
                await conn.close()

    async def find_by_id(self, history_id: int) -> Optional[PromptHistory]:
        """Find a prompt history by ID."""
        conn = None
        try:
            conn = await self._get_connection()
            cursor = await conn.execute(
                "SELECT * FROM prompt_history WHERE id = ?",
                (history_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_entity(row)

        except aiosqlite.Error as e:
            logger.error(f"Database error finding by id {history_id}: {e}")
            raise RepositoryError(f"Failed to find prompt history: {e}")
        finally:
            if conn:
                await conn.close()

    async def find_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        backend: Optional[BackendType] = None
    ) -> List[PromptHistory]:
        """Find recent prompt histories with optional filtering."""
        conn = None
        try:
            conn = await self._get_connection()

            query = "SELECT * FROM prompt_history"
            params = []

            if backend:
                query += " WHERE backend = ?"
                params.append(backend.value)

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_entity(row) for row in rows]

        except aiosqlite.Error as e:
            logger.error(f"Database error finding recent: {e}")
            raise RepositoryError(f"Failed to find recent histories: {e}")
        finally:
            if conn:
                await conn.close()

    async def find_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[PromptHistory]:
        """Find histories within a date range."""
        conn = None
        try:
            conn = await self._get_connection()
            cursor = await conn.execute(
                """
                SELECT * FROM prompt_history
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                """,
                (start, end)
            )
            rows = await cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]

        except aiosqlite.Error as e:
            logger.error(f"Database error finding by date range: {e}")
            raise RepositoryError(f"Failed to find histories by date: {e}")
        finally:
            if conn:
                await conn.close()

    async def get_statistics(self) -> dict:
        """Get usage statistics."""
        conn = None
        try:
            conn = await self._get_connection()

            # Get total count
            count_cursor = await conn.execute(
                "SELECT COUNT(*) FROM prompt_history"
            )
            total_count = (await count_cursor.fetchone())[0]

            # Get average confidence
            conf_cursor = await conn.execute(
                "SELECT AVG(confidence) FROM prompt_history WHERE confidence IS NOT NULL"
            )
            avg_confidence = (await conf_cursor.fetchone())[0] or 0.0

            # Get average latency
            lat_cursor = await conn.execute(
                "SELECT AVG(latency_ms) FROM prompt_history WHERE latency_ms IS NOT NULL"
            )
            avg_latency = (await lat_cursor.fetchone())[0] or 0.0

            # Get backend distribution
            backend_cursor = await conn.execute(
                "SELECT backend, COUNT(*) as count FROM prompt_history GROUP BY backend"
            )
            backend_counts = {row[0]: row[1] for row in await backend_cursor.fetchall()}

            return {
                "total_count": total_count,
                "average_confidence": round(avg_confidence, 3),
                "average_latency_ms": round(avg_latency, 2),
                "backend_distribution": backend_counts
            }

        except aiosqlite.Error as e:
            logger.error(f"Database error getting statistics: {e}")
            raise RepositoryError(f"Failed to get statistics: {e}")
        finally:
            if conn:
                await conn.close()

    async def delete_old(self, days: int) -> int:
        """Delete histories older than specified days."""
        conn = None
        try:
            conn = await self._get_connection()
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            cursor = await conn.execute(
                "DELETE FROM prompt_history WHERE timestamp < ?",
                (cutoff_date,)
            )
            await conn.commit()

            deleted_count = cursor.rowcount
            logger.info(f"Deleted {deleted_count} histories older than {days} days")
            return deleted_count

        except aiosqlite.Error as e:
            logger.error(f"Database error deleting old histories: {e}")
            raise RepositoryError(f"Failed to delete old histories: {e}")
        finally:
            if conn:
                await conn.close()

    def _row_to_entity(self, row) -> PromptHistory:
        """Convert database row to PromptHistory entity."""
        return PromptHistory(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            original_idea=row[2],
            context=row[3],
            improved_prompt=row[4],
            role=row[5],
            directive=row[6],
            framework=row[7],
            guardrails=row[8].split("\n"),
            backend=BackendType(row[9]),
            confidence=row[10],
            reasoning=row[11],
            latency_ms=row[12],
            model_version=row[13]
        )
```

---

## 2. Dependency Injection via HemDov Container

### Current Container Implementation

Located at `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/interfaces.py`:

```python
class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type[T], implementation: T):
        """Register a service implementation."""
        self._services[interface] = implementation

    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        # Check if we have a registered service
        if interface in self._services:
            return self._services[interface]

        # Check for singleton instances
        if interface in self._singletons:
            return self._singletons[interface]

        # Create default instances for known types
        if interface is settings.__class__:
            if settings.__class__ not in self._singletons:
                self._singletons[settings.__class__] = settings
            return self._singletons[settings.__class__]

        raise ValueError(f"No service registered for {interface}")
```

### Required Changes

**Issue:** The current container doesn't support lazy initialization or factory functions, which are needed for database connections.

**Solution:** Extend container to support factory functions:

```python
# hemdov/interfaces.py (extended)
from typing import Dict, Type, TypeVar, Any, Callable, Optional
from hemdov.infrastructure.config import settings
from hemdov.domain.repositories.prompt_repository import PromptRepository

T = TypeVar("T")


class Container:
    """Extended dependency injection container with factory support."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], T]] = {}

    def register(self, interface: Type[T], implementation: T):
        """Register a service implementation (eager)."""
        self._services[interface] = implementation

    def register_factory(self, interface: Type[T], factory: Callable[[], T]):
        """Register a factory function for lazy initialization."""
        self._factories[interface] = factory

    def register_singleton(self, interface: Type[T], implementation: T):
        """Register a singleton instance."""
        self._singletons[interface] = implementation

    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        # Check eager services
        if interface in self._services:
            return self._services[interface]

        # Check singletons
        if interface in self._singletons:
            return self._singletons[interface]

        # Check factories (lazy initialization)
        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance  # Cache as singleton
            del self._factories[interface]  # Remove factory
            return instance

        # Create default instances for known types
        if interface is settings.__class__:
            if settings.__class__ not in self._singletons:
                self._singletons[settings.__class__] = settings
            return self._singletons[settings.__class__]

        raise ValueError(f"No service registered for {interface}")

    def clear(self):
        """Clear all registered services (useful for testing)."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# Global container instance
container = Container()

# Register default services
container.register(settings.__class__, settings)
```

### Repository Registration in main.py

```python
# main.py (additions to lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global lm

    # ... existing DSPy LM initialization ...

    # Initialize repository if persistence is enabled
    if settings.SQLITE_ENABLED:
        from hemdov.infrastructure.persistence.sqlite_prompt_repository import (
            SQLitePromptRepository
        )
        from hemdov.domain.repositories.prompt_repository import PromptRepository

        # Register factory for lazy initialization
        container.register_factory(
            PromptRepository,
            lambda: SQLitePromptRepository(settings)
        )
        logger.info(f"SQLite persistence enabled: db={settings.SQLITE_DB_PATH}")
    else:
        logger.info("SQLite persistence disabled (SQLITE_ENABLED=False)")

    yield

    logger.info("Shutting down DSPy backend...")
```

---

## 3. Error Handling Strategy

### Current Error Handling Issues

**Problem:** The current `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py` has minimal error handling:

```python
@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    # ... validation ...

    try:
        result = improver(original_idea=request.idea, context=request.context)
        return ImprovePromptResponse(...)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prompt improvement failed: {str(e)}"
        )
```

**Issues:**
1. No graceful degradation if repository fails
2. All errors treated the same (500)
3. No logging for debugging
4. No circuit breaker for persistent failures

### Recommended Error Handling

```python
# api/prompt_improver_api.py (improved)
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging
from datetime import datetime
import time

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings
from hemdov.domain.repositories.prompt_repository import (
    PromptRepository,
    RepositoryError
)

router = APIRouter(prefix="/api/v1", tags=["prompts"])
logger = logging.getLogger(__name__)

# ... request/response models unchanged ...

# Circuit breaker state
_repository_failure_count = 0
_MAX_REPOSITORY_FAILURES = 5
_REPOSITORY_DISABLED_UNTIL = None


def _should_use_repository(settings: Settings) -> bool:
    """Check if repository should be used based on circuit breaker."""
    if not settings.SQLITE_ENABLED:
        return False

    if _REPOSITORY_DISABLED_UNTIL:
        if datetime.utcnow() < _REPOSITORY_DISABLED_UNTIL:
            return False
        # Reset circuit breaker after timeout
        global _repository_failure_count, _REPOSITORY_DISABLED_UNTIL
        _repository_failure_count = 0
        _REPOSITORY_DISABLED_UNTIL = None

    return True


@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    Includes graceful degradation if persistence fails.
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Idea must be at least 5 characters"
        )

    # Get module
    from hemdov.interfaces import container

    settings = container.get(Settings)

    # Use few-shot if enabled
    if settings.DSPY_FEWSHOT_ENABLED:
        improver = get_fewshot_improver(settings)
        backend = "few-shot"
    else:
        improver = get_prompt_improver(settings)
        backend = "zero-shot"

    # Measure latency
    start_time = time.time()

    # Improve prompt
    try:
        result = improver(original_idea=request.idea, context=request.context)

    except Exception as e:
        logger.error(f"Prompt improvement failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prompt improvement failed: {str(e)}"
        )

    latency_ms = int((time.time() - start_time) * 1000)

    # Prepare response
    response = ImprovePromptResponse(
        improved_prompt=result.improved_prompt,
        role=result.role,
        directive=result.directive,
        framework=result.framework,
        guardrails=result.guardrails.split("\n")
        if isinstance(result.guardrails, str)
        else result.guardrails,
        reasoning=getattr(result, "reasoning", None),
        confidence=getattr(result, "confidence", None),
        backend=backend,
    )

    # Attempt to save to repository (non-blocking)
    if _should_use_repository(settings):
        await _save_history_async(
            settings=settings,
            request=request,
            result=result,
            backend=backend,
            latency_ms=latency_ms
        )

    return response


async def _save_history_async(
    settings: Settings,
    request: ImprovePromptRequest,
    result: any,
    backend: str,
    latency_ms: int
):
    """Save prompt history to repository with error handling."""
    global _repository_failure_count, _REPOSITORY_DISABLED_UNTIL

    try:
        from hemdov.interfaces import container
        from hemdov.domain.entities.prompt_history import PromptHistory, BackendType

        repository = container.get PromptRepository)

        # Create domain entity
        history = PromptHistory(
            id=None,
            timestamp=datetime.utcnow(),
            original_idea=request.idea,
            context=request.context,
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails,
            backend=BackendType(backend),
            confidence=getattr(result, "confidence", None),
            reasoning=getattr(result, "reasoning", None),
            latency_ms=latency_ms,
            model_version=settings.LLM_MODEL
        )

        # Save to repository
        await repository.save(history)

        # Reset failure counter on success
        _repository_failure_count = 0
        logger.debug(f"Saved prompt history (id={history.id}, latency={latency_ms}ms)")

    except RepositoryConnectionError as e:
        _repository_failure_count += 1
        logger.warning(f"Repository connection failed (count={_repository_failure_count}): {e}")

        # Trip circuit breaker after threshold
        if _repository_failure_count >= _MAX_REPOSITORY_FAILURES:
            from datetime import timedelta
            _REPOSITORY_DISABLED_UNTIL = datetime.utcnow() + timedelta(minutes=5)
            logger.error(
                f"Circuit breaker tripped: repository disabled for 5 minutes "
                f"after {_repository_failure_count} failures"
            )

    except RepositoryError as e:
        _repository_failure_count += 1
        logger.warning(f"Repository error (count={_repository_failure_count}): {e}")

    except Exception as e:
        logger.error(f"Unexpected error saving history: {e}", exc_info=True)
```

---

## 4. Configuration Management

### Required .env Variables

Add to `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/config/__init__.py`:

```python
# hemdov/infrastructure/config/__init__.py (additions)
class Settings(BaseSettings):
    """Global settings for HemDov DSPy integration."""

    # ... existing settings ...

    # SQLite Persistence Settings
    SQLITE_ENABLED: bool = True  # Master switch for persistence
    SQLITE_DB_PATH: str = "data/prompt_history.db"  # Path to SQLite database
    SQLITE_POOL_SIZE: int = 1  # SQLite writes are single-threaded anyway

    # Data Retention Settings
    SQLITE_RETENTION_DAYS: int = 30  # Auto-delete records older than N days
    SQLITE_AUTO_CLEANUP: bool = True  # Run cleanup on startup

    # Performance Settings
    SQLITE_ASYNC_ENABLED: bool = True  # Use aiosqlite for async operations
    SQLITE_WAL_MODE: bool = True  # Write-Ahead Logging for better concurrency

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
```

### Updated .env Example

```bash
# .env (additions)

# SQLite Persistence Configuration
SQLITE_ENABLED=true                    # Master switch (false = no persistence)
SQLITE_DB_PATH=data/prompt_history.db  # Database file location
SQLITE_POOL_SIZE=1                     # SQLite writes are serialized
SQLITE_RETENTION_DAYS=30               # Auto-delete records older than 30 days
SQLITE_AUTO_CLEANUP=true               # Run cleanup on startup
SQLITE_ASYNC_ENABLED=true              # Use async operations
SQLITE_WAL_MODE=true                   # Enable Write-Ahead Logging
```

---

## 5. Latency Measurement Strategy

### Implementation Location

**Best Practice:** Measure latency in the API layer (not repository) to capture full request lifecycle.

### Implementation

Already shown in section 3, but extracted here:

```python
# In api/prompt_improver_api.py
import time

@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    # ... validation ...

    # Start latency measurement
    start_time = time.time()

    # Execute prompt improvement
    result = improver(original_idea=request.idea, context=request.context)

    # Calculate latency in milliseconds
    latency_ms = int((time.time() - start_time) * 1000)

    # Pass latency to repository
    history = PromptHistory(
        # ... other fields ...
        latency_ms=latency_ms
    )

    # ... save to repository ...

    return response
```

### What Latency Captures

This `latency_ms` captures:
- DSPy module execution time
- LLM API call latency
- DSPy prompt compilation (if few-shot)
- Post-processing (parsing results, validation)

It does NOT capture:
- Network latency from client to server (Raycast extension → FastAPI)
- Repository save time (intentional - async/non-blocking)

---

## 6. SQLite Schema Optimizations

### Recommended Schema

```sql
-- Optimized schema for prompt_history table
CREATE TABLE prompt_history (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Timestamp (indexed for time-based queries)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Input data
    original_idea TEXT NOT NULL,
    context TEXT DEFAULT '',

    -- Output data
    improved_prompt TEXT NOT NULL,
    role TEXT NOT NULL,
    directive TEXT NOT NULL,
    framework TEXT NOT NULL,
    guardrails TEXT NOT NULL,  -- Stored as newline-separated string

    -- Metadata
    backend TEXT NOT NULL,  -- "zero-shot" or "few-shot"
    confidence REAL,  -- NULL if not provided
    reasoning TEXT,  -- NULL if not provided
    latency_ms INTEGER,  -- NULL if not provided
    model_version TEXT,  -- e.g., "claude-haiku-4-5-20251001"

    -- Constraints for data integrity
    CHECK(
        confidence IS NULL OR
        (confidence >= 0.0 AND confidence <= 1.0)
    ),
    CHECK(
        latency_ms IS NULL OR
        latency_ms >= 0
    ),
    CHECK(
        backend IN ('zero-shot', 'few-shot')
    ),
    CHECK(
        length(original_idea) >= 5
    )
);

-- Indexes for common query patterns
CREATE INDEX idx_timestamp ON prompt_history(timestamp DESC);
CREATE INDEX idx_backend ON prompt_history(backend);
CREATE INDEX idx_quality ON prompt_history(confidence, latency_ms);
CREATE INDEX idx_model ON prompt_history(model_version);

-- Schema versioning for migrations
CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial schema version
INSERT INTO schema_metadata (key, value)
VALUES ('schema_version', '1');
```

### Key Optimizations

1. **WAL Mode (Write-Ahead Logging)**
   - Enabled via `PRAGMA journal_mode=WAL`
   - Allows concurrent readers during writes
   - Better performance for read-heavy workloads

2. **Synchronous Mode**
   - Set to `NORMAL` instead of `FULL`
   - Faster writes with acceptable safety for local SQLite

3. **Cache Size**
   - Increased to 64MB (`PRAGMA cache_size=-64000`)
   - Reduces disk I/O for common queries

4. **Temp Store**
   - Set to `MEMORY` (`PRAGMA temp_store=MEMORY`)
   - Temporary tables stay in RAM

5. **Indexes**
   - Timestamp DESC for recent queries
   - Backend for filtering
   - Composite index on (confidence, latency_ms) for quality queries

### Migration Strategy

```python
# hemdov/infrastructure/persistence/migrations.py
class SchemaMigration:
    """Handle schema versioning and migrations."""

    MIGRATIONS = {
        1: "_create_v1_schema",
        # Future versions:
        # 2: "_add_user_id_column",
        # 3: "_add_tags_table",
    }

    async def migrate(self, conn: aiosqlite.Connection, current_version: int):
        """Run migrations from current version to latest."""
        for version in sorted(self.MIGRATIONS.keys()):
            if version > current_version:
                migration_func = getattr(self, self.MIGRATIONS[version])
                await migration_func(conn)
                logger.info(f"Applied migration v{version}")
```

---

## 7. Concurrency and Locking

### SQLite Concurrency Limitations

**SQLite Concurrency Model:**
- **Multiple readers:** Unlimited (with WAL mode)
- **Single writer:** Only one write transaction at a time
- **Write serialization:** Writes are queued and executed sequentially

### Recommended Approach

1. **Use WAL Mode**
   ```python
   await conn.execute("PRAGMA journal_mode=WAL")
   ```
   - Allows readers during writes
   - Better concurrency for FastAPI

2. **Connection Pooling**
   - Pool size = 1 for writes (SQLite limitation)
   - Pool size = 5-10 for reads
   - Use `aiosqlite` for async operations

3. **Optimistic Locking**
   - No explicit locks needed for reads
   - SQLite handles write locking automatically

4. **Retry on Busy**
   ```python
   async def _execute_with_retry(self, conn, sql, params, max_retries=3):
       """Execute SQL with retry on 'database is locked'."""
       for attempt in range(max_retries):
           try:
               return await conn.execute(sql, params)
           except aiosqlite.OperationalError as e:
               if "locked" in str(e).lower() and attempt < max_retries - 1:
                   await asyncio.sleep(0.1 * (attempt + 1))  # Backoff
                   continue
               raise
   ```

5. **Timeout Configuration**
   ```python
   conn = await aiosqlite.connect(
       self.db_path,
       timeout=10.0  # 10 second timeout for locks
   )
   ```

### Write Contention Mitigation

For high-write scenarios (unlikely in this project):

1. **Write Queue**
   - Queue writes in memory
   - Batch flush every N seconds or M records

2. **Separate Thread**
   - Run writes in background thread
   - Use `asyncio.to_thread()` for async compatibility

### Recommended Configuration

```python
# In SQLitePromptRepository.__init__
async def _get_connection(self) -> aiosqlite.Connection:
    """Get connection with concurrency settings."""
    conn = await aiosqlite.connect(
        self.db_path,
        check_same_thread=False,
        timeout=10.0  # Wait up to 10s for locks
    )

    # Enable WAL for better concurrency
    await conn.execute("PRAGMA journal_mode=WAL")

    # Optimize locking behavior
    await conn.execute("PRAGMA busy_timeout=10000")  # 10s
    await conn.execute("PRAGMA synchronous=NORMAL")

    return conn
```

---

## 8. Integration with Existing API

### Changes Required to `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py`

**Current Implementation Issues:**
1. No persistence layer integration
2. Global mutable state for module instances
3. No dependency injection

**Recommended Changes:**

```python
# api/prompt_improver_api.py (refactored)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import time
from datetime import datetime

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings
from hemdov.domain.repositories.prompt_repository import PromptRepository, RepositoryError
from hemdov.domain.entities.prompt_history import PromptHistory, BackendType
from hemdov.interfaces import container

router = APIRouter(prefix="/api/v1", tags=["prompts"])
logger = logging.getLogger(__name__)

# ... request/response models unchanged ...

# Circuit breaker state
_repository_failure_count = 0
_MAX_REPOSITORY_FAILURES = 5
_REPOSITORY_DISABLED_UNTIL = None


def get_settings() -> Settings:
    """Dependency injection for settings."""
    return container.get(Settings)


def get_repository() -> Optional[PromptRepository]:
    """
    Dependency injection for repository.

    Returns None if persistence is disabled or circuit breaker is open.
    """
    global _REPOSITORY_DISABLED_UNTIL

    settings = container.get(Settings)

    # Check if persistence is enabled
    if not settings.SQLITE_ENABLED:
        return None

    # Check circuit breaker
    if _REPOSITORY_DISABLED_UNTIL:
        if datetime.utcnow() < _REPOSITORY_DISABLED_UNTIL:
            return None
        # Reset circuit breaker
        global _repository_failure_count
        _repository_failure_count = 0
        _REPOSITORY_DISABLED_UNTIL = None

    try:
        return container.get(PromptRepository)
    except ValueError:
        return None


@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(
    request: ImprovePromptRequest,
    settings: Settings = Depends(get_settings),
    repository: Optional[PromptRepository] = Depends(get_repository)
):
    """
    Improve a raw idea into a high-quality structured prompt.

    Includes optional persistence with graceful degradation.
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Idea must be at least 5 characters"
        )

    # Get module
    if settings.DSPY_FEWSHOT_ENABLED:
        improver = get_fewshot_improver(settings)
        backend = BackendType.FEW_SHOT
    else:
        improver = get_prompt_improver(settings)
        backend = BackendType.ZERO_SHOT

    # Measure latency
    start_time = time.time()

    # Improve prompt
    try:
        result = improver(original_idea=request.idea, context=request.context)
    except Exception as e:
        logger.error(f"Prompt improvement failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prompt improvement failed: {str(e)}"
        )

    latency_ms = int((time.time() - start_time) * 1000)

    # Prepare response
    response = ImprovePromptResponse(
        improved_prompt=result.improved_prompt,
        role=result.role,
        directive=result.directive,
        framework=result.framework,
        guardrails=(
            result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails
        ),
        reasoning=getattr(result, "reasoning", None),
        confidence=getattr(result, "confidence", None),
        backend=backend.value,
    )

    # Save to repository asynchronously (non-blocking)
    if repository:
        asyncio.create_task(
            _save_history_async(
                repository=repository,
                request=request,
                result=result,
                backend=backend,
                latency_ms=latency_ms,
                model_version=settings.LLM_MODEL
            )
        )

    return response


async def _save_history_async(
    repository: PromptRepository,
    request: ImprovePromptRequest,
    result: any,
    backend: BackendType,
    latency_ms: int,
    model_version: str
):
    """Save prompt history in background with error handling."""
    global _repository_failure_count, _REPOSITORY_DISABLED_UNTIL

    try:
        history = PromptHistory(
            id=None,
            timestamp=datetime.utcnow(),
            original_idea=request.idea,
            context=request.context,
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=(
                result.guardrails.split("\n")
                if isinstance(result.guardrails, str)
                else result.guardrails
            ),
            backend=backend,
            confidence=getattr(result, "confidence", None),
            reasoning=getattr(result, "reasoning", None),
            latency_ms=latency_ms,
            model_version=model_version
        )

        await repository.save(history)
        _repository_failure_count = 0  # Reset on success
        logger.debug(f"Saved prompt history (id={history.id})")

    except RepositoryConnectionError as e:
        _repository_failure_count += 1
        logger.warning(f"Repository connection failed: {e}")

        if _repository_failure_count >= _MAX_REPOSITORY_FAILURES:
            from datetime import timedelta
            _REPOSITORY_DISABLED_UNTIL = datetime.utcnow() + timedelta(minutes=5)
            logger.error("Circuit breaker tripped: repository disabled for 5 minutes")

    except RepositoryError as e:
        _repository_failure_count += 1
        logger.warning(f"Repository error: {e}")

    except Exception as e:
        logger.error(f"Unexpected error saving history: {e}", exc_info=True)
```

---

## 9. Testing Strategy

### Unit Tests for Repository

```python
# tests/test_sqlite_prompt_repository.py
import pytest
import aiosqlite
from pathlib import Path
from datetime import datetime

from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from hemdov.domain.entities.prompt_history import PromptHistory, BackendType
from hemdov.domain.repositories.prompt_repository import RepositoryError
from hemdov.infrastructure.config import Settings


@pytest.fixture
async def test_db_path(tmp_path):
    """Create temporary database for testing."""
    return tmp_path / "test.db"


@pytest.fixture
async def test_settings(test_db_path):
    """Create settings for testing."""
    return Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=str(test_db_path),
        SQLITE_POOL_SIZE=1
    )


@pytest.fixture
async def repository(test_settings):
    """Create repository instance for testing."""
    return SQLitePromptRepository(test_settings)


@pytest.mark.asyncio
async def test_save_prompt_history(repository):
    """Test saving a prompt history record."""
    history = PromptHistory(
        id=None,
        timestamp=datetime.utcnow(),
        original_idea="Test idea",
        context="Test context",
        improved_prompt="Improved prompt",
        role="Test role",
        directive="Test directive",
        framework="Test framework",
        guardrails=["guard1", "guard2"],
        backend=BackendType.ZERO_SHOT,
        confidence=0.85,
        reasoning="Test reasoning",
        latency_ms=1500,
        model_version="test-model"
    )

    saved = await repository.save(history)

    assert saved.id is not None
    assert saved.original_idea == history.original_idea
    assert saved.confidence == history.confidence


@pytest.mark.asyncio
async def test_find_by_id(repository):
    """Test finding a history by ID."""
    # Save first
    history = PromptHistory(
        id=None,
        timestamp=datetime.utcnow(),
        original_idea="Test idea",
        context="",
        improved_prompt="Improved",
        role="Role",
        directive="Directive",
        framework="Framework",
        guardrails=[],
        backend=BackendType.FEW_SHOT,
        confidence=0.9,
        reasoning=None,
        latency_ms=1000,
        model_version="model"
    )
    saved = await repository.save(history)

    # Find by ID
    found = await repository.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.original_idea == saved.original_idea


@pytest.mark.asyncio
async def test_find_recent_with_filtering(repository):
    """Test finding recent histories with backend filtering."""
    # Save multiple histories
    for i in range(5):
        history = PromptHistory(
            id=None,
            timestamp=datetime.utcnow(),
            original_idea=f"Idea {i}",
            context="",
            improved_prompt=f"Improved {i}",
            role="Role",
            directive="Directive",
            framework="Framework",
            guardrails=[],
            backend=BackendType.ZERO_SHOT if i % 2 == 0 else BackendType.FEW_SHOT,
            confidence=0.8,
            reasoning=None,
            latency_ms=1000,
            model_version="model"
        )
        await repository.save(history)

    # Find all recent
    all_recent = await repository.find_recent(limit=10)
    assert len(all_recent) == 5

    # Find only zero-shot
    zero_shot = await repository.find_recent(
        limit=10,
        backend=BackendType.ZERO_SHOT
    )
    assert len(zero_shot) == 3
    assert all(h.backend == BackendType.ZERO_SHOT for h in zero_shot)


@pytest.mark.asyncio
async def test_delete_old_histories(repository):
    """Test deleting old histories."""
    from datetime import timedelta

    # Save old history
    old_history = PromptHistory(
        id=None,
        timestamp=datetime.utcnow() - timedelta(days=40),
        original_idea="Old idea",
        context="",
        improved_prompt="Old improved",
        role="Role",
        directive="Directive",
        framework="Framework",
        guardrails=[],
        backend=BackendType.ZERO_SHOT,
        confidence=0.8,
        reasoning=None,
        latency_ms=1000,
        model_version="model"
    )
    await repository.save(old_history)

    # Save recent history
    recent_history = PromptHistory(
        id=None,
        timestamp=datetime.utcnow(),
        original_idea="Recent idea",
        context="",
        improved_prompt="Recent improved",
        role="Role",
        directive="Directive",
        framework="Framework",
        guardrails=[],
        backend=BackendType.ZERO_SHOT,
        confidence=0.8,
        reasoning=None,
        latency_ms=1000,
        model_version="model"
    )
    await repository.save(recent_history)

    # Delete older than 30 days
    deleted_count = await repository.delete_old(days=30)
    assert deleted_count == 1

    # Verify recent still exists
    all_recent = await repository.find_recent()
    assert len(all_recent) == 1
    assert all_recent[0].original_idea == "Recent idea"


@pytest.mark.asyncio
async def test_repository_connection_error():
    """Test repository connection error handling."""
    # Use invalid path
    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH="/invalid/path/db.sqlite",
        SQLITE_POOL_SIZE=1
    )

    repository = SQLitePromptRepository(settings)

    history = PromptHistory(
        id=None,
        timestamp=datetime.utcnow(),
        original_idea="Test",
        context="",
        improved_prompt="Improved",
        role="Role",
        directive="Directive",
        framework="Framework",
        guardrails=[],
        backend=BackendType.ZERO_SHOT,
        confidence=0.8,
        reasoning=None,
        latency_ms=1000,
        model_version="model"
    )

    with pytest.raises(RepositoryError):
        await repository.save(history)
```

### Integration Tests for API

```python
# tests/test_prompt_improver_api_integration.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from hemdov.infrastructure.config import Settings
from hemdov.interfaces import container


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_settings():
    """Configure settings for testing."""
    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH="test_data/test.db",
        SQLITE_POOL_SIZE=1
    )
    container.register(settings.__class__, settings)
    return settings


def test_improve_prompt_with_persistence(client, test_settings):
    """Test prompt improvement with persistence enabled."""
    response = client.post(
        "/api/v1/improve-prompt",
        json={
            "idea": "Design a REST API",
            "context": "FastAPI backend"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "improved_prompt" in data
    assert "role" in data
    assert "backend" in data
    assert "latency_ms" not in data  # Not exposed in response


def test_improve_prompt_without_persistence(client):
    """Test prompt improvement with persistence disabled."""
    settings = Settings(SQLITE_ENABLED=False)
    container.register(settings.__class__, settings)

    response = client.post(
        "/api/v1/improve-prompt",
        json={
            "idea": "Design a REST API",
            "context": "FastAPI backend"
        }
    )

    # Should still work, just without persistence
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
```

---

## 10. Performance Considerations

### Expected Performance

| Operation | Expected Latency | Notes |
|-----------|------------------|-------|
| Save prompt history | 5-15ms | Indexed columns, WAL mode |
| Find by ID | <1ms | Primary key lookup |
| Find recent (limit=100) | 5-20ms | Index scan on timestamp |
| Get statistics | 10-50ms | Full table scans for aggregates |
| Delete old | 50-200ms | Depends on data volume |

### Optimization Strategies

1. **Async Operations**
   - Use `aiosqlite` for non-blocking database calls
   - Save history in background task (`asyncio.create_task`)
   - Don't block API response on repository save

2. **Write Coalescing**
   - Buffer writes in memory
   - Flush every 5 seconds or 100 records
   - Reduces disk I/O for high traffic

3. **Read Caching**
   - Cache statistics in memory (TTL=60s)
   - Cache recent histories (TTL=30s)
   - Use `functools.lru_cache` for hot queries

4. **Connection Pooling**
   - Reuse connections across requests
   - Use `aiosqlite` with connection pool
   - Set appropriate pool size (1 writer, 5 readers)

5. **Index Maintenance**
   - Reindex weekly: `REINDEX`
   - Analyze query performance: `EXPLAIN QUERY PLAN`
   - Monitor index usage with SQLite stats

6. **Database VACUUM**
   - Run monthly to reclaim space
   - Consider `auto_vacuum=FULL` for smaller databases

---

## 11. Monitoring and Observability

### Logging Strategy

```python
# Add to SQLitePromptRepository
import logging

logger = logging.getLogger(__name__)

class SQLitePromptRepository(PromptRepository):
    async def save(self, history: PromptHistory) -> PromptHistory:
        """Save with detailed logging."""
        start_time = time.time()

        try:
            result = await self._save_impl(history)

            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Saved prompt history (id={result.id}, latency={latency_ms}ms, "
                f"backend={history.backend}, confidence={history.confidence})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to save prompt history: {e}", exc_info=True)
            raise
```

### Metrics to Track

1. **Repository Metrics**
   - Save latency (p50, p95, p99)
   - Save success rate (%)
   - Connection failures
   - Circuit breaker trips

2. **Database Metrics**
   - Database size on disk
   - Row count
   - Index hit rate
   - WAL file size

3. **Business Metrics**
   - Average confidence score
   - Average latency_ms
   - Backend distribution (zero-shot vs few-shot)
   - Daily prompt volume

### Health Check Endpoint

```python
# Add to main.py
@app.get("/health/repository")
async def repository_health_check():
    """Check repository health."""
    from hemdov.interfaces import container
    from hemdov.domain.repositories.prompt_repository import PromptRepository

    settings = container.get(Settings)

    if not settings.SQLITE_ENABLED:
        return {"status": "disabled", "reason": "SQLITE_ENABLED=False"}

    try:
        repository = container.get(PromptRepository)
        stats = await repository.get_statistics()
        return {
            "status": "healthy",
            "total_records": stats["total_count"],
            "database_path": settings.SQLITE_DB_PATH
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 12. Security Considerations

### SQL Injection Prevention

**Good:** Use parameterized queries (already done in recommended implementation)

```python
# SAFE
await cursor.execute(
    "SELECT * FROM prompt_history WHERE id = ?",
    (history_id,)
)

# UNSAFE - NEVER DO THIS
await cursor.execute(
    f"SELECT * FROM prompt_history WHERE id = {history_id}"
)
```

### File System Security

```python
# Validate database path
def _validate_db_path(path: str) -> Path:
    """Ensure database path is within allowed directory."""
    db_path = Path(path).resolve()
    allowed_dir = Path("data").resolve()

    # Prevent path traversal attacks
    if not str(db_path).startswith(str(allowed_dir)):
        raise ValueError(f"Database path must be within {allowed_dir}")

    return db_path
```

### Data Sanitization

```python
# Sanitize guardrails before storage
def _sanitize_guardrails(guardrails: list[str]) -> str:
    """Sanitize guardrails list for storage."""
    # Remove empty strings
    cleaned = [g.strip() for g in guardrails if g.strip()]
    # Limit length
    return "\n".join(cleaned)[:10000]  # Max 10KB
```

---

## 13. Deployment Considerations

### Docker Configuration

```dockerfile
# Dockerfile (additions)
RUN mkdir -p /app/data && \
    chmod 777 /app/data

VOLUME ["/app/data"]
```

### Kubernetes Configuration

```yaml
# k8s/persistent-volume-claim.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prompt-history-db
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### Database Backup Strategy

```bash
# scripts/backup_db.sh
#!/bin/bash
BACKUP_DIR="/backups"
DB_PATH="/app/data/prompt_history.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup using SQLite backup command
sqlite3 "$DB_PATH" ".backup '${BACKUP_DIR}/prompt_history_${DATE}.db'"

# Compress
gzip "${BACKUP_DIR}/prompt_history_${DATE}.db"

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "prompt_history_*.db.gz" -mtime +30 -delete
```

---

## 14. Recommendations Summary

### Must-Have (Critical)

1. ✅ **Use `aiosqlite`** for async operations (blocks FastAPI otherwise)
2. ✅ **Implement circuit breaker** to prevent cascading failures
3. ✅ **Add graceful degradation** (API works even if repository fails)
4. ✅ **Extend HemDov Container** with factory functions for lazy initialization
5. ✅ **Use frozen dataclasses** for domain entities (immutability)
6. ✅ **Add `SQLITE_ENABLED` flag** to `.env` for easy disable

### Should-Have (Important)

7. ✅ **Implement schema migrations** for versioning
8. ✅ **Add comprehensive logging** for debugging
9. ✅ **Use WAL mode** for better concurrency
10. ✅ **Add unit tests** for repository layer
11. ✅ **Add integration tests** for API layer
12. ✅ **Implement data retention** (auto-delete old records)

### Nice-to-Have (Optimization)

13. ⚡ **Cache statistics** in memory (reduce DB queries)
14. ⚡ **Add write coalescing** (buffer writes for performance)
15. ⚡ **Implement background cleanup** (async job)
16. ⚡ **Add Prometheus metrics** for monitoring
17. ⚡ **Implement database backup** automation

---

## 15. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create domain entities (`PromptHistory`)
- [ ] Create repository interface (`PromptRepository`)
- [ ] Implement `SQLitePromptRepository`
- [ ] Update `Settings` with SQLite config
- [ ] Add `aiosqlite` to requirements.txt

### Phase 2: Integration (Week 1)
- [ ] Extend `HemDov Container` with factory support
- [ ] Register repository in container
- [ ] Update `main.py` lifespan for repository init
- [ ] Modify `prompt_improver_api.py` to use repository
- [ ] Implement graceful degradation

### Phase 3: Testing (Week 2)
- [ ] Write unit tests for repository
- [ ] Write integration tests for API
- [ ] Add error handling tests
- [ ] Add performance benchmarks

### Phase 4: Production Readiness (Week 2)
- [ ] Add comprehensive logging
- [ ] Implement circuit breaker
- [ ] Add health check endpoint
- [ ] Create database backup scripts
- [ ] Update documentation

---

## Conclusion

The proposed SQLite persistence design is **architecturally sound** but requires **significant improvements** to properly integrate with the HemDov architecture and meet production requirements:

### Architecture Score: 7/10

**Strengths:**
- Follows Hexagonal Architecture principles
- Clean separation of concerns (domain/infrastructure)
- Repository pattern abstracts persistence

**Weaknesses:**
- Missing async support (blocks FastAPI)
- No dependency injection via container
- Incomplete error handling

### Production Readiness: 5/10

**Strengths:**
- SQLite is simple and reliable
- Easy to deploy (no external dependencies)

**Weaknesses:**
- No graceful degradation
- No circuit breaker
- No monitoring/observability
- No backup strategy

### Recommended Next Steps

1. **Implement recommended changes** from this analysis
2. **Add comprehensive tests** (unit + integration)
3. **Deploy with feature flag** (`SQLITE_ENABLED=False` initially)
4. **Monitor performance** in staging environment
5. **Gradually rollout** to production with observability

The design is **viable** but needs the improvements outlined above to be production-ready.
