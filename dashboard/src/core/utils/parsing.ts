/**
 * Pure utility functions for parsing and validation.
 * Extracted from promptify-quick.tsx for testability.
 */

/**
 * Parse timeout value from string, with fallback
 */
export function parseTimeoutMs(value: string | undefined, fallback: number): number {
  const n = Number.parseInt((value ?? "").trim(), 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

/**
 * Determine if fallback model should be tried based on error
 */
export function shouldTryFallback(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const msg = error.message.toLowerCase();
  // Typical Ollama/model issues where a retry with another model makes sense.
  if (msg.includes("model") && msg.includes("not found")) return true;
  if (msg.includes("pull")) return true;
  if (msg.includes("404")) return true;
  if (msg.includes("ollama error") && msg.includes("model")) return true;
  // Output/format issues (some models ignore schema or return unusable outputs).
  if (msg.includes("non-json")) return true;
  if (msg.includes("validation")) return true;
  if (msg.includes("zod")) return true;
  if (msg.includes("improved_prompt")) return true;
  if (msg.includes("contains meta content")) return true;
  if (msg.includes("starts with meta instructions")) return true;
  if (msg.includes("describes creating a prompt")) return true;
  return false;
}

/**
 * Get placeholder text for preset
 */
export function getPlaceholder(preset?: "default" | "specific" | "structured" | "coding"): string {
  const placeholders = {
    default: "Paste your rough prompt here… (⌘I to improve)",
    specific: "What specific task should this prompt accomplish?",
    structured: "Paste your prompt - we'll add structure and clarity…",
    coding: "Describe what you want the code to do…",
  } as const;
  return placeholders[preset || "structured"];
}
