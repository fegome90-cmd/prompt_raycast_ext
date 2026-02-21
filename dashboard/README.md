# Prompt Improver (Raycast Frontend)

Raycast extension for DSPy prompt improvement via the local FastAPI backend (`http://localhost:8000`), backed by LiteLLM and Anthropic Haiku by default.

## Setup

1. Start backend from repo root:
   - `make dev`
   - `make health`
2. In Raycast → Extensions → `Prompt Improver`:
   - Open `Improve Prompt`
   - Verify `DSPy URL` is `http://localhost:8000`
   - Keep `Execution Mode` as `legacy` or `nlac` for backend pipeline

## Commands

- `Improve Prompt`: main command for backend improvement.
- `Promptify Selected`: improves selected text.
- `Prompt History`: shows saved outputs.
- `Prompt Conversation`: wizard-style clarification flow.

## Notes

- `executionMode=legacy|nlac` requires backend availability.
- `executionMode=ollama` is optional local-only mode, not the default production path.
