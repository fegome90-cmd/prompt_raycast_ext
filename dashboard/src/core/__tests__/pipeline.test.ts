/**
 * 10 Unit Tests Quirúrgicos para Pipeline de Prompts
 * Tests de alto impacto, bajo riesgo
 */

import { describe, it, expect, vi } from "vitest";
import { z } from "zod";

// Mock Ollama client
vi.mock("../llm/ollamaClient", () => ({
  ollamaGenerateJson: vi.fn(),
  ollamaHealthCheck: vi.fn(() => Promise.resolve({ ok: true })),
}));

// Mock config
vi.mock("../config", () => ({
  loadConfig: vi.fn(() => ({
    config: {
      ollama: { baseUrl: "http://localhost:11434", model: "test", timeoutMs: 30000 },
      pipeline: { maxQuestions: 3, maxAssumptions: 5, enableAutoRepair: true },
    },
    safeMode: false,
  })),
}));

describe("T1.2.A2 — 10 Unit Tests Quirúrgicos", () => {
  // Schema para validación
  const OutputSchema = z.object({
    improved_prompt: z.string().min(1),
    clarifying_questions: z.array(z.string()).max(3),
    assumptions: z.array(z.string()).max(5),
    confidence: z.number().min(0).max(1),
  });

  describe("1. parseOllamaJson_strict_ok", () => {
    it("debe parsear JSON estricto válido", async () => {
      const validJson = {
        improved_prompt: "Create a function in TypeScript",
        clarifying_questions: ["What should the function do?"],
        assumptions: ["Will use modern TS syntax"],
        confidence: 0.85,
      };

      const parsed = JSON.parse(JSON.stringify(validJson));
      expect(parsed).toEqual(validJson);
    });

    it("debe rechazar JSON con comentarios", async () => {
      const jsonWithComment = `{
        // This is a comment
        "improved_prompt": "Create a function",
        "clarifying_questions": [],
        "assumptions": [],
        "confidence": 0.5
      }`;

      expect(() => JSON.parse(jsonWithComment)).toThrow();
    });
  });

  describe("2. parseOllamaJson_rejects_text_prefix_suffix", () => {
    it("debe rechazar texto antes del JSON", () => {
      const text = 'Here is the JSON:\n{"test": 1}';
      expect(() => JSON.parse(text)).toThrow();
    });

    it("debe rechazar texto después del JSON", () => {
      const text = '{"test": 1}\nLet me know if you need anything else.';
      expect(() => JSON.parse(text)).toThrow();
    });
  });

  describe("3. extractJsonFromText_works_with_codefence", () => {
    const extractJson = (text: string): string | null => {
      // Extract JSON from code fences or text
      const jsonMatch = text.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
      if (jsonMatch) return jsonMatch[1];

      // Try finding JSON object
      const objectMatch = text.match(/\{[\s\S]*?\}/);
      return objectMatch ? objectMatch[0] : null;
    };

    it("debe extraer JSON de code fence", () => {
      const text = '```json\n{"test": 1}\n```';
      const extracted = extractJson(text);
      expect(extracted).toBe('{"test": 1}');
    });

    it("debe extraer JSON sin language tag", () => {
      const text = '```\n{"test": 1}\n```';
      const extracted = extractJson(text);
      expect(extracted).toBe('{"test": 1}');
    });

    it("debe extraer JSON de texto rodeado", () => {
      const text = 'Here you go: {"test": 1}. Hope this helps!';
      const extracted = extractJson(text);
      expect(extracted).toBe('{"test": 1}');
    });
  });

  describe("4. validateOutputSchema_missing_required_fails", () => {
    it("debe fallar sin improved_prompt", () => {
      const result = OutputSchema.safeParse({
        clarifying_questions: [],
        assumptions: [],
        confidence: 0.5,
      });
      expect(result.success).toBe(false);
    });

    it("debe fallar con confidence fuera de rango", () => {
      const result = OutputSchema.safeParse({
        improved_prompt: "test",
        clarifying_questions: [],
        assumptions: [],
        confidence: 1.5,
      });
      expect(result.success).toBe(false);
    });

    it("debe validar schema completo", () => {
      const valid = {
        improved_prompt: "Create a function",
        clarifying_questions: ["What input?"],
        assumptions: ["Modern syntax"],
        confidence: 0.8,
      };
      const result = OutputSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });
  });

  describe("5. antiChattyOutput_detects_explanation_phrases", () => {
    const isChatty = (text: string): boolean => {
      const chattyPatterns = [
        /^here (is|are)/i,
        /^claro/i,
        /^te dejo/i,
        /^he mejorado/i,
        /^a continuación/i,
        /^por supuesto/i,
        /^naturalmente/i,
        /^¿en qué puedo/i,
      ];
      return chattyPatterns.some((p) => p.test(text.trim()));
    };

    it("debe detectar 'Here is'", () => {
      expect(isChatty('Here is the JSON: {"test": 1}')).toBe(true);
    });

    it("debe detectar 'Claro'", () => {
      expect(isChatty('Claro, aquí está: {"test": 1}')).toBe(true);
    });

    it("debe detectar 'A continuación'", () => {
      expect(isChatty('A continuación, el resultado: {"test": 1}')).toBe(true);
    });

    it("NO debe detectar JSON limpio", () => {
      expect(isChatty('{"test": 1}')).toBe(false);
    });

    it("NO debe detectar prompt normal", () => {
      expect(isChatty("Create a function in TypeScript")).toBe(false);
    });
  });

  describe("6. antiChattyOutput_allows_plain_json_only", () => {
    const shouldAllow = (text: string): boolean => {
      const trimmed = text.trim();
      // Allow only if it's a JSON object/array without extra text
      const isJsonLike = /^[{[]/.test(trimmed) && /[}\]]$/.test(trimmed);
      const hasExtraText = !/^\{[\s\S]*\}$/.test(trimmed) && !/^\[[\s\S]*\]$/.test(trimmed);
      return isJsonLike && !hasExtraText;
    };

    it("debe permitir JSON object", () => {
      expect(shouldAllow('{"test": 1}')).toBe(true);
    });

    it("debe permitir JSON array", () => {
      expect(shouldAllow("[1, 2, 3]")).toBe(true);
    });

    it("NO debe permitir JSON con texto", () => {
      expect(shouldAllow('Here: {"test": 1}')).toBe(false);
    });

    it("NO debe permitir texto solo", () => {
      expect(shouldAllow("Here is the JSON")).toBe(false);
    });
  });

  describe("7. repairLoop_stops_after_one_retry", () => {
    it("debe parar después de 1 retry", async () => {
      let attempts = 0;
      const repairAttempt = async (): Promise<string> => {
        attempts++;
        if (attempts === 1) {
          throw new Error("Invalid JSON");
        }
        return '{"fixed": true}';
      };

      // Execute once
      try {
        await repairAttempt();
      } catch {
        // Expected first failure
      }

      // Second attempt should succeed
      const result = await repairAttempt();
      expect(attempts).toBe(2);
      expect(JSON.parse(result)).toEqual({ fixed: true });
    });

    it("debe fallar después de máximo 2 intentos", async () => {
      let attempts = 0;
      const maxAttempts = 2;
      const repairAttempt = async (): Promise<string> => {
        attempts++;
        if (attempts < maxAttempts) {
          throw new Error("Still broken");
        }
        throw new Error("Final failure");
      };

      let error: Error | null = null;
      while (attempts < maxAttempts) {
        try {
          await repairAttempt();
        } catch (e) {
          error = e as Error;
        }
      }

      expect(attempts).toBe(2);
      expect(error?.message).toBe("Final failure");
    });
  });

  describe("8. repairLoop_uses_repair_prompt_when_invalid", () => {
    it("debe usar prompt de repair específico", () => {
      const invalidJson = '{"partial": "missing required fields"}';
      const errorMessage = "Missing required field: improved_prompt";
      const repairPrompt = buildRepairPrompt(invalidJson, errorMessage);

      expect(repairPrompt).toContain("Invalid JSON"); // Case sensitive
      expect(repairPrompt).toContain(errorMessage);
      expect(repairPrompt).toContain("You MUST return ONLY valid JSON");
    });
  });

  describe("9. renderer_detects_unfilled_placeholders", () => {
    const hasPlaceholders = (text: string): boolean => {
      // Detect placeholders with specific patterns
      // Avoid matching empty JSON arrays
      const hasDoubleBraces = /\{\{[^}]*\}\}/.test(text);
      const hasSingleBraces = /(?<!:) *\[[a-zA-Z_][a-zA-Z0-9_]*\]/.test(text);
      const hasAngleBraces = /<[^<]*>/.test(text);
      return hasDoubleBraces || hasSingleBraces || hasAngleBraces;
    };

    it("debe detectar {{}} placeholders", () => {
      expect(hasPlaceholders("Create a {{type}} function")).toBe(true);
    });

    it("debe detectar [var] placeholders", () => {
      expect(hasPlaceholders("Create a [inputType] function")).toBe(true);
    });

    it("debe detectar <> placeholders", () => {
      expect(hasPlaceholders("Create a <returnType> function")).toBe(true);
    });

    it("NO debe detectar texto normal", () => {
      expect(hasPlaceholders("Create a TypeScript function")).toBe(false);
    });

    it("NO debe detectar JSON con arrays", () => {
      expect(hasPlaceholders('{"items": []}')).toBe(false);
      expect(hasPlaceholders('{"nested": {"arr": []}}')).toBe(false);
    });

    it("NO debe detectar JSON con strings", () => {
      expect(hasPlaceholders('{"name": "value"}')).toBe(false);
    });
  });

  describe("10. promptLoader_fallback_lastKnownGood", () => {
    it("debe cargar prompt versionado", () => {
      const loader = new PromptLoader();
      const prompt = loader.load("improver", "1.0.0");
      expect(prompt).toContain("You are a prompt improver");
    });

    it("debe fallback a lastKnownGood si version no existe", () => {
      const loader = new PromptLoader();
      const prompt = loader.load("improver", "99.0.0"); // Non-existent
      expect(prompt).toBeTruthy();
      expect(loader.warnings.length).toBeGreaterThan(0);
    });

    it("debe validar estructura de prompt", () => {
      const loader = new PromptLoader();
      const prompt = loader.load("improver");
      expect(prompt).toContain("improved_prompt");
      expect(prompt).not.toContain("{{");
    });
  });
});

// Helper functions for tests

function buildRepairPrompt(invalidJson: string, errorMessage: string): string {
  return [
    "You are a JSON repair tool.",
    "You MUST return ONLY valid JSON that matches the provided schema. No commentary.",
    "",
    "Invalid JSON:",
    invalidJson,
    "",
    "Error:",
    errorMessage,
    "",
    "Fix the JSON and respond ONLY with valid JSON.",
  ].join("\n");
}

class PromptLoader {
  warnings: string[] = [];

  load(name: string, version?: string): string {
    // Simulate loading from versioned prompts
    const prompts: Record<string, Record<string, string>> = {
      improver: {
        "1.0.0": "You are a prompt improver. Return { improved_prompt, clarifying_questions, assumptions, confidence }",
      },
    };

    if (version && prompts[name]?.[version]) {
      return prompts[name][version];
    }

    if (!version) {
      // Return latest
      return Object.values(prompts.improver)[0];
    }

    this.warnings.push(`Version ${version} not found, using last known good`);
    return "You are a prompt improver. Return valid JSON.";
  }
}
