/**
 * Structured JSON generation wrapper with extraction and repair
 * T1.2-B2: ollamaGenerateStructured<T>
 * Antifrágil: telemetría explícita, máximo 2 intentos, modos claros
 */

import { z } from "zod";
import { extractJsonFromText } from "./jsonExtractor";
import type { OllamaTransport } from "./ollamaRaw";

/**
 * Wrapper configuration
 */
export interface StructuredRequest<T> {
  /** Zod schema for validation */
  schema: z.ZodType<T>;
  /** Prompt to send to Ollama */
  prompt: string;
  /** Mode determines extraction and repair behavior */
  mode: "strict" | "extract" | "extract+repair";
  /** Ollama connection settings */
  baseUrl: string;
  model: string;
  timeoutMs: number;
  temperature?: number;
  /** Metadata for telemetry (optional) */
  requestMeta?: {
    feature: "improve" | "router" | "repair" | "test";
    [key: string]: unknown;
  };
}

/**
 * Result with full telemetría
 * Pipeline decides UX, not wrapper
 */
export interface StructuredResult<T> {
  ok: boolean;
  data?: T;
  raw: string; // Always return raw output
  attempt: 1 | 2;
  usedExtraction: boolean;
  usedRepair: boolean;
  extractionMethod?: "fence" | "tag" | "scan";
  parseStage?: "direct" | "extracted" | "repair";
  latencyMs: number;
  // Optional telemetry: individual attempt latencies for debugging
  attempt1Latency?: number;
  attempt2Latency?: number;
  failureReason?: "timeout" | "invalid_json" | "schema_mismatch" | "unknown";
  validationError?: string;
}

interface ParseAttempt {
  ok: boolean;
  value?: unknown;
  usedExtraction: boolean;
  extractionMethod?: "fence" | "tag" | "scan";
  error?: string;
}

/**
 * Main wrapper function
 * 2 attempts máximo, telemetría completa
 */
export async function ollamaGenerateStructured<T>(request: StructuredRequest<T>): Promise<StructuredResult<T>> {
  const start = Date.now();
  const { schema, prompt, mode, baseUrl, model, timeoutMs, temperature } = request;

  // Attempt 1: Direct call to Ollama
  const attempt1 = await callOllama(prompt, baseUrl, model, timeoutMs, temperature);
  const raw1 = attempt1.raw;
  const latency1 = attempt1.latencyMs;

  // Try to parse attempt 1
  const parse1 = tryParseJson(raw1, mode);

  if (parse1.ok) {
    // Validate against schema
    const validation = schema.safeParse(parse1.value);

    if (validation.success) {
      // Success on first attempt
      return {
        ok: true,
        data: validation.data,
        raw: raw1,
        attempt: 1,
        usedExtraction: parse1.usedExtraction,
        usedRepair: false,
        extractionMethod: parse1.extractionMethod,
        parseStage: parse1.usedExtraction ? "extracted" : "direct",
        latencyMs: latency1,
        attempt1Latency: latency1,
      };
    }

    // Schema mismatch on attempt 1
    if (mode !== "extract+repair") {
      return failResult("schema_mismatch", raw1, 1, parse1.usedExtraction, false, summarizeZodError(validation.error), latency1, latency1, undefined);
    }

    // Attempt repair
    const repairPrompt = buildRepairPrompt({
      rawOutput: raw1,
      validationError: summarizeZodError(validation.error),
      schemaDescription: getSchemaFields(schema),
      originalPrompt: prompt,
    });

    const attempt2 = await callOllama(repairPrompt, baseUrl, model, timeoutMs, temperature);
    const raw2 = attempt2.raw;
    const latency2 = attempt2.latencyMs;

    return parseAndValidateAttempt2(raw2, schema, raw1, latency1 + latency2, latency1, latency2);
  }

  // Parse failed on attempt 1
  if (mode !== "extract+repair") {
    return failResult("invalid_json", raw1, 1, parse1.usedExtraction, false, parse1.error, latency1, latency1, undefined);
  }

  // Attempt repair
  const repairPrompt = buildRepairPrompt({
    rawOutput: raw1,
    validationError: parse1.error || "Invalid JSON syntax",
    schemaDescription: getSchemaFields(schema),
    originalPrompt: prompt,
  });

  const attempt2 = await callOllama(repairPrompt, baseUrl, model, timeoutMs, temperature);
  const raw2 = attempt2.raw;
  const latency2 = attempt2.latencyMs;

  return parseAndValidateAttempt2(raw2, schema, raw1, latency1 + latency2, latency1, latency2);
}

