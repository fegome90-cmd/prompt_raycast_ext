# SQLite Persistence for DSPy Prompt Improver - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement SQLite persistence layer for prompt history with graceful degradation, following HemDov hexagonal architecture principles.

**Architecture:** Repository pattern with domain entities, async SQLite via aiosqlite, circuit breaker for graceful degradation, dependency injection via extended HemDov Container.

**Tech Stack:** Python 3.14, FastAPI, aiosqlite, Pydantic, DSPy, HemDov (Clean Architecture)

---

## Pre-Flight: Critical Prerequisites

### Phase 0: Foundation Setup (30 min)

### Task 0.1: Install aiosqlite Dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add aiosqlite to requirements**

```bash
# Add this line to requirements.txt
aiosqlite>=0.19.0
```

**Step 2: Install dependency**

```bash
pip install aiosqlite
```

**Step 3: Verify installation**

```bash
python -c "import aiosqlite; print(aiosqlite.__version__)"
```
Expected: Output version number (e.g., "0.19.0")

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "deps: add aiosqlite for async SQLite operations"
```

### Task 0.2: Create Test Infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create tests directory and init**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2: Create pytest configuration**

```python
# tests/conftest.py
import pytest
import asyncio
from pathlib import Path

@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Provide temporary database path for tests."""
    return str(tmp_path / "test_prompt_history.db")

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

**Step 3: Create empty test file**

```bash
touch tests/test_sqlite_prompt_repository.py
```

**Step 4: Verify pytest setup**

```bash
pytest tests/ -v
```
Expected: "collected 0 items"

**Step 5: Commit**

```bash
git add tests/
git commit -m "test: add pytest infrastructure for async tests"
```

---

## Phase 1: Extend HemDov Container (45 min)

### Task 1.1: Add Factory Pattern to Container

**Files:**
- Modify: `hemdov/interfaces.py`

**Step 1: Read current Container implementation**

```bash
# Read to understand current structure
cat hemdov/interfaces.py
```

**Step 2: Extend Container class**

```python
# hemdov/interfaces.py
# Add these imports at top
from typing import Callable, Dict, List
from asyncio import iscoroutinefunction

# Modify Container class - add these methods
class Container:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}  # NEW
        self._cleanup_hooks: List[Callable] = []     # NEW

    def register_factory(self, interface: Type[T], factory: Callable[[], T]):
        """Register factory function for lazy initialization."""
        self._factories[interface] = factory

    def get(self, interface: Type[T]) -> T:
        """Get service, instantiating from factory if needed."""
        # Check services
        if interface in self._services:
            return self._services[interface]

        # Check singletons
        if interface in self._singletons:
            return self._singletons[interface]

        # NEW: Check factories - lazy initialization
        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance
            del self._factories[interface]  # Remove after use
            return instance

        # Create default Settings
        if interface is Settings.__class__:
            if interface not in self._singletons:
                self._singletons[interface] = settings
            return self._singletons[interface]

        raise ValueError(f"No service registered for {interface}")

    async def shutdown(self):
        """Cleanup resources on application shutdown."""
        for hook in reversed(self._cleanup_hooks):
            if iscoroutinefunction(hook):
                await hook()
            else:
                hook()
```

**Step 3: Verify syntax**

```bash
python -c "from hemdov.interfaces import Container; print('Container OK')"
```
Expected: "Container OK"

**Step 4: Commit**

```bash
git add hemdov/interfaces.py
git commit -m "refactor(container): add factory pattern and lifecycle management"
```

---

## Phase 2: Domain Layer (60 min)

### Task 2.1: Create Domain Entity

**Files:**
- Create: `hemdov/domain/entities/__init__.py`
- Create: `hemdov/domain/entities/prompt_history.py`

**Step 1: Create directory**

```bash
mkdir -p hemdov/domain/entities
```

**Step 2: Write PromptHistory entity**

```python
# hemdov/domain/entities/prompt_history.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class PromptHistory:
    """
    Domain entity representing a prompt improvement event.

    Immutable value object following Domain-Driven Design principles.
    All validation happens in __post_init__ to enforce business invariants.
    """

    # Input fields
    original_idea: str
    context: str

    # Output fields
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: Optional[str] = None
    confidence: Optional[float] = None

    # Metadata
    backend: str  # "zero-shot" | "few-shot"
    model: str
    provider: str
    latency_ms: Optional[int] = None

    # Timestamp
    created_at: Optional[str] = None

    def __post_init__(self):
        """Validate business invariants."""
        # Validate confidence range
        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

        # Validate latency is non-negative
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError(f"Latency must be >= 0, got {self.latency_ms}")

        # Validate non-empty inputs
        if not self.original_idea or not self.original_idea.strip():
            raise ValueError("original_idea cannot be empty")

        if not self.improved_prompt or not self.improved_prompt.strip():
            raise ValueError("improved_prompt cannot be empty")

        # Validate framework is allowed value
        allowed_frameworks = {
            "chain-of-thought",
            "tree-of-thoughts",
            "decomposition",
            "role-playing"
        }
        if self.framework not in allowed_frameworks:
            raise ValueError(f"Invalid framework: {self.framework}")

        # Validate guardrails is not empty
        if not self.guardrails:
            raise ValueError("guardrails cannot be empty")

        # Set created_at if not provided
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow().isoformat())

    @property
    def quality_score(self) -> float:
        """Calculate composite quality score (0-1)."""
        conf_score = self.confidence or 0.5
        latency_penalty = min((self.latency_ms or 0) / 10000, 0.3)
        return max(0.0, min(1.0, conf_score - latency_penalty))
```

**Step 3: Create package init**

```python
# hemdov/domain/entities/__init__.py
from hemdov.domain.entities.prompt_history import PromptHistory

__all__ = ["PromptHistory"]
```

**Step 4: Verify entity**

```bash
python -c "
from hemdov.domain.entities.prompt_history import PromptHistory
from datetime import datetime
p = PromptHistory(
    original_idea='test',
    context='',
    improved_prompt='improved',
    role='AI',
    directive='do task',
    framework='chain-of-thought',
    guardrails=['be nice'],
    backend='zero-shot',
    model='test',
    provider='test',
    latency_ms=1000,
    confidence=0.9
)
print(f'Quality score: {p.quality_score}')
"
```
Expected: "Quality score: 0.9"

**Step 5: Commit**

```bash
git add hemdov/domain/entities/
git commit -m "feat(domain): add PromptHistory frozen dataclass entity"
```

### Task 2.2: Create Repository Interface

**Files:**
- Create: `hemdov/domain/repositories/__init__.py`
- Create: `hemdov/domain/repositories/prompt_repository.py`

**Step 1: Create directory**

```bash
mkdir -p hemdov/domain/repositories
```

**Step 2: Write repository interface**

```python
# hemdov/domain/repositories/prompt_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from hemdov.domain.entities.prompt_history import PromptHistory


class PromptRepository(ABC):
    """
    Repository interface for prompt history persistence.

    Follows Dependency Inversion Principle - domain defines interface,
    infrastructure provides implementation.
    """

    @abstractmethod
    async def save(self, history: PromptHistory) -> int:
        """
        Save a prompt history record.

        Returns:
            int: The ID of the saved record
        """
        pass

    @abstractmethod
    async def find_by_id(self, history_id: int) -> Optional[PromptHistory]:
        """Find a prompt history by ID."""
        pass

    @abstractmethod
    async def find_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        provider: Optional[str] = None,
        backend: Optional[str] = None,
    ) -> List[PromptHistory]:
        """Find recent prompts with optional filters."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[PromptHistory]:
        """Search prompts by text content."""
        pass

    @abstractmethod
    async def delete_old_records(self, days: int) -> int:
        """
        Delete records older than specified days.

        Returns:
            int: Number of records deleted
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> dict:
        """Get usage statistics."""
        pass

    @abstractmethod
    async def close(self):
        """Close database connections and cleanup resources."""
        pass
```

**Step 3: Create package init**

```python
# hemdov/domain/repositories/__init__.py
from hemdov.domain.repositories.prompt_repository import PromptRepository

__all__ = ["PromptRepository"]
```

**Step 4: Verify interface**

```bash
python -c "
from hemdov.domain.repositories.prompt_repository import PromptRepository
print(f'PromptRepository ABC: {PromptRepository.__abstractmethods__}')
"
```
Expected: Set of abstract method names

**Step 5: Commit**

```bash
git add hemdov/domain/repositories/
git commit -m "feat(domain): add PromptRepository interface"
```

---

## Phase 3: Infrastructure Layer (90 min)

### Task 3.1: Add SQLite Configuration to Settings

**Files:**
- Modify: `hemdov/infrastructure/config/__init__.py`

**Step 1: Read current settings**

```bash
cat hemdov/infrastructure/config/__init__.py
```

**Step 2: Add SQLite settings class**

```python
# hemdov/infrastructure/config/__init__.py
# Add to Settings class (around line 54, after existing fields)

class Settings(BaseSettings):
    # ... existing fields ...

    # SQLite Persistence Settings (NEW)
    SQLITE_ENABLED: bool = True
    SQLITE_DB_PATH: str = "data/prompt_history.db"
    SQLITE_POOL_SIZE: int = 1
    SQLITE_RETENTION_DAYS: int = 30
    SQLITE_AUTO_CLEANUP: bool = True
    SQLITE_WAL_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
```

**Step 3: Verify settings**

```bash
python -c "
from hemdov.infrastructure.config import Settings
s = Settings()
print(f'SQLITE_ENABLED: {s.SQLITE_ENABLED}')
print(f'SQLITE_DB_PATH: {s.SQLITE_DB_PATH}')
"
```
Expected: Default values printed

**Step 4: Commit**

```bash
git add hemdov/infrastructure/config/__init__.py
git commit -m "feat(config): add SQLite persistence settings"
```

### Task 3.2: Create SQLite Repository Implementation

**Files:**
- Create: `hemdov/infrastructure/persistence/__init__.py`
- Create: `hemdov/infrastructure/persistence/sqlite_prompt_repository.py`
- Create: `hemdov/infrastructure/persistence/migrations.py`

**Step 1: Create persistence directory**

```bash
mkdir -p hemdov/infrastructure/persistence
```

**Step 2: Create migrations module**

```python
# hemdov/infrastructure/persistence/migrations.py
"""Database schema migrations for prompt history."""

SCHEMA_VERSION = 1

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    original_idea TEXT NOT NULL,
    context TEXT DEFAULT '',
    improved_prompt TEXT NOT NULL,
    role TEXT NOT NULL,
    directive TEXT NOT NULL,
    framework TEXT NOT NULL,
    guardrails TEXT NOT NULL,
    reasoning TEXT,
    confidence REAL,
    backend TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    latency_ms INTEGER,

    CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    CHECK(latency_ms IS NULL OR latency_ms >= 0)
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_created_at ON prompt_history(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_backend ON prompt_history(backend);",
    "CREATE INDEX IF NOT EXISTS idx_provider ON prompt_history(provider);",
    "CREATE INDEX IF NOT EXISTS idx_confidence ON prompt_history(confidence);",
]

async def run_migrations(conn):
    """Run database migrations to latest version."""
    # Create table
    await conn.execute(CREATE_TABLE_SQL)

    # Create indexes
    for index_sql in CREATE_INDEXES_SQL:
        await conn.execute(index_sql)

    # Store schema version
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_info (version INTEGER PRIMARY KEY)"
    )
    await conn.execute(
        f"INSERT OR REPLACE INTO schema_info (version) VALUES ({SCHEMA_VERSION})"
    )
```

**Step 3: Write SQLite repository**

```python
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
        return PromptHistory(
            original_idea=row["original_idea"],
            context=row["context"] or "",
            improved_prompt=row["improved_prompt"],
            role=row["role"],
            directive=row["directive"],
            framework=row["framework"],
            guardrails=json.loads(row["guardrails"]),
            reasoning=row["reasoning"],
            confidence=row["confidence"],
            backend=row["backend"],
            model=row["model"],
            provider=row["provider"],
            latency_ms=row["latency_ms"],
            created_at=row["created_at"],
        )
```

**Step 4: Create package init**

```python
# hemdov/infrastructure/persistence/__init__.py
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository

__all__ = ["SQLitePromptRepository"]
```

**Step 5: Verify repository compiles**

```bash
python -c "from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository; print('OK')"
```
Expected: "OK"

**Step 6: Commit**

```bash
git add hemdov/infrastructure/persistence/
git commit -m "feat(infrastructure): add SQLite repository implementation with aiosqlite"
```

---

## Phase 4: API Integration with Circuit Breaker (75 min)

### Task 4.1: Implement Thread-Safe Circuit Breaker

**Files:**
- Create: `api/circuit_breaker.py`

**Step 1: Create circuit breaker utility**

```python
# api/circuit_breaker.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Thread-safe circuit breaker for async operations.

    Prevents cascading failures by disabling operations after
    consecutive failures. Automatically re-enables after cooldown period.
    """

    def __init__(self, max_failures: int = 5, timeout_seconds: int = 300):
        self._max_failures = max_failures
        self._timeout_seconds = timeout_seconds
        self._failure_count = 0
        self._disabled_until: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def should_attempt(self) -> bool:
        """Check if operation should be attempted."""
        async with self._lock:
            # Check if disabled
            if self._disabled_until:
                if datetime.utcnow() < self._disabled_until:
                    logger.warning(
                        f"Circuit breaker open until {self._disabled_until.isoformat()}"
                    )
                    return False
                # Reset after timeout
                logger.info("Circuit breaker timeout elapsed, resetting")
                self._failure_count = 0
                self._disabled_until = None

            return True

    async def record_success(self):
        """Record successful operation."""
        async with self._lock:
            if self._failure_count > 0:
                logger.info(f"Circuit breaker reset (was at {self._failure_count} failures)")
            self._failure_count = 0
            self._disabled_until = None

    async def record_failure(self):
        """Record failed operation and trip if needed."""
        async with self._lock:
            self._failure_count += 1

            if self._failure_count >= self._max_failures:
                self._disabled_until = datetime.utcnow() + timedelta(
                    seconds=self._timeout_seconds
                )
                logger.error(
                    f"Circuit breaker tripped after {self._failure_count} failures, "
                    f"disabled until {self._disabled_until.isoformat()}"
                )
            else:
                logger.warning(f"Circuit breaker failure count: {self._failure_count}/{self._max_failures}")
