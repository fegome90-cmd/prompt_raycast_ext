import { Toast, showToast } from "@raycast/api";

/**
 * Progressive toast manager for Apple-like fluidity
 * Maintains a single toast instance that updates progressively
 * to give sense of constant forward progress
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
    console.log("[ProgressiveToast] Toast object:", this.toast);
  }

  /**
   * Update the toast title to show progress
   */
  update(message: string) {
    console.log("[ProgressiveToast] UPDATE called with:", message, "toast exists:", !!this.toast);
    if (this.toast) {
      this.toast.title = message;
      console.log("[ProgressiveToast] Title set to:", this.toast.title);
    }
  }

  /**
   * Transition to success state
   */
  success(title: string, message?: string) {
    console.log("[ProgressiveToast] SUCCESS called");
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
    console.log("[ProgressiveToast] ERROR called");
    if (this.toast) {
      this.toast.style = Toast.Style.Failure;
      this.toast.title = title;
      const errMsg = error instanceof Error ? error.message : error;
      this.toast.message = hint ? `${errMsg} — ${hint}` : errMsg;
    }
  }
}
