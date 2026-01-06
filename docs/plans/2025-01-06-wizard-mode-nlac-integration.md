# Wizard Mode with NLaC Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement conversational wizard mode that uses NLaC analysis (Intent + Complexity) to intelligently decide when to clarify user input before generating prompts, with adaptive turn limits based on input complexity.

**Architecture:** Wizard Mode sits between Stage 1 (NLaC Analysis) and Stage 2 (DSPy KNN) in the hybrid pipeline. It stores conversation sessions locally, uses IntentClassifier + ComplexityAnalyzer to detect ambiguity, generates KNN-informed clarification questions, and enriches prompt generation with conversation context.

**Tech Stack:**
- TypeScript (Raycast Extension API)
- React (List + Form components)
- Node.js fs promises (session persistence)
- DSPy backend (KNNFewShot + ComponentCatalog)
- NLaC backend (IntentClassifier + ComplexityAnalyzer)
- Vitest (testing)

---

## Task 1: Create Core Types for Wizard System

**Files:**
- Create: `dashboard/src/core/conversation/types.ts`

**Step 1: Write the types file**

```typescript
/**
 * Types for conversational wizard mode
 * Integrates with NLaC analysis (Intent + Complexity)
 */

export type WizardMode = "auto" | "always" | "off";
export type IntentType = "DEBUG" | "REFACTOR" | "GENERATE" | "ANALYZE";
export type ComplexityLevel = "SIMPLE" | "MODERATE" | "COMPLEX";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
  timestamp: number;
  metadata?: {
    confidence?: number;
    turnNumber: number;
    intent?: IntentType;
    complexity?: ComplexityLevel;
    knnCount?: number;
  };
}

export interface AmbiguityDetection {
  isAmbiguous: boolean;
  confidence: number;
  missingInfo: string[];
  suggestedQuestions: string[];
  intent?: IntentType;
  complexity?: ComplexityLevel;
  knnExamples?: Array<{
    input: string;
    output: string;
    similarity: number;
  }>;
}

export interface WizardConfig {
  mode: WizardMode;
  maxTurns: number;
  currentTurn: number;
  timeoutPerTurn: number;
  adaptiveTurns: boolean;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  inputContext: {
    originalInput: string;
    preset: string;
    source: "dspy" | "ollama";
  };
  wizard: {
    enabled: boolean;
    config: WizardConfig;
    ambiguityScore: number;
    completed: boolean;
    nlacAnalysis?: {
      intent: IntentType;
      complexity: ComplexityLevel;
      confidence: number;
    };
  };
  createdAt: number;
  lastActivity: number;
}
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```bash
git add dashboard/src/core/conversation/types.ts
git commit -m "feat(wizard): add core types for conversational mode

- Define ChatMessage, ChatSession, WizardConfig
- Support NLaC integration types (IntentType, ComplexityLevel)
- Add AmbiguityDetection interface for KNN-informed questions"
```

---

## Task 2: Implement SessionManager with LRU Cache

**Files:**
- Create: `dashboard/src/core/conversation/SessionManager.ts`

**Step 1: Write SessionManager class**

```typescript
import { promises as fs } from "fs";
import { join } from "path";
import { homedir } from "os";
import { randomUUID } from "crypto";
import type { ChatSession, ChatMessage, WizardMode, IntentType, ComplexityLevel } from "./types";

const SESSIONS_DIR = join(homedir(), ".raycast-prompt-improver", "sessions");
const MAX_SESSIONS = 10;
const SESSION_TTL_MS = 24 * 60 * 60 * 1000;

class SessionCache {
  private cache = new Map<string, ChatSession>();
  private maxSize = 10;

  set(session: ChatSession): void {
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(session.id, session);
  }

  get(id: string): ChatSession | undefined {
    return this.cache.get(id);
  }

  delete(id: string): void {
    this.cache.delete(id);
  }

  getAll(): ChatSession[] {
    return Array.from(this.cache.values());
  }
}

const sessionCache = new SessionCache();

