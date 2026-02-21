/**
 * DSPy Prompt Improver Client for Raycast Extension
 *
 * This client integrates with the Python DSPy backend to provide
 * enhanced prompt improvement capabilities following HemDov patterns.
 */

import { z } from "zod";
import { fetchWithTimeout } from "./fetchWrapper";

export interface DSPyPromptImproverRequest {
  idea: string;
  context?: string;
  mode?: "legacy" | "nlac";
}

// Default confidence when DSPy returns null (common for CoT mode)
// 0.8 chosen as reasonable default based on eval benchmarks
const DEFAULT_CONFIDENCE = 0.8;

/**
 * Zod schema for validating DSPy backend responses.
 * Prevents silent failures when backend returns malformed or unexpected data.
 */
export const DSPyResponseSchema = z.object({
  improved_prompt: z.string().min(1, "improved_prompt cannot be empty"),
  role: z.string(),
  directive: z.string(),
  framework: z.string(),
  guardrails: z.array(z.string()),
  reasoning: z.string().nullish(),
  // Backend DSPy returns null/undefined when not filled; transform to default
  confidence: z
    .number()
    .min(0)
    .max(1)
    .nullish()
    .transform((val) => val ?? DEFAULT_CONFIDENCE),
});

// Derive TypeScript type from Zod schema for type safety
export type DSPyPromptImproverResponse = z.infer<typeof DSPyResponseSchema>;

export interface DSPyBackendConfig {
  baseUrl: string;
  timeoutMs: number;
}

/**
 * Client for DSPy Prompt Improver backend API
 */
export class DSPyPromptImproverClient {
  private config: DSPyBackendConfig;

  constructor(config: DSPyBackendConfig) {
    this.config = config;
  }