```

**Step 2: Commit**

```bash
git add api/circuit_breaker.py
git commit -m "feat(api): add thread-safe circuit breaker for graceful degradation"
```

### Task 4.2: Modify API Endpoint to Use Repository

**Files:**
- Modify: `api/prompt_improver_api.py`

**Step 1: Read current API implementation**

```bash
cat api/prompt_improver_api.py
```

**Step 2: Add imports at top**

```python
# api/prompt_improver_api.py
# Add to existing imports
import time
from hemdov.interfaces import container
from hemdov.infrastructure.config import Settings
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from api.circuit_breaker import CircuitBreaker

# Circuit breaker instance
_circuit_breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

# Repository getter with circuit breaker
async def get_repository(settings: Settings) -> Optional[PromptRepository]:
    """Get repository instance with circuit breaker protection."""
    if not settings.SQLITE_ENABLED:
        return None

    if not await _circuit_breaker.should_attempt():
        return None

    # Get or create repository from container
    try:
        return container.get(PromptRepository)
    except ValueError:
        # Not registered, register it now
        repo = SQLitePromptRepository(settings)
        container.register(PromptRepository, repo)

        # Register cleanup hook
        async def cleanup():
            await repo.close()

        container._cleanup_hooks.append(cleanup)

        return repo
