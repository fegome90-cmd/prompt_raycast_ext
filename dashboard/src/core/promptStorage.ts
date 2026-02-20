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

const LOG_PREFIX = "[PromptStorage]";

/**
 * Check if error is ENOENT (file not found)
 */
function isENOENT(error: unknown): boolean {
  return error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT";
}

/**
 * Ensure storage directory exists
 */
async function ensureStorageDir(): Promise<void> {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`${LOG_PREFIX} Failed to create storage directory: ${message}`);
    throw new Error(`Failed to initialize storage: ${message}`);
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
        } catch (error) {
          // Log warning for corrupted entries (helps detect data corruption)
          console.warn(
            `${LOG_PREFIX} ⚠️ Skipping malformed JSON line (${line.length} chars): ${(error instanceof Error
              ? error.message
              : String(error)
            ).substring(0, 50)}`,
          );
          return null;
        }
      })
      .filter((entry): entry is PromptEntry => entry !== null)
      .sort((a, b) => b.timestamp - a.timestamp); // Most recent first

    return entries.slice(0, limit);
  } catch (error) {
    if (isENOENT(error)) {
      return []; // File doesn't exist yet
    }
    console.error(`${LOG_PREFIX} Failed to read history:`, error);
    throw error;
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
    if (isENOENT(error)) {
      return; // File doesn't exist - already cleared
    }
    console.error(`${LOG_PREFIX} Failed to clear history:`, error);
    throw new Error(`Failed to clear history: ${error instanceof Error ? error.message : String(error)}`);
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
      // Atomic write: temp file + rename
      const tempFile = HISTORY_FILE + ".tmp";
      await fs.writeFile(tempFile, keepLines.join("\n") + "\n", "utf-8");
      await fs.rename(tempFile, HISTORY_FILE);
    }
  } catch (error) {
    if (isENOENT(error)) {
      return; // File doesn't exist yet - this is OK
    }
    console.error(`${LOG_PREFIX} Failed to trim history:`, error);
    throw error;
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
