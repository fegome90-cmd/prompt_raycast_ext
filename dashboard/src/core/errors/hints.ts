/**
 * Error hint utilities for user-friendly error messages.
 */

export type ErrorHintMode = "dspy" | "nlac";

/**
 * Builds a user-friendly hint for common error scenarios.
 *
 * @param error - The error to analyze
 * @param mode - The execution mode (dspy, nlac, or undefined for ollama)
 * @returns A user-friendly hint string, or null if no specific hint applies
 */
export function buildErrorHint(error: unknown, mode?: ErrorHintMode): string | null {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();

  if (lower.includes("timed out")) return "try increasing timeout (ms)";

  if (lower.includes("connect") || lower.includes("econnrefused") || lower.includes("not reachable")) {
    if (mode === "nlac") return "check the NLaC backend is running with 'make dev'";
    if (mode === "dspy") return "check the DSPy backend is running";
    return "check `ollama serve` is running";
  }

  if (lower.includes("model") && lower.includes("not found")) {
    return "Pull the model first: `ollama pull <model>`";
  }

  // Additional error types
  if (lower.includes("schema") || lower.includes("validation")) {
    return "the backend returned an unexpected response format - try again or check backend logs";
  }

  if (lower.includes("json") || lower.includes("parse")) {
    return "the response could not be parsed - try a different model or check backend logs";
  }

  if (lower.includes("401") || lower.includes("unauthorized") || lower.includes("api key")) {
    return "check your API key configuration in environment variables";
  }

  if (lower.includes("429") || lower.includes("rate limit")) {
    return "too many requests - wait a moment and try again";
  }

  return null;
}
