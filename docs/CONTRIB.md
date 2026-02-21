# Contributing Guide

> Development workflow for DSPy Prompt Improver

**Last Updated:** 2026-02-21

## Quick Start

```bash
# 1. Clone and setup
make setup          # Install Python deps via uv
make env            # Create .env from .env.example

# 2. Configure environment
# Edit .env with your API keys (see Environment Setup below)

# 3. Start backend
make dev            # Start backend in background
make health         # Verify backend is running

# 4. Start frontend
cd dashboard && npm run dev
```

## Architecture

This is a full-stack project:
- **Backend**: Python/FastAPI with DSPy framework (hexagonal architecture)
- **Frontend**: TypeScript/React Raycast extension

```
hemdov/domain/ (DSPy modules) -> FastAPI -> LLM providers
dashboard/src/ (React) -> HTTP -> Backend
```

## Makefile Commands Reference

| Command | Description |
|---------|-------------|
| `make setup` | Install Python dependencies via uv |
| `make env` | Create .env from .env.example |
| `make backend` | Start DSPy backend server (foreground) |
| `make dev` | Start backend in background (dev mode) |
| `make stop` | Stop background backend |
| `make restart` | Restart background backend |
| `make health` | Check backend health |
| `make logs` | Show backend logs (tail -f) |
| `make status` | Show backend status |
| `make ray-check` | Check localhost permission in package.json |
| `make ray-dev` | Start Raycast dev server (with pre-check) |
| `make ray-status` | Show Raycast dev server status |
| `make ray-logs` | Show Raycast dev server logs |
| `make dataset` | Generate fewshot training dataset |
| `make normalize` | Normalize ComponentCatalog |
| `make merge` | Merge training datasets |
| `make regen-all` | Regenerate all datasets |
| `make test` | Run Python tests |
| `make test-fewshot` | Test few-shot compilation |
| `make test-backend` | Test backend integration |
| `make eval` | Run quality gates evaluation (5 cases) |
| `make eval-full` | Run full evaluation (30 cases) |
| `make clean` | Clean generated files |

## NPM Scripts Reference (dashboard/)

| Script | Description |
|--------|-------------|
| `npm run setup` | Run setup.sh for initial setup |
| `npm run build` | Build for production (ray build -e dist) |
| `npm run dev` | Start Raycast development mode |
| `npm run lint` | Run ESLint checks |
| `npm run fix-lint` | Auto-fix ESLint issues |
| `npm run publish` | Publish to Raycast Marketplace |
| `npm run eval` | Run TypeScript evaluator |
| `npm run test` | Run Vitest tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run test:e2e` | Run E2E tests |

## Environment Setup

Copy `.env.example` to `.env` and configure:

### LLM Provider Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use | `anthropic` |
| `LLM_MODEL` | Model identifier | `claude-haiku-4-5-20251001` |
| `LLM_BASE_URL` | API base URL | `https://api.anthropic.com` |

**Supported Providers:**
- `anthropic` - Claude models (recommended: Haiku 4.5)
- `ollama` - Local models
- `gemini` - Google Gemini
- `deepseek` - DeepSeek models
- `openai` - GPT models

### API Keys

| Variable | Required When |
|----------|---------------|
| `ANTHROPIC_API_KEY` | `LLM_PROVIDER=anthropic` |
| `HEMDOV_ANTHROPIC_API_KEY` | Alternative to ANTHROPIC_API_KEY |
| `DEEPSEEK_API_KEY` | `LLM_PROVIDER=deepseek` |
| `GEMINI_API_KEY` | `LLM_PROVIDER=gemini` |
| `OPENAI_API_KEY` | `LLM_PROVIDER=openai` |
| `LANGCHAIN_API_KEY` | LangChain Hub integration |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing |
| `LLM_API_KEY` | Generic fallback for any provider |

### SQLite Persistence

