# Project Cleanup Plan - 2026-01-12

## Overview

Large refactor to clean up the codebase after multiple development sessions. This plan breaks down the changes into **4 focused, reviewable PRs** (consolidated from original 7-part split).

## Current State

**PR #2**: `refactor: project cleanup and documentation updates`
- **Branch**: `refactor/cleanup-project-files`
- **Scope**: 32 files changed, 409 insertions, 346 deletions
- **Status**: OPEN - to be closed and replaced with focused PRs

## Problem Statement

The current PR mixes multiple concerns:
- Documentation updates
- Frontend changes
- Backend changes
- Test modifications
- Dependency updates

This makes review difficult and increases merge risk.

---

## Improved Split Plan - 4 Focused PRs

### PR #A: Documentation Updates 📚

**Parts Combined**: 1 + 7

**Files**: `CLAUDE.md`, `docs/`

**Changes**:
- Simplify CLAUDE.md from 175 lines to 59 lines
- Remove verbose architecture diagrams
- Keep essential Quick Start and Critical Rules
- Reorganize `docs/` directory
- Delete: `docs/handoff.md`
- Add: `docs/handoffs/`, `docs/plans/`, `OPTIMIZATIONS.md`

**Justification**: Documentation changes are low-risk and establish context for other changes.

**Risk**: Low - documentation only, no code changes

**Testing**: N/A

**Rollback**: `git revert HEAD~1`

---

### PR #B: Dependency Updates 🔧

**Part**: 2

**Files**: `package.json`, `package-lock.json`, `uv.lock`

**Changes**:
- Update frontend dependencies (npm)
- Update Python dependencies (uv)

**Justification**: Keep dependencies current for security and features.

**Risk**: Medium - dependency updates can introduce breaking changes

**Testing**:
- [ ] `cd dashboard && npm install`
- [ ] `uv sync`
- [ ] `make dev` - backend starts
- [ ] `make test` - tests pass

**Rollback**: `git revert HEAD~1`

**Note**: Run tests immediately after merge to catch breaking changes.

---

### PR #C: Backend Complete (Code + Tests + New Files) 🔧

**Parts Combined**: 4 + 6 + 5

**Files**: `hemdov/domain/`, `eval/src/`, `tests/`

**Changes**:
- **Domain models**: `nlac_models.py`, `prompt_history.py`
- **Services**: `__init__.py`, `knn_provider.py`, `complexity_analyzer.py`, `llm_protocol.py`
- **Eval strategies**: `complex_strategy.py`, `nlac_strategy.py`, `strategy_selector.py`
- **Test updates**: All test files in `tests/`
- **New tests**: `test_intent_classifier_edge_cases.py`, `test_prompt_cache_edge_cases.py`, `test_property_based.py`, `test_service_integration.py`
- **New fixtures**: `tests/fixtures/`

**Justification**: Backend + tests + new files are all in the Python ecosystem. Testing immediately verifies the changes.

**Risk**: Medium - backend changes affect core functionality

**Testing**:
- [ ] `make test` - all tests pass
- [ ] `make eval` - quality gates pass (if applicable)
- [ ] Manual smoke test with backend running

**Rollback**: `git revert HEAD~1`

**Why combined**: These changes are interdependent in the Python ecosystem. Tests verify the backend code, and new files add backend functionality.

---

### PR #D: Frontend Refactoring 🎨

**Part**: 3

**Files**: `dashboard/src/`

**Changes**:
- `conversation-view.tsx` - UI updates
- `core/config/index.ts` - config changes
- `core/design/tokens.ts` - design token updates
- `core/llm/*.ts` - LLM fetch wrapper improvements
- `core/promptStorage.ts` - storage refactoring
- `prompt-*.tsx` - component updates
- `__tests__/promptStorage.test.ts` - test updates

**Justification**: Frontend changes are isolated to the React/TypeScript ecosystem.

**Risk**: Medium - frontend changes affect UX

**Testing**:
- [ ] `cd dashboard && npm run build`
- [ ] `cd dashboard && npm test`
- [ ] Manual smoke test in Raycast

**Rollback**: `git revert HEAD~1`

**Note**: Independent of backend changes - dashboard communicates via API.

---

## Merge Order

```
PR #A (Docs) → PR #B (Deps) → PR #C (Backend) → PR #D (Frontend)
     ↓              ↓               ↓               ↓
   Low          Medium          Medium          Medium
   Risk          Risk           Risk           Risk
```

### Why this order?

1. **#A Docs first** - No dependencies, establishes context
2. **#B Dependencies second** - Foundation for both ecosystems
3. **#C Backend third** - Core functionality, verified by tests
4. **#D Frontend last** - Independent, consumes backend API

### Handling Conflicts

If main receives changes while working on this plan:
```bash
# Before creating each PR branch
git checkout main
git pull origin main

# Rebase your work branch
git checkout your-feature-branch
git rebase main
```

---

## Execution Strategy

### Step 1: Prepare
```bash
# Close PR #2 without merging (keep branch as reference)
gh pr close 2 --comment "Replacing with focused PRs per cleanup plan"

# Keep the branch for reference
git branch -D refactor/cleanup-project-files  # Only after all new PRs created
```

### Step 2: Create Focused Branches

```bash
# Start from main
git checkout main
git pull origin main

# Create branches for each PR
git checkout -b pr-a-documentation
git checkout -b pr-b-dependencies
git checkout -b pr-c-backend-complete
git checkout -b pr-d-frontend
```

### Step 3: Port Changes

For each branch, manually port relevant changes from the reference branch:
```bash
# View reference branch changes
git diff refactor-cleanup-project-files -- <file-pattern>

# Apply to your focused branch
# Copy/modify files as needed
```

### Step 4: Create PRs in Order

```bash
# For each branch (A → B → C → D)
git checkout pr-<letter>
git push origin pr-<letter>
gh pr create --title "<title>" --body "<body from plan>"
```

### Step 5: Merge and Verify

For each PR:
1. Review PR carefully
2. Run verification tests from plan
3. Merge if tests pass
4. Run post-merge verification
5. Close and delete branch

---

## Verification Checklist (Per PR)

Before merging each PR:
- [ ] Descriptive title and description
- [ ] Focused scope (single concern)
- [ ] No unrelated changes
- [ ] Commit messages follow conventions
- [ ] Tests pass locally
- [ ] Build successful (if applicable)

After merging each PR:
- [ ] Run `git pull` to get latest main
- [ ] Run quick smoke test
- [ ] Check for any immediate issues

---

## Time Estimate

| PR | Estimated Time |
|----|---------------|
| #A Documentation | 30 min |
| #B Dependencies | 45 min (includes testing) |
| #C Backend | 1-2 hours (includes testing) |
| #D Frontend | 1 hour (includes testing) |
| **Total** | **~3-4 hours** |

---

## Rollback Strategy

If any PR causes issues:
```bash
# Revert the merge
git revert -m 1 HEAD

# Push the revert
git push origin main

# Create issue to fix the problem
gh issue create --title "Rollback: <PR title>" --body "Describe the issue"
```

---

## Completion Criteria

This cleanup is complete when:
- [ ] All 4 PRs merged to main
- [ ] All tests passing on main
- [ ] Reference branch `refactor/cleanup-project-files` deleted
- [ ] Plan document archived to `docs/plans/completed/`

---

## Notes

- Current branch `refactor/cleanup-project-files` serves as reference
- Each part can be extracted using `git diff` and manual porting
- Do NOT use cherry-pick - changes are in a single commit
- Focus on creating clean, reviewable PRs rather than perfect extraction
