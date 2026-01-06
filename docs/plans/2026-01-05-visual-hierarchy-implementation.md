# Visual Hierarchy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve visual hierarchy in Prompt Improver UI through markdown formatting and DSPy quality signaling

**Architecture:** Hybrid approach (Tiered Metadata + Content-First) - Confidence score as quality hero, improved prompt as main event, metadata organized into three tiers (Quality → Content → Technical)

**Tech Stack:** React, TypeScript, Raycast API, existing Typography utility class

---

## Task 1: Add "## Improved Prompt" Header to Markdown

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:30-49`

**Step 1: Read current markdown generation code**

Read: `dashboard/src/promptify-quick.tsx` lines 30-49
Understand: How sections array is built and joined

**Step 2: Modify markdown to include header**

Find the `PromptPreview` component's `sections.push()` logic (around line 34).

**Current code (line 34):**
```typescript
// Main prompt in code block
sections.push("```text", props.prompt, "```");
```

**Change to:**
```typescript
// Header and main prompt in code block
sections.push("## Improved Prompt", "", "```text", props.prompt, "```");
```

**Step 3: Verify the change**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard && npx ray build`
Expected: Build succeeds with no TypeScript errors

**Step 4: Commit**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add 'Improved Prompt' header to result markdown

Makes the improved prompt feel like the main event by adding
a clear header before the code block. This reinforces the
content-first visual hierarchy."

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 2: Add Blank Lines for Visual Breathing Room

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:36-49`

**Step 1: Read current section structure**

Read: `dashboard/src/promptify-quick.tsx` lines 36-49
Observe: How Clarifying Questions and Assumptions sections are built

**Step 2: Add blank lines before section headers**

**Current code (lines 37-48):**
```typescript
if (props.meta?.clarifyingQuestions?.length) {
  sections.push("", "### Clarifying Questions", "");
  props.meta.clarifyingQuestions.forEach((q, i) => {
    sections.push(`${i + 1}. ${q}`);
  });
}

if (props.meta?.assumptions?.length) {
  sections.push("", "### Assumptions", "");
  props.meta.assumptions.forEach((a, i) => {
    sections.push(`${i + 1}. ${a}`);
  });
}
```

**Change to:**
```typescript
if (props.meta?.clarifyingQuestions?.length) {
  sections.push("", "", "### Clarifying Questions", "");
  props.meta.clarifyingQuestions.forEach((q, i) => {
    sections.push(`${i + 1}. ${q}`);
  });
}

if (props.meta?.assumptions?.length) {
  sections.push("", "", "### Assumptions", "");
  props.meta.assumptions.forEach((a, i) => {
    sections.push(`${i + 1}. ${a}`);
  });
}
```

**What changed:** Added one extra blank line (`""`) before each section header to create visual separation from the main prompt.

**Step 3: Verify the change**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard && npx ray build`
Expected: Build succeeds with no TypeScript errors

**Step 4: Commit**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add visual breathing room around supporting sections

Extra blank lines before Clarifying Questions and Assumptions
sections make them feel like supporting detail rather than
competing with the main improved prompt."

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 3: Add DSPy Quality Signal to Improve Prompt Subtitle

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:324-327`

**Step 1: Read current Improve Prompt action**

Read: `dashboard/src/promptify-quick.tsx` lines 323-330
Observe: The Action.SubmitForm component and its subtitle

**Step 2: Add DSPy quality indicator to subtitle**

**Current code (line 325):**
```typescript
subtitle={`${dspyEnabled ? "DSPy + " : ""}${Typography.truncate(preferences.model || "Ollama", 20)}`}
```

**Change to:**
```typescript
subtitle={`${dspyEnabled ? "DSPy ⤒ " : ""}${Typography.truncate(preferences.model || "Ollama", 20)}`}
```

**What changed:** Added the ⤒ (forward/advanced) symbol after "DSPy" to signal higher quality. This uses the existing `Typography.engine()` symbol system where ⤒ means "forward/advanced" (DSPy) vs ○ (basic/Ollama).

**Step 3: Verify the change**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard && npx ray build`
Expected: Build succeeds with no TypeScript errors

**Step 4: Commit**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add DSPy quality signal to Improve Prompt subtitle

The ⤒ symbol (from Typography.engine) signals that DSPy is the
advanced/high-quality engine vs basic Ollama. This reinforces
the quality hierarchy in the input view."

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 4: Manual Testing in Raycast

**Files:**
- None (manual verification)

**Step 1: Rebuild the extension**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard && npx ray build`
Expected: Build completes successfully

**Step 2: Reload extension in Raycast**

1. Open Raycast
2. Go to Preferences → Extensions
3. Find "Prompt Improver" (thomas.prompt-renderer-local)
4. Disable it
5. Enable it again

**Step 3: Test result view hierarchy**

1. Trigger the extension (⌘+Space → "Prompt Improver" or "improve prompt")
2. Enter a test prompt: "write a function to sort numbers"
3. Press ⌘⇧↩ to improve
4. **Verify:**
   - "## Improved Prompt" header appears above the code block ✅
   - Blank lines create visual separation before Q&A sections ✅
   - Confidence score is first in metadata sidebar ✅
   - Improved prompt feels like the main event ✅

**Step 4: Test input view DSPy signal**

1. Press ⌘⇧R to "Try again" (back to input)
2. **Verify:**
   - "Improve Prompt" subtitle shows "DSPy ⤒ [modelname]" when DSPy enabled ✅
   - Quality symbol is visible and recognizable ✅

**Step 5: Test with DSPy disabled (optional)**

1. Go to Raycast Preferences → Extensions → Prompt Improver
2. Uncheck "Enable DSPy" or similar setting
3. Test again: subtitle should show "[modelname]" without DSPy ⤒

---

## Task 5: Final Verification and Documentation

**Files:**
- Create: `docs/plans/2026-01-05-visual-hierarchy-design.md` ✅ (already created)
- Update: `CLAUDE.md` (if needed)

**Step 1: Verify all changes are committed**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && git status`
Expected: Clean working tree (all changes committed)

**Step 2: Review commit history**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && git log --oneline -5`
Expected: Three new commits for header, spacing, and DSPy signal

**Step 3: Create summary documentation (if needed)**

If CLAUDE.md doesn't mention the visual hierarchy improvements, consider adding a brief note in the "Quick Start" or "Architecture" section.

---

## Success Criteria

After implementation, verify:

1. ✅ **Result view hierarchy:** Eye flows to Confidence → Improved Prompt → Details
2. ✅ **Header visibility:** "## Improved Prompt" clearly frames the main content
3. ✅ **Visual breathing room:** Supporting sections (Q&A, Assumptions) feel secondary
4. ✅ **Quality signal:** DSPy ⤒ symbol is visible in input view subtitle
5. ✅ **Metadata organization:** Three-tier structure (Quality → Content → Technical) is maintained

## Design Reference

See `docs/plans/2026-01-05-visual-hierarchy-design.md` for full design rationale and principles applied (Precision & Density aesthetic, geometric symbols, color for meaning only).

## Notes

- No automated tests needed: These are markdown/formatting changes verified by visual inspection
- The Typography utility class already provides the ⤒ symbol via `Typography.engine("dspy")`
- Metadata sidebar structure (lines 62-110) already implements correct tiered hierarchy - no changes needed
- Action panel structure (lines 112-152) already has correct Primary/Advanced/Settings grouping - no changes needed