| Variable | Description | Default |
|----------|-------------|---------|
| `SQLITE_ENABLED` | Enable prompt history | `true` |
| `SQLITE_DB_PATH` | Database file path | `data/prompt_history.db` |
| `SQLITE_POOL_SIZE` | Connection pool size | `1` |
| `SQLITE_RETENTION_DAYS` | Auto-delete after N days | `30` |
| `SQLITE_AUTO_CLEANUP` | Cleanup on startup | `true` |
| `SQLITE_WAL_MODE` | Write-Ahead Logging | `true` |

### DSPy Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_MAX_BOOTSTRAPPED_DEMOS` | Max few-shot examples | `5` |
| `DSPY_MAX_LABELED_DEMOS` | Max labeled examples | `3` |
| `DSPY_COMPILED_PATH` | Compiled model save path | (empty) |
| `USE_KNN_FEWSHOT` | Enable KNN few-shot | `true` |
| `DSPY_FEWSHOT_K` | KNN neighbors count | `3` |
| `DSPY_FEWSHOT_TRAINSET_PATH` | Training set path | `datasets/exports/unified-fewshot-pool.json` |
| `DSPY_FEWSHOT_COMPILED_PATH` | Compiled model path | `models/fewshot-compiled.json` |

### API Server

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Server host | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `API_RELOAD` | Enable auto-reload | `true` |
| `ANTHROPIC_TIMEOUT` | API timeout (seconds) | `120` |

### Quality Thresholds

| Variable | Description | Default |
|----------|-------------|---------|
| `MIN_CONFIDENCE_THRESHOLD` | Min confidence | `0.7` |
| `MAX_LATENCY_MS` | Max latency | `30000` |

## Development Workflow

### 1. Backend Development

```bash
# Start backend
make dev

# Run tests
make test

# Check logs
make logs

# Stop when done
make stop
```

### 2. Frontend Development

```bash
cd dashboard

# Run tests
npm test

# Start dev mode (requires Raycast)
npm run dev

# Type check
npx tsc --noEmit
```

### 3. Running Quality Gates

```bash
# Quick evaluation (5 cases)
make eval

# Full evaluation (30 cases)
make eval-full
```

## Quality Gates

| Metric | Target | Command |
|--------|--------|---------|
| JSON Valid Pass 1 | >=54% | `make eval` |
| Copyable Rate | >=54% | `make eval` |
| Latency P95 | <=12s | `make eval-full` |

## Critical Rules

| Rule | Why |
|------|-----|
| Domain layer is pure | No IO, no async, no side effects in `hemdov/domain/` |
| Never use `except Exception:` | Catch specific errors (ConnectionError, TimeoutError) |
| Log errors with context | Include exception type and message |
| Optional features degrade gracefully | Use degradation_flags in responses |
| Keep IntentType synced | Same enum values across TS/Python boundary |
| Mocks only in tests | Never mock code in production paths |
| Functions with await must be async | Mark function async if it uses await |

## Error Handling

### HTTP Status Code Mapping

| Status | When to Use | Exception Types |
|--------|-------------|-----------------|
| 400 | Invalid input | ValueError, TypeError, KeyError |
| 404 | Resource missing | (specific to resource) |
| 422 | Validation error | Pydantic ValidationError |
| 503 | Service unavailable | ConnectionError, OSError, TimeoutError |
| 504 | Gateway timeout | asyncio.TimeoutError |
| 500 | Internal error | RuntimeError, MemoryError |

## PM2 Services

| Port | Name | Type |
|------|------|------|
| 8000 | raycast-backend-8000 | FastAPI (Python) |

```bash
pm2 start ecosystem.config.cjs   # First time
pm2 start all                    # After first time
pm2 stop all / pm2 restart all
pm2 logs / pm2 status / pm2 monit
```

## References

- Backend Architecture: `docs/backend/README.md`
- API Error Handling: `docs/api-error-handling.md`
- Frontend Guide: `dashboard/CLAUDE.md`
- MCP Integration: `mcp-server/README.md`
