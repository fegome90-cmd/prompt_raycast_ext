/**
 * Typography utilities for the Prompt Improver
 * Raycast handles most UI typography, but we use these for:
 * - Generated markdown content
 * - Toast messages
 * - Metadata labels
 */

// Confidence thresholds aligned with defaults.ts minConfidence (70%)
const CONFIDENCE_THRESHOLDS = {
  HIGH: 70, // Full circle = high confidence
  MEDIUM: 40, // Half dot = medium
} as const;

// Count symbols for metadata display
const COUNT_SYMBOLS = {
  Questions: "?", // Question mark - direct, functional
  Assumptions: "◐", // Half-filled circle = partial/assumption
  Characters: "#", // Hash = count, technical
  Words: "¶", // Pilcrow = paragraph, document symbol
} as const;

export class Typography {
  /**
   * Convert 0-1 score to 0-100 percentage with clamping.
   * Handles edge cases where score might be outside expected range.
   *
   * @param score - Confidence in 0-1 range
   * @returns Percentage in 0-100 range (clamped)
   */
  private static toPercentage(score: number): number {
    // Clamp to 0-1 range, then convert to percentage
    const clamped = Math.max(0, Math.min(1, score));
    return Math.round(clamped * 100);
  }

  /**
   * Format a confidence score with technical geometric symbols
   * Uses circle fill level to indicate quality: ◉ (high >=70%), ◎ (medium 40-69%), ○ (low <40%)
   *
   * @param score - Confidence in 0-1 range (from DSPy backend)
   * @returns Formatted string with icon and percentage (e.g., "◉ 70%")
   */
  static confidence(score: number): string {
    const rounded = Typography.toPercentage(score);
    // Technical geometric symbols - circle fill indicates quality
    if (rounded >= CONFIDENCE_THRESHOLDS.HIGH) return `◉ ${rounded}%`;
    if (rounded >= CONFIDENCE_THRESHOLDS.MEDIUM) return `◎ ${rounded}%`;
    return `○ ${rounded}%`;
  }

  /**
   * Get only the confidence icon symbol (for metadata display)
   *
   * @param score - Confidence in 0-1 range (from DSPy backend)
   * @returns Icon symbol: ◉ (high >=70%), ◎ (medium 40-69%), ○ (low <40%)
   */
  static confidenceIcon(score: number): string {
    const rounded = Typography.toPercentage(score);
    if (rounded >= CONFIDENCE_THRESHOLDS.HIGH) return "◉";
    if (rounded >= CONFIDENCE_THRESHOLDS.MEDIUM) return "◎";
    return "○";
  }

  /**
   * Format a count with technical minimal symbols
   * Uses single-letter and geometric symbols instead of emojis
   */
  static count(label: string, count: number): string {
    const symbol = COUNT_SYMBOLS[label as keyof typeof COUNT_SYMBOLS] || "•";
    return `${symbol} ${count}`;
  }

  /**
   * Get only the count symbol (for metadata icon display)
   */
  static countSymbol(label: string): string {
    return COUNT_SYMBOLS[label as keyof typeof COUNT_SYMBOLS] || "•";
  }

  /**
   * Get icon symbol for engine/source display
   * Technical symbols instead of emojis
   */
  static engine(source: "dspy" | "ollama"): string {
    return source === "dspy" ? "⤒" : "○"; // ⤒ = forward/advanced, ○ = basic
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
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}
