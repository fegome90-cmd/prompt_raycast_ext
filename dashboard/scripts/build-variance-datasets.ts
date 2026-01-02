import { promises as fs } from "fs";
import { dirname, isAbsolute, join } from "path";

type BuildOptions = {
  componentCatalogPath: string;
  baseCasesPath: string;
  ambiguityPath: string;
  hybridPath: string;
  maxComponents: number;
};

const AMBIGUOUS_TERMS = [
  {
    term: "ADR",
    hints: ["Alternative Dispute Resolution", "Architecture Decision Record", "Adversarial Design Review"],
  },
  { term: "AC", hints: ["Access Control", "Alternating Current", "Air Conditioning"] },
  { term: "PR", hints: ["Pull Request", "Public Relations", "Purchase Request"] },
];

function toCase(id: string, input: string, tags: string[] = [], hints: string[] = []) {
  return {
    id,
    input,
    tags,
    ambiguityHints: hints,
    asserts: {
      minFinalPromptLength: 50,
      maxQuestions: 3,
      minConfidence: 0.6,
      mustNotContain: [],
      mustNotHavePlaceholders: true,
      mustNotBeChatty: true,
      shouldContain: [],
    },
  };
}

async function resolveInputPath(inputPath: string): Promise<string> {
  if (isAbsolute(inputPath)) return inputPath;
  const cwdPath = join(process.cwd(), inputPath);
  try {
    await fs.stat(cwdPath);
    return cwdPath;
  } catch {
    const parentPath = join(process.cwd(), "..", inputPath);
    try {
      await fs.stat(parentPath);
      return parentPath;
    } catch {
      return cwdPath;
    }
  }
}

export async function buildDatasets(options: BuildOptions) {
  const catalogPath = await resolveInputPath(options.componentCatalogPath);
  const baseCasesPath = await resolveInputPath(options.baseCasesPath);
  const catalogRaw = await fs.readFile(catalogPath, "utf-8");
  const catalog = JSON.parse(catalogRaw);
  const components = (catalog.components || []).slice(0, options.maxComponents);

  const ambiguityCases = AMBIGUOUS_TERMS.map((item, i) =>
    toCase(`amb-${String(i + 1).padStart(3, "0")}`, `Design ${item.term} process`, ["ambiguity"], item.hints),
  );

  const componentCases = components.map((comp: { directive?: string }, i: number) =>
    toCase(`comp-${String(i + 1).padStart(3, "0")}`, comp.directive || `Design component ${i + 1} behavior`),
  );

  const baseLines = (await fs.readFile(baseCasesPath, "utf-8")).trim().split("\n").slice(0, 20);
  const baseCases = baseLines.map((line) => JSON.parse(line));

  const writeJsonl = async (path: string, items: unknown[]) => {
    const content = items.map((item) => JSON.stringify(item)).join("\n") + "\n";
    await fs.mkdir(dirname(path), { recursive: true });
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
