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
