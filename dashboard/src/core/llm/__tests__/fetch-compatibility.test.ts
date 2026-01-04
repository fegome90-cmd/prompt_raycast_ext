/**
 * Test native fetch availability in Raycast environment
 * Validates that Node 18+ native fetch works as expected
 */

describe("Native Fetch Compatibility", () => {
  test("fetch is available globally", () => {
    // Verify fetch exists
    expect(typeof fetch).toBe("function");
  });

  test("AbortController is available", () => {
    // Verify AbortController exists (used for timeouts)
    expect(typeof AbortController).toBe("function");
    expect(typeof AbortSignal).toBe("function");
  });

  test("fetch can make GET request", async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch("http://localhost:11434/api/version", {
        method: "GET",
        signal: controller.signal,
      });

      clearTimeout(timeout);

      // Verify response structure matches node-fetch
      expect(response).toHaveProperty("ok");
      expect(response).toHaveProperty("status");
      expect(response).toHaveProperty("json");
      expect(typeof response.json).toBe("function");
    } catch (error) {
      clearTimeout(timeout);
      // If Ollama not running, that's OK for this test
      if ((error as Error).name === "AbortError") {
        console.warn("Ollama not running, skipping request test");
        return;
      }
      throw error;
    }
  });

  test("fetch can make POST request with JSON", async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch("http://localhost:8000/api/v1/improve-prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ idea: "test", context: "" }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      expect(response).toHaveProperty("ok");
      expect(response).toHaveProperty("json");
    } catch (error) {
      clearTimeout(timeout);
      if ((error as Error).name === "AbortError") {
        console.warn("DSPy backend not running, skipping request test");
        return;
      }
      throw error;
    }
  });
});