/**
 * Try to parse JSON based on mode
 * Returns parsed value or failure info
 */
function tryParseJson(raw: string, mode: "strict" | "extract" | "extract+repair"): ParseAttempt {
  // Mode: strict - only direct parse
  if (mode === "strict") {
    try {
      const parsed = JSON.parse(raw);
      const sanitized = sanitizeStructuredOutput(parsed);
      return {
        ok: true,
        value: sanitized,
        usedExtraction: false,
      };
    } catch (e) {
      return {
        ok: false,
        usedExtraction: false,
        error: e instanceof Error ? e.message : "Invalid JSON",
      };
    }
  }

  // Mode: extract or extract+repair
  // Try direct parse first
  try {
    const parsed = JSON.parse(raw);
    const sanitized = sanitizeStructuredOutput(parsed);
    return {
      ok: true,
      value: sanitized,
      usedExtraction: false,
    };
  } catch {
    // Direct parse failed, try extraction
    const extracted = extractJsonFromText(raw);
    if (extracted) {
      try {
        const extractedParsed = JSON.parse(extracted.json);
        const sanitized = sanitizeStructuredOutput(extractedParsed);
        return {
          ok: true,
          value: sanitized,
          usedExtraction: true,
          extractionMethod: extracted.extractionMethod,
        };
      } catch (extractError) {
        return {
          ok: false,
          usedExtraction: true,
          extractionMethod: extracted.extractionMethod,
          error: extractError instanceof Error ? extractError.message : "Extracted JSON invalid",
        };
      }
    }

    // No JSON could be extracted
    return {
      ok: false,
      usedExtraction: false,
      error: "No valid JSON found in output",
    };
  }
}

/**
 * Sanitize structured output to handle null arrays and other common issues
 * Centralized function to avoid duplication
 */
function sanitizeStructuredOutput(parsed: Record<string, unknown>): Record<string, unknown> {
  const sanitized = { ...parsed };

  // Coerce arrays: null/undefined → []
  sanitized.clarifying_questions = coerceStringArray(sanitized.clarifying_questions);
  sanitized.assumptions = coerceStringArray(sanitized.assumptions);

  // Coerce other common issues
  if (sanitized.confidence === null || sanitized.confidence === undefined) {
    sanitized.confidence = 0.5; // Default confidence
  }

  if (typeof sanitized.improved_prompt !== "string" || sanitized.improved_prompt.trim() === "") {
    sanitized.improved_prompt = sanitized.improved_prompt || "Error: Invalid prompt";
  }

  return sanitized;
}

/**
 * Coerce string arrays from potentially null/undefined values
 * This is a compatibility layer that doesn't change semantics: null ≈ "no items"
 */
function coerceStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((x): x is string => typeof x === "string");
  }
  return []; // null, undefined, or other types → empty array
}

/**
 * Parse and validate repair attempt (attempt 2)
 * No more retries after this
 */
