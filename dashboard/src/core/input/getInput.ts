// dashboard/src/core/input/getInput.ts
import { getSelectedText, Clipboard } from "@raycast/api";

export async function getInput(): Promise<{
  source: "selection" | "clipboard" | "none";
  text: string;
}> {
  // Try getSelectedText()
  try {
    const selected = await getSelectedText();
    if (selected?.trim().length >= 5) {
      return { source: "selection", text: selected.trim() };
    }
  } catch {
    // Silent failure - fall through to clipboard
  }

  // Try clipboard
  try {
    const clipboard = await Clipboard.readText();
    if (clipboard?.trim().length >= 5) {
      return { source: "clipboard", text: clipboard.trim() };
    }
  } catch {
    // Silent failure - return none
  }

  // No input found
  return { source: "none", text: "" };
}
