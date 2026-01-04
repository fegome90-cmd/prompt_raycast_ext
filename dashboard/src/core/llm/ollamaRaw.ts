/**
 * Raw Ollama API client - Returns raw string response
 * Foundation for structured extraction and telemetría
 */

import { fetchWithTimeout } from "./fetchWrapper";

export interface OllamaRawResponse {
  raw: string;
  latencyMs: number;
  model?: string;
}

export interface OllamaRawRequest {
  baseUrl: string;
  model: string;
  prompt: string;
  timeoutMs: number;
  temperature?: number;
  format?: unknown; // Ollama format parameter if needed
}

export type OllamaTransport = (req: OllamaRawRequest) => Promise<OllamaRawResponse>;

/**
 * Production transport using fetch
 */
export async function fetchTransport(req: OllamaRawRequest): Promise<OllamaRawResponse> {
  const start = Date.now();

  try {
    const url = new URL("/api/generate", req.baseUrl).toString();
    const res = await fetchWithTimeout(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      timeout: req.timeoutMs,
      body: JSON.stringify({
        model: req.model,
        prompt: req.prompt,
        stream: false,
        options: {
          temperature: req.temperature ?? 0.1,
        },
        ...(req.format ? { format: req.format } : {}),
      }),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`Ollama error (${res.status}): ${text || res.statusText}`);
    }

    const json = (await res.json()) as { response?: string; [key: string]: unknown };

    // Extract raw response text
    const raw = typeof json.response === "string" ? json.response : JSON.stringify(json.response ?? json);

    return {
      raw,
      latencyMs: Date.now() - start,
      model: (json.model as string | undefined) ?? req.model,
    };
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "AbortError" || error.message.includes("abort")) {
        throw Object.assign(error, { failureReason: "timeout" as const });
      }
    }
    throw error;
  }
}

/**
 * Main raw generation function (configurable transport)
 */
export function makeOllamaGenerateRaw(transport: OllamaTransport) {
  return async (req: OllamaRawRequest): Promise<OllamaRawResponse> => {
    return transport(req);
  };
}

// Default export using fetch transport
export const ollamaGenerateRaw = makeOllamaGenerateRaw(fetchTransport);