  /**
   * Improve a raw idea using DSPy backend
   */
  /**
   * ⚠️ RISK: Network operation with multiple failure modes
   *
   * This method makes HTTP calls to DSPy backend. Common failures:
   * - Network errors: ECONNREFUSED, timeout, DNS failure
   * - Backend errors: 5xx, rate limits, malformed JSON
   * - Edge cases: Empty responses, missing fields, schema changes
   *
   * Mitigations in place:
   * - fetchWithTimeout enforces timeout (prevents hangs)
   * - Response validation (checks response.ok)
   * - Comprehensive logging (request/response/latency)
   *
   * 🔴 DO NOT remove try/catch - errors must be caught and logged
   * 🔴 DO NOT remove console.log statements - critical for debugging
   * 🔴 DO NOT reduce timeout without checking defaults.ts:58-80 CRITICAL comment
   * 🔴 DO NOT change this to NOT use fetchWithTimeout wrapper
   */
  async improvePrompt(request: DSPyPromptImproverRequest): Promise<DSPyPromptImproverResponse> {
    const url = `${this.config.baseUrl}/api/v1/improve-prompt`;
    console.log(`[DSPy improvePrompt] 🌐 Calling POST ${url}`);

    // Contract: mode travels end-to-end; when omitted we keep legacy as safe default.
    const mode = request.mode ?? "legacy";

    console.log(`[DSPy improvePrompt] 📤 Request payload:`, {
      idea_length: request.idea.length,
      idea_preview: request.idea.substring(0, 100),
      context_length: request.context?.length || 0,
      mode,
      timeoutMs: this.config.timeoutMs,
    });

    const startTime = Date.now();
    const response = await fetchWithTimeout(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        idea: request.idea,
        context: request.context || "",
        mode,
      }),
      timeout: this.config.timeoutMs,
      operation: "DSPy improvePrompt (/api/v1/improve-prompt)",
    });
    const latencyMs = Date.now() - startTime;

    console.log(
      `[DSPy improvePrompt] 📥 Response: status=${response.status}, ok=${response.ok}, latency=${latencyMs}ms`,
    );

    if (!response.ok) {
      let errorDetails = `${response.status} ${response.statusText}`;
      try {
        const errorText = await response.text();
        if (errorText) {
          errorDetails += ` | Body: ${errorText.substring(0, 200)}`;
        }
      } catch (readError) {
        console.warn(`[DSPy improvePrompt] Failed to read error response body:`, readError);
      }
      console.error(`[DSPy improvePrompt] ❌ Backend error:`, errorDetails);

      // Include actionable info based on status code
      let userMessage = "DSPy backend error";
      if (response.status === 504) {
        userMessage = "Request timed out. Try a shorter prompt or use 'legacy' mode for faster results.";
      } else if (response.status >= 500) {
        userMessage = "Backend error. Check that the server is running with 'make dev'";
      } else if (response.status === 400) {
        userMessage = "Invalid request. Check that your prompt is at least 5 characters.";
      }

      throw new Error(`${userMessage} (${errorDetails})`);
    }

    const rawData = await response.json();

    // Validate response structure with Zod to catch schema mismatches
    try {
      const validatedData = DSPyResponseSchema.parse(rawData);
      console.log(`[DSPy improvePrompt] ✅ Success - improved_prompt length: ${validatedData.improved_prompt.length}`);
      return validatedData;
    } catch (zodError) {
      console.error(`[DSPy improvePrompt] ❌ Schema validation failed:`, zodError);
      console.error(`[DSPy improvePrompt] 📄 Raw response:`, JSON.stringify(rawData, null, 2));
      throw new Error(
        `Backend returned invalid response structure. ${
          zodError instanceof z.ZodError ? zodError.issues.map((i) => i.message).join(", ") : ""
        }`,
      );
    }
  }

  /**
   * Check if DSPy backend is healthy
   */
  async healthCheck(): Promise<{
    status: string;
    provider: string;
    model: string;
    dspy_configured: boolean;
  }> {
    const url = `${this.config.baseUrl}/health`;
    console.log(`[DSPy HealthCheck] 🌐 Attempting: ${url}`);
    console.log(`[DSPy HealthCheck] ⚙️ Config:`, this.config);

    const response = await fetchWithTimeout(url, {
      method: "GET",
      timeout: 30000, // Increased to 30s for slow Anthropic responses
      operation: "DSPy health check (/health)",
    });

    console.log(`[DSPy HealthCheck] 📥 Response status: ${response.status}, ok: ${response.ok}`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const data = await response.json();
    console.log(`[DSPy HealthCheck] ✅ Success:`, data);
    return data;
  }

  /**
   * Get backend information
   */
  async getBackendInfo(): Promise<{
    message: string;
    version: string;
    endpoints: Record<string, string>;
  }> {
    const response = await fetchWithTimeout(`${this.config.baseUrl}/`, {
      method: "GET",
      timeout: 5000,
      operation: "DSPy getBackendInfo (/)",
    });

    if (!response.ok) {
      throw new Error(`Failed to get backend info: ${response.status}`);
    }

    return await response.json();
  }
}

/**
 * Factory to create DSPy client with default configuration
 */
export function createDSPyClient(overrideConfig?: Partial<DSPyBackendConfig>): DSPyPromptImproverClient {
  const defaultConfig: DSPyBackendConfig = {
    baseUrl: "http://localhost:8000",
    // ⚡ INVARIANT: Default timeout MUST match frontend preference (120s)
    // See: dashboard/src/core/config/defaults.ts:58-80 for three-layer sync invariant
    // If caller doesn't specify timeoutMs, use 120s to prevent AbortError
    timeoutMs: 120000,
  };

  const config = { ...defaultConfig, ...overrideConfig };
  return new DSPyPromptImproverClient(config);
}

/**
 * Integration function that can be used in existing improvePrompt.ts
 */
export async function improvePromptWithDSPy(
  rawInput: string,
  preset: string = "default",
  context?: string,
): Promise<DSPyPromptImproverResponse> {
  try {
    const client = createDSPyClient();

    // Check if backend is healthy
    try {
      await client.healthCheck();
    } catch (error) {
      // DSPy backend not available - let caller handle fallback
      throw error;
    }

    // Call DSPy backend
    const result = await client.improvePrompt({
      idea: rawInput,
      context: context || "",
    });

    return result;
  } catch (error) {
    console.error("DSPy prompt improvement failed:", error);
    throw error;
  }
}
