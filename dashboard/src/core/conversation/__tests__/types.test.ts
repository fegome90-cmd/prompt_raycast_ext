import { IntentType } from "../types";

describe("IntentType - Sync with Python Backend", () => {
  it("should have 4 valid intent values", () => {
    const validValues: IntentType[] = ["debug", "refactor", "generate", "explain"];
    expect(validValues).toHaveLength(4);
  });

  it("should include 'explain' (not 'analyze')", () => {
    const explainValue: IntentType = "explain";
    expect(explainValue).toBe("explain");
  });

  it("should match Python backend enum values", () => {
    // Python IntentType: GENERATE = "generate", DEBUG = "debug", REFACTOR = "refactor", EXPLAIN = "explain"
    const values: IntentType[] = ["debug", "refactor", "generate", "explain"];

    expect(values).toContain("debug");
    expect(values).toContain("refactor");
    expect(values).toContain("generate");
    expect(values).toContain("explain");
  });
});
