#!/usr/bin/env tsx
/**
 * CRT-03: Variability Test Script
 *
 * Runs the same ambiguous input multiple times to measure semantic variability.
 * This quantifies the root cause problem identified in CRT-03.
 *
 * Usage:
 *   npx tsx scripts/test-variability.ts [runs]
 *
 * Default: 10 runs
 */

import { improvePromptWithOllama } from "../src/core/llm/improvePrompt";
import { ollamaHealthCheck } from "../src/core/llm/ollamaClient";
import { DEFAULTS } from "../src/core/config/defaults";

// Test inputs - different ambiguity levels
const TEST_CASES = {
  extreme: {
    input: "Create a function that does something with strings",
    description: "Extreme ambiguity - placeholder 'something' with vague object",
  },
  high: {
    input: "Ayúdame a crear una función, pero no sé exactamente qué necesito",
    description: "High ambiguity - user expresses uncertainty explicitly",
  },
  medium: {
    input: "Podrías escribir algo para validar emails?",
    description: "Medium ambiguity - no technology specified",
  },
  specific: {
    input: "Documenta una función en TypeScript",
    description: "Specific input - should have low variability",
  },
} as const;

type TestCase = keyof typeof TEST_CASES;

interface KeywordSet {
  keywords: string[];
  verb?: string;
  object?: string;
  tech?: string[];
  hasSections: boolean;
  hasQuestions: boolean;
  length: number;
}

/**
 * Extract keywords from a prompt
 */
function extractKeywords(prompt: string): KeywordSet {
  const words = prompt.toLowerCase().split(/\s+/);

  // Extract action verbs
  const verbs = ["create", "write", "build", "generate", "document", "implement", "make", "develop"];
  const verb = verbs.find((v) => words.includes(v));

  // Extract objects
  const objects = ["function", "class", "component", "service", "api", "hook", "helper", "util"];
  const object = objects.find((o) => words.includes(o));

  // Extract technologies
  const techStack = ["typescript", "javascript", "python", "react", "vue", "angular", "sql", "rust", "go"];
  const tech = techStack.filter((t) => words.includes(t));

  // Check for sections (markdown headers)
  const hasSections = /^#+\s+\w+/m.test(prompt);

  // Check for questions
  const hasQuestions = /\?$/.test(prompt.trim()) || prompt.includes("?");

  // Get top keywords (by frequency)
  const frequency = new Map<string, number>();
  words.forEach((w) => {
    if (w.length > 3) {
      frequency.set(w, (frequency.get(w) || 0) + 1);
    }
  });
  const keywords = Array.from(frequency.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([w]) => w);

  return {
    keywords,
    verb,
    object,
    tech,
    hasSections,
    hasQuestions,
    length: prompt.length,
  };
}

/**
 * Calculate overlap between two keyword sets
 */
function calculateOverlap(a: KeywordSet, b: KeywordSet): number {
  const aSet = new Set(a.keywords);
  const bSet = new Set(b.keywords);
  const intersection = new Set([...aSet].filter((x) => bSet.has(x)));
  const union = new Set([...aSet, ...bSet]);

  if (union.size === 0) return 0;
  return intersection.size / union.size;
}

/**
 * Calculate Jaccard similarity between two strings
 */
function jaccardSimilarity(a: string, b: string): number {
  const aWords = new Set(a.toLowerCase().split(/\s+/).filter((w) => w.length > 3));
  const bWords = new Set(b.toLowerCase().split(/\s+/).filter((w) => w.length > 3));

  const intersection = new Set([...aWords].filter((x) => bWords.has(x)));
  const union = new Set([...aWords, ...bWords]);

  if (union.size === 0) return 0;
  return intersection.size / union.size;
}

interface RunResult {
  run: number;
  improvedPrompt: string;
  keywords: KeywordSet;
  confidence: number;
  questions: string[];
  latencyMs: number;
}

interface VariabilityReport {
  testCase: TestCase;
  description: string;
  runs: number;
  results: RunResult[];
  metrics: {
    avgKeywordOverlap: number;
    avgJaccardSimilarity: number;
    confidenceStdDev: number;
    lengthStdDev: number;
    verbConsistency: number;
    objectConsistency: number;
    techConsistency: number;
    hasSectionsConsistency: number;
  };
  variability: "low" | "medium" | "high";
}

