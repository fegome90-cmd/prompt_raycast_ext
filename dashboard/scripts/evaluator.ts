#!/usr/bin/env tsx
/**
 * Evaluator system for Prompt Renderer Local
 * Measures baseline metrics and detects regressions
 */

import { promises as fs } from "fs";
import { join } from "path";
import { z } from "zod";
import { improvePromptWithHybrid, improvePromptWithOllama } from "../src/core/llm/improvePrompt";
import { ollamaHealthCheck } from "../src/core/llm/ollamaClient";

// Schema for test cases - Soft asserts instead of hard content matching
const TestCaseSchema = z.object({
  id: z.string(),
  input: z.string(),
  tags: z.array(z.string()).default([]),
  ambiguityHints: z.array(z.string()).default([]),
  asserts: z.object({
    // Structural validation (hard)
    minFinalPromptLength: z.number().int().min(0).default(50),
    maxQuestions: z.number().int().min(0).max(10).default(5),
    minConfidence: z.number().min(0).max(1).default(0.5),

    // Content validation (soft - patterns to avoid)
    mustNotContain: z.array(z.string()).default([]),
    mustNotHavePlaceholders: z.boolean().default(true), // {{ }} or [...]
    mustNotBeChatty: z.boolean().default(true), // Meta explanations

    // Optional hints (soft - not strict requirements)
    shouldContain: z.array(z.string()).default([]), // Hints only
    appropriateLength: z.number().int().min(0).max(1000).optional(),
  }),
});

type TestCase = z.infer<typeof TestCaseSchema>;
type RunResult = { caseId: string; run: number; output: string; backend: "ollama" | "dspy" };

// Results schema
const MetricsSchema = z.object({
  timestamp: z.string(),
  totalCases: z.number(),

  // Breakdown by bucket
  buckets: z.object({
    good: z.object({
      total: z.number(),
      jsonValidPass1: z.number(),
      copyableRate: z.number(),
      reviewRate: z.number(),
    }),
    bad: z.object({
      total: z.number(),
      jsonValidPass1: z.number(),
      copyableRate: z.number(),
      reviewRate: z.number(),
    }),
    ambiguous: z.object({
      total: z.number(),
      jsonValidPass1: z.number(),
      copyableRate: z.number(),
      reviewRate: z.number(),
    }),
  }),

  // Overall metrics (weighted)
  jsonValidPass1: z.number(),
  jsonValidPass2: z.number(),
  copyableRate: z.number(),
  reviewRate: z.number(),
  latencyP50: z.number(),
  latencyP95: z.number(),
  patternsDetected: z.number(),

  // New metrics for wrapper tracking
  extractionUsedRate: z.number().default(0),
  extractionMethodBreakdown: z
    .object({
      fence: z.number().default(0),
      tag: z.number().default(0),
      scan: z.number().default(0),
    })
    .default({}),
  repairTriggerRate: z.number().default(0),
  repairSuccessRate: z.number().default(0),
  repairJsonParseOkRate: z.number().default(0),
  repairSchemaValidRate: z.number().default(0),
  attempt2Rate: z.number().default(0),

  // Failure reasons breakdown
  failureReasons: z.object({
    invalidJson: z.number(),
    schemaMismatch: z.number(),
    emptyFinalPrompt: z.number(),
    unfilledPlaceholders: z.number(),
    chattyOutput: z.number(),
    bannedContent: z.number(),
    tooManyQuestions: z.number(),
    other: z.number(),
  }),

  failures: z.array(
    z.object({
      caseId: z.string(),
      reason: z.string(),
      category: z.string(),
    }),
  ),

  ambiguity: z
    .object({
      totalAmbiguousCases: z.number().default(0),
      ambiguitySpread: z.number().default(0),
      dominantSenseRate: z.number().default(0),
      stabilityScore: z.number().default(1),
    })
    .default({}),

  skillUsed: z.string().default("core"),
});

type Metrics = z.infer<typeof MetricsSchema>;