```

**Step 3: Modify improve_prompt endpoint**

```python
# api/prompt_improver_api.py
# Replace the existing improve_prompt function with this version

@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    Now with async SQLite persistence (if enabled) and graceful degradation.
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400, detail="Idea must be at least 5 characters"
        )

    # Get settings
    settings = container.get(Settings)

    # Start timer for latency
    start_time = time.time()

    # Select module based on few-shot setting
    if settings.DSPY_FEWSHOT_ENABLED:
        improver = get_fewshot_improver(settings)
        backend = "few-shot"
    else:
        improver = get_prompt_improver(settings)
        backend = "zero-shot"

    # Execute prompt improvement
    try:
        result = improver(original_idea=request.idea, context=request.context)
    except Exception as e:
        logger.error(f"Prompt improvement failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Prompt improvement failed"
        )

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Build response
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

    # NEW: Persist to SQLite (async, non-blocking)
    await _save_history_async(
        settings=settings,
        request=request,
        response=response,
        latency_ms=latency_ms,
        backend=backend,
    )

    return response


async def _save_history_async(
    settings: Settings,
    request: ImprovePromptRequest,
    response: ImprovePromptResponse,
    latency_ms: int,
    backend: str,
):
    """
    Save prompt history asynchronously with circuit breaker protection.

    This runs in the background and doesn't block the API response.
    Failures are logged but don't affect the user experience.
    """
    repository = await get_repository(settings)

    if repository is None:
        return  # Persistence disabled or circuit breaker open

    try:
        # Create history entity
        history = PromptHistory(
            original_idea=request.idea,
            context=request.context or "",
            improved_prompt=response.improved_prompt,
            role=response.role,
            directive=response.directive,
            framework=response.framework,
            guardrails=response.guardrails,
            reasoning=response.reasoning,
            confidence=response.confidence,
            backend=backend,
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER,
            latency_ms=latency_ms,
        )

        # Save to database
        history_id = await repository.save(history)

        # Record success
        await _circuit_breaker.record_success()

        logger.debug(f"Saved prompt history (id={history_id}, latency={latency_ms}ms)")

    except Exception as e:
        # Record failure
        await _circuit_breaker.record_failure()

        # Log error but don't fail the request
        logger.error(f"Failed to save prompt history: {e}", exc_info=True)
