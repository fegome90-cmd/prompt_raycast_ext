import { Toast, showToast } from "@raycast/api";

export class ToastHelper {
  /**
   * Show success toast with details
   */
  static async success(title: string, message?: string) {
    return await showToast({
      style: Toast.Style.Success,
      title,
      message,
    });
  }

  /**
   * Show error toast with actionable hint
   */
  static async error(title: string, error: Error | string, hint?: string) {
    const message = error instanceof Error ? error.message : error;
    const fullMessage = hint ? `${message} — ${hint}` : message;

    return await showToast({
      style: Toast.Style.Failure,
      title,
      message: fullMessage,
    });
  }

  /**
   * Show animated loading toast
   */
  static async loading(title: string, message?: string) {
    return await showToast({
      style: Toast.Style.Animated,
      title,
      message,
    });
  }
}
