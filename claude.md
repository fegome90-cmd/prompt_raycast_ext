# Agent Guide (Codex/Claude)

This file defines how an AI agent should work in this repo. It is identical to `claude.md`.

## Official API references (OpenAI)
Based on the OpenAI OpenAPI specification.
- Base URL: `https://api.openai.com/v1`
- Auth: `Authorization: Bearer $OPENAI_API_KEY`
- Primary endpoint: `POST /responses`
- Use endpoint-specific JSON bodies as defined in the OpenAPI spec.

## Official API references (Anthropic)
Based on the Anthropic Claude API docs.
- Base URL: `https://api.anthropic.com`
- Primary endpoint: `POST /v1/messages`
- Required headers: `x-api-key`, `anthropic-version` (e.g., `2023-06-01`), `content-type: application/json`
- Minimal request fields: `model`, `max_tokens`, `messages`

## Repo context
- Shell: `fish`
- Repo root: `/Users/felipe_gonzalez/Developer/raycast_ext`
- DSPy backend docs: `docs/backend/README.md`
- Quickstart: `docs/backend/quickstart.md`
- Dataset exports: `datasets/exports/`

## Sources
- OpenAI OpenAPI spec: `https://app.stainless.com/api/spec/documented/openai/openapi.documented.yml`
- OpenAI API reference: `https://platform.openai.com/docs/api-reference`
- Anthropic API overview: `https://docs.anthropic.com/en/api/overview`
