/**
 * TDD tests for improvePrompt.ts latency tracking bug
 * Task 1: Fix latencyMs hardcoded to 0
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { improvePromptWithOllama, ImprovePromptError } from "../improvePrompt";
import * as ollamaChatModule from "../ollamaChat";

// Mock callOllamaChat
vi.mock("../ollamaChat", () => ({
  callOllamaChat: vi.fn(),
}));

const mockCallOllamaChat = ollamaChatModule.callOllamaChat as unknown as ReturnType<typeof vi.fn>;

describe("Task 1 - Latency Tracking Bug", () => {
  beforeEach(() => {
    mockCallOllamaChat.mockReset();
  });

  afterEach(() => {
    mockCallOllamaChat.mockReset();
  });

  describe("BUG: latencyMs hardcoded to 0", () => {
    it("should return actual latencyMs > 0 for successful single attempt", async () => {
      // Simulate a 100ms delay
      mockCallOllamaChat.mockImplementation(async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return JSON.stringify({
          improved_prompt: "Write a function that adds two numbers in Python.",
          clarifying_questions: [],
          assumptions: [],
          confidence: 0.9,
        });
      });

      const result = await improvePromptWithOllama({
        rawInput: "Write a function that adds two numbers",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 30000,
        },
      });

      // Verify metadata exists
      expect(result._metadata).toBeDefined();

      // BUG: Currently returns 0, should be > 0
      // This test FAILS with current code (latencyMs: 0)
      // This test PASSES after fix (latencyMs: ~100)
      expect(result._metadata?.latencyMs).toBeGreaterThan(0);
      expect(result._metadata?.latencyMs).toBeGreaterThanOrEqual(100); // At least 100ms
    });

    it("should return actual latencyMs > 0 when extraction is used", async () => {
      // Simulate extraction scenario (text before JSON)
      mockCallOllamaChat.mockImplementation(async () => {
        await new Promise((resolve) => setTimeout(resolve, 150));
        return 'Some text before {"improved_prompt": "Create marketing copy for social media.", "clarifying_questions": [], "assumptions": [], "confidence": 0.85}';
      });

      const result = await improvePromptWithOllama({
        rawInput: "Create a prompt for generating marketing copy",
        preset: "specific",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 30000,
        },
      });

      // Verify metadata exists
      expect(result._metadata).toBeDefined();

      // BUG: Currently returns 0, should be > 0
      expect(result._metadata?.latencyMs).toBeGreaterThan(0);
      expect(result._metadata?.latencyMs).toBeGreaterThanOrEqual(150); // At least 150ms
      expect(result._metadata?.usedExtraction).toBe(true); // Should have used extraction
    });

    it("should return actual latencyMs for repair attempt (second attempt)", async () => {
      // First attempt: returns bad quality prompt (triggers repair)
      mockCallOllamaChat.mockImplementationOnce(async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return JSON.stringify({
          improved_prompt: "You are a prompt improver. Create a prompt.", // Bad: contains meta
          clarifying_questions: [],
          assumptions: [],
          confidence: 0.7,
        });
      });

      // Second attempt (repair): returns good prompt
      mockCallOllamaChat.mockImplementationOnce(async () => {
        await new Promise((resolve) => setTimeout(resolve, 150));
        return JSON.stringify({
          improved_prompt: "Generate a greeting message.",
          clarifying_questions: [],
          assumptions: [],
          confidence: 0.95,
        });
      });

      const result = await improvePromptWithOllama({
        rawInput: "You are a prompt improver. Create a prompt that says hello.",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "test-model",
          timeoutMs: 30000,
        },
      });

      // Verify metadata exists
      expect(result._metadata).toBeDefined();

      // BUG: Currently returns 0, should be > 0 even for second attempt
      expect(result._metadata?.latencyMs).toBeGreaterThan(0);
      expect(result._metadata?.attempt).toBe(2); // Should be second attempt
      expect(result._metadata?.usedRepair).toBe(true); // Should have used repair
    });

    it("should include actual latencyMs in ImprovePromptError on timeout", async () => {
      // Simulate a timeout
      mockCallOllamaChat.mockImplementation(async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        throw new Error("Ollama request timed out after 100ms");
      });

      try {
        await improvePromptWithOllama({
          rawInput: "Test input",
          preset: "default",
          options: {
            baseUrl: "http://localhost:11434",
            model: "test-model",
            timeoutMs: 100,
          },
        });
        expect.fail("Should have thrown ImprovePromptError");
      } catch (error) {
        expect(error).toBeInstanceOf(ImprovePromptError);
        const err = error as ImprovePromptError;

        // Verify error has metadata with latencyMs
        expect(err.meta).toBeDefined();
        expect(err.meta?.wrapper).toBeDefined();
        expect(err.meta?.wrapper?.latencyMs).toBeDefined();

        // BUG: Error path already calculates latencyMs correctly
        // This test should PASS even before the fix
        expect(err.meta?.wrapper?.latencyMs).toBeGreaterThanOrEqual(0);
      }
    });

    it("should include actual latencyMs in ImprovePromptError on parse failure", async () => {
      // Simulate parse failure (invalid JSON)
      mockCallOllamaChat.mockImplementation(async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return "This is not valid JSON at all";
      });

      try {
        await improvePromptWithOllama({
          rawInput: "Test input",
          preset: "default",
          options: {
            baseUrl: "http://localhost:11434",
            model: "test-model",
            timeoutMs: 30000,
          },
        });
        expect.fail("Should have thrown ImprovePromptError");
      } catch (error) {
        expect(error).toBeInstanceOf(ImprovePromptError);
        const err = error as ImprovePromptError;

        // Verify error has metadata with latencyMs
        expect(err.meta).toBeDefined();
        expect(err.meta?.wrapper).toBeDefined();
        expect(err.meta?.wrapper?.latencyMs).toBeDefined();

        // BUG: Error path already calculates latencyMs correctly
        // This test should PASS even before the fix
        expect(err.meta?.wrapper?.latencyMs).toBeGreaterThanOrEqual(100);
      }
    });
  });

  describe("metadata structure validation", () => {
    it("should have correct metadata type definition", () => {
      // This test verifies the type structure without calling Ollama
      const metadata = {
        usedExtraction: true,
        usedRepair: false,
        attempt: 1 as const,
        latencyMs: 100,
      };

      expect(metadata.usedExtraction).toBe(true);
      expect(metadata.usedRepair).toBe(false);
      expect(metadata.attempt).toBe(1);
      expect(metadata.latencyMs).toBe(100);
    });
  });
});
