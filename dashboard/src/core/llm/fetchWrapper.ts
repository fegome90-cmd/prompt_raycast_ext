/**
 * Fetch compatibility layer for Raycast extension
 * Uses native fetch (Node 18+) with consistent interface
 */

export interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Wrapper around native fetch with timeout support
 * Matches the interface used by existing node-fetch code
 */
export async function fetchWithTimeout(url: string, options: FetchOptions = {}): Promise<Response> {
  const { timeout, ...fetchOptions } = options;

  // ⚡ INVARIANT: AbortController lifecycle for timeout enforcement
  //
  // The timeout mechanism relies on a specific sequence:
  // 1. Create AbortController before fetch
  // 2. Start timeout that calls controller.abort() after delay
  // 3. Pass signal to fetch so abort cancels the request
  // 4. ALWAYS clear timeout in finally block (prevents memory leaks)
  //
  // ⚡ DO NOT move clearTimeout outside finally - would leak on abort
  // ⚡ DO NOT remove the finally block - timeout must always be cleared
  // ⚡ DO NOT use controller.signal after finally - controller is aborted
  //
  // Context: This pattern prevents fetch from hanging indefinitely
  if (timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      return await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutId);
    }
  }

  return await fetch(url, fetchOptions);
}
