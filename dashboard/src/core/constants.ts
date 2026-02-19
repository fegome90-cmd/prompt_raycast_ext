// dashboard/src/core/constants.ts
/**
 * Shared constants for Raycast extension
 */

// Loading stage type for progressive status updates
export type LoadingStage = "idle" | "validating" | "connecting" | "analyzing" | "improving" | "success" | "error";

// Stage messages for user-facing status display
export const STAGE_MESSAGES: Record<LoadingStage, string> = {
  idle: "",
  validating: "Validating input...",
  connecting: "Connecting to DSPy...",
  analyzing: "Analyzing prompt structure...",
  improving: "Applying few-shot learning...",
  success: "Complete!",
  error: "Failed",
} as const;
