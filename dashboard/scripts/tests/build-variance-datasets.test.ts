import { describe, expect, it } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { buildDatasets } from "../data/build-variance-datasets";

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
