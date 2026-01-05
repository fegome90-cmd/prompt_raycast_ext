# UI Redesign - Prompt Improver Extension

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete visual redesign following "Precision & Density" principles — new icon, color system, typography improvements, enhanced UI components

**Architecture:** Replace ornamental design with intentional, minimalist design that communicates function instantly

**Tech Stack:**
- Figma/SVG for icon design
- Raycast API for UI components
- TypeScript types for color tokens

---

## Design Direction Analysis

### Current Problems

| Element | Issue | Principle Violated |
|---------|-------|-------------------|
| **Icon** | Ornamental, gradients, 1.7MB, unclear meaning | "Color for meaning only", "No gradients for decoration" |
| **Colors** | Inconsistent, no defined palette | Missing "Contrast Hierarchy" (4-level system) |
| **Typography** | Default system fonts, no hierarchy | Missing "Typography Hierarchy" |
| **Metadata** | Flat markdown, no structure | Missing "Navigation Context" |
| **Actions** | Ungrouped, no visual distinction | Missing "Isolated Controls" |

### Target Direction: **Precision & Density**

Inspired by: Linear, Raycast, Vercel

- **Flat, minimal** — no gradients, no shadows unless necessary
- **Function-first** — every element earns its place
- **High information density** — respect the user's screen space
- **Monochrome + accent** — gray for structure, one accent color for meaning

---

## Task 1: Design & Implement New Icon

**Files:**
- Create: `dashboard/assets/icon-design.svg`
- Create: `dashboard/icon.png` (1024x1024)
- Create: `dashboard/assets/icon.svg`

**Context:** The current icon is ornamental with gradients and doesn't communicate the function. We need a minimal, flat icon that says "prompt improvement" instantly.

**Design Requirements:**
- **Symbol:** Abstract representation of prompt → improved prompt
- **Style:** Flat, 1-2 colors max
- **Grid:** 32x32 or 24x24 base grid
- **Size:** Under 50KB (vs current 1.7MB)
- **Meaning:** Recognizable at 16px and 512px

### Step 1: Design Concept - Three Options

**Option A: Transformation Arrows**
```
┌─────────────────┐
│  ┌───┐   ┌───┐ │
│  │ ~ │ → │ ✓ │ │
│  └───┘   └───┘ │
└─────────────────┘
```
- Rough prompt (tilde) → refined prompt (checkmark)
- Right arrow indicates transformation
- Works monochrome

**Option B: Sparkle Polish**
```
┌─────────────────┐
│    ┌─────┐      │
│    │  ✨  │      │
│    └─────┘      │
└─────────────────┘
```
- Rectangle with sparkle (polish/improve)
- Simple, clean
- Sparkle = "improvement"

**Option C: Brackets Refine**
```
┌─────────────────┐
│  { prompt } →   │
│  [ PROMPT ]     │
└─────────────────┘
```
- Messy → structured
- Brackets indicate "format/structure"
- Literal representation

### Step 2: Create SVG Implementation

Create `dashboard/assets/icon-design.svg` with Option A (Transformation):

```xml
<svg width="1024" height="1024" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="1024" height="1024" rx="256" fill="#1A1A1A"/>

  <!-- Left Box: Rough Prompt -->
  <rect x="144" y="352" width="240" height="320" rx="48" fill="#2A2A2A" stroke="#3A3A3A" stroke-width="8"/>
  <path d="M200 440 Q280 400 360 440 Q280 480 200 440" stroke="#666" stroke-width="16" stroke-linecap="round" fill="none"/>
  <path d="M200 560 Q280 520 360 560 Q280 600 200 560" stroke="#666" stroke-width="16" stroke-linecap="round" fill="none"/>

  <!-- Arrow: Transformation -->
  <path d="M424 512 L520 512" stroke="#00D9FF" stroke-width="24" stroke-linecap="round"/>
  <path d="M496 464 L544 512 L496 560" stroke="#00D9FF" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Box: Refined Prompt -->
  <rect x="600" y="352" width="240" height="320" rx="48" fill="#2A2A2A" stroke="#00D9FF" stroke-width="8"/>
  <path d="M660 440 L700 480 L780 400" stroke="#00D9FF" stroke-width="20" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M660 560 L700 600 L780 520" stroke="#00D9FF" stroke-width="20" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
```