function parseAndValidateAttempt2<T>(
  raw: string,
  schema: z.ZodType<T>,
  rawAttempt1: string,
  latencyMs: number,
  attempt1Latency: number,
  attempt2Latency: number,
): StructuredResult<T> {
  // Try direct parse only (no extraction in repair)
  try {
    const parsed = JSON.parse(raw);

    // Centralized sanitization before Zod validation
    const sanitized = sanitizeStructuredOutput(parsed);

    const validation = schema.safeParse(sanitized);

    if (validation.success) {
      return {
        ok: true,
        data: validation.data,
        raw: rawAttempt1, // Always return original raw
        attempt: 2,
        usedExtraction: false,
        usedRepair: true,
        parseStage: "repair",
        latencyMs,
        attempt1Latency,
        attempt2Latency,
      };
    }

    // Schema mismatch after repair
    return failResult("schema_mismatch", rawAttempt1, 2, false, true, summarizeZodError(validation.error), latencyMs, attempt1Latency, attempt2Latency);
  } catch (e) {
    // Invalid JSON after repair
    return failResult(
      "invalid_json",
      rawAttempt1,
      2,
      false,
      true,
      e instanceof Error ? e.message : "Invalid JSON",
      latencyMs,
      attempt1Latency,
      attempt2Latency,
    );
  }
}

/**
 * Call Ollama (using raw transport)
 * Injected transport for testability
 */
let _transport: OllamaTransport | null = null;

export function setTransport(transport: OllamaTransport) {
  _transport = transport;
}

export function resetTransport() {
  _transport = null;
}

export function getTransport(): OllamaTransport | (() => Promise<OllamaTransport>) {
  if (_transport) return _transport;
  return async () => (await import("./ollamaRaw")).fetchTransport;
}

async function callOllama(
  prompt: string,
  baseUrl: string,
  model: string,
  timeoutMs: number,
  temperature?: number,
): Promise<{ raw: string; latencyMs: number }> {
  const start = Date.now();
  try {
    const transport = await getTransportInstance();

    const result = await transport({
      baseUrl,
      model,
      prompt,
      timeoutMs,
      temperature,
    });

    return {
      raw: result.raw,
      latencyMs: result.latencyMs || Date.now() - start,
    };
  } catch (error) {
    const latency = Date.now() - start;
    if (error instanceof Error) {
      if (error.message.includes("timed out") || error.message.includes("Timeout") || error.name === "AbortError") {
        throw Object.assign(error, {
          failureReason: "timeout" as const,
          latencyMs: latency,
        } as Error & { failureReason: "timeout"; latencyMs: number });
      }
      // Re-throw other errors with latency
      throw Object.assign(error, { latencyMs: latency } as Error & { latencyMs: number });
    }
    // If it's not an Error, create a new one
    const errorObj = new Error(String(error));
    errorObj.stack = undefined;
    throw Object.assign(errorObj, { latencyMs: latency });
  }
}

/**
 * Get a transport instance, resolving factory if needed
 */
async function getTransportInstance(): Promise<OllamaTransport> {
  const transportOrFactory = getTransport();

  // If it's already a transport (async function), return it
  if (isOllamaTransport(transportOrFactory)) {
    return transportOrFactory;
  }

  // Otherwise it's a factory function
  const factory = transportOrFactory as () => Promise<OllamaTransport>;
  return await factory();
}

/**
 * Type guard to check if value is an OllamaTransport
 */
function isOllamaTransport(value: unknown): value is OllamaTransport {
  return typeof value === "function" && value.length === 1; // OllamaTransport takes one argument
}

/**
 * Build repair prompt (schema-locked version)
 * INCLUDES complete schema and strict validation rules
 */
function buildRepairPrompt(args: {
  rawOutput: string;
  validationError: string;
  schemaDescription: string;
  originalPrompt: string;
}): string {
  const { rawOutput, validationError, schemaDescription, originalPrompt } = args;

  return [
    "You are a JSON REPAIR tool. Your output MUST be valid JSON matching the exact schema.",
    "",
    "HARD RULES (violations = failure):",
    "1. Return ONLY a JSON object. No explanations, no markdown, no comments, no text before or after.",
    "2. The JSON MUST include ALL keys from the schema below.",
    "3. Each field MUST be the correct type (string, number, array, boolean).",
    "4. Do NOT rename keys, do NOT omit keys, do NOT add new keys.",
    "5. For array fields (clarifying_questions, assumptions): use empty array [] if no items, never null.",
    "6. For string fields: use empty string if unknown, never null.",
    "7. For number fields: use 0 if unknown, never null.",
    "",
    "ORIGINAL USER REQUEST (context only):",
    '"""',
    originalPrompt,
    '"""',
    "",
    "INVALID OUTPUT TO FIX:",
    '"""',
    rawOutput,
    '"""',
    "",
    "VALIDATION ERROR:",
    validationError,
    "",
    "SCHEMA (MUST match exactly):",
    '"""',
    schemaDescription,
    '"""',
    "",
    "OUTPUT INSTRUCTIONS:",
    "- Return ONLY a valid JSON object.",
    "- Do NOT wrap in code fences.",
    "- Do NOT add explanations.",
    "- Include ALL keys from schema above.",
    "- Use EMPTY ARRAYS [] for array fields with no items.",
    "- Use EMPTY STRINGS for string fields with no content.",
    "",
  ].join("\n");
}

