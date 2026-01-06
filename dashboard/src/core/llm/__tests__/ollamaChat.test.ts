/**
 * Integration tests for ollamaChat.ts (/api/chat endpoint)
 * Tests verify proper system/user message separation
 */

import { describe, it, expect } from "vitest";
import { callOllamaChat, ollamaHealthCheckChat, type OllamaMessage } from "../ollamaChat";

// Helper to check if Ollama is running
async function isOllamaAvailable(): Promise<boolean> {
  const health = await ollamaHealthCheckChat({
    baseUrl: "http://localhost:11434",
    timeoutMs: 2000,
  });
  return health.ok;
}

describe("ollamaChat - Integration Tests", () => {
  describe.skip("with Ollama running (requires Ollama service)", () => {
    const defaultOptions = {
      baseUrl: "http://localhost:11434",
      model: "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
      timeoutMs: 30000,
      temperature: 0.1,
    };

    it("should separate system and user messages correctly", async () => {
      const systemPrompt = "You are a coding expert. Always respond with 'CODE: ' prefix.";
      const userPrompt = "Write a hello world function";

      const response = await callOllamaChat(systemPrompt, userPrompt, defaultOptions);

      // System message should influence the response
      expect(response).toBeTruthy();
      expect(typeof response).toBe("string");
      // The model should follow the system instruction
      expect(response.toLowerCase()).toContain("code");
    });

    it("should handle empty system message", async () => {
      const systemPrompt = "";
      const userPrompt = "Say hello";

      const response = await callOllamaChat(systemPrompt, userPrompt, defaultOptions);

      expect(response).toBeTruthy();
      expect(typeof response).toBe("string");
      expect(response.length).toBeGreaterThan(0);
    });

    it("should handle long user prompts", async () => {
      const systemPrompt = "You are a prompt engineer.";
      const userPrompt =
        "Improve this prompt: Write a function that sorts an array of integers in ascending order using bubble sort algorithm in Python, include error handling for empty arrays, and add unit tests.";

      const response = await callOllamaChat(systemPrompt, userPrompt, defaultOptions);

      expect(response).toBeTruthy();
      expect(response.length).toBeGreaterThan(userPrompt.length); // Should improve/expand
    });

    it("should respect temperature setting for deterministic output", async () => {
      const systemPrompt = "You are a helpful assistant.";
      const userPrompt = "What is 2+2?";

      const options = { ...defaultOptions, temperature: 0.0 };

      const response1 = await callOllamaChat(systemPrompt, userPrompt, options);
      const response2 = await callOllamaChat(systemPrompt, userPrompt, options);

      // With temperature 0, responses should be identical
      expect(response1).toBe(response2);
    });

    it("should timeout after specified duration", async () => {
      const systemPrompt = "You are a helpful assistant.";
      const userPrompt = "Count to infinity";

      const options = { ...defaultOptions, timeoutMs: 100 };

      await expect(callOllamaChat(systemPrompt, userPrompt, options)).rejects.toThrow("timed out");
    });

    it("should handle connection errors gracefully", async () => {
      const systemPrompt = "You are a helpful assistant.";
      const userPrompt = "Say hello";

      const options = { ...defaultOptions, baseUrl: "http://localhost:9999" }; // Wrong port

      await expect(callOllamaChat(systemPrompt, userPrompt, options)).rejects.toThrow();
    });
  });

  describe("ollamaHealthCheckChat", () => {
    it("should return ok: true when Ollama is running", async () => {
      const health = await ollamaHealthCheckChat({
        baseUrl: "http://localhost:11434",
        timeoutMs: 2000,
      });

      // Don't fail if Ollama isn't running, just check the structure
      expect(typeof health.ok).toBe("boolean");
      if (health.ok) {
        expect(health.error).toBeUndefined();
      } else {
        expect(health.error).toBeTruthy();
      }
    });

    it("should timeout correctly", async () => {
      const health = await ollamaHealthCheckChat({
        baseUrl: "http://localhost:9999",
        timeoutMs: 100,
      });

      expect(health.ok).toBe(false);
      expect(health.error).toBeTruthy();
    });
  });

  describe("TypeScript Interfaces", () => {
    it("should have correct OllamaMessage type", () => {
      const message: OllamaMessage = {
        role: "system",
        content: "test",
      };

      expect(message.role).toBe("system");
      expect(message.content).toBe("test");
    });

    it("should accept all valid roles", () => {
      const roles: Array<OllamaMessage["role"]> = ["system", "user", "assistant"];

      roles.forEach((role) => {
        const message: OllamaMessage = { role, content: "test" };
        expect(message.role).toBe(role);
      });
    });
  });
});
