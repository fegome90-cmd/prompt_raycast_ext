import { describe, it, expect } from "vitest";
import { Typography } from "../typography";

describe("Typography.confidence", () => {
  it("should format 0-1 range as percentage (multiply by 100)", () => {
    expect(Typography.confidence(0.7)).toBe("◉ 70%");
    expect(Typography.confidence(0.5)).toBe("◎ 50%");
    expect(Typography.confidence(0.3)).toBe("○ 30%");
  });

  it("should handle edge cases", () => {
    expect(Typography.confidence(0)).toBe("○ 0%");
    expect(Typography.confidence(1)).toBe("◉ 100%");
    expect(Typography.confidence(0.699)).toBe("◉ 70%"); // 69.9 rounds to 70, hits high threshold
  });

  it("should show high confidence icon for >=70%", () => {
    expect(Typography.confidence(0.7)).toContain("◉");
    expect(Typography.confidence(0.95)).toContain("◉");
  });

  it("should show medium confidence icon for 40-69%", () => {
    expect(Typography.confidence(0.4)).toContain("◎");
    expect(Typography.confidence(0.5)).toContain("◎");
  });

  it("should show low confidence icon for <40%", () => {
    expect(Typography.confidence(0.3)).toContain("○");
    expect(Typography.confidence(0.1)).toContain("○");
  });

  it("should clamp values below 0 to 0%", () => {
    expect(Typography.confidence(-0.5)).toBe("○ 0%");
    expect(Typography.confidence(-10)).toBe("○ 0%");
  });

  it("should clamp values above 1 to 100%", () => {
    expect(Typography.confidence(1.5)).toBe("◉ 100%");
    expect(Typography.confidence(50)).toBe("◉ 100%");
  });
});

describe("Typography.confidenceIcon", () => {
  it("should return correct icons for 0-1 range", () => {
    expect(Typography.confidenceIcon(0.8)).toBe("◉"); // 80% >= 70%
    expect(Typography.confidenceIcon(0.5)).toBe("◎"); // 50% >= 40%
    expect(Typography.confidenceIcon(0.3)).toBe("○"); // 30% < 40%
  });

  it("should handle edge cases", () => {
    expect(Typography.confidenceIcon(0)).toBe("○"); // 0%
    expect(Typography.confidenceIcon(1)).toBe("◉"); // 100%
    expect(Typography.confidenceIcon(0.7)).toBe("◉"); // 70% is threshold
  });

  it("should clamp values below 0 to 0%", () => {
    expect(Typography.confidenceIcon(-0.5)).toBe("○");
    expect(Typography.confidenceIcon(-10)).toBe("○");
  });

  it("should clamp values above 1 to 100%", () => {
    expect(Typography.confidenceIcon(1.5)).toBe("◉");
    expect(Typography.confidenceIcon(50)).toBe("◉");
  });
});
