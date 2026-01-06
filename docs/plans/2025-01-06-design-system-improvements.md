# Design System Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish a consistent design system with spacing scale, fix typography grid alignment, and apply design tokens across components.

**Architecture:**
- Create new spacing scale utility following 4px grid system
- Update typography tokens to align with 4px grid (12px, 16px, 20px, 24px, 32px)
- Refactor components to use design tokens instead of hardcoded values
- Extract magic strings into named constants for maintainability

**Tech Stack:**
- TypeScript
- React (Raycast Extension API)
- Vitest (testing)
- ESLint (linting)

**Prerequisites:**
- Backend running: `make dev`
- Raycast dev server: `cd dashboard && npm run dev`
- All tests passing: `npm test`

---

## Task 1: Create Spacing Scale Utility

**Files:**
- Create: `dashboard/src/core/design/spacing.ts`

**Step 1: Write the spacing scale utility**

```typescript
/**
 * Spacing scale following 4px grid system
 * All spacing values derive from base 4px unit
 */
export const spacing = {
  xs: "4px",   // 1 unit - micro spacing (icon gaps, tight padding)
  sm: "8px",   // 2 units - tight spacing (within components)
  md: "16px",  // 4 units - standard spacing (between related elements)
  lg: "24px",  // 6 units - comfortable spacing (section padding)
  xl: "32px",  // 8 units - major separation (between sections)
} as const;

export type SpacingValue = keyof typeof spacing;

/**
 * Get spacing value by key
 */
export function getSpacing(value: SpacingValue): string {
  return spacing[value];
}

/**
 * Helper for inline styles requiring spacing
 */
export const gap = {
  xs: spacing.xs,
  sm: spacing.sm,
  md: spacing.md,
  lg: spacing.lg,
  xl: spacing.xl,
} as const;
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Add export to design barrel (optional)**

If `dashboard/src/core/design/index.ts` exists, add:
```typescript
export * from "./spacing";
```

**Step 4: Commit**

```bash
git add dashboard/src/core/design/spacing.ts
git commit -m "feat(design): add 4px grid spacing scale

- Implements xs/sm/md/lg/xl spacing tokens
- Provides getSpacing helper for type-safe access
- Follows design-principles 4px grid system"
```

---

## Task 2: Fix Typography Scale to 4px Grid

**Files:**
- Modify: `dashboard/src/core/design/tokens.ts`

**Step 1: Read current tokens file**

Run: `cat dashboard/src/core/design/tokens.ts`

**Step 2: Update fontSize to align with 4px grid**

Replace the fontSize object:

```typescript
export const fontSize = {
  xs: "12px",   // Was 11px - align to 4px grid (3 units)
  sm: "16px",   // Was 14px - align to 4px grid (4 units)
  base: "16px", // Unchanged
  lg: "24px",   // Unchanged (6 units)
  xl: "32px",   // Unchanged (8 units)
  "2xl": "48px", // Add for completeness (12 units)
} as const;
```

**Step 3: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 4: Run tests to ensure no regressions**

Run: `cd dashboard && npm test`
Expected: All tests pass (113 passed, 6 skipped)

**Step 5: Commit**

```bash
git add dashboard/src/core/design/tokens.ts
git commit -m "fix(design): align typography scale to 4px grid

- Change 11px → 12px (3 units)
- Change 14px → 16px (4 units)
- Add 48px (12 units) for completeness
- Improves consistency with spacing system"
```

---

## Task 3: Use Color Tokens in ToastHelper

**Files:**
- Modify: `dashboard/src/core/design/toast.tsx`

**Step 1: Add color token usage**

At the top of the file, add import:

```typescript
import { tokens } from "./tokens";
```

**Step 2: Replace hardcoded emoji with semantic tokens**

Update the icon method (around line 50-60):

```typescript
static icon(type: "success" | "error" | "loading"): string {
  const icons = {
    success: tokens.color.success.icon || "✅",
    error: tokens.color.error.icon || "❌",
    loading: "⏳",
  };
  return icons[type];
}
```

**Step 3: Update tokens.ts to include icon mappings**

Add to `dashboard/src/core/design/tokens.ts` in the color object:

```typescript
export const tokens = {
  color: {
    // ... existing colors ...
    success: {
      light: "#10b981",
      dark: "#059669",
      icon: "✅",
    },
    error: {
      light: "#ef4444",
      dark: "#dc2626",
      icon: "❌",
    },
    // ... rest of colors ...
  },
};
```

**Step 4: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 5: Run tests**

Run: `cd dashboard && npm test`
Expected: All tests pass

**Step 6: Test manually in Raycast**

1. Run dev server: `cd dashboard && npm run dev`
2. Open "Promptify Quick" command
3. Submit a prompt
4. Verify toast icons appear correctly

**Step 7: Commit**

```bash
git add dashboard/src/core/design/toast.tsx dashboard/src/core/design/tokens.ts
git commit -m "refactor(design): use semantic color tokens in ToastHelper

