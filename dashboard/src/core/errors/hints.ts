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
  return null;
}
