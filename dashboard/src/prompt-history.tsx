import { Action, ActionPanel, Detail, List, showToast, Toast } from "@raycast/api";
import { getPromptById, getPromptHistory, formatTimestamp, clearHistory } from "./core/promptStorage";
import { Typography } from "./core/design/typography";
import type { PromptEntry } from "./core/promptStorage";
import React from "react";

export default function Command() {
  return (
    <List
      navigationTitle="Prompt History"
      actions={
        <ActionPanel>
          <Action
            title="Clear History"
            style={Action.Style.Destructive}
            shortcut={{ modifiers: ["cmd", "shift"], key: "d" }}
            onAction={async () => {
              await clearHistory();
              await showToast({
                style: Toast.Style.Success,
                title: "History cleared",
              });
            }}
          />
        </ActionPanel>
      }
    >
      <PromptHistoryList />
    </List>
  );
}

function PromptHistoryList() {
  const [entries, setEntries] = React.useState<PromptEntry[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    (async () => {
      try {
        const history = await getPromptHistory(20);
        setEntries(history);
      } catch (error) {
        console.error("[PromptHistory] Failed to load:", error);
        await showToast({
          style: Toast.Style.Failure,
          title: "Failed to load history",
          message: error instanceof Error ? error.message : String(error),
        });
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  if (isLoading) {
    return <List.Item.Detail markdown="## Loading..." isLoading={true} />;
  }

  if (entries.length === 0) {
    return (
      <List.EmptyView
        icon="📋"
        title="No Prompt History"
        description="Generate some prompts to see them here"
      />
    );
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
                  shortcut={{ modifiers: ["cmd"], key: "enter" }}
                  onAction={async () => {
                    const details = buildPromptDetail(entry);
                    // In a real implementation, you'd navigate to a detail view
                    // For now, just copy with metadata
                    const withMetadata = [
                      `# Improved Prompt`,
                      ``,
                      entry.prompt,
                      ``,
                      `---`,
                      `**Generated:** ${formatTimestamp(entry.timestamp)}`,
                      `**Engine:** ${entry.source === "dspy" ? "DSPy + Haiku" : "Ollama"}`,
                      entry.meta?.confidence ? `**Confidence:** ${Math.round(entry.meta.confidence)}%` : "",
                      entry.preset ? `**Preset:** ${entry.preset}` : "",
                    ]
                      .filter(Boolean)
                      .join("\n");

                    // Show in a toast for now (could be a detail view)
                    await showToast({
                      style: Toast.Style.Success,
                      title: "Prompt copied with metadata",
                      message: "Paste to view full details",
                    });
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

function buildPromptDetail(entry: PromptEntry): string {
  const sections: string[] = [];

  sections.push("## Improved Prompt");
  sections.push("", "```text", entry.prompt, "```");

  if (entry.meta?.clarifyingQuestions?.length || entry.meta?.assumptions?.length) {
    sections.push("", "---", "");

    if (entry.meta.clarifyingQuestions?.length) {
      sections.push("### Clarifying Questions", "");
      entry.meta.clarifyingQuestions.forEach((q) => {
        sections.push(`- ${q}`);
      });
    }

    if (entry.meta.assumptions?.length) {
      sections.push("", "### Assumptions", "");
      entry.meta.assumptions.forEach((a) => {
        sections.push(`- ${a}`);
      });
    }
  }

  sections.push("", "---", "");
  sections.push(`**Generated:** ${new Date(entry.timestamp).toLocaleString()}`);
  sections.push(`**Engine:** ${entry.source === "dspy" ? "DSPy + Haiku" : "Ollama"}`);
  sections.push(`**Input Length:** ${entry.inputLength} characters`);
  sections.push(`**Output Length:** ${entry.prompt.length} characters`);

  if (entry.meta?.confidence) {
    sections.push(`**Confidence:** ${Math.round(entry.meta.confidence)}%`);
  }

  if (entry.preset) {
    sections.push(`**Preset:** ${entry.preset}`);
  }

  return sections.join("\n");
}
