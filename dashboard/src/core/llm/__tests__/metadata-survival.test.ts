/**
 * T1.2.B4.5 — Tests for metadata survival on failure
 * Verifies that wrapper metadata is preserved when improvePromptWithOllama fails
 */

import { expect, it, describe, beforeEach, afterEach } from "vitest";
import { improvePromptWithOllama, ImprovePromptError } from "../improvePrompt";
import type { OllamaTransport } from "../ollamaRaw";
import { resetTransport, setTransport } from "../ollamaStructured";

describe("T1.2.B4.5 — Metadata survives failure", () => {
  beforeEach(() => {
    resetTransport(); // Ensure clean slate before each test
  });

  afterEach(() => {
    resetTransport(); // Cleanup after each test
  });

  it("preserves wrapper metadata on schema_mismatch after repair", async () => {
    // Mock transport that returns invalid schema on attempt 1
    // and STILL invalid schema on attempt 2 (repair fails)
    let callCount = 0;
    const mockTransport: OllamaTransport = async () => {
      callCount++;
      if (callCount === 1) {
        // First call: missing required fields
        return {
          raw: '{"improved_prompt": "test"}', // missing clarifying_questions, assumptions, confidence
          latencyMs: 100,
          model: "test-model",
        };
      }
      // Repair attempt: STILL missing fields
      return {
        raw: '{"improved_prompt": "test repaired"}', // still missing required fields
        latencyMs: 100,
        model: "test-model",
      };
    };

    setTransport(mockTransport);

    try {
      await improvePromptWithOllama({
        rawInput: "test",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 30000,
        },
      });

      // Should not reach here
      expect.fail("Expected ImprovePromptError to be thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      // Verify metadata is present
      expect(err.meta).toBeDefined();
      expect(err.meta?.wrapper).toBeDefined();

      const wrapper = err.meta!.wrapper!;
      expect(wrapper.attempt).toBe(2); // Should have attempted repair
      expect(wrapper.usedRepair).toBe(true);
      expect(wrapper.usedExtraction).toBe(false);
      expect(wrapper.failureReason).toBe("schema_mismatch");
      expect(wrapper.latencyMs).toBeGreaterThan(0);
      expect(wrapper.validationError).toContain("assumptions");
    } finally {
      resetTransport();
    }
  });

  it("preserves metadata on timeout", async () => {
    // Mock transport that times out
    const mockTransport: OllamaTransport = async () => {
      throw Object.assign(new Error("Request timed out"), { name: "AbortError" });
    };

    setTransport(mockTransport);

    try {
      await improvePromptWithOllama({
        rawInput: "test",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 1000, // Short timeout
        },
      });

      expect.fail("Expected ImprovePromptError to be thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      expect(err.meta).toBeDefined();
      expect(err.meta?.wrapper).toBeDefined();

      const wrapper = err.meta!.wrapper!;
      expect(wrapper.attempt).toBe(1); // Timeout happened on first attempt
      expect(wrapper.usedRepair).toBe(false);
      expect(wrapper.failureReason).toBe("timeout");
      expect(wrapper.latencyMs).toBeGreaterThan(0);
    } finally {
      resetTransport();
    }
  });

  it("preserves extraction metadata when extraction succeeds but validation fails", async () => {
    let callCount = 0;
    const mockTransport: OllamaTransport = async () => {
      callCount++;
      if (callCount === 1) {
        // First call: returns chatty output with JSON inside
        return {
          raw: 'Here is the improved prompt:\n```json\n{"improved_prompt": "test", "clarifying_questions": [], "assumptions": [], "confidence": 0.8}\n```',
          latencyMs: 100,
          model: "test-model",
        };
      }
      // Repair won't be called in this test because extraction will succeed
      throw new Error("Should not reach attempt 2");
    };

    setTransport(mockTransport);

    try {
      await improvePromptWithOllama({
        rawInput: "test",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 30000,
        },
      });

      expect.fail("Expected error due to missing required fields");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      expect(err.meta).toBeDefined();
      expect(err.meta?.wrapper).toBeDefined();

      const wrapper = err.meta!.wrapper!;
      expect(wrapper.attempt).toBe(1); // Failed on first attempt
      expect(wrapper.usedExtraction).toBe(true); // Should have used extraction
      expect(wrapper.extractionMethod).toBe("fence"); // From code fence
    } finally {
      resetTransport();
    }
  });

  it("success case should NOT throw error", async () => {
    const mockTransport: OllamaTransport = async () => ({
      raw: '{"improved_prompt": "test improved prompt", "clarifying_questions": ["q1"], "assumptions": ["a1"], "confidence": 0.85}',
      latencyMs: 100,
      model: "test-model",
    });

    setTransport(mockTransport);

    const result = await improvePromptWithOllama({
      rawInput: "test",
      preset: "default",
      options: {
        baseUrl: "http://localhost:11434",
        model: "test-model",
        timeoutMs: 30000,
      },
    });

    expect(result.improved_prompt).toBeDefined();
    expect((result as { _metadata: { usedRepair: boolean; attempt: number } })._metadata).toBeDefined();
    expect((result as { _metadata: { usedRepair: boolean; attempt: number } })._metadata.usedRepair).toBe(false);
    expect((result as { _metadata: { usedRepair: boolean; attempt: number } })._metadata.attempt).toBe(1);

    resetTransport();
  });
});
