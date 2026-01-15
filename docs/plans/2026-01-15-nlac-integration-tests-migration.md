# NLaC Integration Tests Migration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate valuable integration tests and utilities from obsolete `feature/nlac-integration-complete` branch to a clean branch based on current main, preserving only the unique work that doesn't exist in main.

**Architecture:** Cherry-pick strategy - extract 5 specific commits from the old branch that contain unique integration test infrastructure, ignoring commits that conflict with already-merged Phase 1 error handling framework.

**Tech Stack:** Git worktree, cherry-pick, pytest, Python testing

---

## Context

**Problem:** The `feature/nlac-integration-complete` branch contains valuable integration test code but is based on an old main commit (before Phase 1 error handling). Merging it would delete 40+ files from the newly merged Phase 1 framework.

**Solution:** Create a fresh branch from current main and cherry-pick only the 5 valuable commits that contain unique work not present in main.

**Valuable commits to extract:**
- `bc553b1` - MockLLMClient.generate() for ReflexionService compatibility
- `82e2937` - DatasetLoader utility for integration tests
- `49a77d2` - E2E test with real dataset
- `9bee813` - Integration test dataset with 10 test cases
- `baebd4a` - Mock LLM client for integration tests

**Ignored commits (obsolete/conflicting):**
- `28e0e50` - Typo fix (OPOR → OPRO)
- `1e2cfa6` - Mock LLM client update (superseded by bc553b1)
- `e2251b5` - Expected output in REFACTOR tests
- `35ac779` - Test results report (obsolete)
- `182c189` - Integration completion docs (obsolete)

---

## Task 1: Create New Branch from Current Main

**Files:**
- None (branch creation only)

**Step 1: Create new worktree and branch**

```bash
# Create new worktree from current main
git worktree add .worktrees/nlac-integration-tests -b feature/nlac-integration-tests

# Switch to the new worktree
cd .worktrees/nlac-integration-tests
```

Expected: New worktree created at `.worktrees/nlac-integration-tests/` on branch `feature/nlac-integration-tests`

**Step 2: Verify branch is based on current main**

```bash
git log -1 --oneline
```

Expected: Shows commit `8e69ea2` (merge of feat/error-handling-phase1) or later

---

## Task 2: Cherry-pick MockLLMClient with generate() Method

**Files:**
- Create: `tests/mocks/mock_llm_client.py` (from commit bc553b1)
- Test: `tests/mocks/test_mock_llm_client.py` (verify generate() method)

**Step 1: Cherry-pick the commit**

```bash
git cherry-pick bc553b1
```

Expected: Clean cherry-pick with no conflicts

**Step 2: Verify the MockLLMClient has generate() method**

```bash
python3 -c "
from tests.mocks.mock_llm_client import MockLLMClient
client = MockLLMClient()
assert hasattr(client, 'generate'), 'generate() method missing'
print('✓ MockLLMClient.generate() exists')
"
```

Expected: "✓ MockLLMClient.generate() exists"

**Step 3: Run tests for mock client**

```bash
pytest tests/mocks/ -v -k mock_llm_client 2>&1 | tail -5
```

Expected: Tests pass

**Step 4: Commit**

```bash
git add tests/mocks/
git commit -m "feat(tests): add generate() method to MockLLMClient for ReflexionService compatibility

Original commit: bc553b1
Part of NLaC integration tests migration from obsolete branch.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Cherry-pick DatasetLoader Utility

**Files:**
- Create: `tests/dataset_loader.py` (from commit 82e2937)
- Test: `tests/test_dataset_loader.py` (verify loader works)

**Step 1: Cherry-pick the commit**

```bash
git cherry-pick 82e2937
```

Expected: Clean cherry-pick with no conflicts

**Step 2: Verify DatasetLoader can load the dataset**

```bash
python3 -c "
from tests.dataset_loader import DatasetLoader
loader = DatasetLoader()
assert hasattr(loader, 'load_cases'), 'load_cases() method missing'
print('✓ DatasetLoader.load_cases() exists')
"
```

Expected: "✓ DatasetLoader.load_cases() exists"

**Step 3: Verify dataset file exists**

```bash
ls -la datasets/integration-test-cases.jsonl
```

Expected: File exists with 10 test cases

**Step 4: Run tests for dataset loader**

```bash
pytest tests/test_dataset_loader.py -v 2>&1 | tail -5
```

Expected: Tests pass

**Step 5: Commit**

```bash
git add tests/dataset_loader.py tests/test_dataset_loader.py
git commit -m "feat(tests): add DatasetLoader utility for integration tests

- Load test cases from integration-test-cases.jsonl
- Provides structured dataset access for E2E testing