async function runVariabilityTest(testCase: TestCase, runs: number): Promise<VariabilityReport> {
  const { input, description } = TEST_CASES[testCase];
  const results: RunResult[] = [];

  console.log(`\n🔍 Testing: ${description}`);
  console.log(`   Input: "${input}"`);
  console.log(`   Runs: ${runs}`);

  for (let i = 0; i < runs; i++) {
    const startTime = Date.now();
    try {
      const result = await improvePromptWithOllama({
        rawInput: input,
        preset: "default",
        options: {
          baseUrl: DEFAULTS.ollama.baseUrl,
          model: DEFAULTS.ollama.model,
          timeoutMs: DEFAULTS.ollama.timeoutMs,
          temperature: DEFAULTS.ollama.temperature,
        },
      });

      const latencyMs = Date.now() - startTime;
      const keywords = extractKeywords(result.improved_prompt);

      results.push({
        run: i + 1,
        improvedPrompt: result.improved_prompt,
        keywords,
        confidence: result.confidence,
        questions: result.clarifying_questions,
        latencyMs,
      });

      console.log(`   ✅ Run ${i + 1}/${runs} - ${latencyMs}ms - Confidence: ${result.confidence.toFixed(2)}`);
    } catch (error) {
      const latencyMs = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error(`   ⚠️  Run ${i + 1}/${runs} - Error (${latencyMs}ms): ${errorMessage.substring(0, 100)}`);

      // Add a failed run result for analysis
      results.push({
        run: i + 1,
        improvedPrompt: `[ERROR: ${errorMessage.substring(0, 50)}]`,
        keywords: {
          keywords: ["error", "failed"],
          hasSections: false,
          hasQuestions: false,
          length: 0,
        },
        confidence: 0,
        questions: [],
        latencyMs,
      });
    }
  }

  // Calculate metrics
  const overlaps: number[] = [];
  const jaccardSimilarities: number[] = [];

  for (let i = 0; i < results.length; i++) {
    for (let j = i + 1; j < results.length; j++) {
      overlaps.push(calculateOverlap(results[i].keywords, results[j].keywords));
      jaccardSimilarities.push(jaccardSimilarity(results[i].improvedPrompt, results[j].improvedPrompt));
    }
  }

  const avgKeywordOverlap = overlaps.reduce((a, b) => a + b, 0) / overlaps.length;
  const avgJaccardSimilarity = jaccardSimilarities.reduce((a, b) => a + b, 0) / jaccardSimilarities.length;

  // Confidence std dev
  const avgConfidence = results.reduce((a, b) => a + b.confidence, 0) / results.length;
  const confidenceVariance = results.reduce((a, b) => a + Math.pow(b.confidence - avgConfidence, 2), 0) / results.length;
  const confidenceStdDev = Math.sqrt(confidenceVariance);

  // Length std dev
  const avgLength = results.reduce((a, b) => a + b.keywords.length, 0) / results.length;
  const lengthVariance = results.reduce((a, b) => a + Math.pow(b.keywords.length - avgLength, 2), 0) / results.length;
  const lengthStdDev = Math.sqrt(lengthVariance);

  // Consistency metrics
  const verbCounts = new Map<string, number>();
  const objectCounts = new Map<string, number>();
  const techCounts = new Map<string, number>();
  let hasSectionsCount = 0;

  results.forEach((r) => {
    if (r.keywords.verb) verbCounts.set(r.keywords.verb, (verbCounts.get(r.keywords.verb) || 0) + 1);
    if (r.keywords.object) objectCounts.set(r.keywords.object, (objectCounts.get(r.keywords.object) || 0) + 1);
    if (r.keywords.tech) {
      r.keywords.tech.forEach((t) => techCounts.set(t, (techCounts.get(t) || 0) + 1));
    }
    if (r.keywords.hasSections) hasSectionsCount++;
  });

  const maxVerbCount = verbCounts.size > 0 ? Math.max(...verbCounts.values()) : 0;
  const maxObjectCount = objectCounts.size > 0 ? Math.max(...objectCounts.values()) : 0;
  const maxTechCount = techCounts.size > 0 ? Math.max(...techCounts.values()) : 0;

  const verbConsistency = results.length > 0 ? maxVerbCount / results.length : 0;
  const objectConsistency = results.length > 0 ? maxObjectCount / results.length : 0;
  const techConsistency = results.length > 0 ? maxTechCount / results.length : 0;
  const hasSectionsConsistency = results.length > 0 ? hasSectionsCount / results.length : 0;

  const metrics = {
    avgKeywordOverlap,
    avgJaccardSimilarity,
    confidenceStdDev,
    lengthStdDev,
    verbConsistency,
    objectConsistency,
    techConsistency,
    hasSectionsConsistency,
  };

  // Classify variability
  const variability: "low" | "medium" | "high" =
    avgKeywordOverlap > 0.7 && avgJaccardSimilarity > 0.7 ? "low" : avgKeywordOverlap > 0.4 && avgJaccardSimilarity > 0.4 ? "medium" : "high";

  return {
    testCase,
    description,
    runs,
    results,
    metrics,
    variability,
  };
}

