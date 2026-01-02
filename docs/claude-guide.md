# Raycast DSPy Backend - Agent Guide

DSPy backend para mejora de prompts. Usa FastAPI + LiteLLM para orquestar múltiples proveedores (Ollama, DeepSeek, Gemini, OpenAI).

## Quickstart
```bash
# Backend
uv run python main.py          # Inicia FastAPI en :8000
uv run pytest                   # Tests

# Datasets Phase 2
uv run python -m scripts.phase3_pipeline.main  # Optimización DSPy + Few-Shot
```

## Arquitectura
- **Backend:** FastAPI + DSPy 3.x + LiteLLM
- **Frontend:** Raycast Extension (TypeScript) → `dashboard/`
- **Datasets:** Phase 2 exports en `datasets/exports/synthetic/` (train/val/test)
- **Fases:** Legacy curation → Synthetic examples → DSPy optimization

## Docs
- Backend: `docs/backend/README.md`
- Quickstart: `docs/backend/quickstart.md`
- Planes: `docs/plans/` (implementación por fases)
- DSPy: https://dspy-docs.vercel.app/

## Testing
```bash
uv run pytest                           # Todos los tests
uv run pytest scripts/tests/phase3/     # Phase 3 tests
```

## Estructura
```
main.py              # FastAPI server
api/                 # Endpoints
hemdov/              # Core business logic
scripts/             # Utilidades, generación datasets
  phase3_dspy/      # DSPy optimization
  phase3_fewshot/   # Few-shot learning
  phase3_pipeline/  # Pipeline unificado
datasets/exports/    # Synthetic data
```
