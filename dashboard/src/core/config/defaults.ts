/**
 * Centralized configuration defaults - Single source of truth
 * All tunable values documented with rationale
 */

export const DEFAULTS = {
  /**
   * Ollama connection settings
   */
  ollama: {
    /**
     * Base URL for Ollama API
     * Default: localhost:11434 (standard Ollama installation)
     */
    baseUrl: "http://localhost:11434",

    /**
     * Primary model for prompt improvement
     * Novaeus-Promptist-7B: Specialized prompt engineering model
     */
    model: "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",

    /**
     * Fallback model when primary fails
     * Used for reliability when model not found or errors
     */
    fallbackModel: "devstral:24b",

    /**
     * Default request timeout (ms)
     * 30s allows for complex prompts while preventing hangs
     */
    timeoutMs: 30_000,

    /**
     * Temperature for Ollama generation
     * 0.1 = deterministic, high quality for structured output
     */
    temperature: 0.1,

    /**
     * Health check timeout (ms)
     * Shorter timeout for quick connectivity check
     */
    healthCheckTimeoutMs: 2_000,
  },

  /**
   * DSPy backend settings
   */
  dspy: {
    /**
     * Base URL for DSPy backend
     * Default: localhost:8000 (FastAPI)
     */
    baseUrl: "http://localhost:8000",

    /**
     * Default request timeout (ms)
     * 120s allows for Anthropic Haiku API latency (~30-50s per request)
     */
    timeoutMs: 120_000,

    /**
     * Enable DSPy backend first, fallback to Ollama if unavailable
     */
    enabled: true,
  },

  /**
   * Pipeline behavior settings
   */
  pipeline: {
    /**
     * Maximum clarifying questions to generate
     * 3 questions keeps UX friction low while gathering needed info
     */
    maxQuestions: 3,

    /**
     * Maximum assumptions to list
     * 5 assumptions provides context without overwhelming
     */
    maxAssumptions: 5,

    /**
     * Whether to attempt repair on quality issues
     * true = auto-retry with repair prompt (increases latency but improves quality)
     */
    enableAutoRepair: true,
  },

  /**
   * Quality validation settings
   */
  quality: {
    /**
     * Minimum confidence threshold (0-1)
     * 0.7 = reasonably confident without being overly conservative
     */
    minConfidence: 0.7,

    /**
     * Banned patterns that indicate low-quality output
     * These patterns suggest the model leaked meta-instructions
     */
    bannedSnippets: [
      "you are a prompt improver",
      "hard rules",
      "output rules",
      "clarifying_questions",
      "assumptions",
      "confidence",
      "do you want me to",
      "would you like me to",
      "as an ai",
      "as a language model",
    ],

    /**
     * Patterns that indicate meta-instructions in first line
     * Used to detect instruction leakage
     */
    metaLineStarters: ["task:", "rules:", "guardrails:", "rewrite instruction:", "raw user request:"],
  },

  /**
   * Feature flags for gradual rollouts and emergency fallback
   * All features default to true for maximum functionality
   * Set to false to disable specific features
   */
  features: {
    /**
     * Safe mode: disable all advanced features, use only core functionality
     * Activates automatically when config validation fails
     * Manual override via preference switches to safe mode
     */
    safeMode: false,

    /**
     * Pattern detection for identifying technical debt in prompts
     * Phase 2 feature - detects anti-patterns in prompts
     */
    patternsEnabled: true,

    /**
     * Personality system (skeptical, constructive modes)
     * Phase 3 feature - adds critical-constructive personality
     */
    personalityEnabled: false, // Disabled by default for v2.0

    /**
     * Evaluation system for measuring quality and regression
     * Phase 0 feature - essential for development
     */
    evalEnabled: true,

    /**
     * Auto-update knowledge base patterns
     * If true, automatically fetches latest anti-patterns from knowledge base
     */
    autoUpdateKnowledge: false, // Disabled for local-first principle
  },

  /**
   * Preset configurations for different use cases
   * Each preset modifies the system prompt and expectations
   */
  presets: {
    default: "structured",
    available: ["default", "specific", "structured", "coding"],
  },

  /**
   * Pattern detection settings
   * Used by anti-debt system (Phase 2)
   */
  patterns: {
    /**
     * Maximum characters to scan for patterns
     * Prevents excessive scanning on very long prompts
     */
    maxScanChars: 10_000,

    /**
     * Severity policy: how to handle detected patterns
     * strict = fail on any pattern (not recommended)
     * warn = show warnings but don't block (current behavior)
     */
    severityPolicy: "warn" as const,
  },

  /**
   * Evaluation settings
   * Used by test harness and CI/CD
   */
  eval: {
    /**
     * Gate thresholds for regression prevention
     * Values are percentages (0-1) or milliseconds
     */
    gates: {
      /**
       * Minimum JSON valid rate (pass1)
       * Baseline v2: 56.7% with soft asserts
       */
      jsonValidPass1: 0.54, // -2pp from baseline

      /**
       * Minimum copyable rate
       * Baseline v2: 56.7%
       */
      copyableRate: 0.54, // -2pp from baseline

      /**
       * Maximum allowed review rate (friction metric)
       * Baseline v2: 50.0% (average across buckets)
       * Hard gate: can't increase friction
       */
      reviewRateMax: 0.55, // +5pp from baseline

      /**
       * Maximum P95 latency (ms)
       * Baseline v2: 10072ms
       */
      latencyP95Max: 12_000, // +20% overhead

      /**
       * Minimum patterns detected
       * Baseline v2: 10 patterns
       */
      patternsDetectedMin: 10,
    },

    /**
     * Dataset paths for evaluation
     */
    dataset: {
      path: "testdata/cases.jsonl",
      baseline: "eval/baseline-v2.json",
    },
  },
} as const;

/**
 * Type helper for accessing nested defaults
 */
export type Defaults = typeof DEFAULTS;
