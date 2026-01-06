# DSPy Prompt Improver - Raycast Extension

> Transform rough prompts into SOTA prompts using DSPy with few-shot learning + multiple LLM providers

## Project Overview

**What it does:**
- Takes raw user ideas (selection or clipboard)
- Improves them using DSPy with few-shot learning
- Returns structured, optimized prompts

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│  Raycast Frontend (React/TS)                        │
│  dashboard/src/promptify-quick.tsx                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│  FastAPI Backend (main.py)                          │
│  /api/v1/improve-prompt                             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  DSPy Domain (hexagonal architecture)               │
│  hemdov/domain/dspy_modules/prompt_improver.py      │
│  - FewShot learning with KNN                        │
│  - ComponentCatalog optimization                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  LLM Providers (infrastructure/adapters)            │
│  • DeepSeek (primary, temp=0.0)                     │
│  • Ollama (local, temp=0.1)                         │
│  • Gemini (cloud, temp=0.0)                         │
│  • OpenAI (cloud, temp=0.0)                         │
└─────────────────────────────────────────────────────┘
```

## Quick Start

**All commands use `make` - run `make help` for full list**

```bash
# Setup
make setup          # Install Python deps (uv)
make env            # Create .env from .env.example

# Development
make dev            # Start DSPy backend in background
make health         # Check backend health
make logs           # Tail backend logs
make stop           # Stop backend

# Raycast frontend
cd dashboard && npm run dev
```

## Key Directories

| Path | Purpose |
|------|---------|
| `hemdov/domain/` | DSPy modules (PromptImprover) |
| `hemdov/infrastructure/` | LLM adapters, config |
| `hemdov/interfaces.py` | Dependency injection container |
| `api/` | FastAPI endpoints |
| `dashboard/` | Raycast frontend (React/TS) |
| `scripts/data/` | Dataset generation & normalization |
| `scripts/eval/` | Quality gates evaluation |
| `models/` | Compiled DSPy models (.json) |

## LLM Configuration

**Configure in `.env`:**
```bash
LLM_PROVIDER=deepseek  # ollama, gemini, openai
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-...

# Temperature defaults (hardcoded in main.py)
# DeepSeek: 0.0 (critical for consistency)
# Ollama: 0.1 (local needs variability)
# Gemini/OpenAI: 0.0
```

**Why temp=0.0 for DeepSeek:** Maximum consistency in few-shot selection

## Makefile Commands

**Backend:**
```bash
make backend        # Start in foreground
make dev            # Start in background (for development)
make stop           # Stop background backend
make restart        # Restart backend
make health         # Health check
make logs           # Tail logs
make status         # Show status
```

**Dataset (Few-shot learning):**
```bash
make dataset        # Generate fewshot training dataset
make normalize      # Normalize ComponentCatalog
make merge          # Merge training datasets
make regen-all      # Regenerate all datasets
```

**Testing & Evaluation:**
```bash
make test           # Run Python tests (pytest)
make test-fewshot   # Test few-shot compilation
make test-backend   # Test backend integration
make eval           # Quality gates (5 cases)
make eval-full      # Full evaluation (30 cases)
```

## DSPy Architecture

**Hexagonal/Clean Architecture:**

```
hemdov/
├── domain/
│   └── dspy_modules/
│       └── prompt_improver.py    # DSPy PromptImprover module
├── infrastructure/
│   ├── adapters/
│   │   └── litellm_dspy_adapter_prompt.py  # LLM providers
│   └── config/
│       └── settings.py           # Pydantic settings
└── interfaces.py                 # DI container
```

**Key Files:**
- `main.py:76` - DSPy configuration with LM
- `hemdov/domain/dspy_modules/prompt_improver.py` - Core DSPy module
- `api/prompt_improver_api.py` - FastAPI router

## Quality Gates

**Evaluation scripts in `scripts/eval/`:**

| Metric | Target | Script |
|--------|--------|--------|
| JSON Valid Pass 1 | ≥54% | `compare_quality_gates.py` |
| Copyable Rate | ≥54% | `compare_quality_gates.py` |
| Latency P95 | ≤12s | `compare_quality_gates.py` |

**Run evaluation:**
```bash
make eval           # Quick (5 cases)
make eval-full      # Full (30 cases)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend not running | `make status` then `make dev` |
| DeepSeek API error | Check `DEEPSEEK_API_KEY` in `.env` |
| Port 8000 in use | Change `API_PORT` in `.env` |
| Few-shot not working | Run `make regen-all` to regenerate datasets |

## Documentation

- **Full Spanish Guide:** `.worktrees/dspy-pipeline/CLAUDE.md`
- **DSPy Backend:** `docs/backend/README.md`
- **MCP Integration:** `mcp-server/README.md`

## External References

- [DSPy](https://github.com/stanfordnlp/dspy)
- [DeepSeek API](https://platform.deepseek.com/)
- [Raycast API](https://developers.raycast.com)
