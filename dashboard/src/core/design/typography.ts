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
   * Format a confidence score with technical geometric symbols
   * Uses circle fill level to indicate quality: ◉ (high), ◎ (medium), ○ (low)
   */
  static confidence(score: number): string {
    const rounded = Math.round(score);
    // Technical geometric symbols - circle fill indicates quality
    if (rounded >= 80) return `◉ ${rounded}%`; // Full circle = high confidence
    if (rounded >= 60) return `◎ ${rounded}%`; // Half dot = medium
    if (rounded >= 40) return `○ ${rounded}%`; // Empty = low
    return `○ ${rounded}%`; // Same as low
  }

  /**
   * Get only the confidence icon symbol (for metadata display)
   */
  static confidenceIcon(score: number): string {
    const rounded = Math.round(score);
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
