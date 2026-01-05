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