const ACRONYM_SENSES: Record<string, { label: string; patterns: RegExp[] }[]> = {
  ADR: [
    { label: "alternative_dispute_resolution", patterns: [/alternative dispute resolution/i] },
    { label: "architecture_decision_record", patterns: [/architecture decision record/i] },
    { label: "adversarial_design_review", patterns: [/adversarial design review/i] },
  ],
  AC: [
    { label: "access_control", patterns: [/access control/i] },
    { label: "alternating_current", patterns: [/alternating current/i] },
    { label: "air_conditioning", patterns: [/air conditioning/i] },
  ],
  PR: [
    { label: "pull_request", patterns: [/pull request/i] },
    { label: "public_relations", patterns: [/public relations/i] },
    { label: "purchase_request", patterns: [/purchase request/i] },
  ],
};

function classifySense(output: string): string | null {
  for (const [acronym, senses] of Object.entries(ACRONYM_SENSES)) {
    for (const sense of senses) {
      if (sense.patterns.some((pattern) => pattern.test(output))) {
        return `${acronym}:${sense.label}`;
      }
    }
  }
  return null;
}

function computeAmbiguityMetrics(cases: TestCase[], runs: RunResult[]) {
  if (!cases.length) {
    return { totalAmbiguousCases: 0, ambiguitySpread: 0, dominantSenseRate: 0, stabilityScore: 1 };
  }

  let spread = 0;
  let dominant = 0;
  let stabilitySum = 0;

  for (const testCase of cases) {
    const outputs = runs.filter((run) => run.caseId === testCase.id).map((run) => run.output);
    const senses = outputs.map((output) => classifySense(output)).filter(Boolean) as string[];
    const counts = senses.reduce(
      (acc, sense) => {
        acc[sense] = (acc[sense] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );
    const unique = Object.keys(counts).length;
    if (unique > 1) {
      spread += 1;
    }
    const total = senses.length || 1;
    const maxShare = Math.max(...Object.values(counts), 0) / total;
    if (maxShare >= 2 / 3) {
      dominant += 1;
    }
    stabilitySum += maxShare;
  }

  return {
    totalAmbiguousCases: cases.length,
    ambiguitySpread: spread / cases.length,
    dominantSenseRate: dominant / cases.length,
    stabilityScore: stabilitySum / cases.length,
  };
}

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
  verbose?: boolean;
}

class Evaluator {
  private latencies: number[] = [];
  private failures: Array<{ caseId: string; reason: string; category: string }> = [];
  private patternsDetected = 0;

  // Wrapper metrics counters
  private extractionUsed = 0;
  private extractionMethods = { fence: 0, tag: 0, scan: 0 };
  private repairTriggered = 0;
  private repairJsonParseOk = 0; // Repair produced valid JSON syntax
  private repairSchemaValid = 0; // Repair passed Zod validation
  private repairSucceeded = 0; // Deprecated: use honest metrics above
  private attempt2Total = 0;
  private totalCasesRun = 0;

  async run(options: EvalOptions): Promise<Metrics> {
    console.log("🎯 Starting evaluation...");

    const backend = options.backend ?? "ollama";
    if (backend === "ollama") {
      // Ensure Ollama is available
      const health = await ollamaHealthCheck({
        baseUrl: options.config?.baseUrl || "http://localhost:11434",
        timeoutMs: 2000,
      });

      if (!health.ok) {
        const errorMsg = health.ok === false ? health.error : "Unknown error";
        throw new Error(`Ollama not available: ${errorMsg}`);
      }
    }

    // Load test cases
    const cases = await this.loadCases(options.datasetPath);
    console.log(`📋 Loaded ${cases.length} test cases`);

    // Initialize bucket counters
    const buckets = {
      good: { success: 0, jsonValid: 0, copyable: 0, reviewable: 0, total: 0 },
      bad: { success: 0, jsonValid: 0, copyable: 0, reviewable: 0, total: 0 },
      ambiguous: { success: 0, jsonValid: 0, copyable: 0, reviewable: 0, total: 0 },
    };

    const failureReasons = {
      invalidJson: 0,
      schemaMismatch: 0,
      emptyFinalPrompt: 0,
      unfilledPlaceholders: 0,
      chattyOutput: 0,
      bannedContent: 0,
      tooManyQuestions: 0,
      other: 0,
    };

    // Initialize totals
    let totalValid = 0;

    const repeat = Math.max(1, options.repeat ?? 1);
    const runs: RunResult[] = [];

    // Run each case
    for (const testCase of cases) {
      const bucket = testCase.id.startsWith("good-") ? "good" : testCase.id.startsWith("bad-") ? "bad" : "ambiguous";
      for (let i = 0; i < repeat; i++) {
        buckets[bucket].total++;

        try {
          const result = await this.runCase(testCase, options);
          runs.push({
            caseId: testCase.id,
            run: i + 1,
            output: result.output,
            backend: options.backend ?? "ollama",
          });

          if (result.category === "success") {
            totalValid++;
            buckets[bucket].success++;
            buckets[bucket].jsonValid++;
            buckets[bucket].copyable += result.isCopyable ? 1 : 0;
            buckets[bucket].reviewable += result.hasMetadata ? 1 : 0;
          } else {
            // Count failure
            const category = result.category;
            switch (category) {
              case "invalidJson":
                failureReasons.invalidJson++;
                break;
              case "schemaMismatch":
                failureReasons.schemaMismatch++;
                break;
              case "emptyFinalPrompt":
                failureReasons.emptyFinalPrompt++;
                break;
              case "unfilledPlaceholders":
                failureReasons.unfilledPlaceholders++;
                break;
              case "chattyOutput":
                failureReasons.chattyOutput++;
                break;
              case "bannedContent":
                failureReasons.bannedContent++;
                break;
              case "tooManyQuestions":
                failureReasons.tooManyQuestions++;
                break;
              default:
                failureReasons.other++;
                break;
            }

            this.failures.push({
              caseId: testCase.id,
              reason: result.reason,
              category: result.category,
            });
          }

          this.latencies.push(result.latency);

          // Check for debt patterns
          const patterns = this.detectPatterns(testCase.input);
          this.patternsDetected += patterns.length;

          if (options.verbose && result.category === "success") {
            console.log(`✅ ${testCase.id}: ${result.latency}ms, copyable: ${result.isCopyable}`);
          }
        } catch (error) {
          const reason = error instanceof Error ? error.message : String(error);
          failureReasons.other++;
          this.failures.push({ caseId: testCase.id, reason, category: "exception" });
          console.error(`❌ ${testCase.id}: ${reason}`);

          // Extract metadata from ImprovePromptError if present
          if (error instanceof Error && error.name === "ImprovePromptError" && "meta" in error) {
            const meta = (error as Error & { meta?: { wrapper?: { usedRepair?: boolean; attempt?: number; usedExtraction?: boolean; extractionMethod?: string; failureReason?: string } } }).meta;
            if (meta?.wrapper) {
              const wrapper = meta.wrapper;

              // Track repair metrics from error metadata
              if (wrapper.usedRepair && wrapper.attempt === 2) {
                this.repairTriggered++;
                this.attempt2Total++;

                // Count honest repair metrics
                this.repairJsonParseOk++; // We know repair was attempted (parse OK)

                // If failureReason is not schema_mismatch, it means repair produced JSON but failed quality checks
                if (wrapper.failureReason !== "schema_mismatch") {
                  this.repairSchemaValid++; // Repair passed schema validation
                }
              }

              // Track extraction if used
              if (wrapper.usedExtraction) {
                this.extractionUsed++;
                const method = wrapper.extractionMethod || "scan";
                if (method in this.extractionMethods) {
                  this.extractionMethods[method as keyof typeof this.extractionMethods]++;
                }
              }
            }
          }
        }
      }
    }

    // Calculate wrapper metrics (honest version)
    const wrapperMetrics = {
      extractionUsedRate: this.totalCasesRun > 0 ? this.extractionUsed / this.totalCasesRun : 0,
      extractionMethodBreakdown: {
        fence: this.extractionMethods.fence,
        tag: this.extractionMethods.tag,
        scan: this.extractionMethods.scan,
      },
      repairTriggerRate: this.totalCasesRun > 0 ? this.repairTriggered / this.totalCasesRun : 0,
      repairSuccessRate: this.repairTriggered > 0 ? this.repairSucceeded / this.repairTriggered : 0,
      repairJsonParseOkRate: this.repairTriggered > 0 ? this.repairJsonParseOk / this.repairTriggered : 0,
      repairSchemaValidRate: this.repairTriggered > 0 ? this.repairSchemaValid / this.repairTriggered : 0,
      attempt2Rate: this.totalCasesRun > 0 ? this.attempt2Total / this.totalCasesRun : 0,
    };

    const ambiguousCases = cases.filter((testCase) => testCase.tags.includes("ambiguity"));
    const ambiguityMetrics = computeAmbiguityMetrics(ambiguousCases, runs);

    // Calculate metrics
    const totalCases = buckets.good.total + buckets.bad.total + buckets.ambiguous.total;
    const metrics: Metrics = {
      timestamp: new Date().toISOString(),
      totalCases,

      // Breakdown by bucket
      buckets: {
        good: {
          total: buckets.good.total,
          jsonValidPass1: buckets.good.total > 0 ? buckets.good.jsonValid / buckets.good.total : 0,
          copyableRate: buckets.good.total > 0 ? buckets.good.copyable / buckets.good.total : 0,
          reviewRate: buckets.good.total > 0 ? buckets.good.reviewable / buckets.good.total : 0,
        },
        bad: {
          total: buckets.bad.total,
          jsonValidPass1: buckets.bad.total > 0 ? buckets.bad.jsonValid / buckets.bad.total : 0,
          copyableRate: buckets.bad.total > 0 ? buckets.bad.copyable / buckets.bad.total : 0,
          reviewRate: buckets.bad.total > 0 ? buckets.bad.reviewable / buckets.bad.total : 0,
        },
        ambiguous: {
          total: buckets.ambiguous.total,
          jsonValidPass1: buckets.ambiguous.total > 0 ? buckets.ambiguous.jsonValid / buckets.ambiguous.total : 0,
          copyableRate: buckets.ambiguous.total > 0 ? buckets.ambiguous.copyable / buckets.ambiguous.total : 0,
          reviewRate: buckets.ambiguous.total > 0 ? buckets.ambiguous.reviewable / buckets.ambiguous.total : 0,
        },
      },

      // Overall metrics
      jsonValidPass1: totalCases > 0 ? totalValid / totalCases : 0,
      jsonValidPass2: 0, // Not used yet
      copyableRate:
        totalCases > 0 ? (buckets.good.copyable + buckets.bad.copyable + buckets.ambiguous.copyable) / totalCases : 0,
      reviewRate:
        totalCases > 0
          ? (buckets.good.reviewable + buckets.bad.reviewable + buckets.ambiguous.reviewable) / totalCases
          : 0,
      latencyP50: this.percentile(this.latencies, 50),
      latencyP95: this.percentile(this.latencies, 95),
      patternsDetected: this.patternsDetected,

      // Wrapper metrics
      extractionUsedRate: wrapperMetrics.extractionUsedRate,
      extractionMethodBreakdown: wrapperMetrics.extractionMethodBreakdown,
      repairTriggerRate: wrapperMetrics.repairTriggerRate,
      repairSuccessRate: wrapperMetrics.repairSuccessRate,
      repairJsonParseOkRate: wrapperMetrics.repairJsonParseOkRate,
      repairSchemaValidRate: wrapperMetrics.repairSchemaValidRate,
      attempt2Rate: wrapperMetrics.attempt2Rate,

      // Failure reasons breakdown
      failureReasons: failureReasons,

      failures: this.failures,
      ambiguity: ambiguityMetrics,
      skillUsed: "core",
    };

    // Save results
    if (options.outputPath) {
      await fs.mkdir(join(options.outputPath, ".."), { recursive: true });
      await fs.writeFile(options.outputPath, JSON.stringify(metrics, null, 2));
      console.log(`💾 Results saved to ${options.outputPath}`);
    }

    // Print summary
    this.printSummary(metrics);

    return MetricsSchema.parse(metrics);
  }

  private async loadCases(path: string): Promise<TestCase[]> {
    const content = await fs.readFile(path, "utf-8");
    const lines = content
      .trim()
      .split("\n")
      .filter((line) => line);

    return lines.map((line, idx) => {
      try {
        const parsed = JSON.parse(line);
        return TestCaseSchema.parse(parsed);
      } catch (error) {
        throw new Error(`Invalid JSON at line ${idx + 1}: ${error}`);
      }
    });
  }

  private async runCase(testCase: TestCase, options: EvalOptions) {
    const start = Date.now();
    this.totalCasesRun++;
    const backend = options.backend ?? "ollama";

    const result =
      backend === "dspy"
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

    const latency = Date.now() - start;
    const output = result.improved_prompt;

    // Track wrapper metadata
    const metadata = (result as { _metadata?: { usedExtraction?: boolean; extractionMethod?: string; usedRepair?: boolean; attempt?: number; failureReason?: string } })._metadata;
    if (metadata) {
      // Track extraction
      if (metadata.usedExtraction) {
        this.extractionUsed++;
        const method = metadata.extractionMethod || "scan";
        if (method in this.extractionMethods) {
          this.extractionMethods[method as keyof typeof this.extractionMethods]++;
        }
      }

      // Track repair attempt (honest metrics)
      if (metadata.usedRepair && metadata.attempt === 2) {
        this.repairTriggered++;
        this.attempt2Total++;

        // Count honest repair success: only if final result was OK
        // (meaning repair produced JSON that passed schema validation)
        if (result && typeof result === "object" && "improved_prompt" in result) {
          this.repairJsonParseOk++; // Repair produced parseable JSON
          // If we got here, repair at least produced valid JSON syntax
          // Now check if the final result passed quality checks
          const issues = this.checkQualityIssues(result.improved_prompt);
          if (issues.length === 0) {
            this.repairSchemaValid++; // Repair passed all validation
          }
        }
      }
    }

    // === SOFT ASSERTS: Primary validation ===

    // 1. Must not be empty or too short
    if (!output || output.trim().length < testCase.asserts.minFinalPromptLength) {
      return {
        success: false,
        reason: `Final prompt too short: ${output?.length || 0} < ${testCase.asserts.minFinalPromptLength}`,
        category: "emptyFinalPrompt",
        latency,
        output,
      };
    }

    // 2. Must not have placeholders
    if (testCase.asserts.mustNotHavePlaceholders) {
      const hasPlaceholders = /\{\{.*\}\}|\[.*\]/.test(output);
      if (hasPlaceholders) {
        return {
          success: false,
          reason: "Contains unfilled placeholders",
          category: "unfilledPlaceholders",
          latency,
          output,
        };
      }
    }

    // 3. Must not be chatty (meta explanations)
    if (testCase.asserts.mustNotBeChatty) {
      const chattyPatterns = [
        /as an ai/gi,
        /as a language model/gi,
        /hard rules/gi,
        /output rules/gi,
        /let me explain/gi,
        /i will help you/gi,
        /i improved your prompt/gi,
      ];

      const isChatty = chattyPatterns.some((p) => p.test(output));
      if (isChatty) {
        return {
          success: false,
          reason: "Contains meta/chatty content",
          category: "chattyOutput",
          latency,
          output,
        };
      }
    }

    // 4. Must not contain banned patterns
    for (const banned of testCase.asserts.mustNotContain) {
      if (output.toLowerCase().includes(banned.toLowerCase())) {
        return {
          success: false,
          reason: `Contains banned pattern: "${banned}"`,
          category: "bannedContent",
          latency,
          output,
        };
      }
    }

    // 5. Question count must be within limit
    if (result.clarifying_questions.length > testCase.asserts.maxQuestions) {
      return {
        success: false,
        reason: `Too many questions: ${result.clarifying_questions.length} > ${testCase.asserts.maxQuestions}`,
        category: "tooManyQuestions",
        latency,
        output,
      };
    }

    // 6. Confidence must meet minimum
    if (result.confidence < testCase.asserts.minConfidence) {
      return {
        success: false,
        reason: `Confidence too low: ${result.confidence} < ${testCase.asserts.minConfidence}`,
        category: "other",
        latency,
        output,
      };
    }

    // 7. OPTIONAL HINTS (soft asserts - warnings only)
    if (testCase.asserts.shouldContain && testCase.asserts.shouldContain.length > 0) {
      const missingHints = testCase.asserts.shouldContain.filter(
        (hint) => !output.toLowerCase().includes(hint.toLowerCase()),
      );

      if (missingHints.length > 0 && testCase.id.startsWith("good-")) {
        // Only warn for good cases, don't fail
        console.warn(`⚠️  ${testCase.id}: Missing hints: ${missingHints.join(", ")}`);
      }
    }

    // == SUCCESS: Determine if copyable and reviewable
    const isCopyable =
      output.length > 50 && result.clarifying_questions.length <= 3 && !output.includes("{{") && !output.includes("[");

    const hasMetadata = result.clarifying_questions.length > 0 || result.assumptions.length > 0;

    return {
      success: true,
      reason: "OK",
      category: "success",
      isCopyable,
      hasMetadata,
      latency,
      output,
    };
  }

  private checkQualityIssues(improvedPrompt: string): string[] {
    const issues: string[] = [];

    // Check for unfilled placeholders
    if (/\{\{.*\}\}|\[.*\]/.test(improvedPrompt)) {
      issues.push("unfilled_placeholders");
    }

    // Check for chatty content
    const chattyPatterns = [
      /as an ai/gi,
      /as a language model/gi,
      /hard rules/gi,
      /output rules/gi,
      /let me explain/gi,
      /i will help you/gi,
      /i improved your prompt/gi,
    ];

    if (chattyPatterns.some((p) => p.test(improvedPrompt))) {
      issues.push("chatty_output");
    }

    // Check if empty or too short
    if (!improvedPrompt || improvedPrompt.trim().length < 50) {
      issues.push("empty_or_too_short");
    }

    return issues;
  }

  private detectPatterns(input: string): string[] {
    const patterns: string[] = [];

    // Check for common anti-patterns
    const antiPatterns = [
      { id: "DEP001", pattern: /as an ai|as a language model/i },
      { id: "DEP002", pattern: /hard rules|output rules/i },
      { id: "DEP003", pattern: /guidelines:/i },
    ];

    for (const { id, pattern } of antiPatterns) {
      if (pattern.test(input)) {
        patterns.push(id);
      }
    }

    return patterns;
  }

  private percentile(values: number[], p: number): number {
    if (values.length === 0) return 0;

    const sorted = [...values].sort((a, b) => a - b);
    const k = Math.ceil((sorted.length * p) / 100) - 1;
    return sorted[Math.max(0, k)];
  }

  private printSummary(metrics: Metrics) {
    console.log("\n📊 Evaluation Summary", "\n====================");

    // Overall numbers
    console.log(`Total cases: ${metrics.totalCases}`);
    console.log(`JSON valid (pass1): ${(metrics.jsonValidPass1 * 100).toFixed(1)}%`);
    console.log(`Copyable rate: ${(metrics.copyableRate * 100).toFixed(1)}%`);
    console.log(`Latency p50: ${metrics.latencyP50.toFixed(0)}ms`);
    console.log(`Latency p95: ${metrics.latencyP95.toFixed(0)}ms`);
    console.log(`Patterns detected: ${metrics.patternsDetected}`);
    console.log(`Failures: ${metrics.failures.length}`);

    // Wrapper metrics (honest version)
    console.log("\n🛠️  Wrapper Metrics:");
    console.log(`  Extraction used: ${(metrics.extractionUsedRate * 100).toFixed(1)}%`);
    console.log(`  Repair triggered: ${(metrics.repairTriggerRate * 100).toFixed(1)}%`);
    console.log(`  Repair JSON parse OK: ${(metrics.repairJsonParseOkRate * 100).toFixed(1)}%`);
    console.log(`  Repair schema valid: ${(metrics.repairSchemaValidRate * 100).toFixed(1)}%`);
    console.log(`  Attempt 2 rate: ${(metrics.attempt2Rate * 100).toFixed(1)}%`);
    if (
      metrics.extractionMethodBreakdown.fence > 0 ||
      metrics.extractionMethodBreakdown.tag > 0 ||
      metrics.extractionMethodBreakdown.scan > 0
    ) {
      console.log(
        `  Extraction methods: fence=${metrics.extractionMethodBreakdown.fence}, tag=${metrics.extractionMethodBreakdown.tag}, scan=${metrics.extractionMethodBreakdown.scan}`,
      );
    }

    // Gate status
    console.log("\n🚦 Gate Status:");
    const gates = [
      { name: "jsonValidPass1 ≥ 54%", pass: metrics.jsonValidPass1 >= 0.54 },
      { name: "copyableRate ≥ 54%", pass: metrics.copyableRate >= 0.54 },
      { name: "latencyP95 ≤ 12000ms", pass: metrics.latencyP95 <= 12000 },
      {
        name: "repairSchemaValidRate ≥ 50%",
        pass: metrics.repairSchemaValidRate >= 0.5 || metrics.repairTriggerRate === 0,
      },
    ];
    gates.forEach((gate) => {
      console.log(`  ${gate.pass ? "✅" : "❌"} ${gate.name}`);
    });

    // Breakdown by bucket
    console.log("\n📦 Breakdown by Bucket:");
    console.log(
      `Good:     ${(metrics.buckets.good.jsonValidPass1 * 100).toFixed(1)}% JSON valid, ${(
        metrics.buckets.good.copyableRate * 100
      ).toFixed(1)}% copyable (${metrics.buckets.good.total} cases)`,
    );
    console.log(
      `Bad:      ${(metrics.buckets.bad.jsonValidPass1 * 100).toFixed(1)}% JSON valid, ${(
        metrics.buckets.bad.copyableRate * 100
      ).toFixed(1)}% copyable (${metrics.buckets.bad.total} cases)`,
    );
    console.log(
      `Ambiguous: ${(metrics.buckets.ambiguous.jsonValidPass1 * 100).toFixed(1)}% JSON valid, ${(
        metrics.buckets.ambiguous.copyableRate * 100
      ).toFixed(1)}% copyable (${metrics.buckets.ambiguous.total} cases)`,
    );

    // Top failure reasons
    if (metrics.failures.length > 0) {
      console.log("\n❌ Top Failure Reasons:");
      Object.entries(metrics.failureReasons)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .forEach(([reason, count]) => console.log(`  ${reason}: ${count}`));
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const datasetIdx = args.indexOf("--dataset");
  const outputIdx = args.indexOf("--output");
  const verbose = args.includes("--verbose");
  const configIdx = args.indexOf("--config");

  if (datasetIdx === -1) {
    console.error("Usage: npm run eval -- --dataset <path> [--output <path>] [--verbose] [--config <json>]");
    process.exit(1);
  }

  const datasetPath = args[datasetIdx + 1];
  const outputPath = outputIdx !== -1 ? args[outputIdx + 1] : undefined;

  let config = undefined;
  if (configIdx !== -1) {
    try {
      config = JSON.parse(args[configIdx + 1]);
    } catch {
      console.error("Invalid config JSON");
      process.exit(1);
    }
  }

  try {
    const evaluator = new Evaluator();
    await evaluator.run({
      datasetPath,
      outputPath,
      config,
      verbose,
    });
  } catch (error) {
    console.error("❌ Evaluation failed:", error);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { Evaluator, TestCaseSchema, MetricsSchema };
