// dashboard/src/promptify-selected.tsx
import {
  Action,
  ActionPanel,
  Clipboard,
  Detail,
  showToast,
  Toast,
  getPreferenceValues,
} from "@raycast/api";
import { useState, useEffect } from "react";
import { getInput } from "./core/input/getInput";
import { improvePromptWithHybrid } from "./core/llm/improvePrompt";
import { handleBackendError, NoInputDetail } from "./core/errors/handlers";
import { logTtvMeasurement } from "./core/metrics/ttvLogger";
import { loadConfig } from "./core/config";

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

      try {
        // Get input (selection or clipboard)
        const input = await getInput();

        if (input.source === "none") {
          setError(<NoInputDetail />);
          setIsLoading(false);
          return;
        }

        // Show loading toast
        await showToast({
          style: Toast.Style.Animated,
          title: "Improving prompt...",
        });

        // Load config
        const configState = loadConfig();
        const config = configState.config;

        // Get preferences
        const preferences = getPreferenceValues<Preferences>();
        const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
        const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;
        const timeoutMs = Number.parseInt(preferences.timeoutMs || "30000", 10);

        // Call backend
        if (!dspyEnabled) {
          throw new Error("DSPy backend is disabled in preferences");
        }

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

        // Copy to clipboard
        await Clipboard.copy(response.improved_prompt);

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

        await showToast({
          style: Toast.Style.Success,
          title: "Prompt improved!",
          message: `TTV: ${ttv_ms}ms • Source: ${input.source}`,
        });
      } catch (e) {
        const errorDetail = handleBackendError(e, t0);
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
                `TTV: ${result.ttv_ms}ms\nSource: ${result.source}\nLength: ${result.prompt.length} chars`
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
