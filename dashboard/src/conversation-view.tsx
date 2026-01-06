import {
  List,
  Action,
  ActionPanel,
  Toast,
  showToast,
  Form,
  Clipboard,
  getPreferenceValues,
  popToRoot,
} from "@raycast/api";
import { useState, useEffect } from "react";
import { SessionManager } from "./core/conversation/SessionManager";
import { improvePromptWithWizard, continueWizard } from "./core/llm/improvePromptWithWizard";
import { type ImprovePromptPreset } from "./core/llm/improvePrompt";
import type { ChatSession } from "./core/conversation/types";

const DEFAULT_MODEL = "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M";

type Preferences = {
  wizardMode?: "auto" | "always" | "off";
  maxWizardTurns?: string;
  ollamaBaseUrl?: string;
  model?: string;
  dspyBaseUrl?: string;
  dspyTimeoutMs?: string;
  preset?: string;
};

const getConfig = (prefs: Preferences) => ({
  baseUrl: prefs.ollamaBaseUrl ?? "http://localhost:11434",
  model: prefs.model ?? DEFAULT_MODEL,
  dspyBaseUrl: prefs.dspyBaseUrl ?? "http://localhost:8000",
  dspyTimeoutMs: Number.parseInt(prefs.dspyTimeoutMs ?? "120000", 10),
  preset: prefs.preset ?? "structured",
});

export default function ConversationView() {
  const preferences = getPreferenceValues<Preferences>();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);

  const wizardEnabled = session?.wizard.enabled ?? false;
  const remainingTurns = session ? SessionManager.getRemainingTurns(session) : 0;
  const isWizardComplete = session?.wizard.resolved ?? true;

  useEffect(() => {
    SessionManager.cleanupOldSessions();
  }, []);

  const handleInitialSubmit = async (values: { input: string }) => {
    setIsLoading(true);

    try {
      const config = getConfig(preferences);
      const result = await improvePromptWithWizard({
        rawInput: values.input,
        preset: config.preset as ImprovePromptPreset,
        wizardMode: preferences.wizardMode ?? "auto",
        maxWizardTurns: Number.parseInt(preferences.maxWizardTurns ?? "2", 10),
        baseUrl: config.baseUrl,
        model: config.model,
        dspyBaseUrl: config.dspyBaseUrl,
        dspyTimeoutMs: config.dspyTimeoutMs,
      });

      setSession(result.session);
      setInputText("");

      if (result.isComplete) {
        await Clipboard.copy(result.session.messages[result.session.messages.length - 1].content);
        await showToast({ style: Toast.Style.Success, title: "Prompt copied to clipboard" });
      }
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Failed to process",
        message: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFollowUpSubmit = async (values: { response: string }) => {
    if (!session) return;

    setIsLoading(true);
    setShowFollowUpForm(false);

    try {
      const config = getConfig(preferences);
      const result = await continueWizard(session.id, values.response, {
        baseUrl: config.baseUrl,
        model: config.model,
        dspyBaseUrl: config.dspyBaseUrl,
        dspyTimeoutMs: config.dspyTimeoutMs,
        preset: config.preset as ImprovePromptPreset,
      });

      setSession(result.session);
      setInputText("");

      if (result.isComplete && result.prompt) {
        await Clipboard.copy(result.prompt);
        await showToast({ style: Toast.Style.Success, title: "Prompt copied to clipboard" });
      }
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Failed to continue",
        message: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipWizard = async () => {
    if (!session) return;

    setIsLoading(true);

    try {
      const config = getConfig(preferences);
      const result = await continueWizard(session.id, "", {
        baseUrl: config.baseUrl,
        model: config.model,
        dspyBaseUrl: config.dspyBaseUrl,
        dspyTimeoutMs: config.dspyTimeoutMs,
        preset: config.preset as ImprovePromptPreset,
      });

      setSession(result.session);

      if (result.prompt) {
        await Clipboard.copy(result.prompt);
        await showToast({ style: Toast.Style.Success, title: "Prompt copied to clipboard" });
      }
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Failed to skip wizard",
        message: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSession(null);
    setInputText("");
    setShowFollowUpForm(false);
  };

  // Show follow-up form
  if (session && showFollowUpForm && wizardEnabled && !isWizardComplete) {
    return (
      <Form
        isLoading={isLoading}
        actions={
          <ActionPanel>
            <Action.SubmitForm title="Send Response" onSubmit={handleFollowUpSubmit} />
            <Action title="Cancel" onAction={() => setShowFollowUpForm(false)} />
          </ActionPanel>
        }
      >
        <Form.TextArea
          id="response"
          title="Your Response"
          placeholder="Provide more details or leave empty to use current information..."
          value={inputText}
          onChange={setInputText}
        />
      </Form>
    );
  }

  // Initial form
  if (!session) {
    return (
      <Form
        isLoading={isLoading}
        actions={
          <ActionPanel>
            <Action.SubmitForm title="Start Conversation" onSubmit={handleInitialSubmit} />
          </ActionPanel>
        }
      >
        <Form.TextArea
          id="input"
          title="Describe your prompt idea"
          placeholder="e.g., I need a prompt for analyzing customer feedback..."
          value={inputText}
          onChange={setInputText}
        />
      </Form>
    );
  }

  // Conversation list view
  return (
    <List
      navigationTitle="Prompt Conversation"
      isLoading={isLoading}
      actions={
        <ActionPanel>
          <Action title="New Conversation" onAction={handleReset} shortcut={{ modifiers: ["cmd"], key: "n" }} />
          {wizardEnabled && !isWizardComplete && (
            <Action
              title="Skip Wizard"
              shortcut={{ modifiers: ["cmd"], key: "enter" }}
              onAction={handleSkipWizard}
            />
          )}
        </ActionPanel>
      }
    >
      {session.messages.map((msg) => (
        <List.Item
          key={msg.timestamp}
          icon={msg.role === "user" ? "👤" : "🤖"}
          title={msg.content.slice(0, 80) + (msg.content.length > 80 ? "..." : "")}
          subtitle={formatTimestamp(msg.timestamp)}
          accessories={[{ text: msg.metadata?.turnNumber ? `Turn ${msg.metadata.turnNumber}` : undefined }]}
        />
      ))}

      {wizardEnabled && !isWizardComplete && (
        <List.Item
          icon="🔮"
          title="Wizard Mode Active"
          subtitle={`${remainingTurns} turn${remainingTurns > 1 ? "s" : ""} remaining`}
          accessories={[{ text: "Press Enter to provide more details" }]}
          actions={
            <ActionPanel>
              <Action title="Provide Details" onAction={() => setShowFollowUpForm(true)} shortcut={{ modifiers: ["cmd"], key: "enter" }} />
              <Action title="Skip to Generate" onAction={handleSkipWizard} shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }} />
            </ActionPanel>
          }
        />
      )}

      {isWizardComplete && session.messages.length > 1 && (
        <List.Item
          icon="✅"
          title="Prompt Ready"
          subtitle="Click to copy and view details"
          actions={
            <ActionPanel>
              <Action.CopyToClipboard
                title="Copy Prompt"
                content={SessionManager.extractFinalPrompt(session) || ""}
              />
            </ActionPanel>
          }
        />
      )}
    </List>
  );
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs < 60000) return "Just now";
  if (diffMs < 3600000) {
    const mins = Math.floor(diffMs / 60000);
    return `${mins}m ago`;
  }
  return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}
