# SQLite Persistence - Quick Implementation Guide

This guide provides step-by-step instructions to implement SQLite persistence for the DSPy Prompt Improver project.

## Prerequisites

- Python 3.14+
- Existing project at `/Users/felipe_gonzalez/Developer/raycast_ext`
- SQLite (comes with Python standard library)

---

## Step 1: Install Dependencies

Add to `/Users/felipe_gonzalez/Developer/raycast_ext/requirements.txt`:

```txt
# Existing dependencies...
dspy-ai>=3.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
litellm>=1.0.0
python-dotenv>=1.0.0
requests>=2.32.0
pytest>=7.4.0
pytest-asyncio>=0.21.0

# NEW: SQLite async support
aiosqlite>=0.19.0
```

Install:

```bash
pip install aiosqlite>=0.19.0
```

---

## Step 2: Create Domain Layer

### 2.1 Create Domain Entities

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/__init__.py`:

```python
"""HemDov Domain Entities."""

from hemdov.domain.entities.prompt_history import PromptHistory, BackendType

__all__ = ["PromptHistory", "BackendType"]
```

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/prompt_history.py`:

```python
"""Domain entity for prompt history."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class BackendType(str, Enum):
    """Backend type for prompt improvement."""
    ZERO_SHOT = "zero-shot"
    FEW_SHOT = "few-shot"


@dataclass(frozen=True)
class PromptHistory:
    """
    Domain entity representing a prompt improvement event.

    Immutable value object with business logic.
    """
    # Core identifiers
    id: Optional[int]
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
        latency_penalty = min((self.latency_ms or 0) / 10000, 0.3)
        return max(0.0, min(1.0, conf_score - latency_penalty))
```

### 2.2 Create Repository Interface

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/repositories/__init__.py`:

```python
"""HemDov Domain Repository Interfaces."""

from hemdov.domain.repositories.prompt_repository import (
    PromptRepository,
    RepositoryError,
    RepositoryConnectionError,
    RepositoryConstraintError
)

__all__ = [
    "PromptRepository",
    "RepositoryError",
    "RepositoryConnectionError",
    "RepositoryConstraintError"
]
```

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/repositories/prompt_repository.py`:

```python
"""Repository interface for prompt history persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from hemdov.domain.entities.prompt_history import PromptHistory, BackendType


class PromptRepository(ABC):
    """Repository interface for prompt history persistence."""

    @abstractmethod
    async def save(self, history: PromptHistory) -> PromptHistory:
        """Save a prompt history record."""
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
        """Get usage statistics."""
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

## Step 3: Create Infrastructure Layer

### 3.1 Update Configuration

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/config/__init__.py`:

```python
"""HemDov Infrastructure Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Global settings for HemDov DSPy integration."""

    # LLM Provider Settings
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M"
    LLM_BASE_URL: Optional[str] = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HEMDOV_ANTHROPIC_API_KEY: Optional[str] = None

    # DSPy Settings
    DSPY_MAX_BOOTSTRAPPED_DEMOS: int = 5
    DSPY_MAX_LABELED_DEMOS: int = 3
    DSPY_COMPILED_PATH: Optional[str] = None

    # Few-Shot Settings
    DSPY_FEWSHOT_ENABLED: bool = False
    DSPY_FEWSHOT_TRAINSET_PATH: Optional[str] = None
    DSPY_FEWSHOT_K: int = 3
    DSPY_FEWSHOT_COMPILED_PATH: Optional[str] = "models/prompt_improver_fewshot.json"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Quality Settings
    MIN_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_LATENCY_MS: int = 30000

    # NEW: SQLite Persistence Settings
    SQLITE_ENABLED: bool = True
    SQLITE_DB_PATH: str = "data/prompt_history.db"
    SQLITE_POOL_SIZE: int = 1
    SQLITE_RETENTION_DAYS: int = 30
    SQLITE_AUTO_CLEANUP: bool = True
    SQLITE_ASYNC_ENABLED: bool = True
    SQLITE_WAL_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
```

### 3.2 Create SQLite Implementation

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/__init__.py`:

```python
"""HemDov Infrastructure Persistence Layer."""

from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository

__all__ = ["SQLitePromptRepository"]
```

Create `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/sqlite_prompt_repository.py`:

```python
"""SQLite implementation of PromptRepository."""

See the full implementation in the analysis document at:
/docs/analysis/sqlite-persistence-analysis.md (Section 1, Component 3)

Copy the code from there. It's too long to include here.
```

---

## Step 4: Update Dependency Injection

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/interfaces.py`:

```python
"""HemDov Dependency Injection Container"""

from typing import Dict, Type, TypeVar, Any, Callable
from hemdov.infrastructure.config import settings

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
            self._singletons[interface] = instance
            del self._factories[interface]
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

---

## Step 5: Update Application Initialization

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/main.py`, add to the `lifespan` function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize DSPy LM and repository."""
    global lm

    # Initialize DSPy with appropriate LM
    # ... existing LM initialization code ...
    # (Keep all the existing provider initialization logic)

    logger.info(f"DSPy configured with {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    # NEW: Initialize repository if persistence is enabled
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

        # Create data directory if it doesn't exist
        from pathlib import Path
        db_path = Path(settings.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Run cleanup if enabled
        if settings.SQLITE_AUTO_CLEANUP:
            try:
                repo = container.get(PromptRepository)
                deleted = await repo.delete_old(days=settings.SQLITE_RETENTION_DAYS)
                logger.info(f"Auto-cleanup: deleted {deleted} old records")
            except Exception as e:
                logger.warning(f"Auto-cleanup failed: {e}")
    else:
        logger.info("SQLite persistence disabled (SQLITE_ENABLED=False)")

    yield

    logger.info("Shutting down DSPy backend...")
```

---

## Step 6: Update API Endpoint

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py`:

```python
"""FastAPI endpoint for Prompt Improver with persistence."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import dspy
import asyncio
import time
from datetime import datetime
from typing import Optional

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings
from hemdov.domain.repositories.prompt_repository import (
    PromptRepository,
    RepositoryError
)
from hemdov.domain.entities.prompt_history import PromptHistory, BackendType
from hemdov.interfaces import container

