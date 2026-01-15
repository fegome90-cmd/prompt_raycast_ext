# DSPy Prompt Improver - Raycast Extension

> Transform rough prompts into SOTA prompts using DSPy few-shot learning + multiple LLM providers

## Quick Start

```bash
make setup          # Install deps (uv)
make dev            # Start backend in background
make health         # Check backend is running

cd dashboard && npm run dev   # Start Raycast frontend

make test           # Run Python tests
make eval           # Quality gates evaluation
```

## Architecture

**Full-stack:** Python backend (hexagonal architecture) + TypeScript frontend (Raycast extension)

- Backend: `hemdov/domain/` (DSPy modules) → FastAPI → LLM providers
- Frontend: `dashboard/` (React/TS) → HTTP → Backend
- See `docs/backend/README.md` for complete DSPy architecture

## Critical Rules

| Rule | Why |
|------|-----|
| Domain layer is pure | No IO, no async, no side effects in `hemdov/domain/` |
| Never use `except Exception:` | Catch specific errors (ConnectionError, TimeoutError) |
| Log errors with context | Include exception type and message (type, message) |
| Optional features degrade gracefully | Use degradation_flags in responses |
| Keep `IntentType` synced | Same enum values across TS/Python boundary |
| Mocks only in tests | Never mock code in production paths |
| Functions with `await` must be `async` | Mark function `async` if it uses await; callers must await |

## Configuration

**Backend (`.env`):**
- `LLM_PROVIDER`: anthropic, ollama, gemini, openai
- `LLM_MODEL`: claude-haiku-4-5-20251001, or your preferred model
- `HEMDOV_ANTHROPIC_API_KEY`: Your API key

**Frontend (`dashboard/package.json`):**
- `localhost: true` must be set for backend connection
- See Raycast API docs for extension configuration

## Quality Gates

| Metric | Target | Command |
|--------|--------|---------|
| JSON Valid Pass 1 | ≥54% | `make eval` |
| Copyable Rate | ≥54% | `make eval` |
| Latency P95 | ≤12s | `make eval-full` |

## Error Handling

### HTTP Status Code Mapping

| Status | When to Use | Exception Types |
|--------|-------------|-----------------|
| 400 | Invalid input | `ValueError`, `TypeError`, `KeyError` |
| 404 | Resource missing | (specific to resource) |
| 422 | Validation error | Pydantic `ValidationError` |
| 503 | Service unavailable | `ConnectionError`, `OSError`, `TimeoutError` |
| 504 | Gateway timeout | `asyncio.TimeoutError` |
| 500 | Internal error | `RuntimeError`, `MemoryError`, `AttributeError` |

### Specific Exception Types

**Client errors (400):**
- `ValueError` - Invalid data, bad format
- `TypeError` - Wrong data type
- `KeyError` - Missing dictionary keys
- `AttributeError` - Missing object attributes

**Service errors (503):**
- `ConnectionError` - Network/database unavailable
- `OSError` - File system errors
- `TimeoutError` - Query timeouts

**Internal errors (500):**
- `RuntimeError` - Unexpected bugs
- `MemoryError` - Out of memory
- `AttributeError` - Missing attributes in calculations

**Never catch:**
- `KeyboardInterrupt` - Let it propagate
- `SystemExit` - Let it propagate
- `Exception` - Too broad, use specific types

### Degradation Flags

Optional features can fail gracefully. Include `degradation_flags` in responses:

```python
degradation_flags = {
    "metrics_failed": bool,      # Metrics calculation failed
    "knn_disabled": bool,         # KNNProvider unavailable (NLaC mode)
    "complex_strategy_disabled": bool,  # ComplexStrategy unavailable (legacy)
}
```

### Documentation

See `docs/api-error-handling.md` for complete error handling patterns and examples.

## Source of Truth

- `docs/backend/README.md` - DSPy architecture
- `mcp-server/README.md` - MCP integration
- `Makefile` - All available commands (`make help`)
