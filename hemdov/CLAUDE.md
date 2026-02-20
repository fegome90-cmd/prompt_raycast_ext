# Backend - DSPy Prompt Improver

> Python backend with hexagonal architecture for systematic prompt engineering

## Quick Reference

```bash
# From project root
make dev             # Start backend (uvicorn)
make health          # Check health
make test            # pytest
make eval            # Quality gates
```

## Architecture - Hexagonal (Ports & Adapters)

### Core Principle
**Domain layer is pure** — No IO, no async, no side effects in `hemdov/domain/`

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (FastAPI endpoints)                          │
│  - HTTP request/response handling                       │
│  - Error mapping to status codes                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Domain Layer (Pure business logic)                     │
│  - DSPy signatures and modules                          │
│  - Port interfaces (abstract)                           │
│  - Domain errors and metrics                            │
└─────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────┐
│  Infrastructure Layer (Technical implementation)        │
│  - Adapters for external services                       │
│  - Database persistence                                 │
│  - Configuration and feature flags                      │
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
hemdov/
├── domain/                      # PURE LAYER - No IO, no async
│   ├── dspy_modules/            # DSPy signatures
│   │   ├── prompt_improver.py   # Core PromptImproverSignature
│   │   └── augmenter_sig.py     # Additional DSPy modules
│   ├── ports/                   # Abstract interfaces (contracts)
│   │   ├── cache_port.py        # Caching interface
│   │   ├── context_loader.py    # Context loading interface
│   │   ├── metrics_port.py      # Metrics collection interface
│   │   ├── priority_classifier.py  # Priority classification
│   │   └── vectorizer_port.py   # Vectorization interface
│   ├── repositories/            # Repository interfaces
│   │   └── prompt_repository.py # Data persistence contract
│   ├── errors/                  # Domain-specific errors
│   ├── metrics/                 # Business metrics
│   │   ├── evaluators.py        # Quality evaluation functions
│   │   ├── analyzers.py         # Metrics analysis
│   │   ├── registry.py          # Metrics registry
│   │   └── dimensions.py        # Metric dimensions
│   ├── dto/                     # Data Transfer Objects
│   │   └── nlac_models.py       # NLaC-related DTOs
│   └── types/                   # Core domain types
│       └── result.py            # Result wrapper types
│
├── infrastructure/              # Technical implementation
│   ├── adapters/                # Port implementations
│   │   ├── litellm_dspy_adapter.py   # LLM adapter
│   │   └── parallel_loader.py        # Data loading utilities
│   ├── config/                  # Configuration
│   │   ├── feature_flags.py     # Feature toggles
│   │   └── __init__.py          # Settings (Pydantic)
│   ├── persistence/             # Data persistence
│   │   ├── metrics_repository.py    # Metrics storage
│   │   ├── sqlite_prompt_repository.py  # SQLite implementation
│   │   └── migrations.py        # Database migrations
│   ├── repositories/            # Repository implementations
│   │   └── catalog_repository.py     # Catalog data
│   └── errors/                  # Error infrastructure
│       ├── mapper.py            # Exception mapping
│       └── ids.py               # Error identifiers
│
└── interfaces.py                # Dependency injection container
```

## Critical Rules

| Rule | Why |
|------|-----|
| **Domain is pure** | No IO, no async, no side effects in `hemdov/domain/` |
| **Never use `except Exception:`** | Catch specific errors (ConnectionError, TimeoutError) |
| **Functions with `await` must be `async`** | Mark function `async` if it uses await |
| **Mocks only in tests** | Never mock code in production paths |
| **Depend on ports, not implementations** | Use interfaces from domain layer |

## DSPy Patterns

### Core Signature
```python
from dspy import ChainOfThought, Signature

class PromptImproverSignature(Signature):
    """Improve a prompt using DSPy few-shot learning."""
    input_prompt = InputField(desc="Original prompt to improve")
    context = InputField(desc="Additional context", default="")
    output_prompt = OutputField(desc="Improved prompt")
```

### Module Composition
```python
# Domain layer - pure function
def improve_prompt(prompt: str, context: str) -> str:
    module = ChainOfThought(PromptImproverSignature)
    result = module(input_prompt=prompt, context=context)
    return result.output_prompt
```

### Few-Shot Learning
```python
from dspy import BootstrapFewShot

optimizer = BootstrapFewShot(
    metric=validation_fn,
    max_labeled_demos=3,
    max_rounds=1
)
optimized_module = optimizer.compile(module, trainset=trainset)
```

## Exception Handling

### Specific Exception Types

**Never catch:**
- `KeyboardInterrupt` — Let it propagate
- `SystemExit` — Let it propagate
- `Exception` — Too broad, use specific types

**Use specific types:**

```python
# Client errors (400)
raise ValueError("Invalid data format")
raise TypeError("Expected string, got int")
raise KeyError("Missing required field")

