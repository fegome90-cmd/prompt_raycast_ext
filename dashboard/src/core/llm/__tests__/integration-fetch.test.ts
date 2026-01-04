/**
 * Integration tests validating native fetch works end-to-end
 */

import { improvePromptWithDSPy } from "../dspyPromptImprover";
import { ollamaHealthCheck } from "../ollamaClient";
import { DSPyPromptImproverClient } from "../dspyPromptImprover";

describe("Native Fetch Integration", () => {
  describe("DSPy Backend", () => {
    test("can health check DSPy backend", async () => {
      const client = new DSPyPromptImproverClient({
        baseUrl: "http://localhost:8000",
        timeoutMs: 5000,
      });

      const health = await client.healthCheck();
      expect(health.status).toBe("healthy");
      expect(health.dspy_configured).toBe(true);
    }, 10000);

    test("can improve prompt via DSPy", async () => {
      const result = await improvePromptWithDSPy("write a function", "default");

      expect(result).toHaveProperty("improved_prompt");
      expect(result.improved_prompt).toBeTruthy();
      expect(result.improved_prompt.length).toBeGreaterThan(10);
    }, 30000);
  });

  describe("Ollama Backend", () => {
    test("can health check Ollama", async () => {
      const health = await ollamaHealthCheck({
        baseUrl: "http://localhost:11434",
        timeoutMs: 2000,
      });

      expect(health.ok).toBe(true);
    }, 5000);
  });
});
