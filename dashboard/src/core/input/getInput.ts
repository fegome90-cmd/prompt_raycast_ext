// dashboard/src/core/input/getInput.ts
import { getSelectedText, Clipboard } from "@raycast/api";

export async function getInput(): Promise<{
  source: "selection" | "clipboard" | "none";
  text: string;
}> {
  // Try getSelectedText()
  try {
    const selected = await getSelectedText();
    const trimmed = selected?.trim();
    if (trimmed && trimmed.length >= 5) {
      return { source: "selection", text: trimmed };
    }
  } catch {
    // Silent failure - fall through to clipboard
  }

  // Try clipboard
  try {
    const clipboard = await Clipboard.readText();
    const trimmed = clipboard?.trim();
    if (trimmed && trimmed.length >= 5) {
      return { source: "clipboard", text: trimmed };
    }
  } catch {
    // Silent failure - return none
  }

  // No input found
  return { source: "none", text: "" };
}
