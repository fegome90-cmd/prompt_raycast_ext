// dashboard/src/core/input/getInput.ts
import { getSelectedText, Clipboard } from "@raycast/api";

const LOG_PREFIX = "[Input]";

export async function getInput(): Promise<{
  source: "selection" | "clipboard" | "none";
  text: string;
}> {
  console.log(`${LOG_PREFIX} Starting input detection...`);

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
