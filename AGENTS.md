# AGENTS.md

Repository-level instructions for Codex in `/Users/felipe_gonzalez/Developer/raycast_ext`.

## Scope

- Applies to the full repository unless a deeper `AGENTS.md` overrides it.
- Prefer narrower overrides only when behavior differs by directory.

## Build and Test

- Install deps: `make setup`
- Backend dev: `make dev`
- Backend health: `make health`
- Backend tests: `make test`
- Quality eval: `make eval` (or `make eval-full`)
- Frontend dev: `make ray-dev`
- Frontend tests: `cd dashboard && npm run test`
- Frontend lint: `cd dashboard && npm run lint`

## Working Rules

- Keep changes minimal and reversible; edit only files needed for the task.
- Validate with the smallest relevant command set before claiming completion.
- Do not use broad exception handlers in Python (`except Exception:`); catch specific errors.
- Keep domain purity in `hemdov/domain/`: no IO, no async, no side effects.
- Preserve TS/Python boundary contracts (for example shared enum values and response shapes).
- Backend-first pipeline is DSPy via FastAPI (`http://localhost:8000`) with LiteLLM providers; do not switch execution path or provider defaults unless the user asks.

## Operational Notes

- `make dev` is idempotent: if backend is already running, it should report health and exit successfully.
- If backend is unavailable, verify with `make status` and `make health` before frontend changes.
- Ensure `dashboard/package.json` keeps `"localhost": true` for Raycast localhost access.

## References

- `/Users/felipe_gonzalez/Developer/raycast_ext/README.md`
- `/Users/felipe_gonzalez/Developer/raycast_ext/CLAUDE.md`
- `/Users/felipe_gonzalez/Developer/raycast_ext/dashboard/CLAUDE.md`
- `/Users/felipe_gonzalez/Developer/raycast_ext/docs/backend/README.md`
