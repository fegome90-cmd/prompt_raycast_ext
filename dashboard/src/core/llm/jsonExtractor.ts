/**
 * Robust JSON extraction from text
 * Handles code fences, tags, and nested objects safely
 * Telemetría: extraction_used, extraction_success, extraction_failure_reason
 */

export interface ExtractionResult {
  json: string;
  usedExtraction: true;
  extractionMethod: "fence" | "tag" | "scan";
}

export interface ExtractionFailure {
  reason: "no_json_found" | "unbalanced_braces" | "invalid_syntax";
  details?: string;
}

/**
 * Extract first valid JSON object from text
 * Returns null if no valid JSON can be extracted
 */
export function extractJsonFromText(text: string): ExtractionResult | null {
  // Attempt 1: Extract from code fences
  const fenceResult = extractFromFence(text);
  if (fenceResult) return fenceResult;

  // Attempt 2: Extract from <json> tags
  const tagResult = extractFromTag(text);
  if (tagResult) return tagResult;

  // Attempt 3: Global scan for JSON object
  return extractFirstJsonObject(text);
}

/**
 * Extract JSON from markdown code fences
 * Handles ```json and ```
 */
function extractFromFence(text: string): ExtractionResult | null {
  // Find code fence (json or plain)
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (!fenceMatch) return null;

  const content = fenceMatch[1];

  // Extract first complete JSON object from fence content
  const jsonObj = extractFirstJsonObject(content);
  if (jsonObj) {
    return {
      json: jsonObj.json,
      usedExtraction: true,
      extractionMethod: "fence",
    };
  }

  return null;
}

/**
 * Extract JSON from <json> tags
 */
function extractFromTag(text: string): ExtractionResult | null {
  const tagMatch = text.match(/<json>([\s\S]*?)<\/json>/);
  if (!tagMatch) return null;

  const content = tagMatch[1];

  // Extract first complete JSON object from tag content
  const jsonObj = extractFirstJsonObject(content);
  if (jsonObj) {
    return {
      json: jsonObj.json,
      usedExtraction: true,
      extractionMethod: "tag",
    };
  }

  return null;
}

/**
 * Extract first complete JSON object using balance scanner
 * Ignores braces inside strings with proper escape handling
 */
export function extractFirstJsonObject(text: string): ExtractionResult | null {
  const firstBrace = text.indexOf("{");
  if (firstBrace === -1) return null;

  let balance = 0;
  let inString = false;
  let isEscaped = false;
  let endIndex = -1;

  for (let i = firstBrace; i < text.length; i++) {
    const char = text[i];

    // Handle escapes inside strings
    if (inString && char === "\\" && !isEscaped) {
      isEscaped = true;
      continue;
    }

    // Toggle string state (ignore escaped quotes)
    if (char === '"' && !isEscaped) {
      inString = !inString;
    }

    // Track brace balance only outside strings
    if (!inString) {
      if (char === "{") {
        balance++;
      } else if (char === "}") {
        balance--;

        // Complete object found
        if (balance === 0) {
          endIndex = i;
          break;
        }
      }
    }

    isEscaped = false;
  }

  // No complete object found
  if (endIndex === -1) {
    return null;
  }

  const json = text.slice(firstBrace, endIndex + 1);

  return {
    json,
    usedExtraction: true,
    extractionMethod: "scan",
  };
}

import { z } from "zod";

/**
 * Validate extracted JSON string
 * Returns parsed object or failure reason
 */
export function validateExtractedJson(
  json: string,
  schema?: z.ZodSchema,
): { success: true; data: unknown } | { success: false; error: string } {
  let parsed: unknown;

  // First part: parse raw JSON
  try {
    parsed = JSON.parse(json);
  } catch (e) {
    return {
      success: false,
      error: e instanceof SyntaxError ? e.message : "Invalid JSON syntax",
    };
  }

  // Second part: validate against Zod schema
  if (schema) {
    const validation = schema.safeParse(parsed);
    if (!validation.success) {
      const firstError = validation.error.errors[0];
      const errorPath = firstError.path.length > 0 ? firstError.path.join(".") : "root";
      const errorMsg = firstError.message || "Validation failed";
      return { success: false, error: `${errorPath}: ${errorMsg}` };
    }
    return { success: true, data: validation.data };
  }

  // No schema = success with parsed data
  return { success: true, data: parsed };
}
