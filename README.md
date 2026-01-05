# Prompt Improver (DSPy)

> Transform rough prompts into SOTA prompts using DSPy with few-shot learning

## Overview

**Prompt Improver** is a Raycast extension that converts raw ideas (from selection or clipboard) into structured, production-ready prompts using DSPy with few-shot learning and multiple LLM providers.

### Key Features

- **🚀 Multiple LLM Providers**: Anthropic (Haiku, Sonnet, Opus), DeepSeek, OpenAI, Gemini, Ollama (local)
- **🧠 Few-Shot Learning**: KNN-based example selection for consistent, high-quality outputs
- **⚡ Fast & Reliable**: Anthropic Haiku 4.5 as default (~$0.08/1M tokens, <5s latency)
- **📊 Quality Tracking**: SQLite persistence with automatic history management
- **🔒 Type-Safe**: Full TypeScript implementation with Zod validation
- **🛡️ Resilient**: Circuit breaker pattern for graceful degradation

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Raycast Frontend (React/TS)                        │
│  dashboard/src/promptify-quick.tsx                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│  FastAPI Backend (main.py)                          │
│  /api/v1/improve-prompt                             │
│  • Circuit breaker for resilience                   │
│  • SQLite persistence (optional)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  DSPy Domain (hexagonal architecture)               │
│  hemdov/domain/dspy_modules/prompt_improver.py      │
│  • FewShot learning with KNN                        │
│  • ComponentCatalog optimization                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  LLM Providers (infrastructure/adapters)            │
│  • Anthropic (default: Haiku 4.5)                   │
│  • DeepSeek, OpenAI, Gemini                         │
│  • Ollama (local models)                            │
└─────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- **Node.js** 18+ (for Raycast frontend)
- **Python** 3.10+ (for DSPy backend)
- **Ollama** (optional, for local models)
- **API Keys** for cloud providers (see [Configuration](#configuration))

### 1. Clone & Install Dependencies

```bash
# Clone repository
git clone <repository-url>
cd raycast_ext

# Install Python dependencies (recommended: uv)
make setup

# Or with pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 3. Start DSPy Backend

```bash
# Start in background (recommended for development)
make dev

# Or start in foreground
make backend

# Verify health
make health
# Expected: {"status":"healthy","provider":"anthropic",...}
```

### 4. Install Raycast Extension

```bash
cd dashboard
npm run dev
```

Then enable the extension in Raycast Preferences.

## Configuration

### Environment Variables (.env)

#### LLM Provider

```bash
# Provider selection (default: anthropic)
LLM_PROVIDER=anthropic

# Available providers:
# - anthropic  (Claude Haiku, Sonnet, Opus)
# - deepseek   (DeepSeek Chat, Reasoner)
# - openai     (GPT-4o, GPT-4o-mini)
# - gemini     (Gemini 2.0 Flash, 2.5 Pro)
# - ollama     (Local models via Ollama)
```

#### Model Selection

```bash
# Anthropic Models
LLM_MODEL=claude-haiku-4-5-20251001   # Fastest, ~$0.08/1M tokens
# LLM_MODEL=claude-sonnet-4-5-20250929  # Balanced, ~$3/1M tokens
# LLM_MODEL=claude-opus-4-20250514      # Highest quality, ~$15/1M tokens

# DeepSeek Models
# LLM_MODEL=deepseek-chat              # Lowest cost
# LLM_MODEL=deepseek-reasoner          # Reasoning model

# OpenAI Models
# LLM_MODEL=gpt-4o-mini                # Fastest
# LLM_MODEL=gpt-4o                     # Standard

# Gemini Models
# LLM_MODEL=gemini-2.0-flash-exp       # Experimental
# LLM_MODEL=gemini-2.5-pro             # Latest Pro
```

#### API Keys

```bash
# Anthropic (required when LLM_PROVIDER=anthropic)
HEMDOV_ANTHROPIC_API_KEY=sk-ant-...
# Get your key from: https://console.anthropic.com/

# DeepSeek (required when LLM_PROVIDER=deepseek)
DEEPSEEK_API_KEY=sk-...
# Get your key from: https://platform.deepseek.com/

# OpenAI (required when LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...
# Get your key from: https://platform.openai.com/

# Gemini (required when LLM_PROVIDER=gemini)
GEMINI_API_KEY=...
# Get your key from: https://ai.google.dev/
```

#### SQLite Persistence (Optional)

```bash
# Enable/disable prompt history tracking
SQLITE_ENABLED=true

# Database location
SQLITE_DB_PATH=data/prompt_history.db

# Auto-cleanup settings
SQLITE_RETENTION_DAYS=30
SQLITE_AUTO_CLEANUP=true
```

### Raycast Extension Preferences

Access via **Raycast → Extensions → Prompt Improver → Preferences**

| Preference | Description | Default |
|------------|-------------|---------|
| **DSPy Enabled** | Enable DSPy backend (fallback to Ollama if disabled) | ✓ |
| **DSPy Base URL** | Backend API endpoint | `http://localhost:8000` |
| **Ollama Base URL** | Local Ollama endpoint | `http://localhost:11434` |
| **Model** | Ollama model name (fallback) | `Novaeus-Promptist-7B` |
| **Fallback Model** | Backup model if primary fails | `devstral:24b` |
| **Preset** | Improvement style | `Structured` |
| **Timeout (ms)** | Request timeout | `60000` |

## Usage

### Basic Workflow

1. **Select text** in any app or copy to clipboard
2. **Activate Raycast** (⌘ + Space)
3. **Search**: "Prompt Improver"
4. **View results**: Improved prompt with:
   - Structured format
   - Role & directive
   - Framework (CoT, ToT, etc.)
   - Guardrails
   - Confidence score
   - Latency metrics

### Example Input/Output

**Input:**
```
write a python function to validate email addresses
```

**Output:**
```markdown
# Role: Python Backend Developer

# Task: Email Validation Function

# Context
Create a production-ready email validation function following Python best practices.

# Requirements
- Use regex pattern matching
- Return boolean result
- Handle edge cases (null, empty, invalid format)
- Include docstring with examples
- Follow PEP 8 style guide

# Guardrails
- Validate against RFC 5322 standard
- Reject obviously invalid formats
- Accept common valid formats
- No external dependencies preferred

# Framework: Chain-of-Thought
1. Import necessary modules
2. Define regex pattern
3. Create validation function
4. Add comprehensive tests
5. Document usage examples
```

## Development

### Project Structure

```
raycast_ext/
├── dashboard/              # Raycast extension (React/TS)
│   ├── src/
│   │   └── promptify-quick.tsx
│   └── package.json
├── hemdov/                # DSPy domain (Python)
│   ├── domain/
│   │   └── dspy_modules/
│   ├── infrastructure/
│   │   ├── adapters/      # LLM providers
│   │   └── persistence/   # SQLite repository
│   └── interfaces.py      # DI container
├── api/                   # FastAPI endpoints
│   └── prompt_improver_api.py
├── tests/                 # Python tests (pytest)
├── scripts/               # Utilities
│   ├── data/             # Dataset generation
│   └── eval/             # Quality gates
├── models/               # Compiled DSPy models
├── data/                 # SQLite database
├── main.py               # FastAPI app entrypoint
├── Makefile              # Development commands
├── .env.example          # Environment template
└── CLAUDE.md             # Project documentation
```

### Available Commands

```bash
# Backend
make dev              # Start backend in background
make stop             # Stop backend
make restart          # Restart backend
make health           # Health check
make logs             # Tail backend logs
make status           # Show backend status

# Dataset & Few-Shot Learning
make dataset          # Generate fewshot training dataset
make normalize        # Normalize ComponentCatalog
make merge            # Merge training datasets
make regen-all        # Regenerate all datasets

# Testing & Evaluation
make test             # Run Python tests (pytest)
make test-fewshot     # Test few-shot compilation
make test-backend     # Test backend integration
make eval             # Quality gates (5 cases)
make eval-full        # Full evaluation (30 cases)

# Build
make build            # Build Raycast extension
```

### Quality Gates

| Metric | Target | Script |
|--------|--------|--------|
| JSON Valid Pass 1 | ≥54% | `scripts/eval/compare_quality_gates.py` |
| Copyable Rate | ≥54% | `scripts/eval/compare_quality_gates.py` |
| Latency P95 | ≤12s | `scripts/eval/compare_quality_gates.py` |

Run evaluation: `make eval`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend not running | `make status` then `make dev` |
| Anthropic API error | Check `HEMDOV_ANTHROPIC_API_KEY` in `.env` |
| Port 8000 in use | Change `API_PORT` in `.env` |
| Few-shot not working | Run `make regen-all` to regenerate datasets |
| Extension not appearing in Raycast | Run `cd dashboard && npm run dev` |
| Circuit breaker tripping | Check `.backend.log` for failures, adjust `CIRCUIT_BREAKER_THRESHOLD` |

## Performance

### Anthropic Haiku 4.5 (Default)

- **Latency**: 3-5 seconds (P95)
- **Cost**: ~$0.08 per 1M tokens
- **Quality**: 54% JSON valid, 54% copyable
- **Use case**: Fast iteration, high volume

### Provider Comparison

| Provider | Model | Latency P95 | Cost/1M Tokens | Quality |
|----------|-------|-------------|----------------|---------|
| Anthropic | Haiku 4.5 | ~5s | $0.08 | 54% |
| Anthropic | Sonnet 4.5 | ~8s | $3.00 | 65% |
| DeepSeek | Chat | ~6s | $0.14 | 58% |
| Ollama | Local | ~15s | Free | 45% |

## License

MIT

## Author

**thomas** - Initial work

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests to the main repository.

## Acknowledgments

- [DSPy](https://github.com/stanfordnlp/dspy) - Framework for programming with language models
- [Raycast](https://developers.raycast.com) - Extension platform
- [Anthropic](https://www.anthropic.com) - Claude API
- [LiteLLM](https://github.com/BerriAI/litellm) - Unified LLM interface

---

**Full Documentation**: See [CLAUDE.md](./CLAUDE.md) for detailed development guide and architecture documentation.