- Replace hardcoded emoji with token-based icons
- Add icon mappings to success/error color tokens
- Improves consistency and makes icons themeable"
```

---

## Task 4: Extract Constants from promptify-quick.tsx

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Extract ENGINE_NAMES constant**

Add at top of file after imports:

```typescript
// Engine display names (used in metadata)
const ENGINE_NAMES = {
  dspy: "DSPy + Haiku",
  ollama: "Ollama",
} as const;
```

**Step 2: Extract PLACEHOLDERS constant**

Add after ENGINE_NAMES:

```typescript
// Preset placeholders for input textarea
const PLACEHOLDERS = {
  default: "Paste your rough prompt here… (⌘I to improve)",
  specific: "What specific task should this prompt accomplish?",
  structured: "Paste your prompt - we'll add structure and clarity…",
  coding: "Describe what you want the code to do…",
} as const;
```

**Step 3: Replace inline engine names**

Find and replace in PromptPreview component:
- `props.source === "dspy" ? "DSPy + Haiku" : "Ollama"` → `ENGINE_NAMES[props.source]`

Find and replace in metadata:
- `props.source === "dspy" ? "DSPy + Haiku" : "Ollama"` → `ENGINE_NAMES[props.source]`

**Step 4: Replace placeholder function**

Replace the entire getPlaceholder function:

```typescript
function getPlaceholder(preset?: "default" | "specific" | "structured" | "coding"): string {
  return PLACEHOLDERS[preset || "structured"];
}
```

**Step 5: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 6: Run tests**

Run: `cd dashboard && npm test`
Expected: All tests pass

**Step 7: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "refactor(ui): extract magic strings to named constants

- Extract ENGINE_NAMES for consistent engine display
- Extract PLACEHOLDERS for preset-specific input text
- Improves maintainability and reduces duplication"
```

---

## Task 5: Create MetadataGroup Reusable Component (Optional)

**Files:**
- Create: `dashboard/src/core/design/MetadataGroup.tsx`
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Write MetadataGroup component**

Create new file:

```typescript
import { Detail } from "@raycast/api";
import { Typography } from "./typography";

interface MetadataItem {
  title: string;
  text: string;
  icon?: string;
}

interface MetadataGroupProps {
  items: MetadataItem[];
}

/**
 * Reusable metadata group for Detail views
 * Automatically handles separators between items
 */
export function MetadataGroup(props: MetadataGroupProps) {
  return (
    <>
      {props.items.map((item, index) => (
        <React.Fragment key={item.title || index}>
          <Detail.Metadata.Label
            title={item.title}
            text={item.text}
            icon={item.icon}
          />
          {index < props.items.length - 1 && <Detail.Metadata.Separator />}
        </React.Fragment>
      ))}
    </>
  );
}
```

**Step 2: Update promptify-quick.tsx to use MetadataGroup**

Import the component:

```typescript
import { MetadataGroup } from "./core/design/MetadataGroup";
```

Replace the metadata section (around line 83-131):

```typescript
metadata={
  <Detail.Metadata>
    <MetadataGroup
      items={[
        {
          title: "Confidence",
          text: `${Math.round(props.meta.confidence)}%`,
          icon: Typography.confidenceIcon(props.meta.confidence),
        },
        {
          title: "Questions",
          text: Typography.count("Questions", props.meta.clarifyingQuestions.length),
        },
        {
          title: "Assumptions",
          text: Typography.count("Assumptions", props.meta.assumptions.length),
        },
        {
          title: "Length",
          text: `${props.prompt.length} chars`,
          icon: Typography.countSymbol("Characters"),
        },
        {
          title: "Words",
          text: `${props.prompt.split(/\s+/).length}`,
          icon: Typography.countSymbol("Words"),
        },
        {
          title: "Engine",
          text: ENGINE_NAMES[props.source],
          icon: Typography.engine(props.source),
        },
      ]}
    />
  </Detail.Metadata>
}
```

**Step 3: Add React import**

Add to imports at top:

```typescript
import React from "react";
```

**Step 4: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 5: Test manually**

Run: `cd dashboard && npm run dev`
Open "Promptify Quick" and verify metadata displays correctly

**Step 6: Commit**

```bash
git add dashboard/src/core/design/MetadataGroup.tsx dashboard/src/promptify-quick.tsx
git commit -m "feat(design): add reusable MetadataGroup component

- Extract repeated metadata rendering pattern
- Simplify PromptPreview metadata section
- Improves consistency across Detail views"
```

---

## Task 6: Run Full Test Suite and Linting

**Files:**
- None (verification task)

**Step 1: Run full test suite**

Run: `cd dashboard && npm test`
Expected: All tests pass (113 passed, 6 skipped)

**Step 2: Run TypeScript check**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Run ESLint**

Run: `cd dashboard && npm run lint`
Expected: No linting errors

**Step 4: Manual smoke test**

1. Start dev: `cd dashboard && npm run dev`
2. Test "Promptify Quick" command
3. Test "Promptify Selected" command
4. Verify toasts appear with correct icons
5. Verify metadata displays correctly
6. Verify spacing looks consistent

**Step 5: Create summary commit**

```bash
git add .
git commit -m "chore: design system improvements complete

✅ Implemented 4px grid spacing scale
✅ Fixed typography to align with 4px grid
✅ Applied color tokens to ToastHelper
✅ Extracted magic strings to constants
✅ Created reusable MetadataGroup component

All tests passing, ready for review"
```

---

## Verification Checklist

Before considering this plan complete:

- [ ] All TypeScript files compile without errors
- [ ] All tests pass (113 passed, 6 skipped)
- [ ] No ESLint warnings or errors
- [ ] Manual testing completed in Raycast
- [ ] Design tokens used in at least 2 components
- [ ] Constants extracted for all repeated strings
- [ ] Git history shows clean, logical commits

---

## Next Steps After Implementation

1. **Documentation**: Update `docs/CLAUDE.md` with design system usage
2. **Component Library**: Consider creating `Button`, `Card`, etc. using the new tokens
3. **Testing**: Add visual regression tests for UI components
4. **Migration**: Gradually update other components to use design tokens

---

## References

- Design principles skill: `/Users/felipe_gonzalez/.claude/skills/design-principles/skill.md`
- Current design tokens: `dashboard/src/core/design/tokens.ts`
- Typography utilities: `dashboard/src/core/design/typography.ts`
- Raycast API docs: https://developers.raycast.com
