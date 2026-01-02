# DSPy Variance Auditor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a DSPy-backed evaluation mode with repeatable runs and ambiguity metrics, using a hybrid dataset derived from `datasets/exports/ComponentCatalog.json` plus existing cases.

**Architecture:** Extend `dashboard/scripts/evaluator.ts` to support `backend=dspy` (parity with Raycast via `improvePromptWithHybrid` and `enableDSPyFallback: false`), add repeat runs, and compute ambiguity metrics via a heuristic acronym classifier. Generate a hybrid dataset (ambiguity cases + subset of existing cases + top component directives) using a new script, and document the new evaluator flags.

**Tech Stack:** TypeScript, Vitest, Node fs/path, Raycast LLM utilities.

---

### Task 1: Add DSPy backend option + repeat runs in evaluator

**Files:**
- Modify: `dashboard/scripts/evaluator.ts`
- Test: `dashboard/scripts/__tests__/evaluator.backend.test.ts`

**Step 1: Write the failing test** (REQUIRED SUB-SKILL: @superpowers:test-driven-development)

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { Evaluator } from "../evaluator";
import * as improveModule from "../../src/core/llm/improvePrompt";

vi.mock("../../src/core/llm/improvePrompt", () => ({
  improvePromptWithOllama: vi.fn(),
  improvePromptWithHybrid: vi.fn(),
}));

