import { Action, ActionPanel, List } from "@raycast/api";
import { getPromptHistory, formatTimestamp, clearHistory } from "./core/promptStorage";
import { Typography } from "./core/design/typography";
import { ToastHelper } from "./core/design/toast";
import type { PromptEntry } from "./core/promptStorage";
import React from "react";

// History-specific loading stages (different from prompt improvement stages)
type HistoryLoadingStage = "idle" | "loading" | "success" | "error";

const HISTORY_STAGE_MESSAGES: Record<HistoryLoadingStage, string> = {
  idle: "",
  loading: "Loading history...",
  success: "Loaded",
  error: "Failed",
} as const;

export default function Command() {
  const [loadingStage, setLoadingStage] = React.useState<HistoryLoadingStage>("idle");

  return (
    <List
      navigationTitle={`Prompt History${
        loadingStage !== "idle" && loadingStage !== "success" ? ` — ${HISTORY_STAGE_MESSAGES[loadingStage]}` : ""
      }`}
      actions={
        <ActionPanel>
          <Action
            title="Clear History"
            style={Action.Style.Destructive}
            shortcut={{ modifiers: ["cmd", "shift"], key: "d" }}
            onAction={async () => {
              await clearHistory();
              await ToastHelper.success("History cleared");
            }}
          />
        </ActionPanel>
      }
    >
      <PromptHistoryList setLoadingStage={setLoadingStage} />
    </List>
  );
}

function PromptHistoryList({
  setLoadingStage,
}: {
  setLoadingStage: React.Dispatch<React.SetStateAction<HistoryLoadingStage>>;
}) {
  const [entries, setEntries] = React.useState<PromptEntry[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [loadingStage, setLoadingStageLocal] = React.useState<HistoryLoadingStage>("idle");

  React.useEffect(() => {
    (async () => {
      try {
        setLoadingStage("loading");
        setLoadingStageLocal("loading");
        const history = await getPromptHistory(20);
        setEntries(history);
        setLoadingStage("success");
        setLoadingStageLocal("success");
      } catch (error) {
        console.error("[PromptHistory] Failed to load:", error);
        setLoadingStage("error");
        setLoadingStageLocal("error");
        await ToastHelper.error("Failed to load history", error instanceof Error ? error.message : String(error));
      } finally {
        setIsLoading(false);
      }
    })();
  }, [setLoadingStage]);

  if (isLoading) {
    return (
      <List.Item.Detail
        markdown={`## ${HISTORY_STAGE_MESSAGES[loadingStage] || "Loading..."}${
          loadingStage !== "idle" ? `\n\n_${loadingStage}_` : ""
        }`}
        isLoading={true}
      />
    );
  }

  if (entries.length === 0) {
    return <List.EmptyView icon="📋" title="No Prompt History" description="Generate some prompts to see them here" />;
  }

  return (
    <>
      {entries.map((entry) => (
        <List.Item
          key={entry.id}
          title={entry.prompt.slice(0, 50) + (entry.prompt.length > 50 ? "..." : "")}
          subtitle={`${formatTimestamp(entry.timestamp)} • ${entry.inputLength} → ${entry.prompt.length} chars`}
          accessories={[
            {
              text: entry.source === "dspy" ? "DSPy" : "Ollama",
              icon: entry.source === "dspy" ? "⤒" : "○",
            },
            ...(entry.meta?.confidence
              ? [
                  {
                    text: `${Math.round(entry.meta.confidence)}%`,
                    icon: Typography.confidenceIcon(entry.meta.confidence),
                  },
                ]
              : []),
          ]}
          actions={
            <ActionPanel>
              <ActionPanel.Section title="Actions">
                <Action.CopyToClipboard
                  title="Copy Prompt"
                  content={entry.prompt}
                  shortcut={{ modifiers: ["cmd"], key: "c" }}
                />

                <Action
                  title="View Details"
                  shortcut={{ modifiers: ["cmd", "shift"], key: "v" }}
                  onAction={async () => {
                    // TODO: implement detail view navigation
                    await ToastHelper.success("Prompt copied with metadata", "Paste to view full details");
                  }}
                />
              </ActionPanel.Section>
            </ActionPanel>
          }
        />
      ))}
    </>
  );
}