function printReport(report: VariabilityReport) {
  console.log("\n" + "=".repeat(80));
  console.log(`📊 VARIABILITY REPORT: ${report.testCase.toUpperCase()}`);
  console.log("=".repeat(80));
  console.log(`Description: ${report.description}`);
  console.log(`Runs: ${report.runs}`);
  console.log(`\n📈 Metrics:`);
  console.log(`   Avg Keyword Overlap:     ${(report.metrics.avgKeywordOverlap * 100).toFixed(1)}%`);
  console.log(`   Avg Jaccard Similarity:  ${(report.metrics.avgJaccardSimilarity * 100).toFixed(1)}%`);
  console.log(`   Confidence Std Dev:      ${report.metrics.confidenceStdDev.toFixed(3)}`);
  console.log(`   Length Std Dev:          ${report.metrics.lengthStdDev.toFixed(1)} words`);
  console.log(`   Verb Consistency:        ${(report.metrics.verbConsistency * 100).toFixed(1)}%`);
  console.log(`   Object Consistency:      ${(report.metrics.objectConsistency * 100).toFixed(1)}%`);
  console.log(`   Tech Consistency:        ${(report.metrics.techConsistency * 100).toFixed(1)}%`);
  console.log(`   Has Sections Consistency: ${(report.metrics.hasSectionsConsistency * 100).toFixed(1)}%`);

  console.log(`\n🎯 Variability Level: ${report.variability.toUpperCase()}`);

  // Show sample outputs
  console.log(`\n📝 Sample Outputs:`);
  report.results.slice(0, 3).forEach((r, i) => {
    console.log(`\n   [Run ${r.run}] Confidence: ${r.confidence.toFixed(2)} | Length: ${r.keywords.length} chars`);
    console.log(`   ${r.improvedPrompt.substring(0, 150)}${r.improvedPrompt.length > 150 ? "..." : ""}`);
  });

  // Show keywords comparison
  console.log(`\n🔑 Top Keywords (all runs):`);
  const allKeywords = new Map<string, number>();
  report.results.forEach((r) => {
    r.keywords.keywords.forEach((k) => {
      allKeywords.set(k, (allKeywords.get(k) || 0) + 1);
    });
  });
  const topKeywords = Array.from(allKeywords.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15);

  topKeywords.forEach(([word, count]) => {
    const percentage = (count / report.runs) * 100;
    console.log(`   ${word.padEnd(20)} ${count.toString().padStart(2)}/${report.runs} (${percentage.toFixed(0)}%)`);
  });
}

async function main() {
  const args = process.argv.slice(2);
  const runsArg = args[0];
  const testCaseArg = args[1] as TestCase | undefined;

  const runs = runsArg ? parseInt(runsArg, 10) : 10;
  const testCases: TestCase[] = testCaseArg ? [testCaseArg] : (["extreme", "high", "medium", "specific"] as TestCase[]);

  console.log("╔══════════════════════════════════════════════════════════════════════════════╗");
  console.log("║           CRT-03: VARIABILITY TEST - Semantic Variability Analysis         ║");
  console.log("╚══════════════════════════════════════════════════════════════════════════════╝");

  // Health check
  console.log("\n🔎 Checking Ollama health...");
  const healthy = await ollamaHealthCheck(
    DEFAULTS.ollama.baseUrl,
    DEFAULTS.ollama.healthCheckTimeoutMs,
  );
  if (!healthy) {
    console.error("❌ Ollama is not responding. Please start Ollama first.");
    console.error("   Run: ollama serve");
    process.exit(1);
  }
  console.log("✅ Ollama is healthy");

  // Run tests
  const reports: VariabilityReport[] = [];
  for (const testCase of testCases) {
    const report = await runVariabilityTest(testCase, runs);
    reports.push(report);
    printReport(report);
  }

  // Summary
  console.log("\n" + "=".repeat(80));
  console.log("📋 SUMMARY");
  console.log("=".repeat(80));

  reports.forEach((r) => {
    const emoji = r.variability === "low" ? "🟢" : r.variability === "medium" ? "🟡" : "🔴";
    console.log(`${emoji} ${r.testCase.padEnd(10)} - ${(r.metrics.avgJaccardSimilarity * 100).toFixed(1)}% similarity - ${r.variability.toUpperCase()}`);
  });

  // Verdict
  const avgSimilarity = reports.reduce((a, b) => a + b.metrics.avgJaccardSimilarity, 0) / reports.length;
  console.log(`\n🎯 Overall Average Similarity: ${(avgSimilarity * 100).toFixed(1)}%`);

  if (avgSimilarity < 0.6) {
    console.log("\n🔴 HIGH VARIABILITY DETECTED");
    console.log("   This confirms the CRT-03 hypothesis: the system produces significantly");
    console.log("   different outputs for the same input, making it unpredictable.");
  } else if (avgSimilarity < 0.8) {
    console.log("\n🟡 MEDIUM VARIABILITY DETECTED");
    console.log("   The system shows moderate variability. Consider implementing");
    console.log("   ambiguity detection and temperature differentiation.");
  } else {
    console.log("\n🟢 LOW VARIABILITY");
    console.log("   The system produces consistent outputs. CRT-03 may not be critical.");
  }

  console.log("\n" + "=".repeat(80));
}

main().catch((error) => {
  console.error("❌ Error running variability test:", error);
  process.exit(1);
});
