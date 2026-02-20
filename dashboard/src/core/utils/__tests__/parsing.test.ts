// dashboard/src/core/utils/__tests__/parsing.test.ts
import { describe, it, expect } from "vitest";
import { parseTimeoutMs, shouldTryFallback, getPlaceholder } from "../parsing";

describe("parseTimeoutMs", () => {
  it("parses valid numeric string", () => {
    expect(parseTimeoutMs("5000", 1000)).toBe(5000);
  });

  it("trims whitespace", () => {
    expect(parseTimeoutMs("  3000  ", 1000)).toBe(3000);
  });

  it("returns fallback for undefined", () => {
    expect(parseTimeoutMs(undefined, 1000)).toBe(1000);
  });

  it("returns fallback for empty string", () => {
    expect(parseTimeoutMs("", 1000)).toBe(1000);
  });

  it("returns fallback for non-numeric", () => {
    expect(parseTimeoutMs("abc", 1000)).toBe(1000);
  });

  it("returns fallback for zero", () => {
    expect(parseTimeoutMs("0", 1000)).toBe(1000);
  });

  it("returns fallback for negative", () => {
    expect(parseTimeoutMs("-5", 1000)).toBe(1000);
  });
});

describe("shouldTryFallback", () => {
  it("returns true for 'model not found'", () => {
    expect(shouldTryFallback(new Error("model llama not found"))).toBe(true);
  });

  it("returns true for 'pull' errors", () => {
    expect(shouldTryFallback(new Error("please pull model"))).toBe(true);
  });

  it("returns true for 404 errors", () => {
    expect(shouldTryFallback(new Error("got 404"))).toBe(true);
  });

  it("returns true for ollama error with model", () => {
    expect(shouldTryFallback(new Error("ollama error: model not loaded"))).toBe(true);
  });

  it("returns true for non-JSON output", () => {
    expect(shouldTryFallback(new Error("non-json response"))).toBe(true);
  });

  it("returns true for validation errors", () => {
    expect(shouldTryFallback(new Error("validation failed"))).toBe(true);
  });

  it("returns true for zod errors", () => {
    expect(shouldTryFallback(new Error("zod parse error"))).toBe(true);
  });

  it("returns true for improved_prompt missing", () => {
    expect(shouldTryFallback(new Error("improved_prompt field missing"))).toBe(true);
  });

  it("returns false for network timeouts", () => {
    expect(shouldTryFallback(new Error("ETIMEDOUT"))).toBe(false);
  });

  it("handles non-Error input", () => {
    expect(shouldTryFallback("string error")).toBe(false);
  });
});

describe("getPlaceholder", () => {
  it("returns structured placeholder by default", () => {
    expect(getPlaceholder()).toContain("structure");
  });

  it("returns specific placeholder for specific preset", () => {
    expect(getPlaceholder("specific")).toContain("specific task");
  });
});
