// dashboard/src/promptify-selected.tsx
import { Action, ActionPanel, Clipboard, Detail, getPreferenceValues } from "@raycast/api";
import { useState, useEffect } from "react";
import { getInput } from "./core/input/getInput";
import { improvePromptWithHybrid } from "./core/llm/improvePrompt";
import { handleBackendError, NoInputDetail } from "./core/errors/handlers";
import { logTtvMeasurement } from "./core/metrics/ttvLogger";
import { loadConfig } from "./core/config";
import { ToastHelper } from "./core/design/toast";

const LOG_PREFIX = "[PromptifySelected]";

type LoadingStage = "idle" | "validating" | "connecting" | "analyzing" | "improving" | "success" | "error";

const STAGE_MESSAGES = {
  idle: "",
  validating: "Validating input...",
  connecting: "Connecting to DSPy...",
  analyzing: "Analyzing prompt structure...",
  improving: "Applying few-shot learning...",
  success: "Complete!",
  error: "Failed",
} as const;

type Preferences = {
  dspyBaseUrl?: string;
  dspyEnabled?: boolean;
  timeoutMs?: string;
};

export default function Command() {
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStage, setLoadingStage] = useState<LoadingStage>("idle");
  const [result, setResult] = useState<{
    prompt: string;
    source: "selection" | "clipboard";
    ttv_ms: number;
  } | null>(null);
  const [error, setError] = useState<React.ReactNode>(null);

  useEffect(() => {
    (async () => {
      const t0 = Date.now();
      console.log(`${LOG_PREFIX} 🚀 Starting prompt improvement...`);

      try {
        // Stage 1: Validation
        setLoadingStage("validating");
        console.log(`${LOG_PREFIX} 📥 Getting input...`);
        const input = await getInput();

        if (input.source === "none") {
          console.log(`${LOG_PREFIX} ❌ No input detected`);
          setError(<NoInputDetail />);
          setIsLoading(false);
          setLoadingStage("idle");
          return;
        }

        console.log(`${LOG_PREFIX} ✅ Input received: ${input.source} (${input.text.length} chars)`);
        console.log(`${LOG_PREFIX} 📄 Input preview: "${input.text.substring(0, 100)}..."`);

        setIsLoading(true);

        // Stage 2: Connection
        setLoadingStage("connecting");
        await ToastHelper.loading("Improving prompt...");

        // Load config
        console.log(`${LOG_PREFIX} ⚙️ Loading configuration...`);
        const configState = loadConfig();
        const config = configState.config;
        console.log(
          `${LOG_PREFIX} ⚙️ Config loaded - DSPy baseUrl: ${config.dspy.baseUrl}, enabled: ${config.dspy.enabled}`,
        );

        // Get preferences
        const preferences = getPreferenceValues<Preferences>();
        const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
        const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;
        const timeoutMs = Number.parseInt(preferences.timeoutMs || "120000", 10);

        console.log(
          `${LOG_PREFIX} 🔧 Final config: dspyBaseUrl=${dspyBaseUrl}, dspyEnabled=${dspyEnabled}, timeoutMs=${timeoutMs}`,
        );

        // Call backend
        if (!dspyEnabled) {
          console.error(`${LOG_PREFIX} ❌ DSPy backend is disabled in preferences`);
          throw new Error("DSPy backend is disabled in preferences");
        }

        // Stage 3: Analysis
        setLoadingStage("analyzing");
        console.log(`${LOG_PREFIX} 🌐 Calling backend: ${dspyBaseUrl}/api/v1/improve-prompt`);

        // Stage 4: Improvement
        setLoadingStage("improving");
        const response = await improvePromptWithHybrid({
          rawInput: input.text,
          preset: "structured",
          options: {
            baseUrl: config.ollama.baseUrl,
            model: config.ollama.model,
            timeoutMs,
            dspyBaseUrl,
            dspyTimeoutMs: timeoutMs,
          },
          enableDSPyFallback: false, // Require DSPy backend
        });

        const t_copy = Date.now();
        const ttv_ms = t_copy - t0;

        console.log(`${LOG_PREFIX} ✅ Backend response received in ${ttv_ms}ms`);
        console.log(`${LOG_PREFIX} 📊 Output length: ${response.improved_prompt.length} chars`);

        // Copy to clipboard
        await Clipboard.copy(response.improved_prompt);
        console.log(`${LOG_PREFIX} 📋 Copied to clipboard`);

        // Log TTV (fire-and-forget)
        logTtvMeasurement({
          t0,
          t_copy,
          ttv_ms,
          source: input.source,
          output_length: response.improved_prompt.length,
          error: null,
        }).catch(() => {
          // Silent failure - don't block main flow
        });

        // Stage 5: Success
        setLoadingStage("success");
        setResult({
          prompt: response.improved_prompt,
          source: input.source,
          ttv_ms,
        });

        console.log(`${LOG_PREFIX} 🎉 Success! TTV: ${ttv_ms}ms, Source: ${input.source}`);
        await ToastHelper.success("Prompt improved!", `TTV: ${ttv_ms}ms • ${input.source}`);
      } catch (e) {
        setLoadingStage("error");
        const errorDetail = handleBackendError(e, t0);
        console.error(`${LOG_PREFIX} ❌ Error:`, e);
        setError(errorDetail);
        await ToastHelper.error("Failed to improve prompt", e instanceof Error ? e.message : String(e));
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  if (error) {
    return error as React.ReactElement;
  }

  if (result) {
    return (
      <Detail
        markdown={result.prompt}
        actions={
          <ActionPanel>
            <Action.CopyToClipboard
              title="Copy Prompt"
              content={result.prompt}
              shortcut={{ modifiers: ["cmd"], key: "c" }}
            />
            <Action.OpenInBrowser
              title="Copy Stats"
              url={`data:text/plain,${encodeURIComponent(
                `TTV: ${result.ttv_ms}ms\nSource: ${result.source}\nLength: ${result.prompt.length} chars`,
              )}`}
            />
          </ActionPanel>
        }
        metadata={
          <Detail.Metadata>
            <Detail.Metadata.Label title="TTV" text={`${result.ttv_ms}ms`} />
            <Detail.Metadata.Label title="Source" text={result.source} />
            <Detail.Metadata.Label title="Length" text={`${result.prompt.length} chars`} />
          </Detail.Metadata>
        }
      />
    );
  }

  return (
    <Detail
      markdown={`## ${STAGE_MESSAGES[loadingStage] || "Loading..."}${
        loadingStage !== "idle" ? `\n\n_${loadingStage}_` : ""
      }`}
      isLoading={isLoading}
    />
  );
}
