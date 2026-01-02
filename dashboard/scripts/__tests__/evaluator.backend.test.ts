import { beforeEach, describe, expect, it, vi } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import * as improveModule from "../../src/core/llm/improvePrompt";
import * as ollamaModule from "../../src/core/llm/ollamaClient";

vi.mock("../../src/core/llm/improvePrompt", () => ({
  improvePromptWithOllama: vi.fn(),
  improvePromptWithHybrid: vi.fn(),
}));
vi.mock("../../src/core/llm/ollamaClient", () => ({
  ollamaHealthCheck: vi.fn(),
}));

const mockHybrid = improveModule.improvePromptWithHybrid as unknown as ReturnType<typeof vi.fn>;
const mockOllama = improveModule.improvePromptWithOllama as unknown as ReturnType<typeof vi.fn>;
const mockHealthCheck = ollamaModule.ollamaHealthCheck as unknown as ReturnType<typeof vi.fn>;
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
    mockHybrid.mockReset();
    mockOllama.mockReset();
    mockHealthCheck.mockReset();
    mockHybrid.mockResolvedValue(mockResult);
    mockOllama.mockResolvedValue(mockResult);
    mockHealthCheck.mockResolvedValue({ ok: true });
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

    expect(mockHybrid).toHaveBeenCalledTimes(1);
    expect(mockOllama).not.toHaveBeenCalled();
    expect(mockHybrid.mock.calls[0][0]).toMatchObject({ enableDSPyFallback: false });
  });
});
