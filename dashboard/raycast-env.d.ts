/// <reference types="@raycast/api">

/* 🚧 🚧 🚧
 * This file is auto-generated from the extension's manifest.
 * Do not modify manually. Instead, update the `package.json` file.
 * 🚧 🚧 🚧 */

/* eslint-disable @typescript-eslint/ban-types */

type ExtensionPreferences = {}

/** Preferences accessible in all the extension's commands */
declare type Preferences = ExtensionPreferences

declare namespace Preferences {
  /** Preferences accessible in the `promptify-quick` command */
  export type PromptifyQuick = ExtensionPreferences & {
  /** Ollama Base URL - Base URL for Ollama */
  "ollamaBaseUrl": unknown,
  /** DSPy Base URL - Base URL for DSPy backend */
  "dspyBaseUrl": unknown,
  /** DSPy Enabled - Enable DSPy backend (fallbacks to Ollama if off) */
  "dspyEnabled": boolean,
  /** Model - Ollama model name */
  "model": unknown,
  /** Fallback Model - Fallback Ollama model name (used only if the primary model fails) */
  "fallbackModel": unknown,
  /** Preset - Improvement style preset */
  "preset": "structured" | "default" | "specific" | "coding",
  /** Timeout (ms) - Timeout for Ollama calls */
  "timeoutMs": unknown
}
}

declare namespace Arguments {
  /** Arguments passed to the `promptify-quick` command */
  export type PromptifyQuick = {}
}

