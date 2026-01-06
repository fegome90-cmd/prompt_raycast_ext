import { describe, it, expect, beforeEach } from "vitest";
import { SessionManager } from "../SessionManager";
import type { ChatSession } from "../types";
import { promises as fs } from "fs";
import { join } from "path";
import { homedir } from "os";

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
      expect(session.wizard.bypassed).toBe(false);
      expect(session.wizard.resolved).toBe(false);
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
      expect(session.wizard.bypassed).toBe(true);
      expect(session.wizard.resolved).toBe(true);
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
      expect(session.wizard.bypassed).toBe(false);
      expect(session.wizard.resolved).toBe(false);
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
      expect(session.wizard.bypassed).toBe(true);
      expect(session.wizard.resolved).toBe(true);
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

    it("should enable wizard at exact confidence threshold (0.7)", async () => {
      const session = await SessionManager.createSession(
        "test input",
        "structured",
        "dspy",
        "auto",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.7 }
      );

      // confidence < 0.7 enables wizard, so 0.7 should NOT enable
      expect(session.wizard.enabled).toBe(false);
    });

    it("should always enable wizard when intent is GENERATE regardless of confidence", async () => {
      const session = await SessionManager.createSession(
        "create something",
        "structured",
        "dspy",
        "auto",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.95 }
      );

      expect(session.wizard.enabled).toBe(true);
    });

    it("should always enable wizard when complexity is COMPLEX regardless of confidence", async () => {
      const session = await SessionManager.createSession(
        "very complex input",
        "structured",
        "dspy",
        "auto",
        2,
        { intent: "ANALYZE", complexity: "COMPLEX", confidence: 0.95 }
      );

      expect(session.wizard.enabled).toBe(true);
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

      const updated = await SessionManager.appendUserMessage(session.id, "response");

      expect(updated.wizard.resolved).toBe(true);
    });
  });

  describe("appendAssistantMessage", () => {
    it("should append assistant message and update ambiguity score", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      const updated = await SessionManager.appendAssistantMessage(session.id, "Clarification question", {
        confidence: 0.6,
        isAmbiguous: true,
      });

      expect(updated.messages.length).toBe(2);
      expect(updated.messages[1].role).toBe("assistant");
      expect(updated.messages[1].content).toBe("Clarification question");
      expect(updated.wizard.ambiguityScore).toBe(0.6);
      expect(updated.wizard.resolved).toBe(false);
    });

    it("should complete wizard when isAmbiguous is false", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "always",
        2,
        { intent: "GENERATE", complexity: "SIMPLE", confidence: 0.5 }
      );

      const updated = await SessionManager.appendAssistantMessage(session.id, "Final prompt", {
        confidence: 0.9,
        isAmbiguous: false,
      });

      expect(updated.wizard.resolved).toBe(true);
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

      expect(updated.wizard.resolved).toBe(true);
    });
  });

  describe("extractFinalPrompt", () => {
    it("should extract last assistant message starting with #", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "off",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.8 }
      );

      await SessionManager.appendAssistantMessage(session.id, "Regular message", {
        confidence: 0.5,
        isAmbiguous: true,
      });

      await SessionManager.appendAssistantMessage(session.id, "# Optimized prompt", {
        confidence: 0.9,
        isAmbiguous: false,
      });

      const extracted = SessionManager.extractFinalPrompt(session);

      expect(extracted).toBe("# Optimized prompt");
    });

    it("should return null when no prompt starts with #", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "off",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.8 }
      );

      await SessionManager.appendAssistantMessage(session.id, "Regular message", {
        confidence: 0.5,
        isAmbiguous: false,
      });

      const extracted = SessionManager.extractFinalPrompt(session);

      expect(extracted).toBeNull();
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

  describe("session retrieval", () => {
    it("should get session by id", async () => {
      const session = await SessionManager.createSession(
        "test",
        "structured",
        "dspy",
        "off",
        2,
        { intent: "ANALYZE", complexity: "SIMPLE", confidence: 0.8 }
      );

      const retrieved = SessionManager.getSession(session.id);

      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe(session.id);
    });

    it("should return undefined for non-existent session", () => {
      const retrieved = SessionManager.getSession("non-existent-id");
      expect(retrieved).toBeUndefined();
    });

    it("should get all sessions", async () => {
      await SessionManager.createSession("test1", "structured", "dspy", "off", 2);
      await SessionManager.createSession("test2", "structured", "dspy", "off", 2);

      const all = SessionManager.getAllSessions();

      expect(all.length).toBeGreaterThanOrEqual(2);
    });

    it("should delete session", async () => {
      const session = await SessionManager.createSession("test", "structured", "dspy", "off", 2);

      await SessionManager.deleteSession(session.id);

      const retrieved = SessionManager.getSession(session.id);
      expect(retrieved).toBeUndefined();
    });
  });

  describe("error handling", () => {
    it("should throw error when appending to non-existent session", async () => {
      await expect(
        SessionManager.appendUserMessage("non-existent-id", "test")
      ).rejects.toThrow("Session not found");
    });

    it("should throw error when completing non-existent session", async () => {
      await expect(
        SessionManager.completeWizard("non-existent-id")
      ).rejects.toThrow("Session not found");
    });
  });
});
