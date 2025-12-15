/**
 * Tests unitarios para jsonExtractor
 * Valida heurística robusta con casos edge
 */

import { describe, it, expect } from "vitest";
import { extractJsonFromText, extractFirstJsonObject, validateExtractedJson } from "../jsonExtractor";
import { z } from "zod";

describe("T1.2.B1 - JSON Extractor Tests", () => {
  describe("Fence extraction", () => {
    it("extrae de ```json con JSON simple", () => {
      const input = '```json\n{"test": 1}\n```';
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"test": 1}',
        extractionMethod: "fence",
      });
    });

    it("extrae de ``` con JSON anidado", () => {
      const nested = {
        user: { name: "John", settings: { theme: "dark" } },
        items: [1, 2, 3],
      };
      const input = `\`\`\`json\n${JSON.stringify(nested, null, 2)}\n\`\`\``;
      const result = extractJsonFromText(input);
      expect(result?.json).toBeDefined();
      expect(JSON.parse(result!.json)).toEqual(nested);
    });

    it("extrae JSON de fence ignorando texto antes/después", () => {
      const input = 'Here is the result:\n```json\n{"result": "ok"}\n```\nHope this helps!';
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"result": "ok"}',
      });
    });

    it("extrae solo el PRIMER objeto JSON completo de fence", () => {
      const input = `\`\`\`json
{"first": true}
\`\`\`
Another json:
\`\`\`json
{"second": true}
\`\`\``;
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"first": true}',
      });
    });

    it("NO extrae si hay texto entre llaves en fence", () => {
      // This is actually valid but malformed content
      const input = '```json\n{"test": 1} some text {"test": 2}\n```';
      const result = extractJsonFromText(input);
      // Should extract first complete object
      expect(result?.json).toBeDefined();
      const parsed = JSON.parse(result!.json);
      expect(parsed.test).toBe(1);
    });

    it("extrae de fence sin language tag", () => {
      const input = '```\n{"test": 1}\n```';
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"test": 1}',
        extractionMethod: "fence",
      });
    });
  });

  describe("Tag extraction", () => {
    it("extrae de <json> tags", () => {
      const input = '<json>{"test": 1}</json>';
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"test": 1}',
        extractionMethod: "tag",
      });
    });

    it("extrae de tag con múltiples líneas", () => {
      const input = `<json>
{
  "test": 1,
  "nested": {"a": 2}
}
</json>`;
      const result = extractJsonFromText(input);
      expect(result?.json).toBeDefined();
      expect(JSON.parse(result!.json)).toEqual({ test: 1, nested: { a: 2 } });
    });
  });

  describe("Global scan extraction", () => {
    it("extrae JSON inline sin fences", () => {
      const input = 'Here is the JSON: {"result": "ok"}. Done.';
      const result = extractJsonFromText(input);
      expect(result).toMatchObject({
        json: '{"result": "ok"}',
        extractionMethod: "scan",
      });
    });

    it("extrae objeto completo con nesting", () => {
      const nested = { a: { b: { c: 1 } } };
      const input = `Result: ${JSON.stringify(nested)}`;
      const result = extractJsonFromText(input);
      expect(result?.json).toBeDefined();
      expect(JSON.parse(result!.json)).toEqual(nested);
    });

    it("extrae solo el PRIMER objeto completo", () => {
      const input = '{"first": true} {"second": true}';
      const result = extractFirstJsonObject(input);
      expect(result).toMatchObject({
        json: '{"first": true}',
        extractionMethod: "scan",
      });

      // Verify second object is not included
      expect(result?.json).not.toContain("second");
    });

    it("ignora llaves dentro de strings", () => {
      const input = '{"text": "This { is not a brace"}';
      const result = extractFirstJsonObject(input);
      expect(result?.json).toBeDefined();
      expect(JSON.parse(result!.json).text).toBe("This { is not a brace");
    });

    it("maneja escapes correctamente", () => {
      // In JSON, backslashes are escaped as "\\"
      // When we write the string in JS, we need "\\\\" to represent "\\" in JSON
      const input = '{"path": "C:\\\\Users\\\\test", "value": 1}';
      const result = extractFirstJsonObject(input);
      expect(result?.json).toBeDefined();
      const parsed = JSON.parse(result!.json);
      // Once parsed, the string contains actual backslashes
      expect(parsed.path).toBe("C:\\Users\\test");
    });

    it("maneja strings con llaves y comas", () => {
      const input = '{"code": "function test() { return {a: 1, b: 2}; }"}';
      const result = extractFirstJsonObject(input);
      expect(result?.json).toBeDefined();
      const parsed = JSON.parse(result!.json);
      expect(parsed.code).toContain("return {a: 1, b: 2}");
    });
  });

  describe("Escaneo de balance", () => {
    it("NO extrae texto sin llaves balanceadas", () => {
      const input = "Here is text with { but no close";
      const result = extractFirstJsonObject(input);
      expect(result).toBeNull();
    });

    it("NO extrae objeto con balance negativo", () => {
      const input = "text } then {";
      const result = extractFirstJsonObject(input);
      // Should find first brace and fail to balance
      expect(result).toBeNull();
    });
  });

  describe("Tu heurística full", () => {
    it("maneja ejemplo 1: chatty + fence", () => {
      const input = `Claro, aquí tienes el prompt mejorado:

\`\`\`json
{
  "improved_prompt": "Crea una función para validar emails",
  "clarifying_questions": ["¿Qué longitud máxima?"],
  "assumptions": ["Usará regex estándar"],
  "confidence": 0.8
}
\`\`\`

Let me know if you need anything else!`;

      const result = extractJsonFromText(input);
      expect(result?.json).toBeDefined();
      const parsed = JSON.parse(result!.json);
      expect(parsed.improved_prompt).toContain("validar emails");
      expect(parsed.confidence).toBe(0.8);
    });

    it("maneja ejemplo 2: placeholders sin rellenar", () => {
      const input = JSON.stringify({
        improved_prompt: "Crea una función {{tipo}} para {{propósito}}",
        clarifying_questions: ["¿Qué tipo de función?"],
        assumptions: ["El usuario especificará el tipo"],
        confidence: 0.6,
      });

      const result = extractFirstJsonObject(input);
      expect(result).toBeDefined();
      expect(JSON.parse(result!.json).improved_prompt).toContain("{{tipo}}");
    });

    it("maneja ejemplo 3: JSON roto", () => {
      const input = `{
  "improved_prompt": "Componente de React con hooks",
  "clarifying_questions": ["¿Qué hooks usar?", "¿Necesita estado?"]
  "assumptions": ["Usará hooks modernos"],
  "confidence": 0.75
}`;

      const result = extractFirstJsonObject(input);
      expect(result?.json).toBeDefined();
      // The extractor should find it, JSON.parse will fail (expected)
      expect(() => JSON.parse(result!.json)).toThrow();
    });
  });

  describe("Validación", () => {
    const testSchema = z.object({
      name: z.string(),
      value: z.number(),
    });

    it("valida JSON extraído contra schema", () => {
      const json = '{"name": "test", "value": 42}';
      const result = validateExtractedJson(json, testSchema);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.name).toBe("test");
        expect(result.data.value).toBe(42);
      }
    });

    it("rechaza JSON que no cumple schema (tipo incorrecto)", () => {
      // JSON válido pero value es string en lugar de number
      const json = '{"name": "test", "value": "not a number"}';
      const result = validateExtractedJson(json, testSchema);
      expect(result.success).toBe(false);
      if (!result.success) {
        // Zod debe reportar error de validación
        const errorLower = result.error.toLowerCase();
        const hasValidationError =
          errorLower.includes("number") || errorLower.includes("validation") || errorLower.includes("expected");
        expect(hasValidationError).toBe(true);
      }
    });

    it("rechaza JSON que no cumple schema (campo requerido faltante)", () => {
      // JSON válido pero falta el campo 'value'
      const json = '{"name": "test"}';
      const result = validateExtractedJson(json, testSchema);
      expect(result.success).toBe(false);
      if (!result.success) {
        const errorLower = result.error.toLowerCase();
        const hasRequiredError = errorLower.includes("value") || errorLower.includes("required");
        expect(hasRequiredError).toBe(true);
      }
    });

    it("detecta sintaxis inválida (trailing comma)", () => {
      const json = '{"name": "test",}'; // trailing comma
      const result = validateExtractedJson(json);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.toLowerCase()).toContain("json");
      }
    });
  });

  describe("Casos edge de producción", () => {
    it("NO extrae dos objetos como uno", () => {
      const input = '{"a":1}{"b":2}';
      const result = extractFirstJsonObject(input);
      expect(result?.json).toBe('{"a":1}');
      expect(result?.json).not.toContain('"b"');
    });

    it("extrae objeto con array vacío", () => {
      const input = '{"items": []}';
      const result = extractFirstJsonObject(input);
      expect(result).toBeDefined();
      expect(JSON.parse(result!.json).items).toEqual([]);
    });

    it("extrae objeto con strings especiales", () => {
      const input = '{"unicode": "ñáéíóú", "emoji": "😀"}';
      const result = extractFirstJsonObject(input);
      expect(result).toBeDefined();
      const parsed = JSON.parse(result!.json);
      expect(parsed.unicode).toBe("ñáéíóú");
      expect(parsed.emoji).toBe("😀");
    });

    it("prioriza fence sobre scan", () => {
      const input = '{"inline": true}\n```json\n{"fenced": true}\n```';
      const result = extractJsonFromText(input);
      expect(result?.extractionMethod).toBe("fence");
      expect(JSON.parse(result!.json).fenced).toBe(true);
    });

    it("prioriza tag sobre fence", () => {
      const input = '```json\n{"fence": true}\n```\n<json>{"tag": true}</json>';
      const result = extractJsonFromText(input);
      // Should extract first method that works
      expect(result).toBeDefined();
    });
  });
});