router = APIRouter(prefix="/api/v1", tags=["prompts"])

# ... existing request/response models ...

# Circuit breaker state
_repository_failure_count = 0
_MAX_REPOSITORY_FAILURES = 5
_REPOSITORY_DISABLED_UNTIL = None


def get_settings() -> Settings:
    """Dependency injection for settings."""
    return container.get(Settings)


def get_repository() -> Optional[PromptRepository]:
    """
    Dependency injection for repository with circuit breaker.

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


# ... keep existing get_prompt_improver and get_fewshot_improver functions ...


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
        import logging
        logger = logging.getLogger(__name__)
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

    import logging
    logger = logging.getLogger(__name__)

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

## Step 7: Add Health Check Endpoint

Add to `/Users/felipe_gonzalez/Developer/raycast_ext/main.py`:

```python
@app.get("/health/repository")
async def repository_health_check():
    """Check repository health."""
    from hemdov.domain.repositories.prompt_repository import PromptRepository

    settings = container.get(Settings)

    if not settings.SQLITE_ENABLED:
        return {
            "status": "disabled",
            "reason": "SQLITE_ENABLED=False"
        }

    try:
        repository = container.get(PromptRepository)
        stats = await repository.get_statistics()
        return {
            "status": "healthy",
            "total_records": stats["total_count"],
            "database_path": settings.SQLITE_DB_PATH,
            "average_confidence": stats["average_confidence"],
            "average_latency_ms": stats["average_latency_ms"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## Step 8: Update .env

Add to `/Users/felipe_gonzalez/Developer/raycast_ext/.env`:

```bash
# SQLite Persistence Configuration
SQLITE_ENABLED=true                      # Master switch
SQLITE_DB_PATH=data/prompt_history.db    # Database location
SQLITE_POOL_SIZE=1                       # Connection pool size
SQLITE_RETENTION_DAYS=30                 # Auto-delete old records
SQLITE_AUTO_CLEANUP=true                 # Run cleanup on startup
SQLITE_ASYNC_ENABLED=true                # Use async operations
SQLITE_WAL_MODE=true                     # Write-Ahead Logging
```

---

## Step 9: Create Data Directory

```bash
mkdir -p /Users/felipe_gonzalez/Developer/raycast_ext/data
```

---

## Step 10: Test the Implementation

### 10.1 Start the Server

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
python main.py
```

### 10.2 Test Health Check

```bash
curl http://localhost:8000/health/repository
```

Expected response:
```json
{
  "status": "healthy",
  "total_records": 0,
  "database_path": "data/prompt_history.db",
  "average_confidence": 0.0,
  "average_latency_ms": 0.0
}
```

### 10.3 Test Prompt Improvement

```bash
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Design a REST API for user management",
    "context": "FastAPI backend with PostgreSQL"
  }'
```

### 10.4 Verify Persistence

```bash
# Check database was created
ls -lh /Users/felipe_gonzalez/Developer/raycast_ext/data/

# Query the database
sqlite3 /Users/felipe_gonzalez/Developer/raycast_ext/data/prompt_history.db \
  "SELECT COUNT(*) FROM prompt_history;"
```

### 10.5 Test Graceful Degradation

```bash
# Disable persistence
export SQLITE_ENABLED=false
python main.py

# API should still work, just without persistence
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "Test prompt"}'
```

---

## Step 11: Verify Schema

```bash
sqlite3 /Users/felipe_gonzalez/Developer/raycast_ext/data/prompt_history.db \
  ".schema prompt_history"
```

Expected output:
```sql
CREATE TABLE prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    original_idea TEXT NOT NULL,
    context TEXT DEFAULT '',
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
);
```

---

## Troubleshooting

### Issue: "No module named 'aiosqlite'"

**Solution:**
```bash
pip install aiosqlite
```

### Issue: "Database is locked"

**Solution:** WAL mode should handle this, but if it persists:
```bash
sqlite3 data/prompt_history.db "PRAGMA journal_mode=WAL;"
```

### Issue: "Permission denied" creating database

**Solution:**
```bash
mkdir -p data
chmod 755 data
```

### Issue: Circuit breaker keeps tripping

**Solution:** Check database disk space and permissions:
```bash
df -h
ls -lh data/
```

---

## Next Steps

1. **Add unit tests** for repository layer
2. **Add integration tests** for API endpoints
3. **Set up monitoring** (Prometheus/Grafana)
4. **Configure backups** for the database
5. **Performance testing** with load testing tools

---

## Summary

You now have:
- ✅ Hexagonal architecture with clean separation of concerns
- ✅ Async SQLite repository with `aiosqlite`
- ✅ Dependency injection via extended HemDov Container
- ✅ Graceful degradation with circuit breaker
- ✅ Configuration via `.env`
- ✅ Health check endpoint
- ✅ Error handling and logging
- ✅ Data retention with auto-cleanup

The API continues to work even if the repository fails, ensuring high availability.
