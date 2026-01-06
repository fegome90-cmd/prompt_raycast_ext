// dashboard/src/core/metrics/ttvLogger.ts
import * as fs from "node:fs/promises";
import * as path from "node:path";
import * as os from "node:os";

export interface TtvLog {
  t0: number;
  t_copy: number;
  ttv_ms: number;
  source: "selection" | "clipboard";
  output_length: number;
  error?: string | null;
}

export async function logTtvMeasurement(data: TtvLog): Promise<void> {
  try {
    const logDir = path.join(os.homedir(), "Library/Application Support/raycast-ext");
    await fs.mkdir(logDir, { recursive: true });
    const logPath = path.join(logDir, "ttv-logs.jsonl");
    const logEntry = JSON.stringify({ ...data, timestamp: Date.now() }) + "\n";
    await fs.appendFile(logPath, logEntry);
  } catch (error) {
    // Silent failure for fire-and-forget logging - just log to console
    console.error("[TTV Logger] Failed to write metric:", error);
  }
}
