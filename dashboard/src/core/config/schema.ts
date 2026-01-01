/**
 * Zod schemas for runtime configuration validation
 * Fail-fast on invalid config with clear error messages
 */

import { z } from "zod";

/**
 * Ollama connection configuration
 * All timeouts and URLs validated
 */
export const OllamaConfigSchema = z
  .object({
    baseUrl: z.string().url("baseUrl must be a valid URL (e.g., http://localhost:11434)"),

    model: z
      .string()
      .min(1, "model cannot be empty")
      .regex(/^[a-z0-9][a-z0-9\-._:/]*$/i, "model must be a valid Ollama model name (e.g., hf.co/namespace/model:tag)"),

    fallbackModel: z
      .string()
      .min(1, "fallbackModel cannot be empty")
      .regex(/^[a-z0-9][a-z0-9\-._:/]*$/i, "fallbackModel must be a valid Ollama model name")
      .optional(),

    timeoutMs: z
      .number()
      .int()
      .positive("timeoutMs must be positive")
      .min(1_000, "timeoutMs must be at least 1s (1000ms)")
      .max(120_000, "timeoutMs must not exceed 2 minutes (120000ms)"),

    temperature: z
      .number()
      .min(0, "temperature must be between 0 and 2")
      .max(2, "temperature must be between 0 and 2"),

    healthCheckTimeoutMs: z
      .number()
      .int()
      .positive("healthCheckTimeoutMs must be positive")
      .min(500, "healthCheckTimeoutMs must be at least 500ms")
      .max(10_000, "healthCheckTimeoutMs must not exceed 10s (10000ms)"),
  })
  .strict()
  .refine((data) => !data.fallbackModel || data.fallbackModel !== data.model, {
    message: "fallbackModel must be different from primary model",
    path: ["fallbackModel"],
  });

/**
 * Pipeline behavior configuration
 * Controls retry logic and output limits
 */
export const PipelineConfigSchema = z
  .object({
    maxQuestions: z
      .number()
      .int()
      .nonnegative("maxQuestions cannot be negative")
      .max(10, "maxQuestions must not exceed 10"),

    maxAssumptions: z
      .number()
      .int()
      .nonnegative("maxAssumptions cannot be negative")
      .max(20, "maxAssumptions must not exceed 20"),

    enableAutoRepair: z.boolean().describe("Whether to attempt automatic repair on quality issues"),
  })
  .strict();

/**
 * Quality validation configuration
 * Patterns and thresholds for output validation
 */
export const QualityConfigSchema = z
  .object({
    minConfidence: z
      .number()
      .min(0, "minConfidence must be between 0 and 1")
      .max(1, "minConfidence must be between 0 and 1"),

    bannedSnippets: z
      .array(z.string().min(1))
      .min(1, "bannedSnippets must have at least one pattern")
      .describe("Patterns that indicate low-quality output"),

    metaLineStarters: z.array(z.string().min(1)).describe("Patterns that indicate meta-instructions in first line"),
  })
  .strict();

/**
 * Feature flags for gradual rollouts
 * All features can be toggled on/off
 */
export const FeaturesConfigSchema = z
  .object({
    safeMode: z.boolean().describe("Safe mode: disable advanced features, use only core functionality"),

    patternsEnabled: z.boolean().describe("Pattern detection for anti-patterns"),

    personalityEnabled: z.boolean().describe("Personality system (skeptical, constructive)"),

    evalEnabled: z.boolean().describe("Evaluation system for quality measurement"),

    autoUpdateKnowledge: z.boolean().describe("Auto-update knowledge base patterns (disabled for local-first)"),
  })
  .strict();

/**
 * Preset configuration
 * Available presets for different use cases
 */
export const PresetsConfigSchema = z
  .object({
    default: z.enum(["default", "specific", "structured", "coding"]).describe("Default preset to use"),

    available: z
      .array(z.enum(["default", "specific", "structured", "coding"]))
      .min(1, "available must have at least one preset")
      .describe("List of available presets"),
  })
  .strict()
  .refine((data) => data.available.includes(data.default), {
    message: "default preset must be in available list",
    path: ["default"],
  });

/**
 * Pattern detection configuration
 * Used by anti-debt system
 */
export const PatternsConfigSchema = z
  .object({
    maxScanChars: z
      .number()
      .int()
      .positive("maxScanChars must be positive")
      .min(100, "maxScanChars must be at least 100")
      .max(100_000, "maxScanChars must not exceed 100000"),

    severityPolicy: z.enum(["strict", "warn", "ignore"]).describe("How to handle detected patterns"),
  })
  .strict();

