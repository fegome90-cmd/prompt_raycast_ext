import {
  List,
  Action,
  ActionPanel,
  Form,
  Clipboard,
  getPreferenceValues,
} from "@raycast/api";
import { useState, useEffect } from "react";
import { SessionManager } from "./core/conversation/SessionManager";
import { improvePromptWithWizard, continueWizard } from "./core/llm/improvePromptWithWizard";
import { type ImprovePromptPreset } from "./core/llm/improvePrompt";
import type { ChatSession } from "./core/conversation/types";
import { tokens } from "./core/design/tokens";
import { Typography } from "./core/design/typography";
import { ToastHelper } from "./core/design/toast";
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";

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
  const [loadingStage, setLoadingStage] = useState<LoadingStage>("idle");
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);

  const wizardEnabled = session?.wizard.enabled ?? false;
  const canOfferSkip = session?.wizard.canOfferSkip ?? false;
  const remainingTurns = session ? SessionManager.getRemainingTurns(session) : 0;
  const isWizardComplete = session?.wizard.resolved ?? true;

  useEffect(() => {
    SessionManager.cleanupOldSessions();
  }, []);

  const handleInitialSubmit = async (values: { input: string }) => {
    // Stage 1: Validation
    setLoadingStage("validating");

    if (!values.input?.trim() || values.input.length < 5) {
      await ToastHelper.error("Input too short", "Please provide at least 5 characters");
      setLoadingStage("idle");
      return;
    }

    setIsLoading(true);

    try {
      // Stage 2: Connection
      setLoadingStage("connecting");

      const config = getConfig(preferences);

      // Stage 3: Analysis
      setLoadingStage("analyzing");

      // Stage 4: Improvement
      setLoadingStage("improving");

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

      // Stage 5: Success
      setLoadingStage("success");
      setSession(result.session);
      setInputText("");

      if (result.isComplete) {
        await Clipboard.copy(result.session.messages[result.session.messages.length - 1].content);
        await ToastHelper.success("Prompt copied to clipboard");
      }
    } catch (error) {
      setLoadingStage("error");
      await ToastHelper.error("Failed to process", error instanceof Error ? error.message : String(error));
    } finally {
      setIsLoading(false);
      setLoadingStage("idle");
    }
  };

  const handleFollowUpSubmit = async (values: { response: string }) => {
    if (!session) return;

    // Stage 1: Validation
    setLoadingStage("validating");

    setIsLoading(true);
    setShowFollowUpForm(false);

    try {
      // Stage 2: Connection
      setLoadingStage("connecting");

      const config = getConfig(preferences);

      // Stage 3: Analysis
      setLoadingStage("analyzing");

      // Stage 4: Improvement
      setLoadingStage("improving");

      const result = await continueWizard(session.id, values.response, {
        baseUrl: config.baseUrl,
        model: config.model,
        dspyBaseUrl: config.dspyBaseUrl,
        dspyTimeoutMs: config.dspyTimeoutMs,
        preset: config.preset as ImprovePromptPreset,
      });

      // Stage 5: Success
      setLoadingStage("success");
      setSession(result.session);
      setInputText("");

      if (result.isComplete && result.prompt) {
        await Clipboard.copy(result.prompt);
        await ToastHelper.success("Prompt copied to clipboard");
      }
    } catch (error) {
      setLoadingStage("error");
      await ToastHelper.error("Failed to continue", error instanceof Error ? error.message : String(error));
    } finally {
      setIsLoading(false);
      setLoadingStage("idle");
    }
  };

  const handleSkipWizard = async () => {
    if (!session) return;

    setIsLoading(true);

    try {
      // Stage 2: Connection
      setLoadingStage("connecting");

      const config = getConfig(preferences);

      // Stage 3: Analysis
      setLoadingStage("analyzing");

      // Stage 4: Improvement
      setLoadingStage("improving");

      const result = await continueWizard(session.id, "", {
        baseUrl: config.baseUrl,
        model: config.model,
        dspyBaseUrl: config.dspyBaseUrl,
        dspyTimeoutMs: config.dspyTimeoutMs,
        preset: config.preset as ImprovePromptPreset,
      });

      // Stage 5: Success
      setLoadingStage("success");
      setSession(result.session);

      if (result.prompt) {
        await Clipboard.copy(result.prompt);
        await ToastHelper.success("Prompt copied to clipboard");
      }
    } catch (error) {
      setLoadingStage("error");
      await ToastHelper.error("Failed to skip wizard", error instanceof Error ? error.message : String(error));
    } finally {
      setIsLoading(false);
      setLoadingStage("idle");
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
        {loadingStage !== "idle" && <Form.Description text={`${STAGE_MESSAGES[loadingStage]}`} />}
      </Form>
    );
  }

  // Conversation list view
  return (
    <List
      navigationTitle={`Prompt Conversation${loadingStage !== "idle" ? ` — ${STAGE_MESSAGES[loadingStage]}` : ""}`}
      isLoading={isLoading}
      actions={
        <ActionPanel>
          <Action title="New Conversation" onAction={handleReset} shortcut={{ modifiers: ["cmd"], key: "n" }} />
          {wizardEnabled && !isWizardComplete && (
            <Action
              title="Skip Wizard"
              shortcut={{ modifiers: ["cmd", "shift"], key: "s" }}
              onAction={handleSkipWizard}
            />
          )}
        </ActionPanel>
      }
    >
      {session.messages.map((msg) => (
        <List.Item
          key={msg.timestamp}
          icon={msg.role === "user" ? "•" : "⤒"}
          title={msg.content.slice(0, 80) + (msg.content.length > 80 ? "..." : "")}
          subtitle={formatTimestamp(msg.timestamp)}
          accessories={[
            { text: msg.metadata?.turnNumber ? `T${msg.metadata.turnNumber}` : undefined },
            { icon: msg.role === "user" ? "" : Typography.engine("dspy") },
          ]}
        />
      ))}

      {canOfferSkip && !isWizardComplete && (
        <List.Item
          icon={tokens.semantic.success.icon}
          title="Prompt Looks Good!"
          subtitle={`Confidence: ${Typography.confidence(
            session?.wizard.nlacAnalysis?.confidence ?? 0,
          )} • You configured ${session?.wizard.config.maxTurns ?? 0} turns`}
          accessories={[{ text: `⌘⇧ S: Skip` }, { text: `Enter: Continue` }]}
          actions={
            <ActionPanel>
              <Action title="Skip to Prompt" onAction={handleSkipWizard} />
              <Action
                title="Start Wizard Anyway"
                onAction={() => setShowFollowUpForm(true)}
                shortcut={{ modifiers: ["cmd", "shift"], key: "w" }}
              />
            </ActionPanel>
          }
        />
      )}

      {wizardEnabled && !isWizardComplete && !canOfferSkip && (
        <List.Item
          icon="◐"
          title="Wizard Active"
          subtitle={`${remainingTurns} turn${remainingTurns > 1 ? "s" : ""} remaining`}
          accessories={[{ text: "Enter: Respond" }, { text: `⤒ ${remainingTurns}` }]}
          actions={
            <ActionPanel>
              <Action
                title="Provide Details"
                onAction={() => setShowFollowUpForm(true)}
                shortcut={{ modifiers: ["cmd", "shift"], key: "d" }}
              />
              <Action
                title="Skip to Generate"
                onAction={handleSkipWizard}
                shortcut={{ modifiers: ["cmd", "shift"], key: "g" }}
              />
            </ActionPanel>
          }
        />
      )}

      {isWizardComplete && session.messages.length > 1 && (
        <List.Item
          icon={tokens.semantic.success.icon}
          title="Prompt Ready"
          subtitle="Click to copy and view details"
          actions={
            <ActionPanel>
              <Action.CopyToClipboard title="Copy Prompt" content={SessionManager.extractFinalPrompt(session) || ""} />
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

  if (diffMs < 60000) return "now";
  if (diffMs < 3600000) {
    const mins = Math.floor(diffMs / 60000);
    return `${mins}m`;
  }
  return Typography.timestamp(date);
}
