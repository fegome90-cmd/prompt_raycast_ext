/**
 * DSPy Prompt Improver Client for Raycast Extension
 *
 * This client integrates with the Python DSPy backend to provide
 * enhanced prompt improvement capabilities following HemDov patterns.
 */

import { fetchWithTimeout } from "./fetchWrapper";

export interface DSPyPromptImproverRequest {
  idea: string;
  context?: string;
}

export interface DSPyPromptImproverResponse {
  improved_prompt: string;
  role: string;
  directive: string;
  framework: string;
  guardrails: string[];
  reasoning?: string;
  confidence?: number;
}

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
    console.log(`[DSPy improvePrompt] 📤 Request payload:`, {
      idea_length: request.idea.length,
      idea_preview: request.idea.substring(0, 100),
      context_length: request.context?.length || 0,
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
      }),
      timeout: this.config.timeoutMs,
    });
    const latencyMs = Date.now() - startTime;

    console.log(
      `[DSPy improvePrompt] 📥 Response: status=${response.status}, ok=${response.ok}, latency=${latencyMs}ms`,
    );

    if (!response.ok) {
      const errorText = await response.text().catch(() => "");
      console.error(`[DSPy improvePrompt] ❌ Error response:`, errorText);
      throw new Error(`DSPy backend error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[DSPy improvePrompt] ✅ Success - improved_prompt length: ${data.improved_prompt?.length || 0}`);

    return data as DSPyPromptImproverResponse;
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
): Promise<{
  improved_prompt: string;
  role: string;
  directive: string;
  framework: string;
  guardrails: string[];
  reasoning?: string;
  confidence?: number;
}> {
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
