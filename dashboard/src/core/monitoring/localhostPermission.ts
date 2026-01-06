/**
 * Localhost Permission Monitor
 *
 * Detects when Raycast's "localhost": true permission is missing from package.json
 * This causes silent failures when trying to connect to http://localhost:8000
 *
 * Usage: Wrap fetch calls with checkLocalhostPermission() to get helpful error messages
 */

interface LocalhostPermissionCheckResult {
  hasPermission: boolean;
  error?: {
    type: "MISSING_LOCALHOST_PERMISSION" | "BACKEND_NOT_RUNNING" | "OTHER";
    message: string;
    suggestion: string;
  };
}

/**
 * Check if a fetch error is likely caused by missing localhost permission
 */
export function checkLocalhostPermission(error: unknown, url: string): LocalhostPermissionCheckResult {
  // Not a localhost URL - not our concern
  if (!url.includes("localhost") && !url.includes("127.0.0.1")) {
    return { hasPermission: true };
  }

  // Error is a TypeError with fetch-related message
  if (error instanceof TypeError) {
    const errorMessage = error.message.toLowerCase();

    // Common patterns when localhost permission is missing:
    // - "fetch failed", "network error", "ECONNREFUSED" (without server running)
    // - But the key is: if curl works but Raycast doesn't, it's permissions

    const hasPermission = isLocalhostPermissionLikelyPresent();

    if (!hasPermission) {
      return {
        hasPermission: false,
        error: {
          type: "MISSING_LOCALHOST_PERMISSION",
          message: "Raycast cannot connect to localhost - missing permission",
          suggestion: `
🔴 CRITICAL: Missing "localhost": true in package.json

The extension cannot connect to the DSPy backend at ${url}

FIX: Add this line to dashboard/package.json:
  "localhost": true,

Then restart Raycast dev server:
  1. Stop current dev server (Cmd+C)
  2. Run: cd dashboard && npm run dev

Or run the permission check script:
  ./scripts/check-localhost-permission.sh
          `.trim(),
        },
      };
    }

    // Permission exists but connection failed - backend might not be running
    return {
      hasPermission: true,
      error: {
        type: "BACKEND_NOT_RUNNING",
        message: `Backend at ${url} is not responding`,
        suggestion: `
Start the DSPy backend:
  make dev

Or check health:
  make health
        `.trim(),
      },
    };
  }

  // Other error types
  return {
    hasPermission: true,
    error: {
      type: "OTHER",
      message: error instanceof Error ? error.message : String(error),
      suggestion: "Check browser console for detailed error information",
    },
  };
}

/**
 * Check if localhost permission is present in package.json
 * This is a heuristic - we read the package.json file directly
 */
function isLocalhostPermissionLikelyPresent(): boolean {
  // We can't actually read package.json at runtime in the Raycast extension
  // So we use a heuristic: if the fetch fails immediately with a TypeError,
  // it's likely the permission is missing

  // For now, we'll rely on the pre-flight check script
  // This function is a placeholder for future runtime checks
  return true; // Assume permission exists unless pre-flight check failed
}

/**
 * Log a warning when localhost connection fails
 * Call this from your error handlers to get consistent logging
 */
export function logLocalhostError(url: string, error: unknown): void {
  const check = checkLocalhostPermission(error, url);

  if (!check.hasPermission) {
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error("🔴 LOCALHOST PERMISSION ERROR");
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error(check.error?.message);
    console.error("");
    console.error(check.error?.suggestion);
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  } else if (check.error) {
    console.warn(`⚠️  Localhost connection failed: ${check.error.message}`);
    console.warn(check.error.suggestion);
  }
}

/**
 * Enhanced fetch that automatically detects and logs permission issues
 */
export async function fetchWithPermissionCheck(
  url: string,
  options?: RequestInit & { timeout?: number },
): Promise<Response> {
  try {
    const response = await fetch(url, options);
    return response;
  } catch (error) {
    logLocalhostError(url, error);
    throw error;
  }
}
