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
    const wizardEnabled = this.shouldEnableWizard(wizardMode, nlacAnalysis);
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
        enabled: wizardEnabled,
        bypassed: !wizardEnabled,
        resolved: !wizardEnabled,
        config: {
          mode: wizardMode,
          maxTurns: this.calculateMaxTurns(maxTurns, nlacAnalysis?.complexity),
          currentTurn: 0,
          timeoutPerTurn: 60_000,
          adaptiveTurns: true,
        },
        ambiguityScore: nlacAnalysis?.confidence ?? 0,
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

    if (session.wizard.enabled && !session.wizard.resolved) {
      session.wizard.config.currentTurn++;
      if (session.wizard.config.currentTurn >= session.wizard.config.maxTurns) {
        session.wizard.resolved = true;
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
      session.wizard.resolved = !ambiguityInfo.isAmbiguous;
    }

    sessionCache.set(session);
    await this.saveSession(session);
    return session;
  }

  static shouldContinueWizard(session: ChatSession): boolean {
    return (
      session.wizard.enabled &&
      !session.wizard.resolved &&
      session.wizard.config.currentTurn < session.wizard.config.maxTurns
    );
  }

  static getRemainingTurns(session: ChatSession): number {
    return Math.max(0, session.wizard.config.maxTurns - session.wizard.config.currentTurn);
  }

  static async completeWizard(sessionId: string): Promise<ChatSession> {
    const session = sessionCache.get(sessionId);
    if (!session) throw new Error(`Session not found: ${sessionId}`);
    session.wizard.resolved = true;
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
    // Delete file first, then cache
    try {
      await fs.unlink(join(SESSIONS_DIR, `${sessionId}.json`));
    } catch (error) {
      console.warn(`[SessionManager] Failed to delete session file: ${error}`);
      // Don't remove from cache if file deletion failed
      return;
    }
    sessionCache.delete(sessionId);
  }

  private static async saveSession(session: ChatSession): Promise<void> {
    try {
      await fs.mkdir(SESSIONS_DIR, { recursive: true });
      await fs.writeFile(join(SESSIONS_DIR, `${session.id}.json`), JSON.stringify(session, null, 2), "utf-8");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error("[SessionManager] Failed to save session:", errorMessage);
      // Propagate to caller so they can handle it
      throw new Error(`Failed to persist session ${session.id}: ${errorMessage}`);
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
