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
    this.toast = await showToast({
      style: Toast.Style.Animated,
      title: initial,
    });
  }

  /**
   * Update the toast title to show progress
   */
  async update(message: string) {
    if (this.toast) {
      await this.toast.setTitle(message);
    }
  }

  /**
   * Transition to success state
   */
  async success(title: string, message?: string) {
    if (this.toast) {
      await this.toast.setStyle(Toast.Style.Success);
      await this.toast.setTitle(title);
      if (message) {
        await this.toast.setMessage(message);
      }
    }
  }

  /**
   * Transition to error state with hint
   */
  async error(title: string, error: Error | string, hint?: string) {
    if (this.toast) {
      await this.toast.setStyle(Toast.Style.Failure);
      await this.toast.setTitle(title);
      const errMsg = error instanceof Error ? error.message : error;
      await this.toast.setMessage(hint ? `${errMsg} — ${hint}` : errMsg);
    }
  }
}
