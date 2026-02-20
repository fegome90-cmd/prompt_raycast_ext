// dashboard/src/core/__tests__/constants.test.ts
import { describe, it, expect } from "vitest";
import { STAGE_MESSAGES, ENGINE_NAMES, type LoadingStage } from "../constants";

describe("constants", () => {
  describe("STAGE_MESSAGES", () => {
    it("contains all LoadingStage keys", () => {
      const stages: LoadingStage[] = ["idle", "validating", "connecting", "analyzing", "improving", "success", "error"];
      stages.forEach((stage) => {
        expect(STAGE_MESSAGES).toHaveProperty(stage);
      });
    });

    it("has non-empty strings for non-idle stages", () => {
      const nonIdleStages: LoadingStage[] = ["validating", "connecting", "analyzing", "improving", "success", "error"];
      nonIdleStages.forEach((stage) => {
        expect(STAGE_MESSAGES[stage].length).toBeGreaterThan(0);
      });
    });

    it("has empty string for idle stage", () => {
      expect(STAGE_MESSAGES.idle).toBe("");
    });
  });

  describe("ENGINE_NAMES", () => {
    it("contains dspy and ollama keys", () => {
      expect(ENGINE_NAMES).toHaveProperty("dspy");
      expect(ENGINE_NAMES).toHaveProperty("ollama");
    });

    it("has non-empty display names", () => {
      expect(ENGINE_NAMES.dspy.length).toBeGreaterThan(0);
      expect(ENGINE_NAMES.ollama.length).toBeGreaterThan(0);
    });

    it("dspy name indicates Haiku model", () => {
      expect(ENGINE_NAMES.dspy.toLowerCase()).toContain("haiku");
    });
  });
});