```

**Step 3: Verify syntax**

```bash
python -c "import api.prompt_improver_api; print('API module loads OK')"
```
Expected: "API module loads OK"

**Step 4: Commit**

```bash
git add api/prompt_improver_api.py
git commit -m "feat(api): integrate SQLite persistence with circuit breaker"
```

---

## Phase 5: Testing (60 min)

### Task 5.1: Write Repository Unit Tests

**Files:**
- Modify: `tests/test_sqlite_prompt_repository.py`

**Step 1: Write tests**

```python
# tests/test_sqlite_prompt_repository.py
import pytest
from pathlib import Path
from datetime import datetime

from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository


@pytest.fixture
async def repository(temp_db_path, settings):
    """Provide repository instance with test database."""
    settings.SQLITE_DB_PATH = temp_db_path
    repo = SQLitePromptRepository(settings)
    yield repo
    await repo.close()


@pytest.fixture
def settings():
    """Provide test settings."""
    return Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_RETENTION_DAYS=30,
    )


@pytest.mark.asyncio
async def test_save_prompt_history(repository):
    """Test saving a prompt history record."""
    history = PromptHistory(
        original_idea="test idea",
        context="test context",
        improved_prompt="improved test",
        role="AI Assistant",
        directive="Help with task",
        framework="chain-of-thought",
        guardrails=["be helpful", "be concise"],
        confidence=0.9,
        backend="zero-shot",
        model="test-model",
        provider="test-provider",
        latency_ms=1000,
    )

    history_id = await repository.save(history)

    assert history_id > 0
    assert history.id == history_id


