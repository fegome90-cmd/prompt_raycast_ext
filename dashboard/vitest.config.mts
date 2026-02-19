import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/**",
        "dist/**",
        "**/*.test.ts",
        "**/*.spec.ts",
        "scripts/**",
        "testdata/**",
        "eval/**",
        "docs/**",
      ],
    },
    server: {
      deps: {
        external: ["@raycast/api"],
      },
    },
  },
  resolve: {
    conditions: ["node"],
    alias: {
      "@raycast/api": path.resolve(__dirname, "__mocks__/@raycast/api.ts"),
    },
  },
});

