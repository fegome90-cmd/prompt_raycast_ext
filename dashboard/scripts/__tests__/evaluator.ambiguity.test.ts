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
  improvePromptWithHybrid: mocks.hybrid,
  improvePromptWithOllama: mocks.ollama,
}));
vi.mock("../../src/core/llm/ollamaClient", () => ({
  ollamaHealthCheck: mocks.healthCheck,
}));

let EvaluatorClass: typeof import("../evaluator").Evaluator;

async function writeDataset(): Promise<string> {
  const dir = await fs.mkdtemp(join(tmpdir(), "eval-amb-"));
  const path = join(dir, "cases.jsonl");
  await fs.writeFile(
    path,
    JSON.stringify({
      id: "amb-001",
      input: "desing adr process",
      tags: ["ambiguity"],
      asserts: { minFinalPromptLength: 5, maxQuestions: 3, minConfidence: 0.1 },
    }) + "\n",
  );
  return path;
}

const makeResult = (text: string) => ({
  improved_prompt: text,
  clarifying_questions: [],
  assumptions: [],
  confidence: 0.8,
});

describe("ambiguity metrics", () => {
  beforeEach(async () => {
    mocks.hybrid.mockReset();
    mocks.ollama.mockReset();
    mocks.healthCheck.mockReset();
    mocks.hybrid
      .mockResolvedValueOnce(makeResult("Alternative Dispute Resolution"))
      .mockResolvedValueOnce(makeResult("Adversarial Design Review"))
      .mockResolvedValueOnce(makeResult("Alternative Dispute Resolution"));
    mocks.healthCheck.mockResolvedValue({ ok: true });
    vi.resetModules();
    ({ Evaluator: EvaluatorClass } = await import("../evaluator"));
  });

  it("computes ambiguity spread and dominant sense", async () => {
    const datasetPath = await writeDataset();
    const evaluator = new EvaluatorClass();

    const metrics = await evaluator.run({
      datasetPath,
      backend: "dspy",
      repeat: 3,
      config: { baseUrl: "http://localhost:11434", dspyBaseUrl: "http://localhost:8000" },
    });

    expect(metrics.ambiguity).toMatchObject({
      totalAmbiguousCases: 1,
      ambiguitySpread: 1,
      dominantSenseRate: 1,
      stabilityScore: 2 / 3,
    });
  });
});
