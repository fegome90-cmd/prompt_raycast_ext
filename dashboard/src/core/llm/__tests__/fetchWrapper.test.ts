/**
 * Tests for fetch wrapper compatibility
 */

import { fetchWithTimeout } from "../fetchWrapper";

describe("fetchWrapper", () => {
  test("fetchWithTimeout works without timeout", async () => {
    const response = await fetchWithTimeout("http://localhost:11434/api/tags", {
      method: "GET",
    });

    expect(response).toHaveProperty("ok");
  });

  test("fetchWithTimeout aborts on timeout", async () => {
    await expect(
      fetchWithTimeout("http://localhost:1/nonexistent", {
        method: "GET",
        timeout: 100,
      })
    ).rejects.toThrow();
  }, 10000);

  test("fetchWithTimeout works with headers and body", async () => {
    const response = await fetchWithTimeout("http://localhost:8000/health", {
      method: "GET",
      headers: { "Accept": "application/json" },
      timeout: 5000,
    });

    expect(response.ok).toBe(true);
  });
});
