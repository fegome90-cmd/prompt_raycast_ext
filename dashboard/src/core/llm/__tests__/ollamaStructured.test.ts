/**
 * Task 2: Fix Latency Accumulation Bug in ollamaStructured.ts
 * TDD Approach: Failing test first, then implementation
 *
 * Bug: When both attempts are used (attempt 1 fails validation, attempt 2 is repair),
 * only attempt 2's latency is returned. Total latency should be cumulative (latency1 + latency2).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ollamaGenerateStructured, setTransport, resetTransport } from "../ollamaStructured";
import type { OllamaTransport } from "../ollamaRaw";
import { z } from "zod";

describe("Task 2 - Latency Accumulation Bug", () => {
  const testSchema = z.object({
    improved_prompt: z.string(),
    confidence: z.number().min(0).max(1),
    clarifying_questions: z.array(z.string()),
    assumptions: z.array(z.string()),
  });

  const validResponse = {
    improved_prompt: "Write a function that adds two numbers in Python.",
    clarifying_questions: [],
    assumptions: [],
    confidence: 0.9,
  };

  const validResponseRaw = JSON.stringify(validResponse);

  let mockTransport: OllamaTransport;

  beforeEach(() => {
    vi.clearAllMocks();
    resetTransport();
  });

  afterEach(() => {
    resetTransport();
  });

  describe("BUG: Cumulative latency not returned when both attempts are used", () => {
    it("should return cumulative latency (latency1 + latency2) when repair attempt is used", async () => {
      // Attempt 1: Invalid JSON (triggers repair)
      // Attempt 2: Successful repair
      const latency1 = 100;
      const latency2 = 150;
      const expectedTotalLatency = latency1 + latency2; // Should be 250

      let callCount = 0;
      mockTransport = vi.fn(async (req) => {
        callCount++;

        if (callCount === 1) {
          // First call: attempt 1 - invalid JSON that can't be parsed
          return {
            raw: "{invalid json",
            latencyMs: latency1,
            model: req.model,
          };
        } else {
          // Second call: attempt 2 - repair succeeds
          return {
            raw: validResponseRaw,
            latencyMs: latency2,
            model: req.model,
          };
        }
      });

      setTransport(mockTransport);

      const result = await ollamaGenerateStructured({
        schema: testSchema,
        prompt: "Create a prompt.",
        mode: "extract+repair",
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      });

      // Verify both attempts were made
      expect(mockTransport).toHaveBeenCalledTimes(2);

      // Verify result structure
      expect(result.ok).toBe(true);
      expect(result.attempt).toBe(2);
      expect(result.usedRepair).toBe(true);

      // BUG: Currently returns only latency2 (150), should return latency1 + latency2 (250)
      // This test FAILS with current code
      expect(result.latencyMs).toBe(expectedTotalLatency);
      expect(result.latencyMs).toBe(250);

      // Verify telemetry fields are populated (after fix)
      // These will fail initially because the fields don't exist yet
      expect(result.attempt1Latency).toBe(latency1);
      expect(result.attempt2Latency).toBe(latency2);
    });

    it("should return only attempt1Latency when single attempt succeeds", async () => {
      const latency1 = 100;

      mockTransport = vi.fn(async (req) => ({
        raw: validResponseRaw,
        latencyMs: latency1,
        model: req.model,
      }));

      setTransport(mockTransport);

      const result = await ollamaGenerateStructured({
        schema: testSchema,
        prompt: "Create a prompt that says hello.",
        mode: "extract+repair",
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      });

      // Verify only one attempt was made
      expect(mockTransport).toHaveBeenCalledTimes(1);

      // Verify result structure
      expect(result.ok).toBe(true);
      expect(result.attempt).toBe(1);
      expect(result.usedRepair).toBe(false);

      // Single attempt: latencyMs should equal attempt1Latency
      expect(result.latencyMs).toBe(latency1);
      expect(result.attempt1Latency).toBe(latency1);
      expect(result.attempt2Latency).toBeUndefined();
    });

    it("should handle repair attempt that fails (still accumulates latency)", async () => {
      const latency1 = 100;
      const latency2 = 150;
      const expectedTotalLatency = latency1 + latency2;

      let callCount = 0;
      mockTransport = vi.fn(async (req) => {
        callCount++;

        if (callCount === 1) {
          // First call: attempt 1 - invalid JSON
          return {
            raw: "{invalid json",
            latencyMs: latency1,
            model: req.model,
          };
        } else {
          // Second call: attempt 2 - repair fails (still invalid JSON)
          return {
            raw: "{still invalid json", // Still invalid JSON
            latencyMs: latency2,
            model: req.model,
          };
        }
      });

      setTransport(mockTransport);

      const result = await ollamaGenerateStructured({
        schema: testSchema,
        prompt: "You are a prompt improver. Create a prompt.",
        mode: "extract+repair",
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      });

      // Verify both attempts were made
      expect(mockTransport).toHaveBeenCalledTimes(2);

      // Verify failure
      expect(result.ok).toBe(false);
      expect(result.attempt).toBe(2);
      expect(result.usedRepair).toBe(true);

      // Even on failure, latency should be cumulative
      expect(result.latencyMs).toBe(expectedTotalLatency);
      expect(result.attempt1Latency).toBe(latency1);
      expect(result.attempt2Latency).toBe(latency2);
    });

    it("should accumulate latency when schema validation fails on attempt 1", async () => {
      const latency1 = 80;
      const latency2 = 120;
      const expectedTotalLatency = latency1 + latency2;

      let callCount = 0;
      mockTransport = vi.fn(async (req) => {
        callCount++;

        if (callCount === 1) {
          // First call: attempt 1 - valid JSON but schema mismatch (confidence is out of range)
          return {
            raw: JSON.stringify({
              improved_prompt: "Bad prompt",
              clarifying_questions: [],
              assumptions: [],
              confidence: 1.5, // Invalid: should be between 0 and 1
            }),
            latencyMs: latency1,
            model: req.model,
          };
        } else {
          // Second call: attempt 2 - repair succeeds
          return {
            raw: validResponseRaw,
            latencyMs: latency2,
            model: req.model,
          };
        }
      });

      setTransport(mockTransport);

      const result = await ollamaGenerateStructured({
        schema: testSchema,
        prompt: "Create a prompt.",
        mode: "extract+repair",
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      });

      // Verify both attempts were made
      expect(mockTransport).toHaveBeenCalledTimes(2);

      // Verify success after repair
      expect(result.ok).toBe(true);
      expect(result.attempt).toBe(2);
      expect(result.usedRepair).toBe(true);

      // BUG: Currently returns only latency2 (120), should return latency1 + latency2 (200)
      expect(result.latencyMs).toBe(expectedTotalLatency);
      expect(result.attempt1Latency).toBe(latency1);
      expect(result.attempt2Latency).toBe(latency2);
    });
  });

  describe("Edge cases", () => {
    it("should handle zero latency on first attempt", async () => {
      const latency1 = 0;
      const latency2 = 100;

      let callCount = 0;
      mockTransport = vi.fn(async (req) => {
        callCount++;

        if (callCount === 1) {
          // Invalid JSON to trigger repair
          return {
            raw: "{invalid",
            latencyMs: latency1,
            model: req.model,
          };
        } else {
          // Repair succeeds
          return {
            raw: validResponseRaw,
            latencyMs: latency2,
            model: req.model,
          };
        }
      });

      setTransport(mockTransport);

      const result = await ollamaGenerateStructured({
        schema: testSchema,
        prompt: "Test.",
        mode: "extract+repair",
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      });

      // Should still accumulate even with zero latency
      expect(result.latencyMs).toBe(latency1 + latency2);
      expect(result.attempt1Latency).toBe(latency1);
      expect(result.attempt2Latency).toBe(latency2);
    });
  });
});
