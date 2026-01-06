/**
 * Ollama Chat API Client - Uses /api/chat endpoint with proper system/user separation
 * Fixes the issue where /api/generate concatenated system instructions with user input
 *
 * Source: docs/research/prompt-engineering-investigation.md
 */

import { fetchWithTimeout } from "./fetchWrapper";

const LOG_PREFIX = "[OllamaChat]";

export interface OllamaMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface OllamaChatRequest {
  model: string;
  messages: OllamaMessage[];
  stream: boolean;
  temperature?: number;
}

export interface OllamaChatResponse {
  model: string;
  created_at: string;
  message: {
    role: string;
    content: string;
  };
  done: boolean;
}

export interface OllamaChatOptions {
  baseUrl: string;
  model: string;
  timeoutMs: number;
  temperature?: number;
}

/**
 * Call Ollama /api/chat endpoint with proper system/user message separation
 */
export async function callOllamaChat(
  systemPrompt: string,
  userPrompt: string,
  options: OllamaChatOptions,
): Promise<string> {
  console.log(`${LOG_PREFIX} 🚀 Calling Ollama /api/chat`);
  const { baseUrl, model, timeoutMs, temperature = 0.1 } = options;

  const requestBody: OllamaChatRequest = {
    model,
    messages: [
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: userPrompt,
      },
    ],
    stream: false,
    temperature,
  };

  try {
    const url = new URL("/api/chat", baseUrl).toString();

    console.log(`${LOG_PREFIX} 🌐 POST ${url} (model: ${model}, timeout: ${timeoutMs}ms)`);
    const response = await fetchWithTimeout(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
      timeout: timeoutMs,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`${LOG_PREFIX} ❌ API error: ${response.status} ${response.statusText} - ${errorText}`);
      throw new Error(`Ollama API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = (await response.json()) as OllamaChatResponse;

    if (!data.message || !data.message.content) {
      console.error(`${LOG_PREFIX} ❌ Invalid response: missing message.content`);
      throw new Error(`Invalid Ollama response: missing message.content. Response: ${JSON.stringify(data)}`);
    }

    console.log(`${LOG_PREFIX} ✅ Success: ${data.message.content.length} chars returned`);
    return data.message.content;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`${LOG_PREFIX} ❌ Operation failed: ${error.message}`);
      throw error;
    }

    console.error(`${LOG_PREFIX} ❌ Unknown error: ${String(error)}`);
    throw new Error(`Unknown error calling Ollama: ${String(error)}`);
  }
}

/**
 * Health check for Ollama using /api/tags
 */
export async function ollamaHealthCheckChat(options: {
  baseUrl: string;
  timeoutMs: number;
}): Promise<{ ok: boolean; error?: string }> {
  console.log(`${LOG_PREFIX} 🏥 Starting health check...`);
  try {
    const url = new URL("/api/tags", options.baseUrl).toString();

    const response = await fetchWithTimeout(url, {
      method: "GET",
      timeout: options.timeoutMs,
    });

    if (!response.ok) {
      console.error(`${LOG_PREFIX} ❌ Health check failed: ${response.status} ${response.statusText}`);
      return {
        ok: false,
        error: `Ollama returned ${response.status} ${response.statusText}`,
      };
    }

    console.log(`${LOG_PREFIX} ✅ Health check passed`);
    return { ok: true };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error(`${LOG_PREFIX} ❌ Health check error: ${errorMsg}`);
    if (error instanceof Error) {
      return {
        ok: false,
        error: error.message,
      };
    }

    return {
      ok: false,
      error: String(error),
    };
  }
}
