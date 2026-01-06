/**
 * Legacy adapter - Maintains backward compatibility
 * ollamaGenerateJson now uses ollamaGenerateRaw under the hood
 */

import type { OllamaTransport } from "./ollamaRaw";
import { makeOllamaGenerateRaw } from "./ollamaRaw";

export class OllamaError extends Error {
  constructor(
    message: string,
    readonly cause?: unknown,
    readonly rawResponse?: string,
  ) {
    super(message);
    this.name = "OllamaError";
  }
}

/**
 * Legacy ollamaGenerateJson - Now uses raw transport internally
 * This maintains the existing API for backward compatibility
 */
export function makeOllamaGenerateJson(transport?: OllamaTransport) {
  const generateRaw = makeOllamaGenerateRaw(transport!); // ! assertion - transport is checked inside makeOllamaGenerateRaw

  return async (args: {
    baseUrl: string;
    model: string;
    prompt: string;
    schema: Record<string, unknown>;
    timeoutMs: number;
  }): Promise<unknown> => {
    try {
      // Call raw generation
      const rawResponse = await generateRaw({
        baseUrl: args.baseUrl,
        model: args.model,
        prompt: args.prompt,
        timeoutMs: args.timeoutMs,
        format: args.schema,
      });

      // Parse JSON response
      try {
        return JSON.parse(rawResponse.raw);
      } catch (parseError) {
        throw new OllamaError("Ollama returned non-JSON output", parseError, rawResponse.raw);
      }
    } catch (error) {
      if (error instanceof OllamaError) throw error;

      if (error instanceof Error) {
        if (error.message.includes("timed out") || error.message.includes("Timeout")) {
          throw new OllamaError(`Ollama request timed out after ${args.timeoutMs}ms`, error);
        }
        if (error.name === "AbortError") {
          throw new OllamaError(`Ollama request timed out after ${args.timeoutMs}ms`, error);
        }
        throw new OllamaError(`Failed calling Ollama (is it running at the configured URL?)`, error);
      }

      throw error;
    }
  };
}

/**
 * Legacy adapter with default transport
 * Usage: import { ollamaGenerateJson } from './ollamaClient.legacy'
 * This maintains backward compatibility - uses fetch transport by default
 */
let transport: OllamaTransport | null = null;

async function getTransport(): Promise<OllamaTransport> {
  if (transport) return transport;
  const mod = await import("./ollamaRaw");
  transport = mod.fetchTransport;
  return transport;
}

/**
 * Backward-compatible ollamaGenerateJson function
 * Uses fetch transport by default
 */
export async function ollamaGenerateJson(args: {
  baseUrl: string;
  model: string;
  prompt: string;
  schema: Record<string, unknown>;
  timeoutMs: number;
}): Promise<unknown> {
  const actualTransport = await getTransport();
  const generate = makeOllamaGenerateJson(actualTransport);
  return generate(args);
}
