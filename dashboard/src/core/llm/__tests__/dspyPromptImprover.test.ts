/**
 * Tests for DSPy Prompt Improver Zod schema validation
 *
 * Covers the confidence field handling:
 * - null → default 0.8 transformation
 * - valid confidence preservation
 * - range validation (0-1)
 */

import { describe, it, expect } from "vitest";
import { DSPyResponseSchema } from "../dspyPromptImprover";

describe("DSPyResponseSchema", () => {
  // Valid response factory
  const validResponse = {
    improved_prompt: "Test improved prompt",
    role: "Senior Assistant",
    directive: "Help the user",
    framework: "chain-of-thought",
    guardrails: ["Be concise", "Be accurate"],
  };

  describe("confidence field", () => {
    it("should transform null confidence to default 0.8", () => {
      const result = DSPyResponseSchema.parse({
        ...validResponse,
        confidence: null,
      });
      expect(result.confidence).toBe(0.8);
    });

    it("should preserve valid confidence values", () => {
      const result = DSPyResponseSchema.parse({
        ...validResponse,
        confidence: 0.95,
      });
      expect(result.confidence).toBe(0.95);
    });

    it("should handle missing confidence field (undefined)", () => {
      const result = DSPyResponseSchema.parse(validResponse);
      expect(result.confidence).toBe(0.8);
    });

    it("should accept confidence at lower bound (0)", () => {
      const result = DSPyResponseSchema.parse({
        ...validResponse,
        confidence: 0,
      });
      expect(result.confidence).toBe(0);
    });

    it("should accept confidence at upper bound (1)", () => {
      const result = DSPyResponseSchema.parse({
        ...validResponse,
        confidence: 1,
      });
      expect(result.confidence).toBe(1);
    });

    it("should reject confidence below 0", () => {
      expect(() =>
        DSPyResponseSchema.parse({
          ...validResponse,
          confidence: -0.1,
        }),
      ).toThrow();
    });

    it("should reject confidence above 1", () => {
      expect(() =>
        DSPyResponseSchema.parse({
          ...validResponse,
          confidence: 1.5,
        }),
      ).toThrow();
    });
  });

  describe("required fields", () => {
    it("should reject empty improved_prompt", () => {
      expect(() =>
        DSPyResponseSchema.parse({
          ...validResponse,
          improved_prompt: "",
        }),
      ).toThrow();
    });

    it("should accept optional reasoning field", () => {
      const result = DSPyResponseSchema.parse({
        ...validResponse,
        reasoning: "This is why I improved it this way",
      });
      expect(result.reasoning).toBe("This is why I improved it this way");
    });

    it("should handle missing reasoning field", () => {
      const result = DSPyResponseSchema.parse(validResponse);
      expect(result.reasoning).toBeUndefined();
    });
  });
});
