/**
 * DSPy Prompt Improver Client for Raycast Extension
 *
 * This client integrates with the Python DSPy backend to provide
 * enhanced prompt improvement capabilities following HemDov patterns.
 */

declare global {
  namespace NodeJS {
    interface RequestInit {
      headers?: Record<string, string>;
      method?: string;
      body?: string;
      signal?: AbortSignal;
    }
  }

  function fetch(url: string, init?: NodeJS.RequestInit): Promise<{
    ok: boolean;
    status: number;
    statusText: string;
    json(): Promise<any>;
  }>;
}

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
  async improvePrompt(request: DSPyPromptImproverRequest): Promise<DSPyPromptImproverResponse> {
    const response = await fetch(`${this.config.baseUrl}/api/v1/improve-prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idea: request.idea,
        context: request.context || ''
      }),
      signal: AbortSignal.timeout(this.config.timeoutMs)
    });

    if (!response.ok) {
      throw new Error(`DSPy backend error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
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
    const response = await fetch(`${this.config.baseUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Get backend information
   */
  async getBackendInfo(): Promise<{
    message: string;
    version: string;
    endpoints: Record<string, string>;
  }> {
    const response = await fetch(`${this.config.baseUrl}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000)
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
    baseUrl: 'http://localhost:8000',
    timeoutMs: 30000
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
  context?: string
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
      context: context || ''
    });

    return result;
  } catch (error) {
    console.error('DSPy prompt improvement failed:', error);
    throw error;
  }
}
