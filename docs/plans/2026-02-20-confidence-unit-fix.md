# Implementation Plan: Fix Confidence Unit Mismatch and Redundant Fallback

> Created: 2026-02-20
> Status: COMPLETED
> Priority: MEDIUM

## Overview

This plan addresses two code quality issues identified in the code review:
1. **CRITICAL**: Confidence is stored internally as 0-1 but `Typography.confidence()` expects 0-100, causing display bugs (e.g., "1%" instead of "80%")
2. **SUGGESTION**: Redundant fallback logic in `improvePrompt.ts:144` is dead code since Zod schema already guarantees non-null

## Requirements

- Confidence stored internally as 0-1 (required by `SessionManager.shouldEnableWizard()`)
- Confidence displayed as 0-100 percentage (expected by users)
- Remove redundant fallback `dspyResult.confidence || 0.8` in `improvePrompt.ts:144`
- Maintain backward compatibility
- 80%+ test coverage for affected modules

## Architecture Analysis

### Current Data Flow

```
Backend (DSPy) returns 0-1
     |
     v
dspyPromptImprover.ts (Zod transform: nullish → 0.8 default)
     |
     v
improvePrompt.ts (DEAD CODE: confidence || 0.8 fallback)
     |
     v
SessionManager (expects 0-1, threshold < 0.7)  <-- CORRECT
     |
     v
Typography.confidence() (expects 0-100)        <-- BUG
     |
     v
promptify-quick.tsx (displays Math.round(confidence) + "%")
```

### Root Cause Analysis

**Issue 1**: The bug is in `Typography.confidence()` at line 17 - it calls `Math.round(score)` directly without multiplying by 100, so a confidence of 0.8 becomes `Math.round(0.8) = 1`, displayed as "1%".

**Issue 2**: In `improvePrompt.ts:144`, the code `confidence: dspyResult.confidence || 0.8` is dead code because the Zod schema in `dspyPromptImprover.ts` already transforms nullish values to `DEFAULT_CONFIDENCE` (0.8).

## Affected Files

| File | Change Type | Description |
|------|-------------|-------------|
| `dashboard/src/core/design/typography.ts` | BUG FIX | Multiply by 100 before rounding |
| `dashboard/src/core/design/__tests__/typography.test.ts` | NEW | Add unit tests for confidence formatting |
| `dashboard/src/core/llm/improvePrompt.ts` | CLEANUP | Remove dead code fallback at line 144 |
| `dashboard/src/core/llm/__tests__/improvePrompt.test.ts` | UPDATE | Add test for confidence passthrough |

## Implementation Steps

### Phase 1: Test Coverage (TDD - RED)

**Complexity:** Low
**Dependencies:** None

1. **Create Typography Tests** (File: `dashboard/src/core/design/__tests__/typography.test.ts`)
   - Action: Create new test file with comprehensive coverage for `Typography.confidence()` and `Typography.confidenceIcon()`
   - Why: TDD requires writing failing tests first
   - Dependencies: None
   - Risk: Low

   Test cases needed:
   ```typescript
   describe("Typography.confidence", () => {
     it("should format 0-1 range as percentage (multiply by 100)", () => {
       expect(Typography.confidence(0.8)).toBe("◉ 80%");
       expect(Typography.confidence(0.65)).toBe("◎ 65%");
       expect(Typography.confidence(0.3)).toBe("○ 30%");
     });

     it("should handle edge cases", () => {
       expect(Typography.confidence(0)).toBe("○ 0%");
       expect(Typography.confidence(1)).toBe("◉ 100%");
       expect(Typography.confidence(0.799)).toBe("◎ 80%"); // rounds to 80
     });

     it("should show high confidence icon for >=80%", () => {
       expect(Typography.confidence(0.8)).toContain("◉");
       expect(Typography.confidence(0.95)).toContain("◉");
     });

     it("should show medium confidence icon for 60-79%", () => {
       expect(Typography.confidence(0.6)).toContain("◎");
       expect(Typography.confidence(0.7)).toContain("◎");
     });

     it("should show low confidence icon for <60%", () => {
       expect(Typography.confidence(0.5)).toContain("○");
       expect(Typography.confidence(0.1)).toContain("○");
     });
   });

   describe("Typography.confidenceIcon", () => {
     it("should return correct icons for 0-1 range", () => {
       expect(Typography.confidenceIcon(0.8)).toBe("◉");
       expect(Typography.confidenceIcon(0.5)).toBe("◎");
       expect(Typography.confidenceIcon(0.3)).toBe("○");
     });
   });
   ```

2. **Add improvePrompt Confidence Test** (File: `dashboard/src/core/llm/__tests__/improvePrompt.test.ts`)
   - Action: Add test case verifying confidence is passed through without redundant fallback
   - Why: Document expected behavior and catch regressions
   - Dependencies: None
   - Risk: Low

