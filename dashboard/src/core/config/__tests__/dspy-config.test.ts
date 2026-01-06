import { describe, expect, it } from "vitest";
import { validateConfig } from "../schema";

describe("dspy config", () => {
  it("requires dspy baseUrl, timeoutMs, enabled", () => {
    expect(() =>
      validateConfig({
        ollama: {
          baseUrl: "http://localhost:11434",
          model: "test",
          fallbackModel: "test2",
          timeoutMs: 30000,
          temperature: 0.1,
          healthCheckTimeoutMs: 2000,
        },
        dspy: {
          baseUrl: "http://localhost:8000",
          timeoutMs: 30000,
          enabled: true,
        },
        pipeline: { maxQuestions: 3, maxAssumptions: 5, enableAutoRepair: true },
        quality: { minConfidence: 0.7, bannedSnippets: ["x"], metaLineStarters: ["task:"] },
        features: {
          safeMode: false,
          patternsEnabled: true,
          personalityEnabled: true,
          evalEnabled: false,
          autoUpdateKnowledge: false,
        },
        presets: { default: "default", available: ["default"] },
        wizard: { mode: "auto", maxTurns: 2, adaptiveTurns: true },
        patterns: { maxScanChars: 1000, severityPolicy: "warn" },
        eval: {
          gates: {
            jsonValidPass1: 0.9,
            copyableRate: 0.9,
            reviewRateMax: 0.2,
            latencyP95Max: 60000,
            patternsDetectedMin: 0,
          },
          dataset: { path: "x", baseline: "y" },
        },
      }),
    ).not.toThrow();
  });
});
