/**
 * Spacing scale following 4px grid system
 * All spacing values derive from base 4px unit
 */
export const spacing = {
  xs: "4px", // 1 unit - micro spacing (icon gaps, tight padding)
  sm: "8px", // 2 units - tight spacing (within components)
  md: "16px", // 4 units - standard spacing (between related elements)
  lg: "24px", // 6 units - comfortable spacing (section padding)
  xl: "32px", // 8 units - major separation (between sections)
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
