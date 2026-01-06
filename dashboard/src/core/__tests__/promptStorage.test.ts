/**
 * Tests for promptStorage module
 *
 * Tests local persistence of prompt history with proper trimming and error handling
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import { tmpdir } from "os";

// Mock os module before importing promptStorage
vi.mock("os", async () => {
  const actualOs = await vi.importActual("os");
  return {
    ...actualOs,
    homedir: vi.fn(),
  };
});

describe("promptStorage", () => {
  const TEST_TIMESTAMP = Date.now();
  const TEMP_STORAGE_DIR = join(tmpdir(), `raycast-test-${TEST_TIMESTAMP}`);
  const TEMP_HISTORY_FILE = join(TEMP_STORAGE_DIR, "history.jsonl");

  let storageModule: any;
  let osModule: any;

  beforeEach(async () => {
    // Clear entire temp directory before each test
    try {
      await fs.rm(TEMP_STORAGE_DIR, { recursive: true, force: true });
    } catch {
      // Directory doesn't exist, ignore
    }

    // Clear module cache to get fresh instance
    vi.resetModules();
    vi.clearAllMocks();

    // Get mocked os module and configure it
    osModule = await import("os");
    vi.mocked(osModule.homedir).mockReturnValue(TEMP_STORAGE_DIR);

    // Import promptStorage after mocking
    storageModule = await import("../promptStorage");
  });

  afterEach(async () => {
    // Clean up entire directory after each test
    try {
      await fs.rm(TEMP_STORAGE_DIR, { recursive: true, force: true });
    } catch {
      // Directory doesn't exist, ignore
    }
    vi.restoreAllMocks();
  });

  describe("savePrompt", () => {
    it("should save a prompt with generated id and timestamp", async () => {
      const entry = {
        prompt: "Test prompt",
        meta: { confidence: 0.8 },
        source: "ollama" as const,
        inputLength: 12,
        preset: "structured" as const,
      };

      await storageModule.savePrompt(entry);

      const history = await storageModule.getPromptHistory();
      expect(history).toHaveLength(1);
      expect(history[0].prompt).toBe("Test prompt");
      expect(history[0].id).toBeDefined();
      expect(history[0].timestamp).toBeDefined();
      expect(history[0].meta?.confidence).toBe(0.8);
    });

    it("should append multiple prompts to history", async () => {
      await storageModule.savePrompt({ prompt: "First", source: "ollama" as const, inputLength: 5 });
      await new Promise((resolve) => setTimeout(resolve, 10)); // Ensure unique timestamps
      await storageModule.savePrompt({ prompt: "Second", source: "dspy" as const, inputLength: 6 });

      const history = await storageModule.getPromptHistory();
      expect(history).toHaveLength(2);
      expect(history[0].prompt).toBe("Second"); // Most recent first
      expect(history[1].prompt).toBe("First");
    });

    it("should handle prompts without optional metadata", async () => {
      await storageModule.savePrompt({ prompt: "Minimal prompt", source: "ollama" as const, inputLength: 14 });

      const history = await storageModule.getPromptHistory();
      expect(history).toHaveLength(1);
      expect(history[0].meta).toBeUndefined();
      expect(history[0].preset).toBeUndefined();
    });
  });

  describe("getPromptHistory", () => {
    it("should return empty array when no history exists", async () => {
      const history = await storageModule.getPromptHistory();
      expect(history).toEqual([]);
    });

    it("should return prompts sorted by timestamp (most recent first)", async () => {
      await storageModule.savePrompt({ prompt: "First", source: "ollama" as const, inputLength: 5 });
      await new Promise((resolve) => setTimeout(resolve, 10)); // Ensure different timestamps
      await storageModule.savePrompt({ prompt: "Second", source: "dspy" as const, inputLength: 6 });

      const history = await storageModule.getPromptHistory();
      expect(history[0].prompt).toBe("Second");
      expect(history[1].prompt).toBe("First");
      expect(history[0].timestamp).toBeGreaterThan(history[1].timestamp);
    });

    it("should respect the limit parameter", async () => {
      for (let i = 0; i < 5; i++) {
        await storageModule.savePrompt({ prompt: `Prompt ${i}`, source: "ollama" as const, inputLength: 8 + i });
        await new Promise((resolve) => setTimeout(resolve, 5));
      }

      const history3 = await storageModule.getPromptHistory(3);
      expect(history3).toHaveLength(3);

      const history10 = await storageModule.getPromptHistory(10);
      expect(history10).toHaveLength(5);
    });

  });

  describe("trimHistory (MAX_HISTORY enforcement)", () => {
    it("should trim history to MAX_HISTORY (20) entries", async () => {
      // Save 25 prompts
      for (let i = 0; i < 25; i++) {
        await storageModule.savePrompt({
          prompt: `Prompt ${i.toString().padStart(2, "0")}`,
          source: i % 2 === 0 ? "ollama" : "dspy",
          inputLength: 9 + i,
        });
        await new Promise((resolve) => setTimeout(resolve, 5)); // Ensure unique timestamps
      }

      const history = await storageModule.getPromptHistory(100); // Request more than MAX
      expect(history).toHaveLength(20); // Should be capped at MAX_HISTORY

      // Oldest entries should be removed
      const promptNumbers = history.map((entry: any) => parseInt(entry.prompt.split(" ")[1], 10));
      expect(Math.min(...promptNumbers)).toBeGreaterThanOrEqual(5); // Prompts 0-4 should be trimmed
      expect(Math.max(...promptNumbers)).toBe(24); // Most recent should be kept
    });

    it("should not trim when under MAX_HISTORY", async () => {
      for (let i = 0; i < 10; i++) {
        await storageModule.savePrompt({ prompt: `Prompt ${i}`, source: "ollama" as const, inputLength: 8 + i });
        await new Promise((resolve) => setTimeout(resolve, 5));
      }

      const history = await storageModule.getPromptHistory();
      expect(history).toHaveLength(10);
    });
  });

  describe("getPromptById", () => {
    it("should return null when history is empty", async () => {
      const result = await storageModule.getPromptById("nonexistent");
      expect(result).toBeNull();
    });

    it("should return null when id not found", async () => {
      await storageModule.savePrompt({ prompt: "Test", source: "ollama" as const, inputLength: 4 });
      const result = await storageModule.getPromptById("nonexistent");
      expect(result).toBeNull();
    });

    it("should return the prompt when id matches", async () => {
      await storageModule.savePrompt({ prompt: "Test prompt", source: "dspy" as const, inputLength: 11 });
      const history = await storageModule.getPromptHistory();
      const id = history[0].id;

      const result = await storageModule.getPromptById(id);
      expect(result).not.toBeNull();
      expect(result?.prompt).toBe("Test prompt");
      expect(result?.id).toBe(id);
    });
  });

  describe("clearHistory", () => {
    it("should remove all history", async () => {
      await storageModule.savePrompt({ prompt: "First", source: "ollama" as const, inputLength: 5 });
      await storageModule.savePrompt({ prompt: "Second", source: "dspy" as const, inputLength: 6 });

      expect(await storageModule.getPromptHistory()).toHaveLength(2);

      await storageModule.clearHistory();

      expect(await storageModule.getPromptHistory()).toEqual([]);
    });

    it("should not error when clearing empty history", async () => {
      await expect(storageModule.clearHistory()).resolves.not.toThrow();
      expect(await storageModule.getPromptHistory()).toEqual([]);
    });
  });

  describe("formatTimestamp", () => {
    it('should return "Just now" for timestamps less than 1 minute ago', () => {
      const now = Date.now();
      const result = storageModule.formatTimestamp(now - 30000); // 30 seconds ago
      expect(result).toBe("Just now");
    });

    it("should return minutes ago for timestamps less than 1 hour ago", () => {
      const now = Date.now();
      const result = storageModule.formatTimestamp(now - 180000); // 3 minutes ago
      expect(result).toBe("3m ago");
    });

    it("should return hours ago for timestamps less than 24 hours ago", () => {
      const now = Date.now();
      const result = storageModule.formatTimestamp(now - 7200000); // 2 hours ago
      expect(result).toBe("2h ago");
    });

    it("should return formatted date for older timestamps", () => {
      const twoDaysAgo = Date.now() - 172800000; // 2 days ago
      const result = storageModule.formatTimestamp(twoDaysAgo);
      // Format varies by locale, accept common formats
      expect(result).toMatch(/^[A-Z][a-z]{2} \d{1,2}/); // e.g., "Jan 5" or "Jan 5, 01:26 PM"
    });
  });
});
