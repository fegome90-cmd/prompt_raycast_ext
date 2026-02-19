import { Action, ActionPanel, Clipboard, Detail, Form, getPreferenceValues } from "@raycast/api";
import { useState, useEffect } from "react";
import { improvePromptWithHybrid, improvePromptWithOllama } from "./core/llm/improvePrompt";
import { ollamaHealthCheck } from "./core/llm/ollamaClient";
import { createDSPyClient } from "./core/llm/dspyPromptImprover";
import { loadConfig } from "./core/config";
import { getCustomPatternSync } from "./core/templates/pattern";
import { Typography } from "./core/design/typography";
import { ToastHelper } from "./core/design/toast";
import { savePrompt, formatTimestamp } from "./core/promptStorage";
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";
import { buildErrorHint } from "./core/errors/hints";

// Engine display names (used in metadata)
const ENGINE_NAMES = {
  dspy: "DSPy + Haiku",
  ollama: "Ollama",
} as const;

// Preset placeholders for input textarea
const PLACEHOLDERS = {
  default: "Paste your rough prompt here… (⌘I to improve)",
  specific: "What specific task should this prompt accomplish?",
  structured: "Paste your prompt - we'll add structure and clarity…",
  coding: "Describe what you want the code to do…",
} as const;

// Logging prefixes for consistent filtering in Console.app
const LOG_PREFIX = "[PromptifyQuick]";
const FALLBACK_PREFIX = "[Fallback]";

// Backend status for health check indicator
type BackendStatus = "checking" | "healthy" | "unavailable";

const BACKEND_STATUS_DISPLAY = {
  checking: "⚪ Checking backend...",
  healthy: "🟢 Backend ready",
  unavailable: "🔴 Backend offline",
} as const;

type Preferences = {
  ollamaBaseUrl?: string;
  model?: string;
  fallbackModel?: string;
  preset?: "default" | "specific" | "structured" | "coding";
  timeoutMs?: string;
  dspyBaseUrl?: string;
  executionMode?: "legacy" | "nlac" | "ollama";
};

