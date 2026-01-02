import { beforeEach, describe, expect, it, vi } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
const mocks = vi.hoisted(() => ({
  hybrid: vi.fn(),
  ollama: vi.fn(),
  healthCheck: vi.fn(),
}));

vi.mock("../../src/core/llm/improvePrompt", () => ({
  improvePromptWithOllama: mocks.ollama,
  improvePromptWithHybrid: mocks.hybrid,
}));
vi.mock("../../src/core/llm/ollamaClient", () => ({
  ollamaHealthCheck: mocks.healthCheck,
}));
let EvaluatorClass: typeof import("../evaluator").Evaluator;

async function writeDataset(): Promise<string> {
  const dir = await fs.mkdtemp(join(tmpdir(), "eval-backend-"));
  const path = join(dir, "cases.jsonl");
  await fs.writeFile(
    path,
    JSON.stringify({
      id: "amb-001",
      input: "desing adr process",
      asserts: { minFinalPromptLength: 5, maxQuestions: 3, minConfidence: 0.1 },
    }) + "\n",
  );
  return path;
}

const mockResult = {
  improved_prompt: "Role: X\nDirective: Y\nFramework: Z\nGuardrails: - A",
  clarifying_questions: [],
  assumptions: [],
  confidence: 0.8,
  _metadata: { backend: "dspy", usedExtraction: false, usedRepair: false, attempt: 1, latencyMs: 1 },
};

describe("evaluator backend selection", () => {
  beforeEach(async () => {
    mocks.hybrid.mockReset();
    mocks.ollama.mockReset();
    mocks.healthCheck.mockReset();
    mocks.hybrid.mockResolvedValue(mockResult);
    mocks.ollama.mockResolvedValue(mockResult);
    mocks.healthCheck.mockResolvedValue({ ok: true });
    vi.resetModules();
    ({ Evaluator: EvaluatorClass } = await import("../evaluator"));
  });

  it("uses improvePromptWithHybrid when backend=dspy", async () => {
    const datasetPath = await writeDataset();
    const evaluator = new EvaluatorClass();

    await evaluator.run({
      datasetPath,
      backend: "dspy",
      repeat: 1,
      config: { baseUrl: "http://localhost:11434", dspyBaseUrl: "http://localhost:8000" },
    });

    expect(mocks.healthCheck).not.toHaveBeenCalled();
    expect(mocks.hybrid).toHaveBeenCalledTimes(1);
    expect(mocks.ollama).not.toHaveBeenCalled();
    expect(mocks.hybrid.mock.calls[0][0]).toMatchObject({ enableDSPyFallback: false });
  });
});
