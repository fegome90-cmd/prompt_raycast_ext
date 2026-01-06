import { Action, ActionPanel, Clipboard, Detail, Form, getPreferenceValues } from "@raycast/api";
import { useState, useEffect } from "react";
import { improvePromptWithHybrid, improvePromptWithOllama } from "./core/llm/improvePrompt";
import { ollamaHealthCheck } from "./core/llm/ollamaClient";
import { loadConfig } from "./core/config";
import { getCustomPatternSync } from "./core/templates/pattern";
import { Typography } from "./core/design/typography";
import { ToastHelper } from "./core/design/toast";

type Preferences = {
  ollamaBaseUrl?: string;
  model?: string;
  fallbackModel?: string;
  preset?: "default" | "specific" | "structured" | "coding";
  timeoutMs?: string;
  dspyBaseUrl?: string;
  dspyEnabled?: boolean;
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

  // Header and main prompt in code block
  sections.push("## Improved Prompt", "", "```text", props.prompt, "```");

  // Metadata sections
  if (props.meta?.clarifyingQuestions?.length) {
    sections.push("", "", "### Clarifying Questions", "");
    props.meta.clarifyingQuestions.forEach((q, i) => {
      sections.push(`${i + 1}. ${q}`);
    });
  }

  if (props.meta?.assumptions?.length) {
    sections.push("", "", "### Assumptions", "");
    props.meta.assumptions.forEach((a, i) => {
      sections.push(`${i + 1}. ${a}`);
    });
  }

  // Stats for "Copy with stats" action
  const stats = [
    props.meta?.confidence !== undefined ? `Confidence: ${Typography.confidence(props.meta.confidence)}` : null,
    `Length: ${props.prompt.length} chars`,
    `Words: ${props.prompt.split(/\s+/).length} words`,
    `Source: ${props.source === "dspy" ? "DSPy + Haiku" : "Ollama"}`,
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
            text={props.source === "dspy" ? "DSPy + Haiku" : "Ollama"}
            icon={Typography.engine(props.source ?? "ollama")}
          />
        </Detail.Metadata>
      }
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Primary Actions">
            <Action
              title="Copy prompt"
              onAction={async () => {
                await Clipboard.copy(props.prompt);
                await ToastHelper.success("Copied", `${props.prompt.length} characters`);
              }}
              shortcut={{ modifiers: ["cmd"], key: "c" }}
            />

            <Action
              title="Try again"
              shortcut={{ modifiers: ["cmd", "shift"], key: "r" }}
              onAction={() => {
                props.onReset?.();
                ToastHelper.loading("Ready to improve again");
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Advanced">
            <Action
              title="Copy with stats"
              onAction={async () => {
                const withStats = [`# Improved Prompt`, "", props.prompt, "", "---", ...stats].join("\n");
                await Clipboard.copy(withStats);
                await ToastHelper.success("Copied with stats", "Includes metadata");
              }}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Settings">
            <Action.OpenInBrowser
              title="Open preferences"
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
  const placeholders = {
    default: "Paste your rough prompt here… (⌘I to improve)",
    specific: "What specific task should this prompt accomplish?",
    structured: "Paste your prompt - we'll add structure and clarity…",
    coding: "Describe what you want the code to do…",
  };

  return placeholders[preset || "structured"];
}

export default function Command() {
  const preferences = getPreferenceValues<Preferences>();

  // Load config and check safe mode
  const configState = loadConfig();
  const isInSafeMode = configState.safeMode;

  // Compute DSPy enabled state for use in JSX
  const dspyEnabled = preferences.dspyEnabled ?? configState.config.dspy.enabled;

  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<{
    prompt: string;
    meta?: { confidence?: number; clarifyingQuestions?: string[]; assumptions?: string[] };
    source?: "dspy" | "ollama";
  } | null>(null);

  // Show diagnostic toast if safe mode activated automatically
  const [safeModeToastShown, setSafeModeToastShown] = useState(false);

  useEffect(() => {
    if (isInSafeMode && !safeModeToastShown && configState.source === "defaults") {
      setSafeModeToastShown(true);
      ToastHelper.error("Invalid Configuration", "Using safe mode (defaults). Check logs for details.");
    }
  }, [isInSafeMode, safeModeToastShown, configState.source]);

  async function handleGenerateFinal(values: { inputText: string }) {
    const text = values.inputText.trim();
    if (!text.length) {
      await ToastHelper.error("Empty Input", "Paste or type some text first");
      return;
    }
    if (text.length < 5) {
      await ToastHelper.error("Input Too Short", "Please enter at least 5 characters");
      return;
    }

    setIsLoading(true);
    await ToastHelper.loading("Generating prompt…");
    try {
      // Use configuration (preferences override config defaults)
      const config = configState.config;

      // Use preferences or fall back to config defaults
      const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
      const model = preferences.model?.trim() || config.ollama.model;
      const fallbackModel = preferences.fallbackModel?.trim() || config.ollama.fallbackModel || config.ollama.model;
      const preset = preferences.preset ?? config.presets.default;
      const timeoutMs = parseTimeoutMs(preferences.timeoutMs, config.ollama.timeoutMs);
      const temperature = config.ollama.temperature ?? 0.1;
      const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
      const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;

      if (!dspyEnabled) {
        const health = await ollamaHealthCheck({ baseUrl, timeoutMs: Math.min(2_000, timeoutMs) });
        if (!health.ok) {
          await ToastHelper.error("Ollama is not reachable", health.error, `Check ${baseUrl}`);
          return;
        }
      }

      const result = dspyEnabled
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
              dspyTimeoutMs: config.dspy.timeoutMs,
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

      const finalPrompt = result.improved_prompt.trim();
      await Clipboard.copy(finalPrompt);
      await ToastHelper.success("Copied final prompt");
      setPreview({
        prompt: finalPrompt,
        meta: {
          confidence: result.confidence,
          clarifyingQuestions: result.clarifying_questions,
          assumptions: result.assumptions,
        },
        source: dspyEnabled ? "dspy" : "ollama",
      });
    } catch (e) {
      const config = configState.config;
      const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
      const model = preferences.model?.trim() || config.ollama.model;
      const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
      const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;
      const hint = dspyEnabled ? buildDSPyHint(e) : buildErrorHint(e);

      // Debug logging
      console.error("[Promptify] Error details:", {
        error: e instanceof Error ? e.message : String(e),
        preferencesModel: preferences.model,
        configModel: config.ollama.model,
        finalModel: model,
        dspyEnabled,
      });

      if (dspyEnabled) {
        await ToastHelper.error(
          "DSPy backend not available",
          e instanceof Error ? e.message : String(e),
          `${dspyBaseUrl}${hint ? ` — ${hint}` : ""}`
        );
        return;
      }

      await ToastHelper.error(
        "Prompt improvement failed",
        e instanceof Error ? e.message : String(e),
        `(${model} @ ${baseUrl})${hint ? ` — ${hint}` : ""}`
      );
    } finally {
      setIsLoading(false);
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
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Improve">
            <Action.SubmitForm
              title={isLoading ? "Improving…" : "Improve Prompt"}
              subtitle={`${dspyEnabled ? "DSPy ⤒ " : ""}${Typography.truncate(preferences.model || "Ollama", 20)}`}
              onSubmit={handleGenerateFinal}
              shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }}
              disabled={isLoading}
            />
            <Action
              title="Quick improve"
              subtitle="Use default settings"
              shortcut={{ modifiers: ["cmd"], key: "i" }}
              onAction={() => {
                if (inputText.trim()) {
                  handleGenerateFinal({ inputText });
                }
              }}
              disabled={isLoading || !inputText.trim()}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Edit">
            <Action
              title="Clear input"
              onAction={() => setInputText("")}
              shortcut={{ modifiers: ["cmd"], key: "backspace" }}
              style={Action.Style.Destructive}
              disabled={!inputText.trim() || isLoading}
            />
          </ActionPanel.Section>

          <ActionPanel.Section title="Settings">
            <Action.OpenInBrowser
              title="Open preferences"
              url="raycast://extensions/preferences/thomas.prompt-renderer-local"
              shortcut={{ modifiers: ["ctrl"], key: "," }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    >
      <Form.TextArea
        id="inputText"
        title="Prompt"
        placeholder={getPlaceholder(preferences.preset)}
        value={inputText}
        onChange={setInputText}
        disabled={isLoading}
        enableMarkdown={true}
      />
    </Form>
  );
}

function parseTimeoutMs(value: string | undefined, fallback: number): number {
  const n = Number.parseInt((value ?? "").trim(), 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function buildErrorHint(error: unknown): string | null {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();
  if (lower.includes("timed out")) return "try increasing timeout (ms)";
  if (
    lower.includes("failed calling ollama") ||
    lower.includes("connect") ||
    lower.includes("econnrefused") ||
    lower.includes("not reachable")
  )
    return "check `ollama serve` is running";
  if (lower.includes("model") && lower.includes("not found")) return "Pull the model first: `ollama pull <model>`";
  return null;
}

function buildDSPyHint(error: unknown): string | null {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();
  if (lower.includes("timed out")) return "try increasing timeout (ms)";
  if (lower.includes("connect") || lower.includes("econnrefused") || lower.includes("not reachable")) {
    return "check the DSPy backend is running";
  }
  return null;
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

    await ToastHelper.loading("Retrying with fallback model…", args.fallbackModel);

    return await improvePromptWithOllama({
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