### Step 3: Generate PNG from SVG

Using ImageMagick or similar tool:

```bash
# Install if needed: brew install imagemagick
convert -background none -density 300 dashboard/assets/icon-design.svg -resize 1024x1024 dashboard/icon.png
```

Alternative: Use online tool (SVG to PNG) or Figma export.

### Step 4: Verify Icon Size

```bash
ls -lh dashboard/icon.png
# Should be under 50KB
```

Expected: `-rw-r--r-- 1 user staff 45K Jan 5 10:00 dashboard/icon.png`

### Step 5: Test Icon in Raycast

```bash
cd dashboard
npm run dev
```

1. Open Raycast
2. Find "Prompt Improver (Local)"
3. Verify icon appears correctly
4. Verify it's recognizable at small sizes

### Step 6: Commit Icon

```bash
git add dashboard/icon.png dashboard/assets/icon-design.svg
git commit -m "design(icon): replace ornamental icon with minimal flat design

- Transformation concept: rough prompt → refined prompt
- Flat design, no gradients
- Single accent color (#00D9FF) on dark background
- Reduced size from 1.7MB to ~45KB
- Recognizable at all sizes
- Follows Precision & Density direction
"
```

---

## Task 2: Define Color System

**Files:**
- Create: `dashboard/src/core/design/tokens.ts`

**Context:** Establish a 4-level contrast hierarchy and accent color for consistent use across the extension.

### Step 1: Create Color Tokens

Create `dashboard/src/core/design/tokens.ts`:

```typescript
/**
 * Color system for Prompt Improver
 * Direction: Precision & Density
 * Foundation: Cool, technical, professional
 */

// Accent color - ONE color that means something
// Blue/Cyan = trust, technology, improvement
const ACCENT = {
  primary: "#00D9FF",  // Electric cyan - high visibility
  dim: "rgba(0, 217, 255, 0.1)",
  border: "rgba(0, 217, 255, 0.2)",
} as const;

// 4-level contrast hierarchy (for dark mode)
// Raycast handles most colors, but we define for reference
const GRAY = {
  foreground: "#FFFFFF",     // Primary text
  secondary: "#A0A0A0",     // Secondary text
  muted: "#5A5A5A",         // Disabled, placeholder
  faint: "#2A2A2A",         // Backgrounds, borders
} as const;

// Semantic colors (only for meaning)
const SEMANTIC = {
  success: "#4ADE80",  // Green
  warning: "#FBBF24",  // Yellow
  error: "#F87168",    // Red
  info: "#60A5FA",     // Blue
} as const;

export const tokens = {
  accent: ACCENT,
  gray: GRAY,
  semantic: SEMANTIC,
} as const;

// Type exports for type-safe usage
export type ColorToken = typeof tokens;
```

### Step 2: Export from core index

