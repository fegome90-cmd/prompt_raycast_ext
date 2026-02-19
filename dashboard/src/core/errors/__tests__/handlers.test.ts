// dashboard/src/core/errors/__tests__/handlers.test.ts
import { describe, it, expect } from "vitest";
import { handleBackendError } from "../handlers";

/**
 * Tests for handleBackendError React component.
 * Since this function returns JSX, we verify it doesn't throw and returns defined values.
 * Detailed error classification logic is tested in buildErrorHint tests.
 */
describe("handleBackendError", () => {
  describe("AbortError (timeout)", () => {
    it("handles AbortError without throwing", () => {
      const error = new Error("Request aborted");
      error.name = "AbortError";
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("Connection errors", () => {
    it("handles ECONNREFUSED without throwing", () => {
      const error = new TypeError("fetch failed: ECONNREFUSED ::1:8000");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles 'fetch failed' errors without throwing", () => {
      const error = new TypeError("fetch failed");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles TypeError with fetch in message without throwing", () => {
      const error = new TypeError("network fetch error occurred");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("Network errors", () => {
    it("handles ENOTFOUND without throwing", () => {
      const error = new Error("getaddrinfo ENOTFOUND localhost");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles ERR_CONNECTION without throwing", () => {
      const error = new Error("ERR_CONNECTION_REFUSED");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("HTTP errors", () => {
    it("handles 504 Gateway Timeout without throwing", () => {
      const error = new Error("DSPy backend error: 504");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles 400 Bad Request without throwing", () => {
      const error = new Error("DSPy backend error: 400 - Invalid prompt");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("Unknown errors", () => {
    it("handles unknown Error types without throwing", () => {
      const error = new Error("Something unexpected");
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles non-Error objects without throwing", () => {
      expect(() => handleBackendError("string error")).not.toThrow();
      const result = handleBackendError("string error");
      expect(result).toBeDefined();
    });

    it("handles errors with cause property without throwing", () => {
      const error = new Error("Main error");
      (error as { cause: unknown }).cause = "Root cause details";
      expect(() => handleBackendError(error)).not.toThrow();
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });
});
