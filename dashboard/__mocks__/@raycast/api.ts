/**
 * Mock for @raycast/api in tests.
 * Provides minimal implementations for testing pure utility functions.
 */

import { vi } from "vitest";

export const showToast = vi.fn();
export const showHUD = vi.fn();
export const Clipboard = {
  copy: vi.fn(),
  paste: vi.fn(),
  read: vi.fn(),
};
export const LocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
export const environment = {
  commandName: "test-command",
  extensionName: "test-extension",
};
export const getPreferenceValues = vi.fn(() => ({
  dspyBaseUrl: "http://localhost:8000",
  ollamaBaseUrl: "http://localhost:11434",
  executionMode: "nlac",
  model: "test-model",
  fallbackModel: "test-fallback-model",
  preset: "structured",
  timeoutMs: "120000",
}));
export const Action = {
  OpenInBrowser: class {},
  CopyToClipboard: class {},
  Paste: class {},
};
export const ActionPanel = class {
  static Section = class {};
};
export const Form = class {
  static TextField = class {};
  static TextArea = class {};
  static Divider = class {};
  static Description = class {};
};
export const Icon = {
  Circle: "circle.png",
  Document: "document.png",
  List: "list.png",
};
export const List = class {
  static Item = class {};
  static Section = class {};
  static EmptyView = class {};
};
export const Color = {
  PrimaryText: "#FFFFFF",
  SecondaryText: "#888888",
};
export const Detail = vi.fn(({ markdown, actions }) => ({
  type: "detail",
  markdown,
  actions,
}));
export const showToastError = vi.fn();
export const showToastSuccess = vi.fn();
