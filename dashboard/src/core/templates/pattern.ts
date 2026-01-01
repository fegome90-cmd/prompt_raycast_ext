/**
 * Pattern loader for custom system prompts
 * Custom system pattern for prompt improvement behavior
 */

// Custom pattern from templates/pattern.md
// This pattern defines the base behavior and personality of the prompt improver
export const DEFAULT_PATTERN = `You are an expert prompt engineer specializing in creating clear, actionable prompts for AI systems.
Your improved prompts should be:
- Specific and unambiguous
- Structured with clear sections
- Include explicit input/output specifications
- Use appropriate technical terminology`;

/**
 * Get the custom system pattern
 * Returns the custom pattern that will be injected as the system prompt
 */
export async function getCustomPattern(): Promise<string> {
  return DEFAULT_PATTERN;
}

/**
 * Synchronous version for environments where async is not available
 */
export function getCustomPatternSync(): string {
  return DEFAULT_PATTERN;
}
