import { promises as fs } from "fs";
import { join } from "path";
import { homedir } from "os";

export interface PromptEntry {
  id: string;
  timestamp: number;
  prompt: string;
  meta?: {
    confidence?: number;
    clarifyingQuestions?: string[];
    assumptions?: string[];
  };
  source?: "dspy" | "ollama";
  inputLength: number;
  preset?: string;
}

// Use home directory for storage (Raycast doesn't expose supportPath directly)
const STORAGE_BASE = join(homedir(), ".raycast-prompt-improver");
const STORAGE_DIR = join(STORAGE_BASE, "prompts");
const HISTORY_FILE = join(STORAGE_DIR, "history.jsonl");
const MAX_HISTORY = 20;

/**
 * Ensure storage directory exists
 */
async function ensureStorageDir(): Promise<void> {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
  } catch (error) {
    // Directory might already exist, ignore error
  }
}

/**
 * Save a prompt to local history
 */
export async function savePrompt(entry: Omit<PromptEntry, "id" | "timestamp">): Promise<void> {
  await ensureStorageDir();

  const fullEntry: PromptEntry = {
    ...entry,
    id: generateId(),
    timestamp: Date.now(),
  };

  const line = JSON.stringify(fullEntry) + "\n";

  // Append to history file
  await fs.appendFile(HISTORY_FILE, line, "utf-8");

  // Trim history if needed
  await trimHistory();
}

/**
 * Get recent prompt history
 */
export async function getPromptHistory(limit: number = 10): Promise<PromptEntry[]> {
  try {
    await ensureStorageDir();

    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    const entries: PromptEntry[] = lines
      .map((line) => {
        try {
          return JSON.parse(line) as PromptEntry;
        } catch {
          return null;
        }
      })
      .filter((entry): entry is PromptEntry => entry !== null)
      .sort((a, b) => b.timestamp - a.timestamp); // Most recent first

    return entries.slice(0, limit);
  } catch (error) {
    // File doesn't exist yet
    return [];
  }
}

/**
 * Get a specific prompt by ID
 */
export async function getPromptById(id: string): Promise<PromptEntry | null> {
  const history = await getPromptHistory(MAX_HISTORY);
  return history.find((entry) => entry.id === id) || null;
}

/**
 * Clear all history
 */
export async function clearHistory(): Promise<void> {
  try {
    await fs.unlink(HISTORY_FILE);
  } catch (error) {
    // File doesn't exist, ignore
  }
}

/**
 * Trim history to MAX_HISTORY entries
 */
async function trimHistory(): Promise<void> {
  try {
    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    if (lines.length > MAX_HISTORY) {
      const keepLines = lines.slice(-MAX_HISTORY);
      await fs.writeFile(HISTORY_FILE, keepLines.join("\n") + "\n", "utf-8");
    }
  } catch (error) {
    // File doesn't exist yet, ignore
  }
}

/**
 * Generate a short ID for the prompt entry
 */
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 6);
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs < 60000) {
    // Less than 1 minute
    return "Just now";
  } else if (diffMs < 3600000) {
    // Less than 1 hour
    const mins = Math.floor(diffMs / 60000);
    return `${mins}m ago`;
  } else if (diffMs < 86400000) {
    // Less than 24 hours
    const hours = Math.floor(diffMs / 3600000);
    return `${hours}h ago`;
  } else {
    // Format as date
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}
