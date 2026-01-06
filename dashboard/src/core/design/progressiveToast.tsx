import { Toast, showToast } from "@raycast/api";

/**
 * Progressive toast manager for Apple-like fluidity
 *
 * NOTE: Raycast Toast instances don't support property mutation after creation.
 * Instead, we call showToast() for each update, which replaces the previous toast.
 * This creates the visual effect of a single, evolving toast.
 */
export class ProgressiveToast {
  /**
   * Start the progressive toast with initial message
   */
  async start(initial: string) {
    console.log("[ProgressiveToast] START called with:", initial);
    await showToast({
      style: Toast.Style.Animated,
      title: initial,
    });
  }

  /**
   * Update the toast title to show progress
   * Creates a new toast, replacing the previous one
   */
  async update(message: string) {
    console.log("[ProgressiveToast] UPDATE called with:", message);
    await showToast({
      style: Toast.Style.Animated,
      title: message,
    });
  }

  /**
   * Transition to success state
   */
  async success(title: string, message?: string) {
    console.log("[ProgressiveToast] SUCCESS called with:", title);
    await showToast({
      style: Toast.Style.Success,
      title: title,
      message: message,
    });
  }

  /**
   * Transition to error state with hint
   */
  async error(title: string, error: Error | string, hint?: string) {
    console.log("[ProgressiveToast] ERROR called with:", title);
    const errMsg = error instanceof Error ? error.message : error;
    await showToast({
      style: Toast.Style.Failure,
      title: title,
      message: hint ? `${errMsg} — ${hint}` : errMsg,
    });
  }
}
