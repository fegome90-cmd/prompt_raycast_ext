// dashboard/src/core/input/getInput.ts
import { getSelectedText, Clipboard } from "@raycast/api";

const LOG_PREFIX = "[Input]";

/**
 * 📝 CONTEXT: Why 5-character minimum input requirement?
 *
 * Historical context (2025-01-06):
 * - Users would accidentally trigger "Promptify Selected" on short selections
 * - Common issues: Single character "a", clipboard fragments like "x", "test"
 * - This caused backend calls with meaningless input, wasting time and API quota
 *
 * Decision: Set minimum to 5 characters
 * - Low enough: Doesn't block legitimate single-word prompts ("help", "fix it")
 * - High enough: Prevents accidental triggers on meaningless fragments
 *
 * ⚡ INVARIANT: Both getSelectedText() and Clipboard.readText() enforce this minimum
 * ⚡ INVARIANT: If selection < 5 chars, we try clipboard as fallback
 * ⚡ INVARIANT: If clipboard < 5 chars, we return { source: "none", text: "" }
 *
 * 🔴 DO NOT lower this minimum below 5 - will re-introduce accidental triggers
 * 🔴 DO NOT make different minimums for selection vs clipboard - must be consistent
 */
export async function getInput(): Promise<{
  source: "selection" | "clipboard" | "none";
  text: string;
}> {
  console.log(`${LOG_PREFIX} 🚀 Starting input detection...`);

  // Try getSelectedText()
  try {
    console.log(`${LOG_PREFIX} Attempting getSelectedText()...`);
    const selected = await getSelectedText();
    const trimmed = selected?.trim();
    console.log(`${LOG_PREFIX} Selection: "${trimmed?.substring(0, 50)}..." (length: ${trimmed?.length || 0})`);

    if (trimmed && trimmed.length >= 5) {
      console.log(`${LOG_PREFIX} ✅ Using selection (${trimmed.length} chars)`);
      return { source: "selection", text: trimmed };
    }

    if (trimmed && trimmed.length < 5) {
      console.log(`${LOG_PREFIX} ⚠️ Selection too short (${trimmed.length} chars, min: 5)`);
    }
  } catch (error) {
    console.error(`${LOG_PREFIX} ❌ getSelectedText() failed:`, error);
  }

  // Try clipboard
  try {
    console.log(`${LOG_PREFIX} Attempting Clipboard.readText()...`);
    const clipboard = await Clipboard.readText();
    const trimmed = clipboard?.trim();
    console.log(`${LOG_PREFIX} Clipboard: "${trimmed?.substring(0, 50)}..." (length: ${trimmed?.length || 0})`);

    if (trimmed && trimmed.length >= 5) {
      console.log(`${LOG_PREFIX} ✅ Using clipboard (${trimmed.length} chars)`);
      return { source: "clipboard", text: trimmed };
    }

    if (trimmed && trimmed.length < 5) {
      console.log(`${LOG_PREFIX} ⚠️ Clipboard too short (${trimmed.length} chars, min: 5)`);
    }
  } catch (error) {
    console.error(`${LOG_PREFIX} ❌ Clipboard.readText() failed:`, error);
  }

  // No input found
  console.log(`${LOG_PREFIX} ❌ No input found (selection: empty/short, clipboard: empty/short)`);
  return { source: "none", text: "" };
}