export class SessionManager {
  static async createSession(
    initialInput: string,
    preset: string,
    source: "dspy" | "ollama",
    wizardMode: WizardMode,
    maxTurns: number,
    nlacAnalysis?: { intent: IntentType; complexity: ComplexityLevel; confidence: number }
  ): Promise<ChatSession> {
    const session: ChatSession = {
      id: randomUUID(),
      messages: [
        {
          role: "user",
          content: initialInput,
          timestamp: Date.now(),
          metadata: { turnNumber: 1, intent: nlacAnalysis?.intent, complexity: nlacAnalysis?.complexity },
        },
      ],
      inputContext: { originalInput: initialInput, preset, source },
      wizard: {
        enabled: this.shouldEnableWizard(wizardMode, nlacAnalysis),
        config: {
          mode: wizardMode,
          maxTurns: this.calculateMaxTurns(maxTurns, nlacAnalysis?.complexity),
          currentTurn: 0,
          timeoutPerTurn: 60_000,
          adaptiveTurns: true,
        },
        ambiguityScore: nlacAnalysis?.confidence ?? 0,
        completed: !this.shouldEnableWizard(wizardMode, nlacAnalysis),
        nlacAnalysis,
      },
      createdAt: Date.now(),
      lastActivity: Date.now(),
    };

    sessionCache.set(session);
    await this.saveSession(session);
    return session;
  }

  private static shouldEnableWizard(
    mode: WizardMode,
    analysis?: { intent: IntentType; complexity: ComplexityLevel; confidence: number }
  ): boolean {
    if (mode === "off") return false;
    if (mode === "always") return true;
    if (!analysis) return false;

    const { confidence, complexity, intent } = analysis;
    return confidence < 0.7 || complexity === "COMPLEX" || intent === "GENERATE";
  }

  private static calculateMaxTurns(baseMaxTurns: number, complexity?: ComplexityLevel): number {
    if (!complexity) return baseMaxTurns;
    switch (complexity) {
      case "SIMPLE": return 1;
      case "MODERATE": return Math.min(baseMaxTurns, 2);
      case "COMPLEX": return Math.max(baseMaxTurns, 3);
      default: return baseMaxTurns;
    }
  }

  static async appendUserMessage(sessionId: string, content: string): Promise<ChatSession> {
    const session = sessionCache.get(sessionId);
    if (!session) throw new Error(`Session not found: ${sessionId}`);

    const message: ChatMessage = {
      role: "user",
      content,
      timestamp: Date.now(),
      metadata: { turnNumber: session.messages.length + 1 },
    };

    session.messages.push(message);
    session.lastActivity = Date.now();

    if (session.wizard.enabled && !session.wizard.completed) {
      session.wizard.config.currentTurn++;
      if (session.wizard.config.currentTurn >= session.wizard.config.maxTurns) {
        session.wizard.completed = true;
      }
    }

    sessionCache.set(session);
    await this.saveSession(session);
    return session;
  }

  static async appendAssistantMessage(
    sessionId: string,
    content: string,
    ambiguityInfo?: { isAmbiguous: boolean; confidence: number; intent?: IntentType; complexity?: ComplexityLevel }
  ): Promise<ChatSession> {
    const session = sessionCache.get(sessionId);
    if (!session) throw new Error(`Session not found: ${sessionId}`);

    const message: ChatMessage = {
      role: "assistant",
      content,
      timestamp: Date.now(),
      metadata: {
        turnNumber: session.messages.length + 1,
        confidence: ambiguityInfo?.confidence,
        intent: ambiguityInfo?.intent,
        complexity: ambiguityInfo?.complexity,
      },
    };

    session.messages.push(message);
    session.lastActivity = Date.now();

    if (ambiguityInfo) {
      session.wizard.ambiguityScore = ambiguityInfo.confidence;
      session.wizard.completed = !ambiguityInfo.isAmbiguous;
    }

    sessionCache.set(session);
    await this.saveSession(session);
    return session;
  }

  static shouldContinueWizard(session: ChatSession): boolean {
    return (
      session.wizard.enabled &&
      !session.wizard.completed &&
      session.wizard.config.currentTurn < session.wizard.config.maxTurns
    );
  }

  static getRemainingTurns(session: ChatSession): number {
    return Math.max(0, session.wizard.config.maxTurns - session.wizard.config.currentTurn);
  }

  static async completeWizard(sessionId: string): Promise<ChatSession> {
    const session = sessionCache.get(sessionId);
    if (!session) throw new Error(`Session not found: ${sessionId}`);
    session.wizard.completed = true;
    sessionCache.set(session);
    await this.saveSession(session);
    return session;
  }

