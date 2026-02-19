import { describe, it, expect } from "vitest";
import { buildErrorHint } from "../core/errors/hints";

describe("buildErrorHint", () => {
  describe("timeout errors", () => {
    it("returns timeout hint for 'timed out' message", () => {
      expect(buildErrorHint(new Error("Request timed out"))).toBe(
        "try increasing timeout (ms)"
      );
    });

    it("returns timeout hint for case-insensitive match", () => {
      expect(buildErrorHint(new Error("TIMED OUT after 30s"))).toBe(
        "try increasing timeout (ms)"
      );
    });
  });

  describe("connection errors", () => {
    it("returns DSPy hint when mode is 'dspy'", () => {
      expect(buildErrorHint(new Error("ECONNREFUSED"), "dspy")).toBe(
        "check the DSPy backend is running"
      );
    });

    it("returns NLaC hint when mode is 'nlac'", () => {
      expect(buildErrorHint(new Error("connect failed"), "nlac")).toBe(
        "check the NLaC backend is running with 'make dev'"
      );
    });

    it("returns Ollama hint when mode is undefined", () => {
      expect(buildErrorHint(new Error("not reachable"))).toBe(
        "check `ollama serve` is running"
      );
    });
  });

  describe("model not found errors", () => {
    it("returns pull hint for model not found", () => {
      expect(buildErrorHint(new Error("model llama3 not found"))).toBe(
        "Pull the model first: `ollama pull <model>`"
      );
    });
  });

  describe("unknown errors", () => {
    it("returns null for unknown error types", () => {
      expect(buildErrorHint(new Error("something weird happened"))).toBeNull();
    });

    it("handles string errors", () => {
      expect(buildErrorHint("random string")).toBeNull();
    });
  });
});
