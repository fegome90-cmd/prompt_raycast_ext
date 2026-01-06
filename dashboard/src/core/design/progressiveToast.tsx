import { Toast, showToast } from "@raycast/api";

/**
 * Progressive toast manager for Apple-like fluidity
 *
 * Strategy: Maintain a single Toast instance and mutate its properties.
 * Raycast Toast has property setters (set title, set style, set message) that
 * trigger UI updates. We use these to progressively update the same toast.
 */
export class ProgressiveToast {
  private toast?: Toast;

  /**
   * Start the progressive toast with initial message
   */
  async start(initial: string) {
    console.log("[ProgressiveToast] START called with:", initial);
    this.toast = await showToast({
      style: Toast.Style.Animated,
      title: initial,
    });
    console.log("[ProgressiveToast] Toast created:", !!this.toast);
  }

  /**
   * Update the toast title to show progress
   */
  update(message: string) {
    console.log("[ProgressiveToast] UPDATE called with:", message);
    if (this.toast) {
      this.toast.title = message;
    }
  }

  /**
   * Transition to success state
   */
  success(title: string, message?: string) {
    console.log("[ProgressiveToast] SUCCESS called with:", title);
    if (this.toast) {
      this.toast.style = Toast.Style.Success;
      this.toast.title = title;
      if (message) {
        this.toast.message = message;
      }
    }
  }

  /**
   * Transition to error state with hint
   */
  error(title: string, error: Error | string, hint?: string) {
    console.log("[ProgressiveToast] ERROR called with:", title);
    if (this.toast) {
      this.toast.style = Toast.Style.Failure;
      this.toast.title = title;
      const errMsg = error instanceof Error ? error.message : error;
      this.toast.message = hint ? `${errMsg} — ${hint}` : errMsg;
    }
  }
}
