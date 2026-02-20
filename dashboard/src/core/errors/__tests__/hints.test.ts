// dashboard/src/core/errors/__tests__/hints.test.ts
import { describe, it, expect } from "vitest";
import { buildErrorHint } from "../hints";

describe("buildErrorHint", () => {
  describe("timeout errors", () => {
    it("returns hint for 'timed out' in message", () => {
      expect(buildErrorHint(new Error("Request timed out"))).toBe("try increasing timeout (ms)");
    });

    it("is case-insensitive", () => {
      expect(buildErrorHint(new Error("TIMED OUT"))).toBe("try increasing timeout (ms)");
      expect(buildErrorHint(new Error("Request Timed Out after 30s"))).toBe("try increasing timeout (ms)");
    });
  });

  describe("connection errors", () => {
    it("returns nlac hint when mode='nlac'", () => {
      expect(buildErrorHint(new Error("connect failed"), "nlac")).toBe(
        "check the NLaC backend is running with 'make dev'",
      );
    });

    it("returns dspy hint when mode='dspy'", () => {
      expect(buildErrorHint(new Error("ECONNREFUSED"), "dspy")).toBe("check the DSPy backend is running");
    });

    it("returns ollama hint when mode is undefined", () => {
      expect(buildErrorHint(new Error("not reachable"))).toBe("check `ollama serve` is running");
    });

    it("matches 'connect' keyword", () => {
      expect(buildErrorHint(new Error("could not connect to server"), "dspy")).toBe(
        "check the DSPy backend is running",
      );
    });
  });

  describe("model not found errors", () => {
    it("returns pull hint for model not found", () => {
      expect(buildErrorHint(new Error("model llama3 not found"))).toBe("Pull the model first: `ollama pull <model>`");
    });

    it("matches case-insensitive", () => {
      expect(buildErrorHint(new Error("Model not found: llama3"))).toBe("Pull the model first: `ollama pull <model>`");
    });
  });

  describe("unknown errors", () => {
    it("returns null for unrecognized errors", () => {
      expect(buildErrorHint(new Error("random error"))).toBeNull();
    });

    it("handles non-Error objects", () => {
      expect(buildErrorHint("string error")).toBeNull();
    });

    it("handles null input gracefully", () => {
      expect(buildErrorHint(null)).toBeNull();
    });

    it("handles undefined input gracefully", () => {
      expect(buildErrorHint(undefined)).toBeNull();
    });
  });

  describe("schema and validation errors", () => {
    it("returns hint for schema errors", () => {
      expect(buildErrorHint(new Error("schema validation failed"))).toBe(
        "the backend returned an unexpected response format - try again or check backend logs",
      );
    });

    it("returns hint for validation errors", () => {
      expect(buildErrorHint(new Error("validation error"))).toBe(
        "the backend returned an unexpected response format - try again or check backend logs",
      );
    });
  });

  describe("JSON and parse errors", () => {
    it("returns hint for JSON errors", () => {
      expect(buildErrorHint(new Error("JSON parse error"))).toBe(
        "the response could not be parsed - try a different model or check backend logs",
      );
    });

    it("returns hint for parse errors", () => {
      expect(buildErrorHint(new Error("failed to parse response"))).toBe(
        "the response could not be parsed - try a different model or check backend logs",
      );
    });
  });

  describe("authentication errors", () => {
    it("returns hint for 401 errors", () => {
      expect(buildErrorHint(new Error("401 Unauthorized"))).toBe(
        "check your API key configuration in environment variables",
      );
    });

    it("returns hint for unauthorized errors", () => {
      expect(buildErrorHint(new Error("unauthorized access"))).toBe(
        "check your API key configuration in environment variables",
      );
    });

    it("returns hint for API key errors", () => {
      expect(buildErrorHint(new Error("invalid api key"))).toBe(
        "check your API key configuration in environment variables",
      );
    });
  });

  describe("rate limit errors", () => {
    it("returns hint for 429 errors", () => {
      expect(buildErrorHint(new Error("429 Too Many Requests"))).toBe(
        "too many requests - wait a moment and try again",
      );
    });

    it("returns hint for rate limit errors", () => {
      expect(buildErrorHint(new Error("rate limit exceeded"))).toBe("too many requests - wait a moment and try again");
    });
  });
});
