/**
 * Color system for Prompt Improver
 * Direction: Precision & Density
 * Foundation: Cool, technical, professional
 */

// Accent color - ONE color that means something
// Blue/Cyan = trust, technology, improvement
const ACCENT = {
  primary: "#00D9FF", // Electric cyan - high visibility
  dim: "rgba(0, 217, 255, 0.1)",
  border: "rgba(0, 217, 255, 0.2)",
} as const;

// 4-level contrast hierarchy (for dark mode)
// Raycast handles most colors, but we define for reference
const GRAY = {
  foreground: "#FFFFFF", // Primary text
  secondary: "#A0A0A0", // Secondary text
  muted: "#5A5A5A", // Disabled, placeholder
  faint: "#2A2A2A", // Backgrounds, borders
} as const;

/**
 * Semantic color and icon tokens
 *
 * BREAKING CHANGE (2025-01-06): Restructured from simple strings to objects
 *
 * Before: tokens.semantic.success returned "#4ADE80"
 * After:  tokens.semantic.success returns { color: "#4ADE80", icon: "✅" }
 *
 * To access just the color: tokens.semantic.success.color
 * To access just the icon:  tokens.semantic.success.icon
 *
 * Rationale: Supports both colors and icons in a single token for consistency
 */
const SEMANTIC = {
  success: {
    color: "#4ADE80", // Green
    icon: "✅",
  },
  warning: {
    color: "#FBBF24", // Yellow
    icon: "⚠️",
  },
  error: {
    color: "#F87168", // Red
    icon: "❌",
  },
  info: {
    color: "#60A5FA", // Blue
    icon: "ℹ️",
  },
} as const;

// Typography scale (for generated text/markdown)
const TYPE = {
  // Sizes (in points, follows 4px grid)
  xs: "12px",   // 3 units of 4px
  sm: "16px",   // 4 units of 4px
  base: "16px", // 4 units of 4px
  lg: "24px",   // 6 units of 4px
  xl: "32px",   // 8 units of 4px
  "2xl": "48px", // 12 units of 4px
  "3xl": "64px", // 16 units of 4px

  // Weights
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",

  // Tracking (letter-spacing)
  tight: "-0.02em", // Headlines
  standard: "0", // Body
  wide: "0.02em", // Labels (uppercase)
} as const;

export const tokens = {
  accent: ACCENT,
  gray: GRAY,
  semantic: SEMANTIC,
  type: TYPE,
} as const;

// Type exports for type-safe usage
export type ColorToken = typeof tokens;