  static toChatFormat(session: ChatSession): Array<{ role: string; content: string }> {
    return session.messages.map((msg) => ({ role: msg.role, content: msg.content }));
  }

  static extractFinalPrompt(session: ChatSession): string | null {
    const lastAssistant = [...session.messages]
      .reverse()
      .find((msg) => msg.role === "assistant" && msg.content.startsWith("#"));
    return lastAssistant?.content || null;
  }

  static getSession(sessionId: string): ChatSession | undefined {
    return sessionCache.get(sessionId);
  }

  static getAllSessions(): ChatSession[] {
    return sessionCache.getAll();
  }

  static async deleteSession(sessionId: string): Promise<void> {
    sessionCache.delete(sessionId);
    try {
      await fs.unlink(join(SESSIONS_DIR, `${sessionId}.json`));
    } catch {}
  }

  private static async saveSession(session: ChatSession): Promise<void> {
    try {
      await fs.mkdir(SESSIONS_DIR, { recursive: true });
      await fs.writeFile(join(SESSIONS_DIR, `${session.id}.json`), JSON.stringify(session, null, 2), "utf-8");
    } catch (error) {
      console.error("[SessionManager] Failed to save session:", error);
    }
  }

  static async cleanupOldSessions(): Promise<void> {
    try {
      const files = await fs.readdir(SESSIONS_DIR);
      const now = Date.now();
      for (const file of files) {
        if (!file.endsWith(".json")) continue;
        const sessionPath = join(SESSIONS_DIR, file);
        const content = await fs.readFile(sessionPath, "utf-8");
        const session: ChatSession = JSON.parse(content);
        if (now - session.lastActivity > SESSION_TTL_MS) {
          await fs.unlink(sessionPath);
          sessionCache.delete(session.id);
        }
      }
    } catch {}
  }
}
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```bash
git add dashboard/src/core/conversation/types.ts dashboard/src/core/conversation/SessionManager.ts
git commit -m "feat(wizard): implement SessionManager with LRU cache

- Add in-memory LRU cache (max 10 sessions)
- Implement session persistence to ~/.raycast-prompt-improver/sessions/
- Add shouldEnableWizard logic based on mode + NLaC analysis
- Add adaptive max turns calculation (SIMPLE=1, MODERATE=2, COMPLEX=3)
- Add TTL-based cleanup (24 hours)"
```

---

## Task 3: Add Wizard Configuration to package.json

**Files:**
- Modify: `dashboard/package.json`

**Step 1: Add wizard preferences to promptify-quick command**

Find the `preferences` array in the `promptify-quick` command (around line 20) and add after the `timeoutMs` preference:

```json
{
  "name": "wizardMode",
  "description": "Interactive clarification before generating prompt",
  "type": "dropdown",
  "required": false,
  "default": "auto",
  "data": [
    {
      "title": "Auto (LLM decides)",
      "value": "auto"
    },
    {
      "title": "Always On",
      "value": "always"
    },
    {
      "title": "Always Off",
      "value": "off"
    }
  ],
  "title": "Wizard Mode"
},
{
  "name": "maxWizardTurns",
  "description": "Maximum clarification rounds in wizard mode",
  "type": "dropdown",
  "required": false,
  "default": "2",
  "data": [
    {
      "title": "1 turn",
      "value": "1"
    },
    {
      "title": "2 turns",
      "value": "2"
    },
    {
      "title": "3 turns",
      "value": "3"
    }
  ],
  "title": "Max Wizard Turns"
}
```

**Step 2: Verify package.json is valid JSON**

Run: `cat package.json | jq empty`
Expected: No output (valid JSON)

**Step 3: Commit**

```bash
git add dashboard/package.json
git commit -m "feat(ui): add wizard mode preferences to Raycast

- Add wizardMode dropdown (auto/always/off)
- Add maxWizardTurns dropdown (1/2/3 turns)
- Default: auto mode with 2 max turns"
```

---

## Task 4: Update Config Schema and Mapping

**Files:**
- Modify: `dashboard/src/core/config/index.ts`
- Modify: `dashboard/src/core/config/schema.ts`

**Step 1: Add wizard config to schema.ts**

