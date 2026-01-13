# Instructions for Implementation Agent

> **To the implementing agent:** Read these instructions carefully before starting.

## Your Mission

Implement the **Code Simplification Plan** located at:
```
/Users/felipe_gonzalez/.claude/plans/parsed-toasting-naur.md
```

## Quick Start

1. **Read the full plan** at `/Users/felipe_gonzalez/.claude/plans/parsed-toasting-naur.md`
2. **Invoke `superpowers:executing-plans` skill** BEFORE starting implementation
3. **Working directory:** `/Users/felipe_gonzalez/Developer/raycast_ext`

## Plan Overview

| Metric | Value |
|--------|-------|
| **Total Tasks** | 17 tasks |
| **Phases** | 5 phases (CRITICAL → HIGH → MEDIUM → LOW → TESTS) |
| **Estimated Time** | ~8-11 hours |
| **Priority** | CRITICAL issues first (silent failures, domain violations) |

## Execution Strategy

### Batch Size
Execute tasks in **batches of 3 tasks** maximum.

**First Batch (Priority: CRITICAL):**
1. Task 1: Expose KNN Failure Metadata to NLaCResponse
2. Task 2: Add KNN Failure Tracking to OptimizeResponse
3. Task 3: Create Repository Layer for Catalog Loading (WORKTREE)

### Important Notes

**Task 3 (Repository Layer)** requires creating a separate worktree:
```bash
git worktree add ../raycast_ext-repo-layer refactor/repository-layer
```

This task should be done in isolation and merged only when stable.

## Workflow (from executing-plans skill)

1. **Load and Review Plan** - Read critically, identify any blockers
2. **Execute Batch** - Follow each step exactly (RED-GREEN-REFACTOR)
3. **Report** - Show what was implemented + verification output
4. **Continue** - Based on feedback, execute next batch

## Critical Rules

✅ **Follow plan steps exactly** - Use exact code, file paths, and commands from the plan
✅ **TDD workflow** - Write failing test first, then implement, then verify
✅ **Run verifications** - Execute test commands after each task
✅ **Commit frequently** - One commit per task with exact commit message from plan

❌ **DO NOT skip steps** - Each step is intentional
❌ **DO NOT guess** - If unclear, stop and ask for clarification
❌ **DO NOT modify plan** - Execute as written, suggest changes via feedback

## When to Stop

**STOP immediately and ask for help:**
- If a test fails repeatedly
- If you encounter a blocker not addressed in the plan
- If plan has critical gaps preventing progress
- If you don't understand an instruction

## Success Criteria

After completing all tasks:
- ✅ All CRITICAL issues resolved
- ✅ All HIGH issues resolved
- ✅ Code duplication reduced by 75%
- ✅ Cyclomatic complexity reduced by 60%
- ✅ Test coverage > 90% for modified files
- ✅ No regressions in existing functionality

## Required Skills

The plan explicitly requires using `superpowers:executing-plans` skill.

**Invoke it BEFORE starting:**
```
Skill: superpowers:executing-plans
```

This skill provides the exact workflow for batch execution with checkpoints.

---

## Ready?

Start by:
1. Reading the plan file
2. Invoking `superpowers:executing-plans`
3. Executing the first 3 tasks (Phase 1 CRITICAL)

**Good luck! 🚀**
