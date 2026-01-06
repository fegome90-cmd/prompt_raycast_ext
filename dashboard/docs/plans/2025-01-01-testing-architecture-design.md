# Testing, Evaluation, and Telemetry Architecture Design

**Date:** 2025-01-01
**Project:** Prompt Renderer Local (Raycast Extension)
**Author:** Designed with superpowers brainstorming skill
**Status:** Approved - Ready for implementation

## Executive Summary

Comprehensive architecture for testing, evaluation, and telemetry of the Raycast "Prompt Renderer Local" extension. This system addresses the critical bug where prompt engineering is not performing (output ≈ input) due to incorrect Ollama API usage, while establishing long-term quality guards.

**Root Cause Identified:** Using `/api/generate` endpoint concatenates system pattern with user input, preventing the Novaeus-Promptist-7B model from distinguishing instructions from data.

**Solution:** Migrate to `/api/chat` with proper system/user message separation, wrapped in comprehensive testing infrastructure.

---

## 1. Architecture Overview

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: Orchestration                                   │
├─────────────────────────────────────────────────────────┤
│ • Vitest: Unit tests (fast, isolated)                   │
│ • Eval CLI: Integration tests (real Ollama calls)       │
│ • Pre-commit hooks: Regression guards                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: Evaluation                                      │
├─────────────────────────────────────────────────────────┤
│ • Quality Metrics: JSON validity, copyability, latency  │
│ • Pattern Compliance: Anti-pattern detection            │
│ • Baseline Comparison: Regression detection             │
│ • Semantic Quality: DeepEval faithfulness scores        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: Data                                            │
├─────────────────────────────────────────────────────────┤
│ • Test Cases: Golden dataset + edge cases               │
│ • Baselines: Versioned reference outputs                │
│ • Metrics Store: Historical performance data            │
└─────────────────────────────────────────────────────────┘
```

### Key Principles

- **Local-First:** All tools run locally, no external services
- **Fast Feedback:** Unit tests < 5s, pre-commit < 30s
- **High ROI:** Tools selected for maximum value with minimal complexity
- **YAGNI:** Implement only what's needed, defer complexity

---

## 2. Tools Selection

### Chosen Stack

| Tool | Purpose | Why High ROI? |
|------|---------|---------------|
| **Vitest** | Unit testing | Already configured, Jest-compatible, fast |
| **DeepEval** | Semantic quality | Local LLM-as-judge, measures faithfulness/relevance without API calls |
| **Husky** | Pre-commit hooks | Simple git hooks integration, prevents bad commits |
| **tsx** | TypeScript execution | Already in project, runs eval scripts directly |

### Tools Considered and Rejected

| Tool | Rejected Because |
|------|------------------|
| Playwright | Overkill for CLI tool, Raycast has its own testing |
| GitHub Actions | User prefers local-first, cloud dependency |
| Custom LLM judge | DeepEval already implements this well |

---

## 3. Data Flow

### Evaluation Pipeline

```
1. INPUT: Test Dataset
   testdata/cases.jsonl → 50 representative prompts
   testdata/golden.jsonl → 10 critical prompts (must pass)

2. EXECUTE: Improve Prompt
   For each test case:
   • Call improvePromptWithOllama()
   • Capture: input, output, latency, model used

3. VALIDATE: 3-Level Cascade
   Level 1 (Structural): JSON valid? → Fast fail if invalid
   Level 2 (Content): Placeholders? Banned content? → Retry with repair
   Level 3 (Semantic): Faithfulness < 0.7? → Warning only

4. MEASURE: Quality Metrics
   • jsonValidPass1: % valid on first try
   • copyableRate: % ready to paste (no manual review needed)
   • reviewRate: % requiring manual review (lower = better UX)
   • latencyP50/P95: Performance tracking

5. COMPARE: Baseline
   Current run vs baseline-v2.json
   • Detect regressions (>2% drop in metrics)
   • Track improvements

6. OUTPUT: Results
   eval/latest.json → Detailed per-case results
   eval/reports/latest.md → Human-readable summary
   eval/metrics/history.jsonl → Append-only metrics for trends
```

### Error Recovery Flow

```
Validation Error (Level 1 or 2)
    ↓
Attempt Repair (add explicit instructions)
    ↓
