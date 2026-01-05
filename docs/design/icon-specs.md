# Icon Specifications

## Design

**Concept:** Transformation — rough prompt becomes refined prompt

**Visual:** Two boxes with arrow between them
- Left: Gray box with wavy lines (messy/rough)
- Right: Cyan-bordered box with checkmarks (refined)
- Arrow: Cyan, pointing left to right

## Technical Specs

### File: `dashboard/icon.png`

| Property | Value |
|----------|-------|
| **Size** | 1024 x 1024 px |
| **Format** | PNG (flat) |
| **File size** | ~47 KB |
| **Background** | Dark (#1A1A1A) |
| **Corner radius** | 256px |

### Colors

| Element | Color | Purpose |
|---------|-------|---------|
| **Background** | #1A1A1A | Dark base |
| **Cyan accent** | #00D9FF | Primary color, improvement |
| **Gray boxes** | #2A2A2A | Subtle containers |
| **Gray strokes** | #666666 | Wavy lines (messy) |
| **Border gray** | #3A3A3A | Subtle borders |

### Composition

```
┌─────────────────────────────────────┐
│  Background: #1A1A1A, radius 256px  │
│                                      │
│  ┌─────┐    →→→     ┌─────┐         │
│  │ ~~~ │             │ ✓✓ │         │
│  │ ~~~ │    Arrow    │ ✓✓ │         │
│  └─────┘             └─────┘         │
│  Gray #2A2A2A        Cyan border     │
│                                      │
└─────────────────────────────────────┘
```

### Source File

**SVG:** `dashboard/assets/icon-design.svg`
- Editable vector source
- ViewBox: 0 0 1024 1024
- No gradients, flat design

### Usage Guidelines

**Do:**
- Use on all light and dark backgrounds
- Maintain minimum 16px for legibility
- Keep full icon intact (don't crop)

**Don't:**
- Stretch or distort
- Add effects (shadows, gradients)
- Change colors
- Rotate or flip

## Implementation Notes

Created with flat design principles:
- No raster effects
- Scalable at any size
- Optimized for file size
- Follows Precision & Density direction