/**
 * Evaluation gate thresholds
 * Regression prevention values
 */
export const EvalGatesSchema = z
  .object({
    jsonValidPass1: z
      .number()
      .min(0, "jsonValidPass1 must be between 0 and 1")
      .max(1, "jsonValidPass1 must be between 0 and 1")
      .describe("Minimum JSON valid rate (0-1)"),

    copyableRate: z
      .number()
      .min(0, "copyableRate must be between 0 and 1")
      .max(1, "copyableRate must be between 0 and 1")
      .describe("Minimum copyable rate (0-1)"),

    reviewRateMax: z
      .number()
      .min(0, "reviewRateMax must be between 0 and 1")
      .max(1, "reviewRateMax must be between 0 and 1")
      .describe("Maximum review rate (friction metric, lower is better for UX)"),

    latencyP95Max: z
      .number()
      .int()
      .positive("latencyP95Max must be positive")
      .min(1000, "latencyP95Max must be at least 1s")
      .max(300_000, "latencyP95Max must not exceed 5 minutes")
      .describe("Maximum P95 latency in milliseconds"),

    patternsDetectedMin: z
      .number()
      .int()
      .nonnegative("patternsDetectedMin cannot be negative")
      .describe("Minimum patterns detected count"),
  })
  .strict();

/**
 * Evaluation configuration
 */
export const EvalConfigSchema = z
  .object({
    gates: EvalGatesSchema,

    dataset: z
      .object({
        path: z.string().min(1, "dataset path cannot be empty"),
        baseline: z.string().min(1, "baseline path cannot be empty"),
      })
      .strict(),
  })
  .strict();

/**
 * Main application configuration schema
 * All config must pass this validation
 */
export const AppConfigSchema = z
  .object({
    ollama: OllamaConfigSchema,
    pipeline: PipelineConfigSchema,
    quality: QualityConfigSchema,
    features: FeaturesConfigSchema,
    presets: PresetsConfigSchema,
    patterns: PatternsConfigSchema,
    eval: EvalConfigSchema,
  })
  .strict();

/**
 * Type exports for TypeScript support
 */
export type AppConfig = z.infer<typeof AppConfigSchema>;
export type OllamaConfig = z.infer<typeof OllamaConfigSchema>;
export type PipelineConfig = z.infer<typeof PipelineConfigSchema>;
export type FeaturesConfig = z.infer<typeof FeaturesConfigSchema>;

/**
 * Validation helper that returns human-readable errors
 */
export function validateConfig(config: unknown): AppConfig {
  const result = AppConfigSchema.safeParse(config);

  if (!result.success) {
    const errors = result.error.errors
      .map((err) => {
        const path = err.path.join(".");
        const message = err.message;
        return `${path}: ${message}`;
      })
      .join("\n");

    throw new Error(`Configuration validation failed:\n${errors}`);
  }

  return result.data;
}

/**
 * Partial config validation (for loading from sources that may be incomplete)
 * Useful for merging with defaults
 * Uses more permissive validation that allows any partial structure
 */
export function validatePartialConfig(partial: unknown): Partial<AppConfig> {
  // For partial config, we validate structure but not completeness
  // This allows any subset of the config to be provided
  try {
    // First do a structural check (is it an object?)
    if (partial === null || typeof partial !== "object") {
      throw new Error("Config must be an object");
    }

    // Validate each top-level section separately if present
    const partialConfig: Partial<AppConfig> = {};
    const configObj = partial as Record<string, unknown>;

    if (configObj.ollama) {
      partialConfig.ollama = OllamaConfigSchema.parse(configObj.ollama);
    }

    if (configObj.pipeline) {
      partialConfig.pipeline = PipelineConfigSchema.parse(configObj.pipeline);
    }

    if (configObj.quality) {
      partialConfig.quality = QualityConfigSchema.parse(configObj.quality);
    }

    if (configObj.features) {
      partialConfig.features = FeaturesConfigSchema.parse(configObj.features);
    }

    if (configObj.presets) {
      partialConfig.presets = PresetsConfigSchema.parse(configObj.presets);
    }

    if (configObj.patterns) {
      partialConfig.patterns = PatternsConfigSchema.parse(configObj.patterns);
    }

    if (configObj.eval) {
      partialConfig.eval = EvalConfigSchema.parse(configObj.eval);
    }

    return partialConfig;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Partial config validation failed: ${errorMessage}`);
  }
}