Original commit: 82e2937
Part of NLaC integration tests migration from obsolete branch.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Cherry-pick E2E Test with Real Dataset

**Files:**
- Create: `tests/test_e2e_with_dataset.py` (from commit 49a77d2)
- Test: Verify test can be discovered and run

**Step 1: Cherry-pick the commit**

```bash
git cherry-pick 49a77d2
```

Expected: Clean cherry-pick with no conflicts

**Step 2: Verify E2E test exists and is importable**

```bash
python3 -c "
import tests.test_e2e_with_dataset
print('✓ E2E test module imports successfully')
"
```

Expected: "✓ E2E test module imports successfully"

**Step 3: Run the E2E test**

```bash
pytest tests/test_e2e_with_dataset.py -v 2>&1 | tail -10
```

Expected: Test runs (may fail if NLaC dependencies not fully set up, but should execute)

**Step 4: Commit**

```bash
git add tests/test_e2e_with_dataset.py
git commit -m "feat(tests): add E2E test with real dataset

- Tests full pipeline using integration-test-cases.jsonl
- Validates end-to-end NLaC execution with real data

Original commit: 49a77d2
Part of NLaC integration tests migration from obsolete branch.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Cherry-pick Integration Test Dataset

**Files:**
- Create: `datasets/integration-test-cases.jsonl` (from commit 9bee813)
- Test: Verify dataset format and content

**Step 1: Cherry-pick the commit**

```bash
git cherry-pick 9bee813
```

Expected: Clean cherry-pick with no conflicts

**Step 2: Verify dataset has 10 test cases**

```bash
wc -l datasets/integration-test-cases.jsonl
cat datasets/integration-test-cases.jsonl | jq -s '. | length'
```

Expected: 10 lines (10 test cases)

**Step 3: Verify dataset format is valid JSONL**

```bash
head -1 datasets/integration-test-cases.jsonl | jq .
```

Expected: Valid JSON object

**Step 4: Commit**

```bash
git add datasets/
git commit -m "feat(tests): add integration test dataset with 10 test cases

- JSONL format with idea, expected_output, metadata
- Covers diverse scenarios for E2E validation

Original commit: 9bee813
Part of NLaC integration tests migration from obsolete branch.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Cherry-pick Mock LLM Client Implementation

**Files:**
- Create: `tests/mocks/mock_llm_client.py` (from commit baebd4a)
- Note: May conflict with Task 2, resolve by keeping Task 2 version

**Step 1: Cherry-pick the commit**

```bash
git cherry-pick baebd4a --strategy-option=theirs
```

Expected: Cherry-pick with their strategy (keeps existing changes from Task 2)

**Step 2: Resolve any conflicts**

If conflict occurs:
```bash
# Keep the version from Task 2 (has generate() method)
git checkout --ours tests/mocks/mock_llm_client.py
git add tests/mocks/mock_llm_client.py
git cherry-pick --continue
```

Expected: Conflict resolved, keeping Task 2 implementation

**Step 3: Verify MockLLMClient has all required methods**

```bash
python3 -c "
from tests.mocks.mock_llm_client import MockLLMClient
client = MockLLMClient()
methods = ['generate', '__call__', '__init__']
for method in methods:
    assert hasattr(client, method), f'{method}() missing'
print('✓ MockLLMClient has all required methods')
"
```

Expected: "✓ MockLLMClient has all required methods"

**Step 4: Run tests for mock client**

```bash
pytest tests/mocks/ -v 2>&1 | tail -10
```

Expected: All mock client tests pass

**Step 5: Commit**

```bash
git add tests/mocks/
git commit -m "feat(tests): add Mock LLM client for integration tests

- Implements DSPy __call__ interface
- Compatible with NLaC pipeline components
- Combines with generate() method from Task 2

Original commit: baebd4a
Part of NLaC integration tests migration from obsolete branch.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Run Full Test Suite on New Branch

**Files:**
- None (verification only)

**Step 1: Run all newly added tests**

```bash
pytest tests/test_e2e_with_dataset.py tests/test_dataset_loader.py tests/mocks/ -v
```

Expected: All tests pass

**Step 2: Verify no conflicts with Phase 1 code**

```bash
python3 -c "
from hemdov.domain.errors import DomainError, ErrorCategory
from hemdov.domain.types.result import Success, Failure, is_success
from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds
print('✓ Phase 1 error handling framework intact')
"
```

Expected: "✓ Phase 1 error handling framework intact"

**Step 3: Verify no files were deleted**

```bash
git diff --name-only main | grep "^D"
```

Expected: No output (no files deleted)

**Step 4: Verify branch is ahead of main**

```bash
git log main..HEAD --oneline
```

Expected: 6 commits ( Tasks 2-6 )

---

## Task 8: Verify and Document Migration

**Files:**
- Create: `docs/plans/2026-01-15-nlac-integration-tests-migration-complete.md`

**Step 1: Document what was migrated**

```bash
cat > docs/plans/2026-01-15-nlac-integration-tests-migration-complete.md << 'EOF'
# NLaC Integration Tests Migration - Complete

