# DSPy Prompt Improver Backend

A Python FastAPI backend that provides State-of-the-Art (SOTA) prompt improvement using DSPy framework. This backend integrates with the Raycast extension to enhance prompt improvement capabilities following HemDov patterns.

## 🎯 Purpose

This backend fills the critical GAP identified in the HemDov audit: **Prompt Improvement**. While HemDov has DSPy modules for Tool Selection, Tool Execution, and Code Generation, it lacked a dedicated Prompt Improvement module.

### What It Does

```
Input:  "Design ADR process"
Output: Complete SOTA prompt (Role + Directive + Framework + Guardrails)
```

The backend transforms raw user ideas into structured, high-quality prompts using:
- **DSPy Framework**: Programmatic prompt optimization
- **Chain of Thought**: Step-by-step reasoning
- **BootstrapFewShot**: Learning from examples
- **Multiple LLM Providers**: Ollama, Gemini, DeepSeek, etc.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Raycast       │    │  FastAPI       │    │  DSPy Module   │
│  Extension     │───▶│  Backend        │───▶│  PromptImprover │
│  (TypeScript)  │    │  /api/v1/*     │    │  (ChainOfThought)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  LiteLLM       │    │  Dataset       │
                       │  Adapter       │    │  Examples      │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### TL;DR (Fish)

```fish
cd /Users/felipe_gonzalez/Developer/raycast_ext/.worktrees/dspy-ollama-hf-pipeline
./setup_dspy_backend.sh
ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
uv run python main.py
```

```fish
curl -s http://localhost:8000/api/v1/improve-prompt \
  -H 'Content-Type: application/json' \
  -d '{"idea":"Design ADR process"}'
```

### 1. Install Dependencies

```fish
./setup_dspy_backend.sh
```

### 2. Configure Environment

```fish
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Key settings:
- `LLM_PROVIDER=ollama` (or gemini, deepseek, openai)
- `LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M`
- `LLM_BASE_URL=http://localhost:11434`

### 3. Start Ollama (if using local models)

```fish
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull model
ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
```

### 4. Start DSPy Backend

```fish
uv run python main.py
```

Expected output:
```
🚀 Starting DSPy Prompt Improver API...
📍 Server: http://0.0.0.0:8000
🧠 LLM: ollama/hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
✅ DSPy configured with ollama/hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
```

### 5. Test the Backend

```fish
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test prompt improvement
curl -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Design ADR process", "context": "Software team"}'
```

## 📁 Project Structure

```
├── hemdov/                          # Core DSPy modules (HemDov patterns)
│   ├── domain/dspy_modules/           # DSPy signatures and modules
│   │   └── prompt_improver.py       # PromptImproverSignature & Module
│   ├── infrastructure/
│   │   ├── adapters/                 # External service adapters
│   │   │   └── litellm_dspy_adapter.py  # Unified LLM provider
│   │   └── config/                  # Configuration management
│   │       └── __init__.py           # Settings with Pydantic
├── eval/src/                        # DSPy training and optimization
│   ├── dspy_prompt_improver.py     # Main DSPy module
│   ├── prompt_improvement_dataset.py # Training examples
│   └── dspy_prompt_optimizer.py     # BootstrapFewShot optimizer
├── api/                             # FastAPI endpoints
│   └── prompt_improver_api.py       # /api/v1/improve-prompt
├── tests/                           # TDD test suite
│   └── test_dspy_prompt_improver.py # Comprehensive tests
├── dashboard/src/core/llm/            # Raycast frontend integration
│   └── dspyPromptImprover.ts       # TypeScript client
├── main.py                          # FastAPI application entry point
├── requirements.txt                  # Python dependencies
└── .env.example                     # Environment template
```

## 🔧 Configuration

### LLM Providers

#### Ollama (Local - Recommended)
```env
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434
```

#### Gemini (Google)
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-pro
GEMINI_API_KEY=your_gemini_api_key
```

#### DeepSeek
```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### DSPy Settings

- `DSPY_MAX_BOOTSTRAPPED_DEMOS=5` - Max few-shot examples to generate
- `DSPY_MAX_LABELED_DEMOS=3` - Max labeled examples from dataset
- `DSPY_COMPILED_PATH` - Path to compiled DSPy module (optional)

### Quality Settings

- `MIN_CONFIDENCE_THRESHOLD=0.7` - Minimum confidence for acceptable prompts
- `MAX_LATENCY_MS=30000` - Request timeout in milliseconds

## 🧪 Development

### Running Tests

```fish
# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=hemdov --cov-report=html
```

### DSPy Development

The DSPy modules follow HemDov patterns:

1. **Signature First**: Define input/output contract
2. **Module Implementation**: Use ChainOfThought for reasoning
3. **Metric Definition**: Quality evaluation function
4. **BootstrapFewShot**: Compile with few-shot examples

Example of adding a new provider:

```python
# In hemdov/infrastructure/adapters/litellm_dspy_adapter.py
def create_custom_adapter(model: str, api_key: str) -> LiteLLMDSPyAdapter:
    return LiteLLMDSPyAdapter(
        model=f"custom/{model}",
        api_key=api_key
    )
```

### Frontend Integration

The Raycast frontend uses `dspyPromptImprover.ts` client:

```typescript
import { improvePromptWithDSPy } from './dspyPromptImprover';

try {
  const result = await improvePromptWithDSPy("Design ADR process");
  console.log(result.improved_prompt);
} catch (error) {
  console.error('DSPy backend unavailable:', error);
  // Fall back to existing Ollama implementation
}
```

## 📊 Performance and Quality

### Metrics

The backend tracks:
- **Latency**: Response time per request
- **Success Rate**: Percentage of successful improvements
- **Quality Score**: Based on completeness and structure
- **Backend Used**: DSPy vs Ollama fallback

### Quality Gates

Following HemDov patterns, prompts must have:
1. **Role**: AI persona description (20+ chars)
2. **Directive**: Core mission statement (30+ chars)
3. **Framework**: Reasoning approach (CoT, ToT, etc.)
4. **Guardrails**: 3-5 constraints
5. **Structured Format**: Proper section headers

### Example Output

```json
{
  "improved_prompt": "**[ROLE & PERSONA]**\nYou are a World-Class Software Architect...\n\n**[CORE DIRECTIVE]**\n**Your ultimate mission is:** To design and detail...",
  "role": "World-Class Software Architect with over 20 years of experience...",
  "directive": "To design and detail a robust, scalable, and developer-friendly process...",
  "framework": "chain-of-thought",
  "guardrails": ["Avoid jargon", "Prioritize pragmatism", "Actionable steps", "Git integration"],
  "reasoning": "Selected role for technical expertise and leadership...",
  "confidence": 0.87
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"Import dspy not found"**
   ```fish
   uv sync --all-extras
   ```

2. **"DSPy backend not available"**
   - Check if Ollama is running: `ollama list`
   - Verify model is pulled: `ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M`
   - Check backend health: `curl http://localhost:8000/health`

3. **"ModuleNotFoundError: hemdov"**
   - Ensure you're running from project root
   - Check Python path: `set -x PYTHONPATH (pwd)`

4. **Slow Response Times**
   - Try faster model: `LLM_MODEL=mistral`
   - Reduce `MAX_LATENCY_MS`
   - Use ZeroShot version for speed

### Debug Mode

Enable debug logging:

```env
# In .env
LOG_LEVEL=DEBUG
```

Or run with verbose output:

```fish
uv run python main.py --log-level DEBUG
```

## 📈 Roadmap

### Phase 1: Core (✅ Complete)
- [x] PromptImproverSignature
- [x] PromptImprover Module
- [x] Basic FastAPI endpoint
- [x] LiteLLM adapter

### Phase 2: Optimization (✅ Complete)
- [x] Dataset with examples
- [x] BootstrapFewShot compilation
- [x] Quality metrics
- [x] Comprehensive tests

### Phase 3: Integration (✅ Complete)
- [x] TypeScript client
- [x] Hybrid frontend (DSPy + Ollama fallback)
- [x] Environment configuration
- [x] Documentation

### Phase 4: Future Enhancements
- [ ] Template RAG integration
- [ ] Real-time quality scoring
- [ ] A/B testing of prompts
- [ ] Prompt versioning and history
- [ ] Multi-language support

## 🤝 Contributing

Follow HemDov patterns for contributions:

1. **TDD First**: Write failing tests, then implement
2. **Type Hints**: 100% type annotation coverage
3. **Documentation**: Every function needs docstring
4. **Quality Gates**: All tests must pass
5. **HemDov Compatible**: Follow existing conventions

### Adding New Examples

To add training examples to `eval/src/prompt_improvement_dataset.py`:

```python
dspy.Example(
    original_idea="Your new example",
    context="Additional context",
    improved_prompt="Complete structured prompt...",
    role="AI role description",
    directive="Core mission statement", 
    framework="chain-of-thought",
    guardrails=["constraint1", "constraint2"]
).with_inputs("original_idea", "context")
```

## 📞 Support

- **Documentation**: Check this README first
- **HemDov Patterns**: See `docs/research/wizard/`
- **Issues**: Create GitHub issue with logs
- **DSPy Documentation**: https://dspy-docs.vercel.app/

---

**Result**: The critical GAP from HemDov audit is now filled. The Raycast extension can now provide State-of-the-Art prompt improvement using DSPy's systematic approach, with fallback to existing Ollama implementation for reliability.
