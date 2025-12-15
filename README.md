# Prompt Renderer Local

Minimal Raycast tool to improve rough prompts into ready-to-paste prompts using a local Ollama model (no cloud).

## Setup

1. Ensure Ollama is running and you have a model pulled (example):
   - `ollama serve`
   - `ollama pull qwen3-coder:30b`
2. In Raycast → Extensions → `Prompt Renderer Local`:
   - Open `Prompt Improver (Local)`
   - Set `Ollama Base URL` (default `http://localhost:11434`) and `Model` if needed.

## Commands

- `Prompt Improver (Local)`: paste a rough prompt and run `Improve Prompt (Ollama)` (`⌘↵`). Copies the improved prompt and shows a preview with confidence/questions/assumptions.
