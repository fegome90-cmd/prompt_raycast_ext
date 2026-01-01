# DSPy Backend Pipeline (Raycast)

## DSPy-First Flow

```
Raycast Extension (TS)
     ↓ DSPy-first
FastAPI /api/v1/improve-prompt
     ↓
PromptImprover DSPy Module
     ↓
LiteLLM Adapter → Ollama (HF model)
```

## Quick Start (Fish)

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

## Config (Ollama + HF)

```
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434
```

See `DSPY_BACKEND_README.md` and `QUICKSTART.md` for details.