const mockHybrid = improveModule.improvePromptWithHybrid as unknown as ReturnType<typeof vi.fn>;
const mockOllama = improveModule.improvePromptWithOllama as unknown as ReturnType<typeof vi.fn>;

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
  beforeEach(() => {
    mockHybrid.mockReset();
    mockOllama.mockReset();
    mockHybrid.mockResolvedValue(mockResult);
    mockOllama.mockResolvedValue(mockResult);
  });

  it("uses improvePromptWithHybrid when backend=dspy", async () => {
    const datasetPath = await writeDataset();
    const evaluator = new Evaluator();

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
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- scripts/__tests__/evaluator.backend.test.ts`
Expected: FAIL (backend/repeat options not supported yet)

**Step 3: Write minimal implementation**

```ts
// evaluator.ts: add backend + repeat to EvalOptions
interface EvalOptions {
  datasetPath: string;
  outputPath?: string;
  backend?: "ollama" | "dspy";
  repeat?: number;
  config?: {
    baseUrl?: string;
    model?: string;
    fallbackModel?: string;
    timeoutMs?: number;
    dspyBaseUrl?: string;
    dspyTimeoutMs?: number;
  };
}

// evaluator.ts: import improvePromptWithHybrid
import { improvePromptWithHybrid, improvePromptWithOllama } from "../src/core/llm/improvePrompt";

// evaluator.ts: in runCase, loop repeat times and choose backend
const repeat = Math.max(1, options.repeat ?? 1);
for (let i = 0; i < repeat; i++) {
  const result = options.backend === "dspy"
    ? await improvePromptWithHybrid({
        rawInput: testCase.input,
        preset: "default",
        options: {
          baseUrl: options.config?.baseUrl || "http://localhost:11434",
          model: options.config?.model || "qwen3-coder:30b",
          timeoutMs: options.config?.timeoutMs || 30000,
          dspyBaseUrl: options.config?.dspyBaseUrl || "http://localhost:8000",
          dspyTimeoutMs: options.config?.dspyTimeoutMs,
        },
        enableDSPyFallback: false,
      })
    : await improvePromptWithOllama({
        rawInput: testCase.input,
        preset: "default",
        options: {
          baseUrl: options.config?.baseUrl || "http://localhost:11434",
          model: options.config?.model || "qwen3-coder:30b",
          timeoutMs: options.config?.timeoutMs || 30000,
        },
      });

  // Track each run in a new runs[] array (add to MetricsSchema later)
  runs.push({ caseId: testCase.id, run: i + 1, output: result.improved_prompt, backend: options.backend ?? "ollama" });
  // Existing metric checks should run per run (keep current behavior)
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- scripts/__tests__/evaluator.backend.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/scripts/evaluator.ts dashboard/scripts/__tests__/evaluator.backend.test.ts
git commit -m "feat: add dspy backend and repeat support to evaluator"
```

---

### Task 2: Add ambiguity classifier + variance metrics

**Files:**
- Modify: `dashboard/scripts/evaluator.ts`
- Test: `dashboard/scripts/__tests__/evaluator.ambiguity.test.ts`

**Step 1: Write the failing test** (REQUIRED SUB-SKILL: @superpowers:test-driven-development)

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { Evaluator } from "../evaluator";
import * as improveModule from "../../src/core/llm/improvePrompt";

vi.mock("../../src/core/llm/improvePrompt", () => ({
  improvePromptWithHybrid: vi.fn(),
  improvePromptWithOllama: vi.fn(),
}));

const mockHybrid = improveModule.improvePromptWithHybrid as unknown as ReturnType<typeof vi.fn>;

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
  beforeEach(() => {
    mockHybrid.mockReset();
    mockHybrid
      .mockResolvedValueOnce(makeResult("Alternative Dispute Resolution"))
      .mockResolvedValueOnce(makeResult("Adversarial Design Review"))
      .mockResolvedValueOnce(makeResult("Alternative Dispute Resolution"));
  });

  it("computes ambiguity spread and dominant sense", async () => {
    const datasetPath = await writeDataset();
    const evaluator = new Evaluator();

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
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- scripts/__tests__/evaluator.ambiguity.test.ts`
Expected: FAIL (metrics not present)

**Step 3: Write minimal implementation**

```ts
// evaluator.ts: extend TestCaseSchema
const TestCaseSchema = z.object({
  id: z.string(),
  input: z.string(),
  tags: z.array(z.string()).default([]),
  ambiguityHints: z.array(z.string()).default([]),
  asserts: z.object({ /* existing fields */ }),
});

// evaluator.ts: extend MetricsSchema
const MetricsSchema = z.object({
  // ...existing fields
  ambiguity: z.object({
    totalAmbiguousCases: z.number().default(0),
    ambiguitySpread: z.number().default(0),
    dominantSenseRate: z.number().default(0),
    stabilityScore: z.number().default(1),
  }).default({}),
});

// evaluator.ts: add classifier
const ACRONYM_SENSES: Record<string, { label: string; patterns: RegExp[] }[]> = {
  ADR: [
    { label: "alternative_dispute_resolution", patterns: [/alternative dispute resolution/i] },
    { label: "architecture_decision_record", patterns: [/architecture decision record/i] },
    { label: "adversarial_design_review", patterns: [/adversarial design review/i] },
  ],
};

function classifySense(output: string): string | null {
  for (const [acronym, senses] of Object.entries(ACRONYM_SENSES)) {
    for (const sense of senses) {
      if (sense.patterns.some((p) => p.test(output))) return `${acronym}:${sense.label}`;
    }
  }
  return null;
}

// evaluator.ts: after runs collected, compute ambiguity metrics for cases with tags.includes("ambiguity")
const ambiguousCases = cases.filter((c) => c.tags.includes("ambiguity"));
const ambiguityMetrics = computeAmbiguityMetrics(ambiguousCases, runs);

function computeAmbiguityMetrics(cases: TestCase[], runs: RunResult[]) {
  if (!cases.length) return { totalAmbiguousCases: 0, ambiguitySpread: 0, dominantSenseRate: 0, stabilityScore: 1 };
  let spread = 0;
  let dominant = 0;
  let stabilitySum = 0;

  for (const testCase of cases) {
    const outputs = runs.filter((r) => r.caseId === testCase.id).map((r) => r.output);
    const senses = outputs.map((o) => classifySense(o)).filter(Boolean) as string[];
    const counts = senses.reduce((acc, s) => ((acc[s] = (acc[s] || 0) + 1), acc), {} as Record<string, number>);
    const unique = Object.keys(counts).length;
    if (unique > 1) spread += 1;
    const total = senses.length || 1;
    const maxShare = Math.max(...Object.values(counts), 0) / total;
    if (maxShare >= 0.7) dominant += 1;
    stabilitySum += maxShare;
  }

  return {
    totalAmbiguousCases: cases.length,
    ambiguitySpread: spread / cases.length,
    dominantSenseRate: dominant / cases.length,
    stabilityScore: stabilitySum / cases.length,
  };
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- scripts/__tests__/evaluator.ambiguity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/scripts/evaluator.ts dashboard/scripts/__tests__/evaluator.ambiguity.test.ts
git commit -m "feat: add ambiguity variance metrics to evaluator"
```

---

### Task 3: Generate hybrid dataset (ambiguity + component directives + subset)

**Files:**
- Create: `dashboard/scripts/build-variance-datasets.ts`
- Create: `dashboard/testdata/ambiguity-cases.jsonl`
- Create: `dashboard/testdata/variance-hybrid.jsonl`

**Step 1: Write the failing test** (REQUIRED SUB-SKILL: @superpowers:test-driven-development)

```ts
import { describe, expect, it } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { buildDatasets } from "../build-variance-datasets";

it("writes ambiguity and hybrid datasets", async () => {
  const dir = await fs.mkdtemp(join(tmpdir(), "variance-ds-"));
  const ambiguityPath = join(dir, "ambiguity.jsonl");
  const hybridPath = join(dir, "hybrid.jsonl");

  await buildDatasets({
    componentCatalogPath: "datasets/exports/ComponentCatalog.json",
    baseCasesPath: "dashboard/testdata/cases.jsonl",
    ambiguityPath,
    hybridPath,
    maxComponents: 20,
  });

  const ambiguity = (await fs.readFile(ambiguityPath, "utf-8")).trim().split("\n");
  const hybrid = (await fs.readFile(hybridPath, "utf-8")).trim().split("\n");

  expect(ambiguity.length).toBeGreaterThan(0);
  expect(hybrid.length).toBeGreaterThan(ambiguity.length);
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- scripts/__tests__/build-variance-datasets.test.ts`
Expected: FAIL (script not implemented)

**Step 3: Write minimal implementation**

```ts
// build-variance-datasets.ts
import { promises as fs } from "fs";
import { join } from "path";

type BuildOptions = {
  componentCatalogPath: string;
  baseCasesPath: string;
  ambiguityPath: string;
  hybridPath: string;
  maxComponents: number;
};

const AMBIGUOUS_TERMS = [
  { term: "ADR", hints: ["Alternative Dispute Resolution", "Architecture Decision Record", "Adversarial Design Review"] },
  { term: "AC", hints: ["Access Control", "Alternating Current", "Air Conditioning"] },
  { term: "PR", hints: ["Pull Request", "Public Relations", "Purchase Request"] },
];

function toCase(id: string, input: string, tags: string[] = [], hints: string[] = []) {
  return {
    id,
    input,
    tags,
    ambiguityHints: hints,
    asserts: { minFinalPromptLength: 50, maxQuestions: 3, minConfidence: 0.6, mustNotContain: [], mustNotHavePlaceholders: true, mustNotBeChatty: true, shouldContain: [] },
  };
}

export async function buildDatasets(options: BuildOptions) {
  const catalogRaw = await fs.readFile(options.componentCatalogPath, "utf-8");
  const catalog = JSON.parse(catalogRaw);
  const components = (catalog.components || []).slice(0, options.maxComponents);

  const ambiguityCases = AMBIGUOUS_TERMS.map((item, i) =>
    toCase(`amb-${String(i + 1).padStart(3, "0")}`, `Design ${item.term} process`, ["ambiguity"], item.hints),
  );

  const componentCases = components.map((comp: { directive?: string }, i: number) =>
    toCase(`comp-${String(i + 1).padStart(3, "0")}`, comp.directive || `Design component ${i + 1} behavior`),
  );

  const baseLines = (await fs.readFile(options.baseCasesPath, "utf-8")).trim().split("\n").slice(0, 20);
  const baseCases = baseLines.map((line) => JSON.parse(line));

  const writeJsonl = async (path: string, items: unknown[]) => {
    const content = items.map((item) => JSON.stringify(item)).join("\n") + "\n";
    await fs.mkdir(join(path, ".."), { recursive: true });
    await fs.writeFile(path, content);
  };

  await writeJsonl(options.ambiguityPath, ambiguityCases);
  await writeJsonl(options.hybridPath, [...ambiguityCases, ...componentCases, ...baseCases]);
}

if (require.main === module) {
  buildDatasets({
    componentCatalogPath: "datasets/exports/ComponentCatalog.json",
    baseCasesPath: "dashboard/testdata/cases.jsonl",
    ambiguityPath: "dashboard/testdata/ambiguity-cases.jsonl",
    hybridPath: "dashboard/testdata/variance-hybrid.jsonl",
    maxComponents: 50,
  });
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- scripts/__tests__/build-variance-datasets.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/scripts/build-variance-datasets.ts dashboard/testdata/ambiguity-cases.jsonl dashboard/testdata/variance-hybrid.jsonl dashboard/scripts/__tests__/build-variance-datasets.test.ts
git commit -m "feat: add hybrid variance dataset generator"
```

---

### Task 4: Document new evaluator flags and usage

**Files:**
- Modify: `docs/claude.md`

**Step 1: Update docs**

Add a new section:
```md
### Evaluator (DSPy variance)

npm run eval -- --dataset testdata/variance-hybrid.jsonl --output eval/ambiguity/latest.json --backend dspy --repeat 5 --config '{"dspyBaseUrl":"http://localhost:8000","timeoutMs":30000}'
```

**Step 2: Commit**

```bash
git add docs/claude.md
git commit -m "docs: document dspy variance evaluator usage"
```

---

**Plan complete and saved to** `docs/plans/2026-01-02-dspy-eval-variance.md`. Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
