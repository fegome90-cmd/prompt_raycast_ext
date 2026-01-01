import { describe, it, expect, afterEach, vi } from "vitest";
import { z } from "zod";
import { ollamaGenerateStructured, setTransport, resetTransport, TEST_HELPERS } from "../ollamaStructured";
import type { OllamaTransport } from "../ollamaRaw";

// Mock transport for testing
const mockTransportWithNullArrays: OllamaTransport = async (req) => ({
  raw: JSON.stringify({
    improved_prompt: "Test prompt",
    clarifying_questions: null, // This should be fixed to []
    assumptions: null, // This should be fixed to []
    confidence: 0.8,
  }),
  latencyMs: 100,
  model: req.model,
});

const mockTransportWithValidArrays: OllamaTransport = async (req) => ({
  raw: JSON.stringify({
    improved_prompt: "Test prompt",
    clarifying_questions: [],
    assumptions: [],
    confidence: 0.8,
  }),
  latencyMs: 100,
  model: req.model,
});

// Mock for chatty output with null arrays inside
const mockTransportChattyWithNullArrays: OllamaTransport = async (req) => ({
  raw: `Here's the improved prompt:

\`\`\`json
{
  "improved_prompt": "Create a function to validate emails",
  "clarifying_questions": null,
  "assumptions": null,
  "confidence": 0.8
}
\`\`\`

Let me know if you need anything else!`,
  latencyMs: 100,
  model: req.model,
});

describe("Null Array Fix", () => {
  afterEach(() => {
    resetTransport();
  });

  it("should handle null arrays in repair mode", async () => {
    const testSchema = z.object({
      improved_prompt: z.string().min(1),
      clarifying_questions: z.array(z.string()).max(3),
      assumptions: z.array(z.string()).max(5),
      confidence: z.number().min(0).max(1),
    });

    // Test with mock that returns null arrays
    setTransport(mockTransportWithNullArrays);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "Test prompt that should handle null arrays",
      mode: "extract+repair",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 5000,
    });

    // Should fail on first attempt but succeed on repair
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(Array.isArray(result.data?.clarifying_questions)).toBe(true);
      expect(Array.isArray(result.data?.assumptions)).toBe(true);
      expect(result.data?.clarifying_questions).toEqual([]);
      expect(result.data?.assumptions).toEqual([]);
    }
  });

  it("should pass through valid arrays without modification", async () => {
    const testSchema = z.object({
      improved_prompt: z.string().min(1),
      clarifying_questions: z.array(z.string()).max(3),
      assumptions: z.array(z.string()).max(5),
      confidence: z.number().min(0).max(1),
    });

    // Test with mock that returns valid arrays
    setTransport(mockTransportWithValidArrays);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "Test prompt with valid arrays",
      mode: "extract+repair",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 5000,
    });

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(Array.isArray(result.data?.clarifying_questions)).toBe(true);
      expect(Array.isArray(result.data?.assumptions)).toBe(true);
      expect(result.data?.clarifying_questions).toEqual([]);
      expect(result.data?.assumptions).toEqual([]);
    }
  });

  it("should handle chatty output with null arrays via extraction", async () => {
    const testSchema = z.object({
      improved_prompt: z.string().min(1),
      clarifying_questions: z.array(z.string()).max(3),
      assumptions: z.array(z.string()).max(5),
      confidence: z.number().min(0).max(1),
    });

    // Test with mock that returns chatty output with null arrays in JSON fence
    setTransport(mockTransportChattyWithNullArrays);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "Test chatty output with null arrays",
      mode: "extract+repair",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 5000,
    });

    // Should extract JSON and sanitize null arrays to []
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(Array.isArray(result.data?.clarifying_questions)).toBe(true);
      expect(Array.isArray(result.data?.assumptions)).toBe(true);
      expect(result.data?.clarifying_questions).toEqual([]);
      expect(result.data?.assumptions).toEqual([]);
      expect(result.usedExtraction).toBe(true);
      expect(result.extractionMethod).toBe("fence");
    }
  });

  it("should handle null arrays in direct parse mode", async () => {
    const testSchema = z.object({
      improved_prompt: z.string().min(1),
      clarifying_questions: z.array(z.string()).max(3),
      assumptions: z.array(z.string()).max(5),
      confidence: z.number().min(0).max(1),
    });

    // Test with mock that returns null arrays
    setTransport(mockTransportWithNullArrays);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "Test direct parse with null arrays",
      mode: "strict", // Should use direct parse with sanitization
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 5000,
    });

    // Should sanitize null arrays to [] even in strict mode
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(Array.isArray(result.data?.clarifying_questions)).toBe(true);
      expect(Array.isArray(result.data?.assumptions)).toBe(true);
      expect(result.data?.clarifying_questions).toEqual([]);
      expect(result.data?.assumptions).toEqual([]);
    }
  });
});

describe("coerceStringArray - Data Loss Detection", () => {
  const { coerceStringArray } = TEST_HELPERS;

  it("should log warning when non-null non-array value is dropped", async () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    const result = coerceStringArray("a string instead of array");

    expect(result).toEqual([]);
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("[COERCION] Unexpected array type")
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("string")
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("a string instead of array")
    );

    consoleSpy.mockRestore();
  });

  it("should not warn for null or undefined", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(coerceStringArray(null)).toEqual([]);
    expect(coerceStringArray(undefined)).toEqual([]);
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should not warn for valid arrays", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(coerceStringArray(["a", "b"])).toEqual(["a", "b"]);
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should handle numbers", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(coerceStringArray(42)).toEqual([]);
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("number"));

    consoleSpy.mockRestore();
  });

  it("should filter out non-string items from arrays", () => {
    expect(coerceStringArray(["a", 42, null, "b"])).toEqual(["a", "b"]);
  });
});