Add to `dashboard/src/core/config/schema.ts` after the `PresetsConfigSchema` (around line 155):

```typescript
/**
 * Wizard configuration for interactive mode
 */
export const WizardConfigSchema = z
  .object({
    mode: z.enum(["auto", "always", "off"]).describe("Wizard mode: auto-detect, always on, or always off"),
    maxTurns: z
      .number()
      .int()
      .positive("maxTurns must be positive")
      .min(1, "maxTurns must be at least 1")
      .max(3, "maxTurns must not exceed 3"),
    adaptiveTurns: z.boolean().describe("Adjust max turns based on complexity"),
  })
  .strict();
```

Add to the `AppConfigSchema` (around line 234, inside the object):

```typescript
wizard: WizardConfigSchema,
```

Add type export (around line 254):

```typescript
export type WizardConfig = z.infer<typeof WizardConfigSchema>;
```

**Step 2: Add wizard to PREFERENCE_PATH_MAP in index.ts**

Add to `dashboard/src/core/config/index.ts` in `PREFERENCE_PATH_MAP` (around line 140):

```typescript
// Wizard settings
wizardMode: "wizard.mode",
maxWizardTurns: "wizard.maxTurns",
```

Add to defaults (if you want defaults):

```typescript
wizard: {
  mode: "auto" as const,
  maxTurns: 2,
  adaptiveTurns: true,
},
```

**Step 3: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 4: Run tests**

Run: `cd dashboard && npm test`
Expected: All tests pass

**Step 5: Commit**

```bash
git add dashboard/src/core/config/schema.ts dashboard/src/core/config/index.ts
git commit -m "feat(config): add wizard mode to config schema

- Add WizardConfigSchema with mode, maxTurns, adaptiveTurns
- Map wizardMode and maxWizardTurns preferences
- Add wizard to AppConfigSchema"
```

---

## Task 5: Implement Wizard Prompt Improvement Service

**Files:**
- Create: `dashboard/src/core/llm/improvePromptWithWizard.ts`

**Step 1: Write wizard improvement service**

