import { beforeEach, describe, expect, it, vi } from "vitest";
import { improvePromptWithHybrid, ImprovePromptError } from "../improvePrompt";
import * as ollamaChatModule from "../ollamaChat";

vi.mock("../ollamaChat", () => ({
  callOllamaChat: vi.fn(),
}));

const mockCallOllamaChat = ollamaChatModule.callOllamaChat as unknown as ReturnType<typeof vi.fn>;

describe("dspy hybrid config", () => {
  beforeEach(() => {
    mockCallOllamaChat.mockReset();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("uses dspyBaseUrl when provided", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "healthy", provider: "ollama", model: "x", dspy_configured: true }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ improved_prompt: "ok", role: "r", directive: "d", framework: "f", guardrails: [] }),
      });

    const result = await improvePromptWithHybrid({
      rawInput: "x",
      preset: "default",
      options: {
        baseUrl: "http://localhost:11434",
        model: "x",
        timeoutMs: 30000,
        dspyBaseUrl: "http://localhost:8000",
      },
    });

    expect(result._metadata?.backend).toBe("dspy");
    expect(mockCallOllamaChat).not.toHaveBeenCalled();
  });

  it("falls back to Ollama when DSPy health check fails", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce({ ok: false, status: 503, statusText: "down", json: async () => ({}) });

    mockCallOllamaChat.mockResolvedValueOnce(
      JSON.stringify({
        improved_prompt: "fallback",
        clarifying_questions: [],
        assumptions: [],
        confidence: 0.7,
      }),
    );

    const result = await improvePromptWithHybrid({
      rawInput: "x",
      preset: "default",
      options: {
        baseUrl: "http://localhost:11434",
        model: "x",
        timeoutMs: 30000,
        dspyBaseUrl: "http://localhost:8000",
      },
    });

    expect(result._metadata?.backend).toBe("ollama");
    expect(mockCallOllamaChat).toHaveBeenCalledTimes(1);
  });

  it("throws when DSPy fails and fallback disabled", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce({ ok: false, status: 503, statusText: "down", json: async () => ({}) });

    await expect(
      improvePromptWithHybrid({
        rawInput: "x",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "x",
          timeoutMs: 30000,
          dspyBaseUrl: "http://localhost:8000",
        },
        enableDSPyFallback: false,
      }),
    ).rejects.toBeInstanceOf(ImprovePromptError);

    expect(mockCallOllamaChat).not.toHaveBeenCalled();
  });
});