Retry improvePromptWithOllama()
    ↓
    ├─→ Success → Record as "repaired"
    └─→ Fail → Mark as "failed" with error details
```

---

## 4. Error Handling and Validation

### 3-Level Validation Cascade

```typescript
export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly level: 'structural' | 'content' | 'semantic',
    public readonly recoverable: boolean
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

export async function validateWithFallback(
  result: PromptResult,
  testCase: TestCase
): Promise<{ valid: boolean; errors: ValidationError[] }> {
  const errors: ValidationError[] = [];

  // Level 1: Structural Validation (Fast fail)
  try {
    JSON.parse(result.improved_prompt);
  } catch (e) {
    errors.push(new ValidationError(
      'Output is not valid JSON',
      'structural',
      false  // Not recoverable
    ));
    return { valid: false, errors };
  }

  // Level 2: Content Validation (Retry with repair)
  if (hasPlaceholders(result.improved_prompt)) {
    errors.push(new ValidationError(
      'Output contains placeholders like {{}}',
      'content',
      true  // Recoverable - retry with repair prompt
    ));
  }

  if (hasBannedContent(result.improved_prompt, DEFAULTS.quality.bannedSnippets)) {
    errors.push(new ValidationError(
      'Output contains meta-instructions (model leaked prompt)',
      'content',
      true  // Recoverable
    ));
  }

  // Level 3: Semantic Validation (Warning only)
  const faithfulness = await measureFaithfulness({
    input: testCase.input,
    output: result.improved_prompt,
    context: testCase.expected_output
  });

  if (faithfulness < DEFAULTS.quality.minConfidence) {
    errors.push(new ValidationError(
      `Low faithfulness score: ${faithfulness}`,
      'semantic',
      false  // Warning only, don't retry
    ));
  }

  return {
    valid: errors.filter(e => e.level !== 'semantic').length === 0,
    errors
  };
}
```

### Recovery Strategy

- **Structural failures:** Fail fast, log error, continue with next test case
- **Content failures:** Retry once with repair prompt that explicitly instructs model to remove placeholders/meta-content
- **Semantic failures:** Log warning, don't retry (requires human judgment)

---

## 5. Testing and Validation Strategy

### Unit Testing Strategy

**Components to test:**
- `src/core/eval/metrics.ts`: Each metric function with mocked LLM responses
- `src/core/eval/validation.ts`: 3-level cascade with synthetic failure cases
- `src/core/eval/regression.ts`: Baseline comparison logic

**Test pattern:**
```typescript
describe('FaithfulnessMetric', () => {
  it('should score high when prompt matches intent', async () => {
    const mockLLM = mockOpenAI({
      '0.9': 'The output clearly addresses the user request'
    });
    const score = await faithfulness({
      input: 'Write a function',
      output: 'Here is a function that...',
      context: mockLLM
    });
    expect(score).toBeGreaterThan(0.8);
  });
});
```

### Integration Testing Strategy

**Objective:** Validate `/api/chat` migration

**Critical tests:**
1. **System Message Separation:** Verify `systemPattern` goes to `system` field, not `messages[0]`
2. **Response Structure:** Validate parsing `message.content` not `response`
3. **Fallback Logic:** Prove fallbackModel activates only on specific errors

**Test data:**
```typescript
const testCases = [
  {
    name: 'system message separation',
    input: 'write hello world',
    pattern: 'You are a coding expert',
    expectedSystemField: 'You are a coding expert',
    expectedUserField: 'write hello world'
  }
];
```

### E2E Testing Strategy

**Complete pipeline:** Input → Ollama → Validation → Metrics → Report

**Scenarios:**
1. **Happy Path:** Valid input → Valid JSON → Score > 0.7
2. **Repair Flow:** Input with placeholders → Retry → Repaired output
3. **Fallback Flow:** Primary model fails → Secondary model succeeds
4. **Regression:** Pattern.md changes → Baseline comparison detects degrade

### Test Data Management

**Baselines:**
- `eval/baseline-v2.json`: Current accepted "correct" output
- `testdata/cases.jsonl`: 50 representative test cases
- `testdata/edge-cases.jsonl`: Known problematic inputs

**Golden Dataset:**
- 10 hand-crafted prompts that MUST pass
- If any fail, block deployment
- Located at `testdata/golden.jsonl`

### CI/CD Integration

**Local-first approach:**
```bash
# Pre-commit hook
.husky/pre-commit → npm run eval -- --dataset testdata/golden.jsonl

