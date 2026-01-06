/**
 * Configuration loader and validator
 * Single source of truth for all application settings
 */

import { getPreferenceValues } from "@raycast/api";
import { DEFAULTS } from "./defaults";
import { AppConfig, validateConfig } from "./schema";

/**
 * Raw preferences from Raycast (untyped)
 */
type RawPreferences = Record<string, unknown>;

/**
 * Configuration state
 */
interface ConfigState {
  config: AppConfig;
  safeMode: boolean;
  errors: string[];
  source: "preferences" | "defaults";
}

let configCache: ConfigState | null = null;

/**
 * Load configuration from all sources with fail-safe fallback
 * @returns Validated configuration with metadata
 */
export function loadConfig(): ConfigState {
  // Return cached config if available
  if (configCache) {
    return configCache;
  }

  try {
    // Try loading from Raycast preferences
    const rawPrefs = getPreferenceValues<RawPreferences>();
    const merged = mergeWithDefaults(rawPrefs);
    const validated = validateConfig(merged);

    configCache = {
      config: JSON.parse(JSON.stringify(validated)) as AppConfig,
      safeMode: false,
      errors: [],
      source: "preferences" as const,
    };

    return configCache;
  } catch (error) {
    // On error, activate safe mode with defaults
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Log error for debugging
    console.error("[Config] Failed to load config, activating safe mode:", errorMessage);

    // Use defaults as fallback (never fails because defaults are pre-validated)
    // Clone DEFAULTS to avoid readonly issues
    const safeConfig = {
      config: JSON.parse(JSON.stringify(DEFAULTS)) as AppConfig,
      safeMode: true,
      errors: [errorMessage],
      source: "defaults" as const,
    };

    configCache = safeConfig;
    return safeConfig;
  }
}

/**
 * Load configuration without caching (for testing)
 */
export function loadConfigFresh(): ConfigState {
  configCache = null;
  return loadConfig();
}

/**
 * Clear configuration cache
 * Useful when preferences change
 */
export function clearConfigCache(): void {
  configCache = null;
}

/**
 * Is safe mode active?
 * When true, only core features are available
 */
export function isSafeMode(): boolean {
  // Check feature flag first (manual override)
  const prefs = getPreferenceValues<RawPreferences>();
  const manualSafeMode = prefs["safeMode"] as boolean | undefined;

  if (manualSafeMode === true) {
    return true;
  }

  // Otherwise check from loaded config
  const state = loadConfig();
  return state.safeMode;
}

/**
 * Get safe mode errors (empty array if not in safe mode)
 */
export function getSafeModeErrors(): string[] {
  const state = loadConfig();
  return state.safeMode ? state.errors : [];
}

/**
 * Get configuration source
 * Returns whether we loaded from preferences or fell back to defaults
 */
export function getConfigSource(): "preferences" | "defaults" {
  const state = loadConfig();
  return state.source;
}

/**
 * Merge raw preferences with defaults
 * Fills in missing values with defaults, validates structure
 */
export function mergeWithDefaults(rawPrefs: RawPreferences): Record<string, unknown> {
  // Start with deep copy of defaults
  const merged = JSON.parse(JSON.stringify(DEFAULTS)) as Record<string, unknown>;

  // Helper to safely set nested values
  const setNested = (obj: Record<string, unknown>, path: string[], value: unknown): void => {
    if (!path.length) return;

    let current = obj;
    for (let i = 0; i < path.length - 1; i++) {
      const key = path[i];
      if (!(key in current) || typeof current[key] !== "object" || current[key] === null) {
        return; // Skip if path doesn't exist in defaults
      }
      current = current[key] as Record<string, unknown>;
    }

    const lastKey = path[path.length - 1];
    current[lastKey] = value;
  };

  // Helper to convert snake_case to camelCase for nested paths
  const toCamelCase = (str: string): string => {
    return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
  };

  // Flatten prefs for easier processing
  const flattenPrefs = (obj: Record<string, unknown>, prefix = ""): Record<string, unknown> => {
    const result: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(obj)) {
      const newKey = prefix ? `${prefix}.${key}` : key;

      if (value !== null && typeof value === "object" && !Array.isArray(value) && !(value instanceof Date)) {
        Object.assign(result, flattenPrefs(value as Record<string, unknown>, newKey));
      } else {
        result[newKey] = value;
      }
    }

    return result;
  };

  // Process preferences and override defaults
  const flatPrefs = flattenPrefs(rawPrefs);

  for (const [key, value] of Object.entries(flatPrefs)) {
    // Skip undefined values
    if (value === undefined) continue;

    // Convert key to path (handle both dot notation and nested objects)
    const path = key.split(".").map(toCamelCase);

    // Only set if path exists in defaults (prevents adding unknown config)
    try {
      // Validate the partial path exists
      let current = DEFAULTS as Record<string, unknown>;
      for (let i = 0; i < path.length; i++) {
        const key = path[i];
        if (!(key in current)) {
          throw new Error(`Unknown config path: ${path.join(".")}`);
        }
        if (i < path.length - 1) {
          current = current[key] as Record<string, unknown>;
        }
      }

      // Set the value
      setNested(merged, path, value);
    } catch {
      // Silently skip unknown config paths (backwards compatibility)
      continue;
    }
  }

  return merged;
}

/**
 * Get a specific config value by path
 * Example: getConfigValue("ollama.timeoutMs")
 */
export function getConfigValue<T>(path: string): T {
  const state = loadConfig();
  const keys = path.split(".");

  let current: unknown = state.config;
  for (const key of keys) {
    if (!current || typeof current !== "object" || !(key in current)) {
      throw new Error(`Config path not found: ${path}`);
    }
    current = (current as Record<string, unknown>)[key];
  }

  return current as T;
}

/**
 * Update configuration at runtime (for testing only)
 * Clears cache and reloads from preferences
 */
export function reloadConfig(): void {
  clearConfigCache();
  loadConfig();
}

/**
 * Validate configuration without loading (for testing)
 */
export function validateConfigOnly(config: unknown): {
  valid: boolean;
  errors: string[];
  config?: AppConfig;
} {
  try {
    const validated = validateConfig(config);
    return { valid: true, errors: [], config: validated };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return { valid: false, errors: [errorMessage] };
  }
}

/**
 * Safe mode indicator for UI
 * Returns human-readable status
 */
export function getConfigStatus(): {
  status: "ok" | "safe" | "error";
  message: string;
  errors: string[];
} {
  const state = loadConfig();

  if (!state.safeMode && !state.errors.length) {
    return {
      status: "ok",
      message: "Configuration loaded successfully from preferences",
      errors: [],
    };
  }

  if (state.safeMode) {
    return {
      status: "safe",
      message: "Safe mode active - using defaults due to configuration error",
      errors: state.errors,
    };
  }

  return {
    status: "error",
    message: "Configuration loaded with warnings",
    errors: state.errors,
  };
}
