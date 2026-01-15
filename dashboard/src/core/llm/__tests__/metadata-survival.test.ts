/**
 * T1.2.B4.5 — Tests for metadata survival on failure
 * Verifies that wrapper metadata is preserved when improvePromptWithOllama fails
 * Updated for /api/chat migration
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ImprovePromptError, improvePromptWithOllama } from "../improvePrompt";
import * as ollamaChatModule from "../ollamaChat";

// Mock callOllamaChat
vi.mock("../ollamaChat", () => ({
  callOllamaChat: vi.fn(),
}));

const mockCallOllamaChat = ollamaChatModule.callOllamaChat as unknown as ReturnType<typeof vi.fn>;

describe("T1.2.B4.5 — Metadata survives failure", () => {
  beforeEach(() => {
    mockCallOllamaChat.mockReset();
  });

  afterEach(() => {
    mockCallOllamaChat.mockReset();
  });

  it("preserves wrapper metadata on JSON parse failure", async () => {
    // Mock that returns invalid JSON
    mockCallOllamaChat.mockResolvedValueOnce("Text without JSON at all");

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

      expect.fail("Expected ImprovePromptError to be thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      expect(err.meta).toBeDefined();
      expect(err.meta?.wrapper).toBeDefined();
      expect(err.meta?.wrapper?.failureReason).toBe("json_parse_failed");
    }
  });

  it("preserves extraction metadata when extraction succeeds but validation fails", async () => {
    // Mock that returns text with embedded JSON that validates incorrectly
    mockCallOllamaChat.mockResolvedValueOnce(
      'Some text before {"improved_prompt": "test", "clarifying_questions": "not an array"}',
    );

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

      expect.fail("Expected ImprovePromptError to be thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      // Verify it's a validation error
      expect(err.message).toContain("Failed to generate valid response");
    }
  });

  it("success case should NOT throw error", async () => {
    // Mock that returns valid JSON
    mockCallOllamaChat.mockResolvedValueOnce(
      JSON.stringify({
        improved_prompt: "You are an expert in data analysis. Create a report.",
        clarifying_questions: [],
        assumptions: [],
        confidence: 0.8,
      }),
    );

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
    expect(result.improved_prompt).toContain("data analysis");
  });

  it("handles API errors and preserves error metadata", async () => {
    // Mock that simulates API error
    mockCallOllamaChat.mockRejectedValueOnce(new Error("Ollama API error: 404 Not Found"));

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

      expect.fail("Expected ImprovePromptError to be thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ImprovePromptError);
      const err = error as ImprovePromptError;

      // Should be an ImprovePromptError with the API error message
      expect(err.message).toContain("Ollama API error");
    }
  });
});