@pytest.mark.asyncio
async def test_find_by_id(repository):
    """Test finding a prompt history by ID."""
    history = PromptHistory(
        original_idea="test idea",
        context="",
        improved_prompt="improved",
        role="AI",
        directive="Do task",
        framework="chain-of-thought",
        guardrails=["be nice"],
        backend="zero-shot",
        model="test",
        provider="test",
        latency_ms=500,
    )

    history_id = await repository.save(history)

    # Get entity with ID
    history_with_id = PromptHistory(
        **history.__dict__,
        id=history_id,
    )

    found = await repository.find_by_id(history_id)
    assert found is not None
    assert found.original_idea == "test idea"


@pytest.mark.asyncio
async def test_find_recent(repository):
    """Test finding recent prompts."""
    # Save 3 prompts
    for i in range(3):
        history = PromptHistory(
            original_idea=f"idea {i}",
            context="",
            improved_prompt=f"improved {i}",
            role="AI",
            directive=f"Task {i}",
            framework="chain-of-thought",
            guardrails=[f"rule {i}"],
            backend="zero-shot",
            model="test",
            provider="test",
            latency_ms=100 * i,
        )
        await repository.save(history)

    # Find recent
    recent = await repository.find_recent(limit=2)
    assert len(recent) == 2

    # Should be in reverse chronological order
    assert recent[0].original_idea == "idea 2"
    assert recent[1].original_idea == "idea 1"