/**
 * Summarize ZodError (máximo 300 chars)
 * Format: path: expected X, received Y
 */
function summarizeZodError(error: z.ZodError): string {
  const issues = error.errors.slice(0, 3); // Max 3 issues

  const summary = issues
    .map((issue) => {
      const path = issue.path.length > 0 ? issue.path.join(".") : "root";
      // ZodIssue doesn't have expected/received properties
      // Instead, use the message field which contains the error description
      return `${path}: ${issue.message}`;
    })
    .join("; ");

  return summary || "Schema validation failed";
}

/**
 * Get schema fields description
 * Returns the complete schema as JSON for schema-locked repair
 */
function getSchemaFields(schema: z.ZodType): string {
  try {
    // Serialize the Zod schema to a readable format
    const jsonSchema: Record<string, unknown> = {};

    // Try to extract basic structure from common Zod types
    if ("shape" in schema && typeof schema.shape === "function") {
      // For ZodObject
      const shape = schema.shape();
      for (const [key, field] of Object.entries(shape)) {
        let typeDesc = "unknown";

        if (field instanceof z.ZodString) typeDesc = "string (required)";
        else if (field instanceof z.ZodNumber) typeDesc = "number (required)";
        else if (field instanceof z.ZodBoolean) typeDesc = "boolean (required)";
        else if (field instanceof z.ZodArray) {
          const innerType =
            field.element instanceof z.ZodString
              ? "string"
              : field.element instanceof z.ZodNumber
              ? "number"
              : "unknown";
          typeDesc = `array of ${innerType} (max items: ${field._def.maxLength ?? "unlimited"})`;
        } else if (field instanceof z.ZodOptional) {
          const inner = field.unwrap();
          if (inner instanceof z.ZodString) typeDesc = "string (optional)";
          else if (inner instanceof z.ZodNumber) typeDesc = "number (optional)";
        }

        jsonSchema[key] = typeDesc;
      }
    }

    return JSON.stringify(jsonSchema, null, 2);
  } catch {
    return "Check the required fields in your original prompt";
  }
}

/**
 * Helper: Create failure result with logging for debugging
 */
function failResult<T>(
  failureReason: StructuredResult<T>["failureReason"],
  raw: string,
  attempt: 1 | 2,
  usedExtraction: boolean,
  usedRepair: boolean,
  validationError?: string,
  latencyMs = 0,
  attempt1Latency?: number,
  attempt2Latency?: number,
): StructuredResult<T> {
  // Log failures for debugging (especially schema mismatches)
  if (failureReason === "schema_mismatch" || failureReason === "invalid_json") {
    console.error(`[WRAPPER-FAIL] Attempt ${attempt}, Reason: ${failureReason}`);
    console.error(`[WRAPPER-FAIL] Raw output: ${raw}`);
    if (validationError) {
      console.error(`[WRAPPER-FAIL] Validation error: ${validationError}`);
    }
  }

  return {
    ok: false,
    raw,
    attempt,
    usedExtraction,
    usedRepair,
    latencyMs,
    attempt1Latency,
    attempt2Latency,
    failureReason,
    validationError,
  };
}

// Export helper for testing
export const TEST_HELPERS = {
  tryParseJson,
  parseAndValidateAttempt2,
  summarizeZodError,
  getSchemaFields,
  failResult,
};
