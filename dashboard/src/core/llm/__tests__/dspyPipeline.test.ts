import { describe, expect, it, vi } from "vitest";
import { improvePromptWithDSPy } from "../dspyPromptImprover";

const fetchMock = vi.fn();
global.fetch = fetchMock as any;

describe("DSPy pipeline", () => {
  it("uses configured DSPy baseUrl when provided", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ status: "healthy", dspy_configured: true }) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ improved_prompt: "ok", role: "r", directive: "d", framework: "f", guardrails: [] }) });

    const result = await improvePromptWithDSPy("idea", "default", "ctx", {
      baseUrl: "http://localhost:8001",
      timeoutMs: 1000,
    });

    expect(fetchMock.mock.calls[0][0]).toContain("http://localhost:8001/health");
    expect(result.improved_prompt).toBe("ok");
  });
});