@pytest.mark.asyncio
async def test_delete_old_records(repository):
    """Test deleting old records."""
    # Save a record with old timestamp
    old_history = PromptHistory(
        original_idea="old idea",
        context="",
        improved_prompt="old improved",
        role="AI",
        directive="Old task",
        framework="chain-of-thought",
        guardrails=["old rule"],
        backend="zero-shot",
        model="test",
        provider="test",
        latency_ms=100,
        created_at="2024-01-01T00:00:00",
    )
    await repository.save(old_history)

    # Save current record
    new_history = PromptHistory(
        original_idea="new idea",
        context="",
        improved_prompt="new improved",
        role="AI",
        directive="New task",
        framework="chain-of-thought",
        guardrails=["new rule"],
        backend="zero-shot",
        model="test",
        provider="test",
        latency_ms=100,
    )
    await repository.save(new_history)

    # Delete records older than 30 days
    deleted = await repository.delete_old_records(30)

    assert deleted == 1

    # Verify only new record remains
    recent = await repository.find_recent()
    assert len(recent) == 1
    assert recent[0].original_idea == "new idea"


@pytest.mark.asyncio
async def test_quality_score_calculation():
    """Test quality score property calculation."""
    history = PromptHistory(
        original_idea="test",
        context="",
        improved_prompt="test improved",
        role="AI",
        directive="Test",
        framework="chain-of-thought",
        guardrails=["rule1"],
        confidence=0.9,
        backend="zero-shot",
        model="test",
        provider="test",
        latency_ms=2000,  # 0.2 penalty
    )

    # Expected: 0.9 - (2000/10000) = 0.9 - 0.2 = 0.7
    assert history.quality_score == pytest.approx(0.7, rel=0.01)


@pytest.mark.asyncio
async def test_validation_empty_original_idea():
    """Test that empty original_idea raises error."""
    with pytest.raises(ValueError, match="original_idea cannot be empty"):
        PromptHistory(
            original_idea="",  # Invalid
            context="",
            improved_prompt="test",
            role="AI",
            directive="Test",
            framework="chain-of-thought",
            guardrails=["rule1"],
            backend="zero-shot",
            model="test",
            provider="test",
        )


@pytest.mark.asyncio
async def test_validation_invalid_confidence():
    """Test that invalid confidence raises error."""
    with pytest.raises(ValueError, match="Confidence must be 0-1"):
        PromptHistory(
            original_idea="test",
            context="",
            improved_prompt="test",
            role="AI",
            directive="Test",
            framework="chain-of-thought",
            guardrails=["rule1"],
            confidence=1.5,  # Invalid
            backend="zero-shot",
            model="test",
            provider="test",
        )
```

**Step 2: Run tests**

```bash
pytest tests/test_sqlite_prompt_repository.py -v
```
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_sqlite_prompt_repository.py
git commit -m "test: add repository unit tests"
```

### Task 5.2: Write API Integration Tests

**Files:**
- Create: `tests/test_api_integration.py`

**Step 1: Write integration tests**

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


