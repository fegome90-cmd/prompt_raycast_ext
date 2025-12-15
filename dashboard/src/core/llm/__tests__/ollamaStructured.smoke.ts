/**
 * Smoke test for ollamaGenerateStructured
 * Minimal test to verify basic functionality
 */

import { describe, it, expect } from "vitest";
import { ollamaGenerateStructured, setTransport } from "../ollamaStructured";
import { z } from "zod";
import type { OllamaTransport } from "../ollamaRaw";

describe("T1.2-B2 Smoke Tests", () => {
  const testSchema = z.object({
    name: z.string(),
    value: z.number(),
  });

  it("debe funcionar con JSON limpio en modo strict", async () => {
    const mockTransport: OllamaTransport = async () => ({
      raw: '{"name": "test", "value": 42}',
      latencyMs: 100,
      model: "test-model",
    });

    setTransport(mockTransport);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "test",
      mode: "strict",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 30000,
    });

    expect(result.ok).toBe(true);
    expect(result.data).toEqual({ name: "test", value: 42 });
    expect(result.attempt).toBe(1);
    expect(result.usedExtraction).toBe(false);
    expect(result.usedRepair).toBe(false);
  });

  it("debe extraer JSON de code fence", async () => {
    const mockTransport: OllamaTransport = async () => ({
      raw: 'Here is the result:\n```json\n{"name": "test", "value": 42}\n```\nDone!',
      latencyMs: 100,
      model: "test-model",
    });

    setTransport(mockTransport);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "test",
      mode: "extract",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 30000,
    });

    expect(result.ok).toBe(true);
    expect(result.data).toEqual({ name: "test", value: 42 });
    expect(result.usedExtraction).toBe(true);
    expect(result.extractionMethod).toBe("fence");
  });

  it("debe fallback a repair en schema mismatch", async () => {
    let callCount = 0;
    const mockTransport: OllamaTransport = async () => {
      callCount++;
      if (callCount === 1) {
        // First attempt: wrong type
        return {
          raw: '{"name": 123, "value": "not a number"}',
          latencyMs: 100,
          model: "test-model",
        };
      }
      // Repair attempt: fixed
      return {
        raw: '{"name": "test", "value": 42}',
        latencyMs: 100,
        model: "test-model",
      };
    };

    setTransport(mockTransport);

    const result = await ollamaGenerateStructured({
      schema: testSchema,
      prompt: "test",
      mode: "extract+repair",
      baseUrl: "http://localhost:11434",
      model: "test-model",
      timeoutMs: 30000,
    });

    expect(result.ok).toBe(true);
    expect(result.attempt).toBe(2);
    expect(result.usedRepair).toBe(true);
  });
});