# Manual before major changes
npm run eval -- --full --baseline eval/baseline-v2.json
```

### Performance Testing

**Thresholds in `defaults.ts`:**
```typescript
eval: {
  gates: {
    jsonValidPass1: 0.54,      // 54% minimum first-pass validity
    copyableRate: 0.54,        // 54% minimum copyable outputs
    reviewRateMax: 0.55,       // Max 55% requiring review (UX friction)
    latencyP95Max: 12_000,     // Max 12s P95 latency
    patternsDetectedMin: 10    // Minimum pattern detection
  }
}
```

**Tracking:**
```typescript
const metrics = {
  latency: await measureLatency(() => improvePrompt(input)),
  timestamp: Date.now(),
  model: 'Novaeus-Promptist-7B'
};
// Append to eval/metrics/history.jsonl
```

---

## 6. Implementation Phases

### Phase 0: Foundation (CRITICAL) - Week 1

**Objective:** Migrate to `/api/chat` to fix root cause

**Tasks:**
1. Create `ollamaChat.ts` with `/api/chat` endpoint
2. Update `improvePrompt.ts` to use `ollamaChat`
3. Add integration tests for system/user separation
4. Update all callers

**Success Criteria:**
- System pattern in `system` field, not `messages[0]`
- Tests pass without Ollama mocks
- Output visibly improves (no more output ≈ input)

**Files to create/modify:**
- `src/core/llm/ollamaChat.ts` (new)
- `src/core/llm/improvePrompt.ts` (modify)
- `src/core/llm/__tests__/ollamaChat.test.ts` (new)
- `src/promptify-quick.tsx` (update import)

### Phase 1: Core Evaluation (HIGH) - Week 2

**Objective:** Baseline measurement + regression guards

**Tasks:**
1. Create `src/core/eval/` with `metrics.ts`, `validation.ts`
2. Run baseline: `npm run eval -- --output eval/baseline-v3.json`
3. Setup Husky pre-commit hook
4. Create `testdata/golden.jsonl` (10 critical prompts)

**Success Criteria:**
- Baseline saved to `eval/baseline-v3.json`
- Pre-commit hook completes in < 30s
- Golden dataset tests pass 100%

**Files to create/modify:**
- `src/core/eval/metrics.ts` (new)
- `src/core/eval/validation.ts` (new)
- `src/core/eval/regression.ts` (new)
- `.husky/pre-commit` (new)
- `testdata/golden.jsonl` (new)
- `scripts/evaluator.ts` (extend)

### Phase 2: Semantic Quality (MEDIUM) - Week 3

**Objective:** DeepEval integration for faithfulness

**Tasks:**
1. Install `deepeval` and configure pytest-like runner
2. Create `src/core/eval/faithfulness.ts`
3. Extend evaluator with semantic scores
4. Create markdown report dashboard (`eval/reports/latest.md`)

**Success Criteria:**
- Faithfulness score tracking functional
- Auto-generated report with trends
- Configurable thresholds in `defaults.ts`

**Files to create/modify:**
- `package.json` (add deepeval dependency)
- `src/core/eval/faithfulness.ts` (new)
- `src/core/eval/__tests__/faithfulness.test.ts` (new)
- `scripts/evaluator.ts` (extend with semantic metrics)
- `eval/reports/latest.md` (auto-generated)

### Phase 3: Telemetry & Insights (LOW) - Week 4+

**Objective:** Performance tracking + historical analysis

**Tasks:**
1. Create `src/core/telemetry/` with `metricsStore.ts`
2. Implement latency tracking (P50, P95, P99)
3. Create `eval/metrics/history.jsonl` (append-only)
4. Scripts for trend analysis

**Success Criteria:**
- Latency tracking on every eval run
- Historical analysis functional
- Alerts if P95 > threshold

**Files to create/modify:**
- `src/core/telemetry/metricsStore.ts` (new)
- `src/core/telemetry/latency.ts` (new)
- `eval/metrics/history.jsonl` (append-only log)
- `scripts/analyze-trends.ts` (new)

### Rollback Strategy

**If something fails:**
```bash
# Revert to /api/generate
git revert <commit>

