import { Action, ActionPanel, Clipboard, Detail, Form, Toast, getPreferenceValues, showToast } from "@raycast/api";
import { useState } from "react";
import { improvePromptWithOllama } from "./core/llm/improvePrompt";
import { ollamaHealthCheck } from "./core/llm/ollamaClient";
import { loadConfig } from "./core/config";

type Preferences = {
  ollamaBaseUrl?: string;
  model?: string;
  fallbackModel?: string;
  preset?: "default" | "specific" | "structured" | "coding";
  timeoutMs?: string;
};

function PromptPreview(props: {
  prompt: string;
  meta?: {
    confidence?: number;
    clarifyingQuestions?: string[];
    assumptions?: string[];
  };
}) {
  const metaLines: string[] = [];
  if (props.meta?.confidence !== undefined) metaLines.push(`**Confidence:** ${props.meta.confidence}`);
  if (props.meta?.clarifyingQuestions?.length) {
    metaLines.push("", "**Clarifying Questions:**", ...props.meta.clarifyingQuestions.map((q) => `- ${q}`));
  }
  if (props.meta?.assumptions?.length) {
    metaLines.push("", "**Assumptions:**", ...props.meta.assumptions.map((a) => `- ${a}`));
  }

  return (
    <Detail
      markdown={["```text", props.prompt, "```", metaLines.join("\n")].filter(Boolean).join("\n")}
      actions={
        <ActionPanel>
          <Action
            title="Copy Prompt"
            onAction={async () => {
              await Clipboard.copy(props.prompt);
              await showToast({ style: Toast.Style.Success, title: "Copied prompt" });
            }}
          />
        </ActionPanel>
      }
    />
  );
}

export default function Command() {
  const preferences = getPreferenceValues<Preferences>();

  // Load config and check safe mode
  const configState = loadConfig();
  const isInSafeMode = configState.safeMode;

  const [inputText, setInputText] = useState("");
  const [preview, setPreview] = useState<{
    prompt: string;
    meta?: { confidence?: number; clarifyingQuestions?: string[]; assumptions?: string[] };
  } | null>(null);

  // Show diagnostic toast if safe mode activated automatically
  const [safeModeToastShown, setSafeModeToastShown] = useState(false);
  if (isInSafeMode && !safeModeToastShown && configState.source === "defaults") {
    setSafeModeToastShown(true);
    showToast({
      style: Toast.Style.Failure,
      title: "Invalid Configuration",
      message: "Using safe mode (defaults). Check logs for details.",
    });
  }

  async function handleGenerateFinal(values: { inputText: string }) {
    const text = values.inputText.trim();
    if (!text.length) {
      await showToast({ style: Toast.Style.Failure, title: "Paste or type some text first" });
      return;
    }

    await showToast({ style: Toast.Style.Animated, title: "Generating with Ollama…" });
    try {
      // Use configuration (preferences override config defaults)
      const config = configState.config;

      // Use preferences or fall back to config defaults
      const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
      const model = preferences.model?.trim() || config.ollama.model;
      const fallbackModel = preferences.fallbackModel?.trim() || config.ollama.fallbackModel || config.ollama.model;
      const preset = preferences.preset ?? config.presets.default;
      const timeoutMs = parseTimeoutMs(preferences.timeoutMs, config.ollama.timeoutMs);

      const health = await ollamaHealthCheck({ baseUrl, timeoutMs: Math.min(2_000, timeoutMs) });
      if (!health.ok) {
        await showToast({
          style: Toast.Style.Failure,
          title: "Ollama is not reachable",
          message: `${baseUrl} (${health.error})`,
        });
        return;
      }

      const result = await runWithModelFallback({
        baseUrl,
        model,
        fallbackModel,
        timeoutMs,
        rawInput: text,
        preset,
      });

      const finalPrompt = result.improved_prompt.trim();
      await Clipboard.copy(finalPrompt);
      await showToast({ style: Toast.Style.Success, title: "Copied final prompt" });
      setPreview({
        prompt: finalPrompt,
        meta: {
          confidence: result.confidence,
          clarifyingQuestions: result.clarifying_questions,
          assumptions: result.assumptions,
        },
      });
    } catch (e) {
      const baseUrl = preferences.ollamaBaseUrl?.trim() || "http://localhost:11434";
      const model = preferences.model?.trim() || "qwen3-coder:30b";
      const hint = buildErrorHint(e);
      await showToast({
        style: Toast.Style.Failure,
        title: "Ollama failed",
        message: `${e instanceof Error ? e.message : String(e)} (${model} @ ${baseUrl})${hint ? ` — ${hint}` : ""}`,
      });
    }
  }

  if (preview) {
    return <PromptPreview prompt={preview.prompt} meta={preview.meta} />;
  }

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Improve Prompt (Ollama)"
            onSubmit={handleGenerateFinal}
            shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }}
          />
          <Action title="Clear" onAction={() => setInputText("")} shortcut={{ modifiers: ["cmd"], key: "backspace" }} />
        </ActionPanel>
      }
    >
      <Form.TextArea
        id="inputText"
        title="Prompt"
        placeholder="Paste your rough prompt here… (⌘⇧↵ to improve)"
        value={inputText}
        onChange={setInputText}
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
  if (lower.includes("timed out")) return "Try increasing Timeout (ms)";
  if (
    lower.includes("failed calling ollama") ||
    lower.includes("connect") ||
    lower.includes("econnrefused") ||
    lower.includes("not reachable")
  )
    return "Check `ollama serve` is running";
  if (lower.includes("model") && lower.includes("not found")) return "Pull the model first: `ollama pull <model>`";
  return null;
}

async function runWithModelFallback(args: {
  baseUrl: string;
  model: string;
  fallbackModel: string;
  timeoutMs: number;
  rawInput: string;
  preset: "default" | "specific" | "structured" | "coding";
}) {
  try {
    return await improvePromptWithOllama({
      rawInput: args.rawInput,
      preset: args.preset,
      options: { baseUrl: args.baseUrl, model: args.model, timeoutMs: args.timeoutMs },
    });
  } catch (e) {
    if (!args.fallbackModel || args.fallbackModel === args.model) throw e;
    if (!shouldTryFallback(e)) throw e;

    await showToast({
      style: Toast.Style.Animated,
      title: "Retrying with fallback model…",
      message: args.fallbackModel,
    });

    return await improvePromptWithOllama({
      rawInput: args.rawInput,
      preset: args.preset,
      options: { baseUrl: args.baseUrl, model: args.fallbackModel, timeoutMs: args.timeoutMs },
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
