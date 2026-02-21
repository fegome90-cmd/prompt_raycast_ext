import { tokens } from "./tokens";

/**
 * Typography utilities for the Prompt Improver
 * Raycast handles most UI typography, but we use these for:
 * - Generated markdown content
 * - Toast messages
 * - Metadata labels
 */

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
   * Uses circle fill level to indicate quality: ◉ (high), ◎ (medium), ○ (low)
   *
   * @param score - Confidence in 0-1 range (from DSPy backend)
   * @returns Formatted string with icon and percentage (e.g., "◉ 80%")
   */
  static confidence(score: number): string {
    const rounded = Typography.toPercentage(score);
    // Technical geometric symbols - circle fill indicates quality
    if (rounded >= 80) return `◉ ${rounded}%`; // Full circle = high confidence
    if (rounded >= 60) return `◎ ${rounded}%`; // Half dot = medium
    if (rounded >= 40) return `○ ${rounded}%`; // Empty = low
    return `○ ${rounded}%`; // Same as low
  }

  /**
   * Get only the confidence icon symbol (for metadata display)
   *
   * @param score - Confidence in 0-1 range (from DSPy backend)
   * @returns Icon symbol: ◉ (high >=70%), ◎ (medium 40-69%), ○ (low <40%)
   */
  static confidenceIcon(score: number): string {
    const rounded = Typography.toPercentage(score);
    if (rounded >= 70) return "◉"; // High = full circle
    if (rounded >= 40) return "◎"; // Medium = half dot
    return "○"; // Low = empty circle
  }

  /**
   * Format a count with technical minimal symbols
   * Uses single-letter and geometric symbols instead of emojis
   */
  static count(label: string, count: number): string {
    const symbols = {
      Questions: "?", // Question mark - direct, functional
      Assumptions: "◐", // Half-filled circle = partial/assumption
      Characters: "#", // Hash = count, technical
      Words: "¶", // Pilcrow = paragraph, document symbol
    };

    const symbol = symbols[label as keyof typeof symbols] || "•";
    return `${symbol} ${count}`;
  }

  /**
   * Get only the count symbol (for metadata icon display)
   */
  static countSymbol(label: string): string {
    const symbols = {
      Questions: "?",
      Assumptions: "◐",
      Characters: "#",
      Words: "¶",
    };
    return symbols[label as keyof typeof symbols] || "•";
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
