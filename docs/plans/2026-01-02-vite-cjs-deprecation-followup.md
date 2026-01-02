# Follow-up: Vite CJS Node API Deprecation Warning

## Context
While running `npm test`, Vitest prints:

```
The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated
```

This is likely coming from Vitest using Vite's Node API in CJS mode.

## Scope
- Repo area: `dashboard/`
- Suspect files: `dashboard/vitest.config.ts`, `dashboard/package.json`
- Tooling versions: `vitest`, `@vitest/coverage-v8` (Vite is a dependency of Vitest)

## Goals
- Remove the warning without changing test behavior.
- Keep Node 18 compatibility.

## Next Steps (TBD)
1. Check the Vite troubleshooting guide for the recommended fix.
2. Verify current `vitest` and `vite` versions and update if needed.
3. If the fix requires ESM-only Node API usage, adjust test config accordingly.
4. Re-run `npm test` to confirm the warning is gone.