# Compare against old baseline
npm run eval -- --baseline eval/baseline-v2.json
```

---

## 7. Directory Structure

```
dashboard/
├── src/
│   ├── core/
│   │   ├── llm/
│   │   │   ├── ollamaRaw.ts           # Legacy /api/generate (Phase 0: remove)
│   │   │   ├── ollamaChat.ts          # NEW: /api/chat (Phase 0)
│   │   │   ├── improvePrompt.ts       # UPDATE: Use ollamaChat (Phase 0)
│   │   │   └── __tests__/
│   │   │       ├── ollamaChat.test.ts # NEW: Integration tests (Phase 0)
│   │   │       └── novaeus-promptist.test.ts
│   │   ├── eval/                      # NEW: Evaluation system (Phase 1-2)
│   │   │   ├── metrics.ts             # Quality metrics (Phase 1)
│   │   │   ├── validation.ts          # 3-level validation (Phase 1)
│   │   │   ├── regression.ts          # Baseline comparison (Phase 1)
│   │   │   ├── faithfulness.ts        # DeepEval integration (Phase 2)
│   │   │   └── __tests__/
│   │   │       ├── metrics.test.ts
│   │   │       ├── validation.test.ts
│   │   │       └── faithfulness.test.ts
│   │   ├── telemetry/                 # NEW: Performance tracking (Phase 3)
│   │   │   ├── metricsStore.ts        # Append-only metrics storage
│   │   │   └── latency.ts             # P50/P95/P99 tracking
│   │   └── config/
│   │       ├── defaults.ts            # UPDATE: Add eval.gates (Phase 1)
│   │       └── schema.ts              # Already validated
│   └── promptify-quick.tsx            # UPDATE: Use ollamaChat (Phase 0)
├── testdata/
│   ├── cases.jsonl                    # Already exists
│   ├── edge-cases.jsonl               # NEW: Known problematic inputs (Phase 1)
│   └── golden.jsonl                   # NEW: 10 critical prompts (Phase 1)
├── eval/
│   ├── baseline-v2.json               # Current baseline
│   ├── baseline-v3.json               # NEW: Post-/api/chat migration (Phase 1)
│   ├── latest.json                    # NEW: Most recent eval results
│   ├── metrics/
│   │   └── history.jsonl              # NEW: Append-only metrics log (Phase 3)
│   └── reports/
│       └── latest.md                  # NEW: Human-readable summary (Phase 2)
├── scripts/
│   ├── evaluator.ts                   # EXTEND: Add validation, metrics (Phase 1-2)
│   └── analyze-trends.ts              # NEW: Trend analysis (Phase 3)
├── .husky/
│   └── pre-commit                     # NEW: Regression guard (Phase 1)
└── package.json                       # UPDATE: Add deepeval (Phase 2)
```

---

## 8. Success Metrics

### Phase 0 (Foundation)
- [ ] All tests pass with `/api/chat`
- [ ] System pattern verified in `system` field
- [ ] Output quality improves (subjective validation)

### Phase 1 (Core Evaluation)
- [ ] Baseline v3 generated
- [ ] Pre-commit hook < 30s
- [ ] Golden dataset 100% pass rate

### Phase 2 (Semantic Quality)
- [ ] Faithfulness tracking operational
- [ ] Auto-generated reports working
- [ ] Thresholds configurable

### Phase 3 (Telemetry)
- [ ] Latency tracking (P50/P95/P99)
- [ ] Historical trends analysis
- [ ] P95 alerting functional

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `/api/chat` response format differs | High | Comprehensive integration tests before rollout |
| DeepEval installation issues | Medium | Fallback to structural validation only |
| Pre-commit hook too slow | Medium | Limit to golden dataset, not full test suite |
| Baseline becomes outdated | Low | Manual review before each major version |
| Ollama model behavior changes | Low | Pin model version in config |

---

## 10. Next Steps

1. **Begin Phase 0:** Create `ollamaChat.ts` with `/api/chat` implementation
2. **Write integration tests:** Verify system/user message separation
3. **Update all callers:** Switch from `ollamaRaw` to `ollamaChat`
4. **Generate baseline v3:** Run full evaluation with new architecture
5. **Setup pre-commit hook:** Prevent regressions going forward

---

**Document Status:** Complete and approved
**Ready for:** Phase 0 implementation
**Estimated Timeline:** 4 weeks for full system, 1 week for critical fixes
