// dashboard/src/promptify-selected.tsx
import { Action, ActionPanel, Clipboard, Detail, showToast, Toast, getPreferenceValues } from "@raycast/api";
import { useState, useEffect } from "react";
import { getInput } from "./core/input/getInput";
import { improvePromptWithHybrid } from "./core/llm/improvePrompt";
import { handleBackendError, NoInputDetail } from "./core/errors/handlers";
import { logTtvMeasurement } from "./core/metrics/ttvLogger";
import { loadConfig } from "./core/config";

const LOG_PREFIX = "[PromptifySelected]";

type Preferences = {
  dspyBaseUrl?: string;
  dspyEnabled?: boolean;
  timeoutMs?: string;
};

export default function Command() {
  const [isLoading, setIsLoading] = useState(true);
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
        // Get input (selection or clipboard)
        console.log(`${LOG_PREFIX} 📥 Getting input...`);
        const input = await getInput();

        if (input.source === "none") {
          console.log(`${LOG_PREFIX} ❌ No input detected`);
          setError(<NoInputDetail />);
          setIsLoading(false);
          return;
        }

        console.log(`${LOG_PREFIX} ✅ Input received: ${input.source} (${input.text.length} chars)`);
        console.log(`${LOG_PREFIX} 📄 Input preview: "${input.text.substring(0, 100)}..."`);

        // Show loading toast
        await showToast({
          style: Toast.Style.Animated,
          title: "Improving prompt...",
        });

        // Load config
        console.log(`${LOG_PREFIX} ⚙️ Loading configuration...`);
        const configState = loadConfig();
        const config = configState.config;
        console.log(`${LOG_PREFIX} ⚙️ Config loaded - DSPy baseUrl: ${config.dspy.baseUrl}, enabled: ${config.dspy.enabled}`);

        // Get preferences
        const preferences = getPreferenceValues<Preferences>();
        const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
        const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;
        const timeoutMs = Number.parseInt(preferences.timeoutMs || "120000", 10);

        console.log(`${LOG_PREFIX} 🔧 Final config: dspyBaseUrl=${dspyBaseUrl}, dspyEnabled=${dspyEnabled}, timeoutMs=${timeoutMs}`);

        // Call backend
        if (!dspyEnabled) {
          console.error(`${LOG_PREFIX} ❌ DSPy backend is disabled in preferences`);
          throw new Error("DSPy backend is disabled in preferences");
        }

        console.log(`${LOG_PREFIX} 🌐 Calling backend: ${dspyBaseUrl}/api/v1/improve-prompt`);
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

        // Set result
        setResult({
          prompt: response.improved_prompt,
          source: input.source,
          ttv_ms,
        });

        console.log(`${LOG_PREFIX} 🎉 Success! TTV: ${ttv_ms}ms, Source: ${input.source}`);
        await showToast({
          style: Toast.Style.Success,
          title: "Prompt improved!",
          message: `TTV: ${ttv_ms}ms • Source: ${input.source}`,
        });
      } catch (e) {
        const errorDetail = handleBackendError(e, t0);
        console.error(`${LOG_PREFIX} ❌ Error:`, e);
        setError(errorDetail);
        await showToast({
          style: Toast.Style.Failure,
          title: "Failed to improve prompt",
        });
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

  return <Detail markdown="## Loading..." isLoading={isLoading} />;
}
