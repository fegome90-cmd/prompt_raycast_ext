# Visual Hierarchy Design for Prompt Improver

**Date:** 2026-01-05
**Designer:** Claude ( Elle ) with design-principles skill
**Status:** Approved for implementation

## Problem Statement

The Prompt Improver UI has solid foundations (Precision & Density aesthetic, geometric symbols, clean metadata organization) but suffers from three visual hierarchy issues:

1. **Primary actions blend in** - Key actions (Copy, Improve) don't stand out from secondary actions
2. **Metadata is flat** - Confidence score, questions count, and other metrics fight for attention equally
3. **Result content doesn't dominate** - The improved prompt doesn't feel like the "main event"

## Design Direction: Hybrid (Tiered Metadata + Content-First)

Combines Approach 1 (Confidence as quality hero) with Approach 2 (Prompt as main event) for balanced information hierarchy.

**Philosophy:** Quality assurance (confidence score) + Content focus (improved prompt text) = Trust + Utility

## Implementation Plan

### 1. Metadata Hierarchy (Tiered)

**Current:** All metadata labels appear equally - confidence, questions, assumptions, length, words, engine.

**Changes:**
- **Confidence as hero:** Keep first in sidebar, icon (◉◎○) + percentage reads like a grade
- **Content metrics:** Questions/Assumptions only if present, compact format
- **Technical stats recede:** Length, Words, Engine in supporting section (already grouped via Separator ✅)

**Code:** `promptify-quick.tsx:62-110` (already correctly structured)

### 2. Result Content Presentation (Main Event)

**Current markdown:**
```markdown
```text
[prompt]
```

### Clarifying Questions
1. [questions]

### Assumptions
1. [assumptions]
```

**Changes:**
- Add "## Improved Prompt" header before code block
- Add blank lines for breathing room
- Sections feel secondary to main prompt

**New markdown:**
```markdown
## Improved Prompt

```text
[prompt]
```

### Clarifying Questions

1. [questions]

### Assumptions

1. [assumptions]
```

**Code:** `promptify-quick.tsx:30-49` (PromptPreview component)

### 3. Action Hierarchy

**Current:** Primary Actions → Advanced → Settings (already correct ✅)

**No changes needed** - The three-section structure works perfectly:
- Primary: Copy prompt, Try again
- Advanced: Copy with stats (kept for future extensibility)
- Settings: Preferences

### 4. Input View Enhancement

**Current subtitle:** Shows model name (e.g., "DSPy + Haiku" or "Ollama - llama3.2")

**Enhancement:** Add DSPy quality signal when enabled
- When `dspyEnabled`: Show "DSPy ⤒" to signal advanced/quality
- Keeps existing model truncation via `Typography.truncate()`

**Code:** `promptify-quick.tsx:325` (Improve Prompt subtitle)

## Design Principles Applied

From `design-principles` skill:

- **Precision & Density:** Information-forward, technical aesthetic (geometric symbols, no emojis)
- **Typography Hierarchy:** Clear levels (Confidence → Content → Technical)
- **Color for Meaning Only:** Monochrome structure, icons only for functional signaling
- **Symmetrical Padding:** Consistent spacing via Raycast's layout system
- **YAGNI:** No unnecessary features, just clarify what exists

## Success Criteria

1. Eye flow: Confidence score → Improved prompt → Details (on closer look)
2. Actions: Primary actions (Copy, Try again) are unmistakable
3. Content: Improved prompt feels like the main event
4. Quality signal: DSPy engine is recognizable as higher quality

## Files to Modify

1. `dashboard/src/promptify-quick.tsx` - Main UI component
   - Lines 30-49: Markdown formatting (PromptPreview)
   - Line 325: DSPy quality signal in subtitle

## Testing

- [ ] Test with DSPy enabled (confidence score should be prominent)
- [ ] Test with DSPy disabled (Ollama mode should still look good)
- [ ] Test with no questions/assumptions (metadata should condense)
- [ ] Test with long model names (truncate should work)

## Future Enhancements (Out of Scope)

- "Save to library" action (in Advanced section)
- "Compare versions" action (in Advanced section)
- History view with previous improvements
- Confidence trend over time