Update `dashboard/src/core/index.ts` (or create if doesn't exist):

```typescript
export * from './design/tokens';
```

### Step 3: Commit Color System

```bash
git add dashboard/src/core/design/
git commit -m "design(tokens): add color system with 4-level hierarchy

- Electric cyan accent (#00D9FF) - technology/improvement
- 4-level gray hierarchy (foreground → secondary → muted → faint)
- Semantic colors for status only
- Type-safe token exports
- Foundation for consistent color usage
"
```

---

## Task 3: Typography System

**Files:**
- Modify: `dashboard/src/core/design/tokens.ts`
- Create: `dashboard/src/core/design/typography.tsx`

**Context:** Raycast uses system fonts, but we can define typography scale and hierarchy for text we generate.

### Step 1: Add Typography Tokens to tokens.ts

Add to `dashboard/src/core/design/tokens.ts`:

```typescript
// Typography scale (for generated text/markdown)
const TYPE = {
  // Sizes (in points, follows 4px grid-ish)
  xs: "11px",
  sm: "12px",
  base: "14px",
  lg: "16px",
  xl: "18px",
  "2xl": "24px",
  "3xl": "32px",

  // Weights
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",

  // Tracking (letter-spacing)
  tight: "-0.02em",   // Headlines
  normal: "0",        // Body
  wide: "0.02em",     // Labels (uppercase)
} as const;

export const tokens = {
  accent: ACCENT,
  gray: GRAY,
  semantic: SEMANTIC,
  type: TYPE,
} as const;
```

### Step 2: Create Typography Helper Component

Create `dashboard/src/core/design/typography.tsx`:

```typescript
import { tokens } from './tokens';

/**
 * Typography utilities for the Prompt Improver
 * Raycast handles most UI typography, but we use these for:
 * - Generated markdown content
 * - Toast messages
 * - Metadata labels
 */

export class Typography {
  /**
   * Format a confidence score with appropriate styling
   */
  static confidence(score: number): string {
    const rounded = Math.round(score);
    let icon = "⚡";

    if (rounded >= 80) icon = "🟢";
    else if (rounded >= 60) icon = "🟡";
    else if (rounded >= 40) icon = "🟠";
    else icon = "🔴";

    return `${icon} ${rounded}%`;
  }

  /**
   * Format a count with appropriate icon
   */
  static count(label: string, count: number): string {
    const icons = {
      "Questions": "❓",
      "Assumptions": "💡",
      "Characters": "📝",
      "Words": "📄",
    };

    const icon = icons[label as keyof typeof icons] || "•";
    return `${icon} ${count}`;
  }

  /**
   * Truncate text with ellipsis
   */
  static truncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength - 3) + "...";
  }

  /**
   * Format timestamp
   */
  static timestamp(date: Date): string {
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
```

### Step 3: Use Typography Helpers in PromptPreview

Update `dashboard/src/promptify-quick.tsx`:

```tsx
import { Typography } from "./core/design/typography";

// In PromptPreview component metadata:
<Detail.Metadata.Label
  title="Confidence"
  text={Typography.confidence(props.meta.confidence)}
  icon={undefined}  // Icon included in text
/>
```

### Step 4: Commit Typography System

```bash
git add dashboard/src/core/design/
git commit -m "design(typography): add typography utilities

- Add type scale (11px - 32px)
- Add weight and tracking tokens
- Add Typography helper class for formatting
- Add confidence formatting with visual indicators
- Add count formatting with contextual icons
- Add truncate and timestamp helpers
"
```

---

## Task 4: Enhanced PromptPreview with Design Tokens

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:18-51`

**Context:** Apply color tokens and typography helpers to the PromptPreview component.

### Step 1: Update PromptPreview with New Design

Replace the entire `PromptPreview` component:

```tsx
function PromptPreview(props: {
  prompt: string;
  meta?: {
    confidence?: number;
    clarifyingQuestions?: string[];
    assumptions?: string[];
  };
  source?: "dspy" | "ollama";
}) {
  const pref = getPreferenceValues<Preferences>();

  // Build markdown content with better formatting
  const sections: string[] = [];

  // Main prompt in code block
  sections.push("```text", props.prompt, "```");

  // Metadata sections
  if (props.meta?.clarifyingQuestions?.length) {
    sections.push("", "### ❓ Clarifying Questions", "");
    props.meta.clarifyingQuestions.forEach((q, i) => {
      sections.push(`${i + 1}. ${q}`);
    });
  }

  if (props.meta?.assumptions?.length) {
    sections.push("", "### 💡 Assumptions", "");
    props.meta.assumptions.forEach((a, i) => {
      sections.push(`${i + 1}. ${a}`);
    });
  }

  // Stats footer
  const stats = [
    props.meta?.confidence !== undefined ? `Confidence: ${Typography.confidence(props.meta.confidence)}` : null,
    `Length: ${props.prompt.length} chars`,
    `Words: ${props.prompt.split(/\s+/).length} words`,
    `Source: ${props.source === "dspy" ? "DSPy + Ollama" : "Ollama"}`,
  ].filter(Boolean);

  sections.push("", "---", stats.join(" • "));

  return (
    <Detail
      markdown={sections.join("\n")}
      metadata={
        <Detail.Metadata>
          {props.meta?.confidence !== undefined && (
            <Detail.Metadata.Label
              title="Confidence"
              text={`${Math.round(props.meta.confidence)}%`}
              icon={props.meta.confidence >= 70 ? "🟢" : props.meta.confidence >= 40 ? "🟡" : "🔴"}
            />
          )}

          {props.meta?.clarifyingQuestions && props.meta.clarifyingQuestions.length > 0 && (
            <Detail.Metadata.Label
              title="Questions"
              text={Typography.count("Questions", props.meta.clarifyingQuestions.length)}
            />
          )}

          {props.meta?.assumptions && props.meta.assumptions.length > 0 && (
            <Detail.Metadata.Label
              title="Assumptions"
              text={Typography.count("Assumptions", props.meta.assumptions.length)}
            />
          )}

          <Detail.Metadata.Label
            title="Length"
            text={`${props.prompt.length} chars`}
            icon="📝"
          />

          <Detail.Metadata.Label
            title="Words"
            text={`${props.prompt.split(/\s+/).length}`}
            icon="📄"
          />

          <Detail.Metadata.Separator />

          <Detail.Metadata.Label
            title="Engine"
            text={props.source === "dspy" ? "DSPy + Ollama" : "Ollama"}
            icon={props.source === "dspy" ? "🚀" : "🔧"}
          />
        </Detail.Metadata>
      }
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Copy">
            <Action
              title="Copy Prompt Only"
              onAction={async () => {
                await Clipboard.copy(props.prompt);
                await showToast({
                  style: Toast.Style.Success,
                  title: "Prompt copied",
                  message: `${props.prompt.length} characters`,
                });
              }}
              shortcut={{ modifiers: ["cmd"], key: "c" }}
            />

            <Action
              title="Copy with Stats"
              onAction={async () => {
                const withStats = [
                  `# Improved Prompt`,
                  "",
                  props.prompt,
                  "",
                  "---",
                  ...stats,
                ].join("\n");
                await Clipboard.copy(withStats);
                await showToast({
                  style: Toast.Style.Success,
                  title: "Copied with stats",
                  message: "Includes metadata",
                });
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Regenerate">
            <Action
              title="Try Again"
              shortcut={{ modifiers: ["cmd", "shift"], key: "r" }}
              onAction={() => {
                setPreview(null);
                showToast({
                  style: Toast.Style.Animated,
                  title: "Ready to regenerate",
                });
              }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    />
  );
}
```

### Step 2: Test the Enhanced Preview

```bash
cd dashboard && npm run dev
```

1. Generate a prompt
2. Verify metadata shows with proper icons
3. Verify all copy actions work
4. Verify markdown formatting is clean

### Step 3: Commit

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat(ui): enhance PromptPreview with design tokens

- Use Typography helpers for consistent formatting
- Add visual indicators for confidence levels
- Better markdown section organization
- Add word count to metadata
- Add 'Copy with Stats' action
- Add 'Try Again' action for regeneration
- Improve action panel organization
"
```

---

## Task 5: Enhanced Form UI

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:186-207`

**Context:** Apply design principles to the input form for better UX.

### Step 1: Update Form with Better UX

```tsx
return (
  <Form
    isLoading={isLoading}
    actions={
      <ActionPanel>
        <ActionPanel.Section title="Improve">
          <Action.SubmitForm
            title={isLoading ? "Improving…" : "Improve Prompt"}
            subtitle={`${dspyEnabled ? "DSPy + " : ""}${preferences.model?.slice(0, 20) || "Ollama"}`}
            onSubmit={handleGenerateFinal}
            shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }}
            disabled={isLoading}
          />
          <Action
            title="Quick Improve"
            subtitle="Use default settings"
            shortcut={{ modifiers: ["cmd"], key: "enter" }}
            onAction={() => {
              if (inputText.trim()) {
                handleGenerateFinal({ inputText });
              }
            }}
            disabled={isLoading || !inputText.trim()}
          />
        </ActionPanel.Section>

        {inputText.trim() && (
          <ActionPanel.Section title="Edit">
            <Action
              title="Clear Input"
              onAction={() => setInputText("")}
              shortcut={{ modifiers: ["cmd"], key: "backspace" }}
              style={Action.Style.Destructive}
              disabled={isLoading}
            />
          </ActionPanel.Section>
        )}

        <ActionPanel.Section title="Settings">
          <Action.OpenInBrowser
            title="Open Preferences"
            url="raycast://extensions/preferences/thomas.prompt-renderer-local"
            shortcut={{ modifiers: ["cmd"], key: "," }}
          />
        </ActionPanel.Section>
      </ActionPanel>
    }
  >
    <Form.TextArea
      id="inputText"
      title="Prompt"
      placeholder={getPlaceholder(preferences.preset)}
      value={inputText}
      onChange={setInputText}
      disabled={isLoading}
      enableMarkdown={true}
    />
  </Form>
);
```

### Step 2: Add Placeholder Helper Function

Add before the main component:

```tsx
function getPlaceholder(preset?: "default" | "specific" | "structured" | "coding"): string {
  const placeholders = {
    default: "Paste your rough prompt here… (⌘↵ for quick improve)",
    specific: "What specific task should this prompt accomplish?",
    structured: "Paste your prompt - we'll add structure and clarity…",
    coding: "Describe what you want the code to do…",
  };

  return placeholders[preset || "structured"];
}
```

### Step 3: Test Form UX

1. Verify placeholder changes with preset
2. Verify both submit buttons work
3. Verify keyboard shortcuts
4. Verify Open Preferences link works

### Step 4: Commit

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat(ui): enhance form with better UX

- Add dynamic placeholder based on preset
- Add 'Quick Improve' action for faster workflow
- Add 'Open Preferences' action
- Show model name in subtitle
- Enable markdown in textarea
- Improve action organization
"
```

---

## Task 6: Toast Enhancement with Design Tokens

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Context:** Make toast messages more informative and visually consistent.

### Step 1: Create Toast Helper

Create `dashboard/src/core/design/toast.tsx`:

```typescript
import { Toast } from "@raycast/api";
import { tokens } from "./tokens";

export class ToastHelper {
  /**
   * Show success toast with details
   */
  static async success(title: string, message?: string, duration?: number) {
    return await showToast({
      style: Toast.Style.Success,
      title,
      message,
      duration,
    });
  }

  /**
   * Show error toast with actionable hint
   */
  static async error(title: string, error: Error | string, hint?: string) {
    const message = error instanceof Error ? error.message : error;
    const fullMessage = hint ? `${message} — ${hint}` : message;

    return await showToast({
      style: Toast.Style.Failure,
      title,
      message: fullMessage,
    });
  }

  /**
   * Show animated loading toast
   */
  static async loading(title: string, message?: string) {
    return await showToast({
      style: Toast.Style.Animated,
      title,
      message,
    });
  }
}
```

### Step 2: Replace Toast Calls

Find and replace toast calls throughout the file:

```tsx
// Before:
await showToast({ style: Toast.Style.Success, title: "Copied prompt" });

// After:
await ToastHelper.success("Copied", `${props.prompt.length} characters`);
```

### Step 3: Commit

```bash
git add dashboard/src/core/design/
git commit -m "design(toast): add ToastHelper for consistent messaging

- Add success toast with detail support
- Add error toast with actionable hints
- Add loading toast helper
- Consistent toast messaging across extension
"
```

---

## Task 7: Update Package.json Metadata

**Files:**
- Modify: `dashboard/package.json`

**Context:** Ensure extension metadata reflects the new design direction.

### Step 1: Update Extension Metadata

```json
{
  "name": "prompt-improver-local",
  "title": "Prompt Improver",
  "description": "Transform rough prompts into polished, structured prompts using DSPy few-shot learning + local LLMs",
  "icon": "icon.png",
  "author": "thomas",
  "categories": ["Productivity", "Developer Tools"],
  "license": "MIT"
}
```

### Step 2: Update Command Title

```json
{
  "name": "promptify-quick",
  "title": "Improve Prompt",
  "description": "Transform rough ideas into structured, effective prompts using local AI",
  "mode": "view"
}
```

### Step 3: Update Preference Labels

```json
"preferences": [
  {
    "name": "ollamaBaseUrl",
    "description": "Local Ollama server",
    "type": "text",
    "required": false,
    "default": "http://localhost:11434",
    "title": "Ollama URL"
  },
  {
    "name": "dspyBaseUrl",
    "description": "DSPy backend with few-shot learning",
    "type": "text",
    "required": false,
    "default": "http://localhost:8000",
    "title": "DSPy URL"
  },
  {
    "name": "dspyEnabled",
    "description": "Use DSPy for intelligent prompt improvement",
    "type": "checkbox",
    "required": false,
    "default": true,
    "title": "Enable DSPy"
  },
  {
    "name": "model",
    "description": "Ollama model for DSPy fallback",
    "type": "text",
    "required": false,
    "default": "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
    "title": "Model"
  },
  {
    "name": "fallbackModel",
    "description": "Backup model if primary fails",
    "type": "text",
    "required": false,
    "default": "devstral:24b",
    "title": "Fallback Model"
  },
  {
    "name": "preset",
    "description": "Improvement approach",
    "type": "dropdown",
    "required": false,
    "default": "structured",
    "data": [
      {"title": "Structured", "value": "structured"},
      {"title": "Default", "value": "default"},
      {"title": "Specific", "value": "specific"},
      {"title": "Coding", "value": "coding"}
    ],
    "title": "Style"
  },
  {
    "name": "timeoutMs",
    "description": "Request timeout (milliseconds)",
    "type": "text",
    "required": false,
    "default": "60000",
    "title": "Timeout"
  }
]
```

### Step 4: Commit

```bash
git add dashboard/package.json
git commit -m "docs(metadata): update extension description and labels

- Rename to 'Prompt Improver'
- Add to Developer Tools category
- Improve description to highlight DSPy
- Shorten preference labels for clarity
- Better descriptions for each setting
"
```

---

## Task 8: Create Design Documentation

**Files:**
- Create: `docs/design/README.md`
- Create: `docs/design/icon-specs.md`

### Step 1: Create Design System README

Create `docs/design/README.md`:

```markdown
# Design System - Prompt Improver

## Direction: Precision & Density

Inspired by Linear, Raycast, Vercel — minimal, information-dense, function-first.

## Core Principles

### 1. Meaning Over Decoration
- Every element earns its place
- Color used for meaning only
- No gradients, no ornamental effects
- Flat, minimal depth

### 2. Information Density
- Respect user's screen space
- High but comfortable density
- Clear hierarchy through typography
- Progressive disclosure

### 3. Consistent Hierarchy
- 4-level contrast system
- Type scale follows 4px grid
- Consistent spacing (handled by Raycast)
- Intentional asymmetry only

## Color System

```typescript
// Accent: Electric Cyan (#00D9FF)
// Meaning: Technology, improvement, precision
ACCENT = {
  primary: "#00D9FF",
  dim: "rgba(0, 217, 255, 0.1)",
  border: "rgba(0, 217, 255, 0.2)",
}

// Gray hierarchy (dark mode)
GRAY = {
  foreground: "#FFFFFF",    // Primary text
  secondary: "#A0A0A0",    // Secondary text
  muted: "#5A5A5A",        // Disabled
  faint: "#2A2A2A",        // Backgrounds
}
```

## Typography

- System fonts (Raycast default)
- Scale: 11px, 12px, 14px (base), 16px, 18px, 24px, 32px
- Weights: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)
- Tight tracking for headlines (-0.02em)
- Wide tracking for labels (0.02em)

## Icon Design

**Concept:** Transformation (rough → refined)

- Flat, no gradients
- 2 colors max
- Works at 16px and 512px
- Under 50KB file size
- Rounded square container (radius 256px on 1024px canvas)

See: `docs/design/icon-specs.md`

## Components

### Form with Sections
```tsx
<ActionPanel>
  <ActionPanel.Section title="Primary">
    {/* Main actions */}
  </ActionPanel.Section>
  <ActionPanel.Section title="Secondary">
    {/* Contextual actions */}
  </ActionPanel.Section>
</ActionPanel>
```

### Detail with Metadata
```tsx
<Detail
  markdown={content}
  metadata={
    <Detail.Metadata>
      <Detail.Metadata.Label title="Metric" text="Value" />
      <Detail.Metadata.Separator />
      {/* More labels */}
    </Detail.Metadata>
  }
/>
```

## Anti-Patterns

❌ Don't:
- Use gradients for decoration
- Add shadows without purpose
- Use multiple accent colors
- Make actions without clear grouping
- Use ornamental icons

✅ Do:
- Use color for meaning only
- Group related actions
- Show metadata in sidebar
- Use semantic toast styles
- Keep everything minimal

## Future

- [ ] Compact mode for power users
- [ ] List view for history
- [ ] Export to markdown/PDF
- [ ] Custom theme support