# Service errors (503)
raise ConnectionError("Database unavailable")
raise OSError("File system error")
raise TimeoutError("Query timeout")

# Internal errors (500)
raise RuntimeError("Unexpected bug")
raise MemoryError("Out of memory")
```

### Error Mapping (`infrastructure/errors/mapper.py`)
```python
def map_exception_to_status(error: Exception) -> int:
    if isinstance(error, (ValueError, TypeError, KeyError)):
        return 400
    if isinstance(error, (ConnectionError, OSError, TimeoutError)):
        return 503
    return 500
```

### Logging with Context
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = process_data(data)
except ValueError as e:
    logger.error(
        "Validation failed",
        extra={
            "error_type": type(e).__name__,
            "error_message": str(e),
            "input_data": data,
        }
    )
    raise
```

## Dependency Injection

### Container (`interfaces.py`)
```python
class Container:
    def __init__(self):
        self._services = {}
        self._factories = {}
        self._cleanup_hooks = []

    def register(self, interface: type, implementation: type):
        self._services[interface] = implementation

    def resolve(self, interface: type):
        if interface in self._factories:
            return self._factories[interface]()
        return self._services.get(interface)

    def add_cleanup_hook(self, hook: Callable):
        self._cleanup_hooks.append(hook)

    async def cleanup(self):
        for hook in self._cleanup_hooks:
            await hook()
```

## Configuration

### Environment Variables
```bash
# LLM Provider
LLM_PROVIDER=anthropic  # anthropic, ollama, gemini, openai
LLM_MODEL=claude-haiku-4-5-20251001

# API Keys
HEMDOV_ANTHROPIC_API_KEY=your_key_here

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### Pydantic Settings
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "anthropic"
    llm_model: str = "claude-haiku-4-5-20251001"
    anthropic_api_key: str

    class Config:
        env_file = ".env"
        env_prefix = "HEMDOV_"
```

### Feature Flags
```python
# infrastructure/config/feature_flags.py
feature_flags = {
    "knn_provider_enabled": True,
    "complex_strategy_enabled": True,
    "metrics_enabled": True,
}
```

## Testing

### pytest Setup
```python
# tests/conftest.py
import pytest

@pytest.fixture
async def container():
    container = Container()
    yield container
    await container.cleanup()

@pytest.fixture
def mock_llm(monkeypatch):
    monkeypatch.setattr("litellm.completion", mock_completion)
```

### Test Patterns
```python
# Unit tests - domain layer only
def test_prompt_improver_signature():
    sig = PromptImproverSignature()
    assert hasattr(sig, "input_prompt")
    assert hasattr(sig, "output_prompt")

# Integration tests - with real dependencies
@pytest.mark.asyncio
async def test_api_endpoint(container):
    response = await client.post("/improve", json={"prompt": "test"})
    assert response.status_code == 200
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_improve_prompt_always_returns_string(prompt):
    result = improve_prompt(prompt, "")
    assert isinstance(result, str)
    assert len(result) > 0
```

## Metrics & Quality Gates

### Metrics Registry
```python
# domain/metrics/registry.py
class MetricsRegistry:
    def record(self, metric: Metric):
        self.metrics.append(metric)

    def get_metrics(self, filter: MetricFilter) -> List[Metric]:
        return [m for m in self.metrics if filter.matches(m)]
```

### Quality Gates
```python
# Target metrics
JSON_VALID_PASS_1_TARGET = 0.54  # 54%
COPYABLE_RATE_TARGET = 0.54      # 54%
LATENCY_P95_TARGET = 12.0        # seconds

# Evaluation
def evaluate_quality(result: ImprovementResult) -> bool:
    return (
        result.json_valid_pass_1 >= JSON_VALID_PASS_1_TARGET
        and result.copyable_rate >= COPYABLE_RATE_TARGET
        and result.latency_p95 <= LATENCY_P95_TARGET
    )
```

## Persistence

### SQLite Repository
```python
# infrastructure/persistence/sqlite_prompt_repository.py
import aiosqlite

class SQLitePromptRepository:
    async def save(self, prompt: Prompt) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO prompts (input, output) VALUES (?, ?)",
                (prompt.input, prompt.output)
            )
            await db.commit()
```

### Migrations
```python
# infrastructure/persistence/migrations.py
async def migrate(db: aiosqlite.Connection):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            input TEXT NOT NULL,
            output TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

## Documentation

### Backend Documentation (`docs/backend/`)
- `README.md` — Complete architecture overview
- `quickstart.md` — Fast setup path
- `implementation-summary.md` — Detailed walkthrough
- `status.md` — Current implementation status
- `verification.md` — Testing strategy
- `files-created.md` — Complete file inventory

## Source of Truth

- `docs/backend/README.md` — DSPy architecture
- `hemdov/interfaces.py` — Dependency injection
- `hemdov/domain/` — Pure business logic
- `api/` — FastAPI endpoints
