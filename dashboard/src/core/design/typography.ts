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
