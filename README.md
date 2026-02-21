# Prompt Improver (DSPy)

> Transform rough prompts into SOTA prompts using DSPy with few-shot learning

## Overview

**Prompt Improver** is a Raycast extension that converts raw ideas (from selection or clipboard) into structured, production-ready prompts using DSPy with few-shot learning and multiple LLM providers.

### Key Features

- **🚀 Multiple LLM Providers**: Anthropic (Haiku, Sonnet, Opus), DeepSeek, OpenAI, Gemini, Ollama (local)
- **🧠 Few-Shot Learning**: KNN-based example selection for consistent, high-quality outputs
- **⚡ Fast & Reliable**: Anthropic Haiku 4.5 as default (~$0.08/1M tokens, <5s latency)
- **📊 Metrics Framework**: Multi-dimensional quality tracking (quality, performance, impact)
- **📈 Trend Analysis**: Built-in analytics for monitoring prompt quality over time
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
│  /api/v1/improve-prompt, /api/v1/metrics/*          │
│  • Circuit breaker for resilience                   │
│  • SQLite persistence (optional)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Metrics Framework (hemdov/domain/metrics/)         │
│  • Quality, Performance, Impact evaluators          │
│  • Trend analysis & comparison                      │
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
| **DSPy Base URL** | Backend API endpoint | `http://localhost:8000` |
| **Execution Mode** | `legacy`/`nlac` use backend, `ollama` is local-only mode | `nlac` |
| **Ollama Base URL** | Local Ollama endpoint (used only in `ollama` mode) | `http://localhost:11434` |
| **Model** | Model used by local Ollama mode | `hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M` |
| **Fallback Model** | Backup model for Ollama mode failures | `devstral:24b` |
| **Preset** | Improvement style | `Structured` |
| **Timeout (ms)** | Request timeout | `120000` |

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

## Metrics Framework

> **Production-ready multi-dimensional quality tracking system for prompt improvements**

### Overview

The Metrics Framework provides comprehensive, automated quality assessment across four key dimensions:

| Dimension | Description | Key Metrics |
|-----------|-------------|-------------|
| **Quality** | Prompt structure and effectiveness | Coherence, Relevance, Completeness, Clarity |
| **Performance** | Resource utilization | Latency, Token Usage, Cost |
| **Impact** | User satisfaction and engagement | Success Rate, Copy Count, Feedback |
| **Improvement** | Progress tracking over time | Quality Delta, Trend Analysis |

### Four Dimensions Explained

#### 1. Quality Metrics (`QualityMetrics`)

Evaluates the intrinsic quality of improved prompts:

```python
{
    "coherence_score": 0.85,        # Logical flow and structure
    "relevance_score": 0.90,        # Alignment with original intent
    "completeness_score": 0.80,     # Presence of required sections
    "clarity_score": 0.88,          # Absence of ambiguity
    "composite_score": 0.86,        # Weighted average
    "guardrails_count": 3,          # Number of guardrails
    "has_required_structure": true  # Has role + directive
}
```

**Bonus System:**
- Guardrails Bonus: Up to +15% for quality guardrails
- Structure Bonus: +10% for required structure (role + directive)

#### 2. Performance Metrics (`PerformanceMetrics`)

Tracks resource utilization and efficiency:

```python
{
    "latency_ms": 4500,             # Response time
    "total_tokens": 1250,           # Input + Output tokens
    "cost_usd": 0.00035,            # Estimated API cost
    "performance_score": 0.82,      # Normalized efficiency score
    "provider": "anthropic",        # LLM provider
    "model": "claude-haiku-4-5",    # Model name
    "backend": "few-shot"           # Backend type
}
```

#### 3. Impact Metrics (`ImpactMetrics`)

Measures user satisfaction and engagement:

```python
{
    "copy_count": 8,                # Times result was copied
    "regeneration_count": 0,        # Times result was regenerated
    "feedback_score": 5,            # User rating (1-5)
    "reuse_count": 4,               # Times result was reused
    "success_rate": 0.89,           # First-attempt acceptance
    "impact_score": 0.85            # Overall impact score
}
```

#### 4. Improvement Metrics (`PromptImprovementMetrics`)

Tracks progress and trends over time:

```python
{
    "baseline_score": 0.65,         # Starting quality
    "current_score": 0.82,          # Current quality
    "quality_delta": 0.17,          # Improvement amount
    "trend_direction": "upward",    # Quality trend
    "confidence": 0.95              # Trend confidence
}
```

### API Endpoints

```bash
# Get metrics summary (averages across all prompts)
GET /api/v1/metrics/summary
Response: {"quality": 0.82, "performance": 0.75, "impact": 0.85}

# Get quality trends over time
GET /api/v1/metrics/trends?days=7
Response: {"dates": [...], "quality": [...], "performance": [...]}

# Compare two specific prompts
POST /api/v1/metrics/compare
Body: {"prompt_id_1": "uuid-1", "prompt_id_2": "uuid-2"}
Response: {"winner": "uuid-1", "quality_diff": 0.15, ...}
```

### Usage in Python

```python
from hemdov.domain.metrics.evaluators import PromptMetricsCalculator, ImpactData
from hemdov.domain.metrics.registry import get_registry

# Calculate metrics
calculator = PromptMetricsCalculator()
metrics = calculator.calculate(
    original_idea="Create a Python function",
    result=improvement_result,
    impact_data=ImpactData(copy_count=5, feedback_score=5)
)

# Check if quality is acceptable
registry = get_registry()
is_acceptable = registry.is_acceptable("quality.composite_score", metrics.quality.composite_score)

# Get letter grade
grade = registry.get_grade("quality.composite_score", metrics.quality.composite_score)
# Returns: MetricGrade.A_PLUS
```

### Metrics by Provider

| Provider | Model | Quality | Performance | Impact |
|----------|-------|---------|-------------|--------|
| Anthropic | Haiku 4.5 | 0.78 | 0.92 | 0.81 |
| Anthropic | Sonnet 4.5 | 0.85 | 0.78 | 0.87 |
| DeepSeek | Chat | 0.72 | 0.85 | 0.76 |
| Ollama | Local | 0.65 | 0.45 | 0.68 |

**Key Insights:**
- Haiku 4.5: Best performance (fastest, cheapest)
- Sonnet 4.5: Best quality (highest scores)
- DeepSeek: Balanced option
- Ollama: Free but slower

### Configuration

```bash
# Metrics are calculated automatically for all prompt improvements
# Configure thresholds in hemdov/domain/metrics/registry.py

# Example thresholds (can be customized):
QUALITY_MIN_ACCEPTABLE = 0.60  # C grade
QUALITY_TARGET = 0.80          # B grade
QUALITY_EXCELLENT = 0.90       # A grade
```

**Full Documentation:** See [docs/metrics-framework.md](./docs/metrics-framework.md) for detailed implementation guide.

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
│   │   ├── dspy_modules/
│   │   └── metrics/       # Metrics framework
│   │       ├── dimensions.py    # Quality, Performance, Impact
│   │       ├── evaluators.py    # Metrics calculation
│   │       ├── registry.py      # Thresholds & definitions
│   │       └── analyzers.py     # Trend analysis
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
├── docs/                  # Documentation
│   └── metrics-framework.md
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