### Phase 2: Bug Fix (TDD - GREEN)

**Complexity:** Low
**Dependencies:** Phase 1 complete

3. **Fix Typography.confidence()** (File: `dashboard/src/core/design/typography.ts`)
   - Action: Multiply input by 100 before processing
   - Why: Confidence is stored as 0-1 internally, needs conversion for display
   - Dependencies: Tests from Phase 1 must fail first
   - Risk: Low

   Current code (lines 16-23):
   ```typescript
   static confidence(score: number): string {
     const rounded = Math.round(score);  // BUG: doesn't multiply
     if (rounded >= 80) return `◉ ${rounded}%`;
     // ...
   }
   ```

   Fixed code:
   ```typescript
   static confidence(score: number): string {
     // Input is 0-1 range (from DSPy backend)
     // Convert to 0-100 for display
     const percentage = score * 100;
     const rounded = Math.round(percentage);
     if (rounded >= 80) return `◉ ${rounded}%`;
     if (rounded >= 60) return `◎ ${rounded}%`;
     if (rounded >= 40) return `○ ${rounded}%`;
     return `○ ${rounded}%`;
   }
   ```

4. **Fix Typography.confidenceIcon()** (File: `dashboard/src/core/design/typography.ts`)
   - Action: Apply same fix (multiply by 100)
   - Why: Consistency with `confidence()` method
   - Dependencies: None (same file)
   - Risk: Low

   Fixed code:
   ```typescript
   static confidenceIcon(score: number): string {
     const percentage = score * 100;
     const rounded = Math.round(percentage);
     if (rounded >= 70) return "◉";
     if (rounded >= 40) return "◎";
     return "○";
   }
   ```

### Phase 3: Dead Code Removal

**Complexity:** Low
**Dependencies:** None (independent of Phase 1/2)

5. **Remove Redundant Fallback** (File: `dashboard/src/core/llm/improvePrompt.ts`)
   - Action: Remove `|| 0.8` fallback at line 144
   - Why: Zod schema already guarantees non-null value
   - Dependencies: None
   - Risk: Low

   Current code (line 144):
   ```typescript
   confidence: dspyResult.confidence || 0.8,
   ```

   Fixed code:
   ```typescript
   confidence: dspyResult.confidence,
   ```

### Phase 4: Verification

**Complexity:** Low
**Dependencies:** Phases 1-3 complete

6. **Run Tests and Verify**
   - Action: Run `npm run test` and verify all tests pass
   - Why: Ensure no regressions
   - Dependencies: All changes complete
   - Risk: Low

7. **Manual Integration Test**
   - Action: Run `npm run dev` in Raycast, test with real prompt
   - Why: Verify display shows correct percentage (e.g., "80%" not "1%")
   - Dependencies: Tests pass
   - Risk: Low

## Testing Strategy

### Unit Tests
- **New file**: `dashboard/src/core/design/__tests__/typography.test.ts`
  - Test `confidence()` with 0-1 input range
  - Test `confidenceIcon()` with 0-1 input range
  - Test edge cases (0, 1, 0.5, negative, >1)
  - Test icon thresholds

### Integration Tests
- **Existing**: `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`
  - Already tests confidence thresholds (0.7) correctly
  - No changes needed, but verify they still pass

### Coverage Target
- Typography module: 100% (small module, easy to cover)
- improvePrompt changes: Covered by existing tests

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking SessionManager threshold logic | LOW | SessionManager uses 0-1 range, we keep internal storage as 0-1 |
| Existing code passes confidence as 0-100 somewhere | MEDIUM | Search codebase for confidence usages; all found usages expect 0-1 |
| Typography used elsewhere with 0-100 input | LOW | Code review shows no such usage; promptify-quick.tsx passes confidence from DSPy (0-1) |

## Success Criteria

- [ ] `Typography.confidence(0.8)` returns `"◉ 80%"` (not `"◉ 1%"`)
- [ ] `Typography.confidenceIcon(0.8)` returns `"◉"` (not `"○"`)
- [ ] Dead code removed from `improvePrompt.ts:144`
- [ ] All existing tests pass
- [ ] New typography tests pass with 100% coverage
- [ ] SessionManager tests continue to pass (threshold logic unchanged)
- [ ] Manual test shows correct percentage in Raycast UI

## Estimated Complexity

| Phase | Effort | Risk |
|-------|--------|------|
| Phase 1: Tests | 30 min | Low |
| Phase 2: Bug Fix | 15 min | Low |
| Phase 3: Cleanup | 5 min | Low |
| Phase 4: Verify | 15 min | Low |
| **Total** | **~1 hour** | **Low** |