## Migrated Components

✅ **MockLLMClient** - Full DSPy-compatible mock with generate() method
✅ **DatasetLoader** - Utility for loading integration test cases
✅ **E2E Test** - End-to-end test with real dataset
✅ **Test Dataset** - 10 diverse test cases in JSONL format

## Preserved from Original Branch

These commits were extracted from feature/nlac-integration-complete:
- bc553b1 - MockLLMClient.generate()
- 82e2937 - DatasetLoader utility
- 49a77d2 - E2E test
- 9bee813 - Test dataset
- baebd4a - Mock LLM client base

## Intentionally Omitted

These commits were NOT migrated (obsolete or conflicting):
- 28e0e50 - Typo fix (OPOR → OPRO)
- 1e2cfa6 - Mock client update (superseded)
- e2251b5 - REFACTOR test expectations
- 35ac779 - Test results report (obsolete)
- 182c189 - Completion docs (obsolete)

## Verification

All integration test infrastructure is now available on:
- Branch: feature/nlac-integration-tests
- Worktree: .worktrees/nlac-integration-tests/
- Phase 1 error handling framework: ✅ Preserved
- NLaC code: ✅ Already in main
EOF
```

Expected: Documentation file created

**Step 2: Create completion marker**

```bash
touch .worktrees/nlac-integration-tests/MIGRATION_COMPLETE
cat > .worktrees/nlac-integration-tests/MIGRATION_COMPLETE << 'EOF'
# NLaC Integration Tests Migration Complete

✅ All valuable integration test infrastructure migrated
✅ Phase 1 error handling framework preserved
✅ Ready for execution and validation
EOF
```

Expected: Completion marker created

**Step 3: Commit documentation**

```bash
git add docs/plans/2026-01-15-nlac-integration-tests-migration-complete.md .worktrees/nlac-integration-tests/MIGRATION_COMPLETE
git commit -m "docs(nlac): document integration tests migration completion

- List all migrated components
- Document omitted commits and rationale
- Verify preservation of Phase 1 framework

Migration complete: feature/nlac-integration-tests branch ready.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Cleanup Old Branch

**Files:**
- Delete: branch `feature/nlac-integration-complete`
- Delete: worktree `.worktrees/nlac-integration-complete`

**Step 1: Switch to main branch**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git checkout main
```

Expected: Switched to main

**Step 2: Delete old worktree**

```bash
git worktree remove --force .worktrees/nlac-integration-complete
```

Expected: Worktree directory removed

**Step 3: Delete old branch**

```bash
git branch -D feature/nlac-integration-complete
```

Expected: Branch deleted

**Step 4: Verify cleanup**

```bash
git worktree list | grep nlac-integration-complete || echo "✓ Old worktree removed"
git branch | grep nlac-integration-complete || echo "✓ Old branch removed"
```

Expected: Both removed

---

## Task 10: Final Verification

**Files:**
- None (verification only)

**Step 1: Verify new worktree exists**

```bash
git worktree list | grep nlac-integration-tests
```

Expected: `.worktrees/nlac-integration-tests/` listed

**Step 2: Verify new branch exists**

```bash
git branch | grep nlac-integration-tests
```

Expected: `feature/nlac-integration-tests` listed

**Step 3: Summary of migration**

```bash
echo "=== MIGRATION SUMMARY ===" && echo "Old branch: feature/nlac-integration-complete (DELETED)" && echo "New branch: feature/nlac-integration-tests (ACTIVE)" && echo "Worktree: .worktrees/nlac-integration-tests/" && echo "Commits migrated: 5 unique commits" && echo "Phase 1 preserved: ✓"
```

Expected: Summary shows successful migration

---

## Execution Notes

**Pre-requisites:**
- Git worktree support available
- Original branch `feature/nlac-integration-complete` exists locally
- Current main branch has Phase 1 error handling merged

**Risk Assessment:**
- **LOW** - Only cherry-picking specific commits
- **LOW** - No modification of existing main code
- **LOW** - Each commit tested individually

**Rollback Plan:**
If any cherry-pick fails, use `git reset --hard HEAD~1` to undo that specific cherry-pick and continue with next commit.

**Success Criteria:**
- All 5 valuable commits migrated
- Phase 1 error handling framework intact (no files deleted)
- All new tests passing
- Old branch and worktree cleaned up