def test_improve_prompt_success(client):
    """Test successful prompt improvement."""
    response = client.post(
        "/api/v1/improve-prompt",
        json={"idea": "Create a todo app", "context": "productivity"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "improved_prompt" in data
    assert "role" in data
    assert "directive" in data
    assert "framework" in data
    assert "guardrails" in data
    assert isinstance(data["guardrails"], list)


def test_improve_prompt_validation_error(client):
    """Test that short idea returns 400 error."""
    response = client.post(
        "/api/v1/improve-prompt",
        json={"idea": "hi"}  # Too short
    )

    assert response.status_code == 400


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"


def test_improve_prompt_with_persistence_disabled(client, monkeypatch):
    """Test that API works even when persistence is disabled."""
    # Disable persistence via environment
    monkeypatch.setenv("SQLITE_ENABLED", "false")

    # Reload settings
    from hemdov.infrastructure.config import settings
    from importlib import reload
    import hemdov.infrastructure.config as config_module
    reload(config_module)

    response = client.post(
        "/api/v1/improve-prompt",
        json={"idea": "test idea for persistence disabled"}
    )

    # API should still work even without persistence
    assert response.status_code == 200
```

**Step 2: Run tests**

```bash
pytest tests/test_api_integration.py -v
```
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_api_integration.py
git commit -m "test: add API integration tests"
```

---

## Phase 6: Configuration and Documentation (30 min)

### Task 6.1: Update .env.example

**Files:**
- Modify: `.env.example`

**Step 1: Add SQLite configuration section**

```bash
# Add to .env.example after existing LLM configuration

# SQLite Persistence Configuration
SQLITE_ENABLED=true                      # Master switch for prompt history
SQLITE_DB_PATH=data/prompt_history.db    # Database file location
SQLITE_POOL_SIZE=1                       # Connection pool size (SQLite: 1 is optimal)
SQLITE_RETENTION_DAYS=30                 # Auto-delete records older than N days
SQLITE_AUTO_CLEANUP=true                 # Run cleanup on startup
SQLITE_WAL_MODE=true                     # Write-Ahead Logging for better concurrency
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: add SQLite configuration to .env.example"
```

### Task 6.2: Update main.py for Cleanup

**Files:**
- Modify: `main.py`

**Step 1: Modify lifespan to include cleanup**

```python
# main.py
# Modify the lifespan function (around line 101)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize DSPy LM and cleanup resources."""
    global lm

    # ... existing LM initialization code ...

    yield

    # NEW: Cleanup on shutdown
    logger.info("Shutting down...")
    await container.shutdown()  # Cleanup repository connections
    logger.info("DSPy backend shutdown complete")
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "refactor(main): add container cleanup on shutdown"
```

---

## Phase 7: Verification and Deployment (30 min)

### Task 7.1: Manual Testing

**Step 1: Start backend**

```bash
# Activate venv
source .venv/bin/activate

# Start backend
python main.py
```

**Step 2: Test health check**

```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy","provider":"anthropic","model":"claude-haiku-4-5-20251001",...}`

**Step 3: Test prompt improvement**

```bash
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "Design a REST API for user management"}'
```

**Step 4: Verify persistence**

```bash
# Check database was created
ls -la data/prompt_history.db

# Query database
sqlite3 data/prompt_history.db "SELECT COUNT(*) FROM prompt_history;"
```
Expected: Count > 0

**Step 5: Test circuit breaker**

```bash
# Stop backend, delete DB, start again
# This should trigger circuit breaker after failed saves
rm data/prompt_history.db
python main.py

# Try improving prompts 5+ times
# Circuit breaker should trip and stop trying to save
# Check logs for "Circuit breaker tripped"
```

### Task 7.2: Final Commit

```bash
git add docs/plans/2026-01-04-sqlite-persistence-implementation.md
git commit -m "docs: add SQLite persistence implementation plan"
```

---

## Summary

**Total Estimated Time:** 6-7 hours

**Critical Files Modified:**
- `requirements.txt` - Add aiosqlite
- `hemdov/interfaces.py` - Factory pattern + lifecycle
- `hemdov/domain/entities/prompt_history.py` - NEW
- `hemdov/domain/repositories/prompt_repository.py` - NEW
- `hemdov/infrastructure/config/__init__.py` - SQLite settings
- `hemdov/infrastructure/persistence/sqlite_prompt_repository.py` - NEW
- `api/circuit_breaker.py` - NEW
- `api/prompt_improver_api.py` - Persistence integration
- `main.py` - Cleanup hook
- `.env.example` - Documentation

**Key Features Delivered:**
✅ Async SQLite via aiosqlite (non-blocking)
✅ Circuit breaker for graceful degradation
✅ Frozen dataclasses for domain entities
✅ Repository pattern with clean architecture
✅ Connection pooling and lifecycle management
✅ Comprehensive test coverage
✅ Feature flag for easy disable