```typescript
import { SessionManager } from "../conversation/SessionManager";
import type { ChatSession, WizardMode } from "../conversation/types";
import { improvePromptWithHybrid } from "./improvePrompt";

interface WizardOptions {
  rawInput: string;
  preset: string;
  wizardMode: WizardMode;
  maxWizardTurns: number;
  baseUrl: string;
  model: string;
  dspyBaseUrl: string;
  dspyTimeoutMs: number;
  temperature?: number;
  systemPattern?: string;
}

interface NLaCAnalysis {
  intent: "DEBUG" | "REFACTOR" | "GENERATE" | "ANALYZE";
  complexity: "SIMPLE" | "MODERATE" | "COMPLEX";
  confidence: number;
}

export async function improvePromptWithWizard(options: WizardOptions): Promise<{
  session: ChatSession;
  isComplete: boolean;
  needsClarification: boolean;
}> {
  // Step 1: Analyze input (placeholder for now, will call NLaC backend)
  const nlacAnalysis: NLaCAnalysis = await analyzeInput(options.rawInput);

  // Step 2: Create session
  const session = await SessionManager.createSession(
    options.rawInput,
    options.preset,
    "dspy",
    options.wizardMode,
    options.maxWizardTurns,
    nlacAnalysis
  );

  // Step 3: If wizard disabled, generate directly
  if (!session.wizard.enabled) {
    const result = await improvePromptWithHybrid({
      rawInput: options.rawInput,
      preset: options.preset,
      options: {
        baseUrl: options.baseUrl,
        model: options.model,
        timeoutMs: options.dspyTimeoutMs,
        temperature: options.temperature,
        systemPattern: options.systemPattern,
        dspyBaseUrl: options.dspyBaseUrl,
        dspyTimeoutMs: options.dspyTimeoutMs,
      },
    });

    await SessionManager.appendAssistantMessage(
      session.id,
      result.improved_prompt,
      { confidence: result.confidence }
    );

    return { session, isComplete: true, needsClarification: false };
  }

  // Step 4: Generate clarification questions
  const questions = generateClarificationQuestions(nlacAnalysis);

  const clarificationText =
    `I need clarification on your request:\n\n` +
    questions.map((q, i) => `${i + 1}. ${q}`).join("\n") +
    "\n\nPlease respond to continue, or press Enter to generate with current information.";

  await SessionManager.appendAssistantMessage(session.id, clarificationText, {
    confidence: nlacAnalysis.confidence,
    isAmbiguous: true,
  });

  return { session, isComplete: false, needsClarification: true };
}

export async function continueWizard(
  sessionId: string,
  userResponse: string,
  options: Omit<WizardOptions, "rawInput" | "wizardMode" | "maxWizardTurns">
): Promise<{ session: ChatSession; isComplete: boolean; prompt?: string }> {
  const session = SessionManager.getSession(sessionId);
  if (!session) throw new Error("Session not found");

  await SessionManager.appendUserMessage(sessionId, userResponse);

  if (SessionManager.shouldContinueWizard(session)) {
    const followUp = ["What specific details can you provide?"];
    await SessionManager.appendAssistantMessage(session.id, followUp.join("\n"), {
      confidence: 0.5,
      isAmbiguous: true,
    });

    return { session: SessionManager.getSession(sessionId)!, isComplete: false };
  }

  // Generate final prompt
  const result = await improvePromptWithHybrid({
    rawInput: session.inputContext.originalInput,
    preset: session.inputContext.preset,
    options: {
      ...options,
      conversationContext: SessionManager.toChatFormat(session),
    },
  });

  await SessionManager.appendAssistantMessage(sessionId, result.improved_prompt, {
    confidence: result.confidence,
    isAmbiguous: false,
  });

  await SessionManager.completeWizard(sessionId);

  return {
    session: SessionManager.getSession(sessionId)!,
    isComplete: true,
    prompt: result.improved_prompt,
  };
}

// Placeholder for NLaC analysis (will call backend in Phase 2)
async function analyzeInput(input: string): Promise<NLaCAnalysis> {
  // Simple heuristic for now
  const tokenCount = input.split(/\s+/).length;
  const complexity = tokenCount < 10 ? "SIMPLE" : tokenCount < 20 ? "MODERATE" : "COMPLEX";
  const intent = input.toLowerCase().includes("create") || input.toLowerCase().includes("build") ? "GENERATE" : "ANALYZE";
  const confidence = tokenCount < 5 ? 0.4 : 0.8;

  return { intent: intent as any, complexity: complexity as any, confidence };
}

function generateClarificationQuestions(analysis: NLaCAnalysis): string[] {
  if (analysis.intent === "GENERATE") {
    return ["What specific components or features do you need?", "What are the key requirements or constraints?"];
  }
  if (analysis.complexity === "COMPLEX") {
    return ["What is your primary goal or objective?", "Who is the intended audience?"];
  }
  return ["Can you provide more details about what you need?"];
}
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```bash
git add dashboard/src/core/llm/improvePromptWithWizard.ts
git commit -m "feat(wizard): implement wizard prompt improvement service

- Add improvePromptWithWizard for initial request
- Add continueWizard for follow-up responses
- Add placeholder analyzeInput with heuristics
- Add generateClarificationQuestions based on intent/complexity"
```

---

## Task 6: Create ConversationView UI Component

**Files:**
- Create: `dashboard/src/conversation-view.tsx`

**Step 1: Write conversation view component**

```typescript
import { List, Action, ActionPanel, Toast, showToast, Form, TextInput } from "@raycast/api";
import { useState, useEffect } from "react";
import { SessionManager } from "./core/conversation/SessionManager";
import { improvePromptWithWizard, continueWizard } from "./core/llm/improvePromptWithWizard";
import { getPreferenceValues } from "@raycast/api";
import { Clipboard } from "@raycast/api";

type Preferences = {
  wizardMode?: "auto" | "always" | "off";
  maxWizardTurns?: string;
  ollamaBaseUrl?: string;
  model?: string;
  dspyBaseUrl?: string;
  dspyTimeoutMs?: string;
  preset?: string;
};

