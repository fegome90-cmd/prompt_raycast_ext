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
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout, ...fetchOptions } = options;

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