function PromptPreview(props: {
  prompt: string;
  meta?: {
    confidence?: number;
    clarifyingQuestions?: string[];
    assumptions?: string[];
  };
  source?: "dspy" | "ollama";
  onReset?: () => void;
}) {
  // Build markdown content with better formatting
  const sections: string[] = [];

  // Header
  sections.push("## Improved Prompt");

  // Metadata line: source + confidence (Apple-style minimal)
  if (props.meta?.confidence || props.source) {
    const metaLine = [
      props.source === "dspy" ? `⤒ ${ENGINE_NAMES.dspy}` : `○ ${ENGINE_NAMES.ollama}`,
      props.meta?.confidence ? `${Math.round(props.meta.confidence)}% confidence` : null,
    ]
      .filter(Boolean)
      .join(" • ");

    sections.push("", `*${metaLine}*`);
  }

  // Main prompt in code block
  sections.push("```text", props.prompt, "```");

  // Metadata sections
  if (props.meta?.clarifyingQuestions?.length) {
    sections.push("", "### Clarifying Questions", "");
    props.meta.clarifyingQuestions.forEach((q) => {
      sections.push(`- ${q}`);
    });
  }

  if (props.meta?.assumptions?.length) {
    sections.push("", "### Assumptions", "");
    props.meta.assumptions.forEach((a) => {
      sections.push(`- ${a}`);
    });
  }

  // Visual separator at end
  const hasMetadataSections = props.meta?.clarifyingQuestions?.length || props.meta?.assumptions?.length;
  if (hasMetadataSections) {
    sections.push("", "---", "");
  }

  // Stats for "Copy with stats" action
  const stats = [
    props.meta?.confidence !== undefined ? `Confidence: ${Typography.confidence(props.meta.confidence)}` : null,
    `Length: ${props.prompt.length} chars`,
    `Words: ${props.prompt.split(/\s+/).length} words`,
    `Source: ${ENGINE_NAMES[props.source ?? "ollama"]}`,
  ].filter(Boolean);

  return (
    <Detail
      markdown={sections.join("\n")}
      metadata={
        <Detail.Metadata>
          {/* Group 1: Quality Metrics (measures prompt quality) */}
          {props.meta?.confidence !== undefined && (
            <Detail.Metadata.Label
              title="Confidence"
              text={`${Math.round(props.meta.confidence)}%`}
              icon={Typography.confidenceIcon(props.meta.confidence)}
            />
          )}

          {/* Group 2: Prompt Metadata (content about the prompt) */}
          <Detail.Metadata.Separator />

          {props.meta?.clarifyingQuestions && props.meta.clarifyingQuestions.length > 0 && (
            <Detail.Metadata.Label
              title="Questions"
              text={Typography.count("Questions", props.meta.clarifyingQuestions.length)}
            />
          )}

          {props.meta?.assumptions && props.meta.assumptions.length > 0 && (
            <Detail.Metadata.Label
              title="Assumptions"
              text={Typography.count("Assumptions", props.meta.assumptions.length)}
            />
          )}

          {/* Group 3: Technical Stats (implementation details) */}
          <Detail.Metadata.Separator />

          <Detail.Metadata.Label
            title="Length"
            text={`${props.prompt.length} chars`}
            icon={Typography.countSymbol("Characters")}
          />

          <Detail.Metadata.Label
            title="Words"
            text={`${props.prompt.split(/\s+/).length}`}
            icon={Typography.countSymbol("Words")}
          />

          <Detail.Metadata.Label
            title="Engine"
            text={ENGINE_NAMES[props.source ?? "ollama"]}
            icon={Typography.engine(props.source ?? "ollama")}
          />
        </Detail.Metadata>
      }
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Primary Actions">
            <Action
              title="Copy Prompt"
              onAction={async () => {
                await Clipboard.copy(props.prompt);
                await ToastHelper.success("Copied", `${props.prompt.length} characters`);
              }}
              shortcut={{ modifiers: ["cmd"], key: "c" }}
            />

            <Action
              title="Try Again"
              shortcut={{ modifiers: ["cmd", "shift"], key: "r" }}
              onAction={() => {
                props.onReset?.();
                ToastHelper.loading("Ready to improve again");
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Advanced">
            <Action
              title="Copy with Stats"
              onAction={async () => {
                const withStats = [`# Improved Prompt`, "", props.prompt, "", "---", ...stats].join("\n");
                await Clipboard.copy(withStats);
                await ToastHelper.success("Copied with stats", "Includes metadata");
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Settings">
            <Action.OpenInBrowser
              title="Open Preferences"
              url="raycast://extensions/preferences/thomas.prompt-renderer-local"
              shortcut={{ modifiers: ["ctrl"], key: "," }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    />
  );
}

function getPlaceholder(preset?: "default" | "specific" | "structured" | "coding"): string {
  return PLACEHOLDERS[preset || "structured"];
}

// type LoadingStage = "validating" | "connecting" | "processing" | "finalizing";

export default function Command() {
  const preferences = getPreferenceValues<Preferences>();

  // Load config and check safe mode
  const configState = loadConfig();
  const isInSafeMode = configState.safeMode;

  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<LoadingStage>("idle");
  const [preview, setPreview] = useState<{
    prompt: string;
    meta?: { confidence?: number; clarifyingQuestions?: string[]; assumptions?: string[] };
    source?: "dspy" | "ollama";
  } | null>(null);

  // Backend health check status
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");

  // Show diagnostic toast if safe mode activated automatically
  const [safeModeToastShown, setSafeModeToastShown] = useState(false);

  // Health check on component load (only for backend modes)
  useEffect(() => {
    const checkHealth = async () => {
      const executionMode = preferences.executionMode ?? "legacy";
      const useBackend = executionMode !== "ollama";

      // Only check health if using backend (legacy or nlac mode)
      if (!useBackend) {
        setBackendStatus("healthy"); // Ollama mode doesn't need backend
        return;
      }

      try {
        const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || configState.config.dspy.baseUrl;
        const client = createDSPyClient({ baseUrl: dspyBaseUrl, timeoutMs: 3000 });
        await client.healthCheck();
        setBackendStatus("healthy");
      } catch (error) {
        console.error(`${LOG_PREFIX} Health check failed:`, {
          error: error instanceof Error ? error.message : String(error),
          dspyBaseUrl: preferences.dspyBaseUrl?.trim() || configState.config.dspy.baseUrl,
        });
        setBackendStatus("unavailable");
      }
    };

    checkHealth();
  }, []);

  useEffect(() => {
    if (isInSafeMode && !safeModeToastShown && configState.source === "defaults") {
      setSafeModeToastShown(true);
      ToastHelper.error("Invalid Configuration", "Using safe mode (defaults). Check logs for details.");
    }
  }, [isInSafeMode, safeModeToastShown, configState.source]);

  async function handleGenerateFinal(values: { inputText: string }) {
    console.log(`${LOG_PREFIX} 🚀 Starting prompt improvement (manual input)...`);
    const text = values.inputText.trim();

    // Stage 1: Validation
    setLoadingStage("validating");
    if (!text.length) {
      await ToastHelper.error("Empty Input", "Paste or type some text first");
      setLoadingStage("idle");
      return;
    }
    if (text.length < 5) {
      await ToastHelper.error("Input Too Short", "Please enter at least 5 characters");
      setLoadingStage("idle");
      return;
    }

    setIsLoading(true);

    try {
      const config = configState.config;
      const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
      const model = preferences.model?.trim() || config.ollama.model;
      const fallbackModel = preferences.fallbackModel?.trim() || config.ollama.fallbackModel || config.ollama.model;
      const preset = preferences.preset ?? config.presets.default;
      const timeoutMs = parseTimeoutMs(preferences.timeoutMs, config.ollama.timeoutMs);
      const temperature = config.ollama.temperature ?? 0.1;
      const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
      const executionMode = preferences.executionMode ?? "legacy";
      const useBackend = executionMode !== "ollama"; // legacy or nlac requires backend

      // Stage 2: Connection
      setLoadingStage("connecting");
      console.log(`${LOG_PREFIX} 🔌 Connecting to ${useBackend ? "backend" : "Ollama"}...`);

      // Stage 3: Analysis
      setLoadingStage("analyzing");
      console.log(`${LOG_PREFIX} 🔍 Analyzing prompt structure and complexity...`);

      // Progress happens automatically - Form.isLoading shows native progress bar
      if (!useBackend) {
        const health = await ollamaHealthCheck({ baseUrl, timeoutMs: Math.min(2_000, timeoutMs) });
        console.log(`${LOG_PREFIX} 🏥 Ollama health check result: ${health.ok ? "OK" : `FAILED - ${health.error}`}`);
        if (!health.ok) {
          setLoadingStage("error");
          await ToastHelper.error("Ollama is not reachable", health.error);
          setLoadingStage("idle");
          return;
        }
      }

      // ⚡ INVARIANT: Frontend timeout synchronization with DSPy backend
      //
      // The timeoutMs variable (from preferences.timeoutMs) MUST be used for BOTH:
      // - options.timeoutMs (Ollama/local LM timeout)
      // - options.dspyTimeoutMs (DSPy backend timeout - forwards to Anthropic Haiku)
      //
      // Previous bug (2025-01-05):
      // - Used config.dspy.timeoutMs (30s) for dspyTimeoutMs
      // - Frontend aborted at 28s with AbortError before Haiku completed (~40s)
      // - Fix: Use preferences.timeoutMs (120s) for BOTH timeout values
      //
      // See defaults.ts:58-80 for CRITICAL comment about 3-layer synchronization
      //
      // ⚡ DO NOT use config.dspy.timeoutMs here - it's a fallback default only
      // ⚡ DO NOT use different values for timeoutMs and dspyTimeoutMs

      console.log(
        `${LOG_PREFIX} 🌐 Using ${useBackend ? `${executionMode} backend` : "Ollama"} path ${
          useBackend ? `(dspyBaseUrl: ${dspyBaseUrl})` : `(model: ${model})`
        }`,
      );

      // Stage 4: Improvement
      setLoadingStage("improving");
      console.log(`${LOG_PREFIX} ⚙️ Generating improved prompt with ${useBackend ? executionMode : "Ollama"}...`);

      const result = useBackend
        ? await improvePromptWithHybrid({
            rawInput: text,
            preset,
            options: {
              baseUrl,
              model,
              timeoutMs,
              temperature,
              systemPattern: getCustomPatternSync(),
              dspyBaseUrl,
              dspyTimeoutMs: timeoutMs, // Use same timeout from preferences, not config.dspy.timeoutMs
              mode: (useBackend ? executionMode : undefined) as "legacy" | "nlac" | undefined, // legacy or nlac when using backend
            },
            enableDSPyFallback: false,
          })
        : await runWithModelFallback({
            baseUrl,
            model,
            fallbackModel,
            timeoutMs,
            temperature,
            rawInput: text,
            preset,
            systemPattern: getCustomPatternSync(),
          });

      // Stage 5: Finalizing
      setLoadingStage("success");
      console.log(`${LOG_PREFIX} 🎨 Finalizing result and copying to clipboard...`);

      const finalPrompt = result.improved_prompt.trim();
      await Clipboard.copy(finalPrompt);

      // Save to local history for persistence
      await savePrompt({
        prompt: finalPrompt,
        meta: {
          confidence: result.confidence,
          clarifyingQuestions: result.clarifying_questions,
          assumptions: result.assumptions,
        },
        source: useBackend ? "dspy" : "ollama",
        inputLength: text.length,
        preset,
      }).catch((error) => {
        console.error(`${LOG_PREFIX} ❌ Failed to save prompt:`, error);
      });

      await ToastHelper.success("Copied to clipboard", `${finalPrompt.length} characters • Saved to history`);

      // Clear loading stage on success
      setLoadingStage("idle");
      console.log(
        `${LOG_PREFIX} ✅ Prompt improved successfully (${finalPrompt.length} chars, source: ${
          useBackend ? executionMode : "Ollama"
        })`,
      );

      setPreview({
        prompt: finalPrompt,
        meta: {
          confidence: result.confidence,
          clarifyingQuestions: result.clarifying_questions,
          assumptions: result.assumptions,
        },
        source: useBackend ? "dspy" : "ollama",
      });
    } catch (e) {
      // Note: setLoadingStage("error") is intentionally NOT called here
      // because the finally block always resets to "idle". The toast
      // provides the error feedback to the user.
      const config = configState.config;
      const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
      const model = preferences.model?.trim() || config.ollama.model;
      const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
      const executionMode = preferences.executionMode ?? "legacy";
      const useBackend = executionMode !== "ollama";
      const hint = buildErrorHint(e, useBackend ? (executionMode === "nlac" ? "nlac" : "dspy") : undefined);

      // Debug logging
      console.error(`${LOG_PREFIX} ❌ Error details:`, {
        error: e instanceof Error ? e.message : String(e),
        preferencesModel: preferences.model,
        configModel: config.ollama.model,
        finalModel: model,
        executionMode,
      });

      if (useBackend) {
        await ToastHelper.error(
          `${executionMode === "nlac" ? "NLaC" : "DSPy"} backend not available`,
          e instanceof Error ? e.message : String(e),
          `${dspyBaseUrl}${hint ? ` — ${hint}` : ""}`,
        );
      } else {
        await ToastHelper.error(
          "Prompt improvement failed",
          e instanceof Error ? e.message : String(e),
          `(${model} @ ${baseUrl})${hint ? ` — ${hint}` : ""}`,
        );
      }
    } finally {
      setIsLoading(false);
      // Clear loading stage on completion (success or error)
      setLoadingStage("idle");
    }
  }

  if (preview) {
    return (
      <PromptPreview
        prompt={preview.prompt}
        meta={preview.meta}
        source={preview.source}
        onReset={() => setPreview(null)}
      />
    );
  }

  return (
    <Form
      isLoading={isLoading}
      navigationTitle={`Prompt Improver${loadingStage !== "idle" ? ` — ${STAGE_MESSAGES[loadingStage]}` : ""}`}
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Improve">
            <Action.SubmitForm
              title={isLoading ? "Improving…" : "Improve Prompt"}
              onSubmit={handleGenerateFinal}
              shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }}
            />
            <Action
              title="Quick Improve"
              shortcut={{ modifiers: ["cmd"], key: "i" }}
              onAction={() => {
                if (inputText.trim() && !isLoading) {
                  handleGenerateFinal({ inputText });
                }
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Edit">
            <Action
              title="Clear Input"
              onAction={() => {
                if (!isLoading) {
                  setInputText("");
                }
              }}
              shortcut={{ modifiers: ["cmd"], key: "backspace" }}
              style={Action.Style.Destructive}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Settings">
            <Action.OpenInBrowser
              title="Open Preferences"
              url="raycast://extensions/preferences/thomas.prompt-renderer-local"
              shortcut={{ modifiers: ["ctrl"], key: "," }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    >
      {loadingStage !== "idle" && <Form.Description text={`${STAGE_MESSAGES[loadingStage]}`} />}
      {loadingStage === "idle" && backendStatus !== "healthy" && (
        <Form.Description text={BACKEND_STATUS_DISPLAY[backendStatus]} />
      )}
      <Form.TextArea
        id="inputText"
        title="Prompt"
        placeholder={getPlaceholder(preferences.preset)}
        value={inputText}
        onChange={setInputText}
        enableMarkdown={true}
      />
    </Form>
  );
}

function parseTimeoutMs(value: string | undefined, fallback: number): number {
  const n = Number.parseInt((value ?? "").trim(), 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

async function runWithModelFallback(args: {
  baseUrl: string;
  model: string;
  fallbackModel: string;
  timeoutMs: number;
  temperature: number;
  rawInput: string;
  preset: "default" | "specific" | "structured" | "coding";
  systemPattern?: string;
}) {
  try {
    return await improvePromptWithOllama({
      rawInput: args.rawInput,
      preset: args.preset,
      options: {
        baseUrl: args.baseUrl,
        model: args.model,
        timeoutMs: args.timeoutMs,
        temperature: args.temperature,
        systemPattern: args.systemPattern,
      },
    });
  } catch (e) {
    if (!args.fallbackModel || args.fallbackModel === args.model) throw e;
    if (!shouldTryFallback(e)) throw e;

    console.log(`${FALLBACK_PREFIX} ⚠️ Primary model (${args.model}) failed, attempting fallback...`);
    console.log(`${FALLBACK_PREFIX} 🔄 Retrying with model: ${args.fallbackModel}`);
    await ToastHelper.loading("Retrying with fallback model…", args.fallbackModel);

    const result = await improvePromptWithOllama({
      rawInput: args.rawInput,
      preset: args.preset,
      options: {
        baseUrl: args.baseUrl,
        model: args.fallbackModel,
        timeoutMs: args.timeoutMs,
        temperature: args.temperature,
        systemPattern: args.systemPattern,
      },
    });

    console.log(`${FALLBACK_PREFIX} ✅ Fallback successful with ${args.fallbackModel}`);
    return result;
  }
}

function shouldTryFallback(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();
  // Typical Ollama/model issues where a retry with another model makes sense.
  if (lower.includes("model") && lower.includes("not found")) return true;
  if (lower.includes("pull")) return true;
  if (lower.includes("404")) return true;
  if (lower.includes("ollama error") && lower.includes("model")) return true;
  // Output/format issues (some models ignore schema or return unusable outputs).
  if (lower.includes("non-json")) return true;
  if (lower.includes("validation")) return true;
  if (lower.includes("zod")) return true;
  if (lower.includes("improved_prompt")) return true;
  if (lower.includes("contains meta content")) return true;
  if (lower.includes("starts with meta instructions")) return true;
  if (lower.includes("describes creating a prompt")) return true;
  return false;
}