export default function ConversationView() {
  const preferences = getPreferenceValues<Preferences>();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const wizardEnabled = session?.wizard.enabled ?? false;
  const remainingTurns = session ? SessionManager.getRemainingTurns(session) : 0;
  const isWizardComplete = session?.wizard.completed ?? true;

  useEffect(() => {
    SessionManager.cleanupOldSessions();
  }, []);

  const handleInitialSubmit = async (values: { input: string }) => {
    setIsLoading(true);

    try {
      const result = await improvePromptWithWizard({
        rawInput: values.input,
        preset: preferences.preset ?? "structured",
        wizardMode: preferences.wizardMode ?? "auto",
        maxWizardTurns: Number.parseInt(preferences.maxWizardTurns ?? "2", 10),
        baseUrl: preferences.ollamaBaseUrl ?? "http://localhost:11434",
        model: preferences.model ?? "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
        dspyBaseUrl: preferences.dspyBaseUrl ?? "http://localhost:8000",
        dspyTimeoutMs: Number.parseInt(preferences.dspyTimeoutMs ?? "120000", 10),
      });

      setSession(result.session);

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

  const handleFollowUp = async (values: { response: string }) => {
    if (!session) return;

    setIsLoading(true);

    try {
      const result = await continueWizard(session.id, values.response, {
        baseUrl: preferences.ollamaBaseUrl ?? "http://localhost:11434",
        model: preferences.model ?? "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
        dspyBaseUrl: preferences.dspyBaseUrl ?? "http://localhost:8000",
        dspyTimeoutMs: Number.parseInt(preferences.dspyTimeoutMs ?? "120000", 10),
        preset: preferences.preset ?? "structured",
      });

      setSession(result.session);

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
      const result = await continueWizard(session.id, "", {
        baseUrl: preferences.ollamaBaseUrl ?? "http://localhost:11434",
        model: preferences.model ?? "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
        dspyBaseUrl: preferences.dspyBaseUrl ?? "http://localhost:8000",
        dspyTimeoutMs: Number.parseInt(preferences.dspyTimeoutMs ?? "120000", 10),
        preset: preferences.preset ?? "structured",
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

  if (!session) {
    return (
      <Form
        actions={
          <ActionPanel>
            <Action.SubmitForm title="Start Conversation" onSubmit={handleInitialSubmit} />
          </ActionPanel>
        }
      >
        <Form.TextInput
          id="input"
          title="Describe your prompt idea"
          placeholder="e.g., I need a prompt for analyzing customer feedback..."
          value={inputText}
          onChange={setInputText}
        />
      </Form>
    );
  }

  return (
    <List
      navigationTitle="Prompt Conversation"
      actions={
        <ActionPanel>
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
      {session.messages.map((msg, idx) => (
        <List.Item
          key={idx}
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
          actions={
            <ActionPanel>
              <Action.SubmitForm
                title="Continue"
                onSubmit={handleFollowUp}
                shortcut={{ modifiers: ["cmd"], key: "enter" }}
              />
            </ActionPanel>
          }
        >
          <List.Item.Detail
            markdown="Provide more details or press Enter to generate with current information."
          />
        </List.Item>
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
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```bash
git add dashboard/src/conversation-view.tsx
git commit -m "feat(ui): add ConversationView component for wizard mode

- Display conversation history with user/assistant messages
- Show wizard status with remaining turns
- Add skip wizard action (Cmd+Enter)
- Add form inputs for initial and follow-up responses
- Auto-copy final prompt to clipboard when complete"
```

---

## Task 7: Register Conversation Command in package.json

**Files:**
- Modify: `dashboard/package.json`

**Step 1: Add conversation command to commands array**

Add to the `commands` array in `package.json` (after `prompt-history` command):

```json
{
  "name": "conversation",
  "title": "Prompt Conversation",
  "description": "Interactive wizard mode for clarifying ambiguous requests",
  "mode": "view"
}
```

**Step 2: Verify package.json is valid JSON**

Run: `cat package.json | jq empty`
Expected: No output

**Step 3: Commit**

```bash
git add dashboard/package.json
git commit -m "feat(ui): register Conversation command in Raycast

- Add conversation command with interactive wizard mode
- Mode: view for List-based conversation interface"
```

---

## Task 8: Create Conversation Command Entry Point

**Files:**
- Create: `dashboard/src/conversation.tsx`

**Step 1: Write conversation command entry point (simple redirect)**

```typescript
export { default } from "./conversation-view";
```

**Step 2: Verify TypeScript compilation**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```bash
git add dashboard/src/conversation.tsx
git commit -m "feat(ui): add conversation command entry point

- Export ConversationView as default export"
```

---

## Task 9: Write Tests for SessionManager

**Files:**
- Create: `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`

**Step 1: Write SessionManager tests**

```typescript
import { describe, it, expect, beforeEach } from "vitest";
import { SessionManager } from "../SessionManager";
import type { ChatSession } from "../types";
import { promises as fs } from "fs";
import { join } from "path";
import { homedir } from "os";
import { randomUUID } from "crypto";

describe("SessionManager", () => {
  const TEST_SESSIONS_DIR = join(homedir(), ".raycast-prompt-improver", "sessions-test");

  beforeEach(async () => {
    // Clean up test sessions
    try {
      await fs.rmdir(TEST_SESSIONS_DIR, { recursive: true });
    } catch {}
  });

  describe("createSession", () => {
    it("should create session with wizard enabled in auto mode when confidence is low", async () => {
      const session = await SessionManager.createSession(
        "test input",
        "structured",
        "dspy",
        "auto",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      expect(session.wizard.enabled).toBe(true);
      expect(session.wizard.completed).toBe(false);
      expect(session.wizard.nlacAnalysis).toEqual({
        intent: "GENERATE",
        complexity: "SIMPLE",
        confidence: 0.5,
      });
    });

    it("should disable wizard when confidence is high", async () => {
      const session = await SessionManager.createSession(
        "clear detailed input with specific requirements",
        "structured",
        "dspy",
        "auto",
        2,
        { intent: "REFACTOR", complexity: "SIMPLE", confidence: 0.9 }
      );

      expect(session.wizard.enabled).toBe(false);
      expect(session.wizard.completed).toBe(true);
    });

    it("should always enable wizard in always mode", async () => {
      const session = await SessionManager.createSession(
        "any input",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.95 }
      );

      expect(session.wizard.enabled).toBe(true);
      expect(session.wizard.completed).toBe(false);
    });

    it("should never enable wizard in off mode", async () => {
      const session = await SessionManager.createSession(
        "ambiguous input",
        "structured",
        "dspy",
        "off",
        2,
        { intent: "GENERATE", complexity: "COMPLEX", confidence: 0.3 }
      );

      expect(session.wizard.enabled).toBe(false);
      expect(session.wizard.completed).toBe(true);
    });

    it("should use adaptive max turns based on complexity", async () => {
      const simpleSession = await SessionManager.createSession(
        "simple",
        "structured",
        "dspy",
        "always",
        3,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.5 }
      );

      expect(simpleSession.wizard.config.maxTurns).toBe(1);

      const complexSession = await SessionManager.createSession(
        "complex with many requirements",
        "structured",
        "dspy",
        "always",
        1,
        { intent: "GENERATE", complexity: "COMPLEX", confidence: 0.5 }
      );

      expect(complexSession.wizard.config.maxTurns).toBe(3);
    });
  });

  describe("appendUserMessage", () => {
    it("should append user message and increment turn counter", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      const updated = await SessionManager.appendUserMessage(session.id, "user response");

      expect(updated.messages.length).toBe(2);
      expect(updated.messages[1].role).toBe("user");
      expect(updated.messages[1].content).toBe("user response");
      expect(updated.wizard.config.currentTurn).toBe(1);
    });

    it("should complete wizard when max turns reached", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        1,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      await SessionManager.appendUserMessage(session.id, "response");

      expect(session.wizard.completed).toBe(true);
    });
  });

  describe("shouldContinueWizard", () => {
    it("should return true when wizard enabled and not complete", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      expect(SessionManager.shouldContinueWizard(session)).toBe(true);
    });

    it("should return false after max turns reached", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        1,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      await SessionManager.appendUserMessage(session.id, "response");

      expect(SessionManager.shouldContinueWizard(session)).toBe(false);
    });
  });

  describe("getRemainingTurns", () => {
    it("should return remaining turns", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        3,
        { intent: "GENERATE", complexity: "COMPLEX", confidence: 0.5 }
      );

      expect(SessionManager.getRemainingTurns(session)).toBe(3);

      await SessionManager.appendUserMessage(session.id, "response");
      expect(SessionManager.getRemainingTurns(session)).toBe(2);
    });
  });

  describe("completeWizard", () => {
    it("should mark wizard as complete", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      const updated = await SessionManager.completeWizard(session.id);

      expect(updated.wizard.completed).toBe(true);
    });
  });

  describe("toChatFormat", () => {
    it("should convert session to chat format for LLM", async () => {
      const session = await SessionManager.createSession(
        "test input",
        "structured",
        "dspy",
        "off",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.8 }
      );

      await SessionManager.appendUserMessage(session.id, "user message");
      await SessionManager.appendAssistantMessage(session.id, "assistant message", {
        confidence: 0.9,
        isAmbiguous: false,
      });

      const chatFormat = SessionManager.toChatFormat(session);

      expect(chatFormat).toEqual([
        { role: "user", content: "test input" },
        { role: "user", content: "user message" },
        { role: "assistant", content: "assistant message" },
      ]);
    });
  });
});
```

**Step 2: Run tests to verify they pass**

Run: `cd dashboard && npm test -- src/core/conversation/__tests__/SessionManager.test.ts`
Expected: All tests pass

**Step 3: Commit**

```bash
git add dashboard/src/core/conversation/__tests__/SessionManager.test.ts
git commit -m "test(wizard): add SessionManager tests

- Test createSession with different wizard modes
- Test appendUserMessage and turn counting
- Test shouldContinueWizard logic
- Test getRemainingTurns calculation
- Test completeWizard
- Test toChatFormat conversion"
```

---

## Task 10: Run Full Test Suite and Verification

**Files:**
- None (verification task)

**Step 1: Run full test suite**

Run: `cd dashboard && npm test`
Expected: All tests pass

**Step 2: Run TypeScript check**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No type errors

**Step 3: Manual smoke test**

1. Start dev: `cd dashboard && npm run dev`
2. Test "Prompt Conversation" command
3. Enter ambiguous input: "create something"
4. Verify wizard activates and asks questions
5. Respond to question
6. Verify prompt generates and copies to clipboard
7. Test skip wizard with Cmd+Enter

**Step 4: Create summary commit**

```bash
git add .
git commit -m "chore: wizard mode with NLaC integration complete

✅ Implemented core types for conversation system
✅ SessionManager with LRU cache and persistence
✅ Wizard mode preferences in Raycast
✅ Config schema and mapping updated
✅ Wizard prompt improvement service
✅ ConversationView UI component
✅ Conversation command registered
✅ Full test coverage

Wizard mode integrates with NLaC analysis:
- Auto mode: Enables wizard based on intent + complexity + confidence
- Always/Off modes: Manual override
- Adaptive max turns: SIMPLE=1, MODERATE=2, COMPLEX=3
- KNN-informed questions (Phase 2 will add backend calls)

Next Phase: Connect to NLaC backend for IntentClassifier + ComplexityAnalyzer + KNNFewShot"
```

---

## Verification Checklist

Before considering this plan complete:

- [ ] All TypeScript files compile without errors
- [ ] All tests pass
- [ ] Manual testing completed in Raycast
- [ ] Wizard mode activates correctly in auto mode
- [ ] Wizard respects max turns limit
- [ ] Skip wizard action works (Cmd+Enter)
- [ ] Final prompt copies to clipboard
- [ ] Session persistence works across Raycast restarts
- [ ] Cleanup removes old sessions (TTL)

---

## Next Steps After Implementation

### Phase 2: NLaC Backend Integration (Future)

1. **Connect IntentClassifier**: Replace placeholder `analyzeInput()` with actual backend call
2. **Connect ComplexityAnalyzer**: Get complexity score from NLaC backend
3. **Connect KNNFewShot**: Fetch examples to enrich clarification questions
4. **Add conversationContext**: Pass chat history to DSPy backend for context-aware generation

### Phase 3: Enhancements (Optional)

1. **Session persistence in history**: Save completed conversations to prompt history
2. **Multi-language support**: Detect language and adjust questions
3. **Export conversation**: Allow saving conversation as markdown
4. **Visual indicators**: Show wizard status with icons/badges

---

## References

- NLaC Integration Analysis: `docs/architecture/nlac-integration-analysis.md`
- Design Principles Skill: `/Users/felipe_gonzalez/.claude/skills/design-principles/skill.md`
- DSPy Backend: `docs/backend/README.md`
- Raycast API Docs: https://developers.raycast.com
