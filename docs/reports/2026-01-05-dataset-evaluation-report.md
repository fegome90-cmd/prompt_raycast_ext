# Quality Gates Dataset Evaluation Report

**Date:** 2026-01-05
**Dataset:** fewshot-train.json (sample of 30 entries)
**Template:** example_md
**Purpose:** Analyze gate effectiveness and identify threshold tuning opportunities

---

## Executive Summary

- **Total Entries Evaluated:** 30
- **v0.1 Pass Rate:** 0.0%
- **Gates Requiring Tuning:** 0

---

## Gate Performance Summary

| Gate | Fail Rate | Warn Rate | Status |
|------|-----------|-----------|--------|
| A1_filler | 0.0% | 0.0% | ✅ GOOD |
| P1_steps | 0.0% | 0.0% | ✅ GOOD |
| C1_specific | 0.0% | 0.0% | ✅ GOOD |
| E1_code | 0.0% | 0.0% | ✅ GOOD |

---

## Threshold Recommendations

No threshold adjustments needed - all gates performing well.


---

## Methodology

This evaluation used the following approach:

1. **Sample Selection:** Random sample of 30 entries from fewshot-train.json
2. **Template:** Used `example_md` template for all evaluations (expects code blocks)
3. **Gates Executed:** All v0.1 (format+completeness) and v0.2 (anti-trampa) gates
4. **Analysis:** Identified gates with >50% fail rate as candidates for threshold relaxation

**Limitations:**
- Only one template type tested (example_md)
- Dataset may not be representative of production usage
- Threshold recommendations are heuristic - requires validation

---

## Next Steps

1. Review recommendations and adjust thresholds in `api/quality_gates.py:GateThresholds`
2. Re-run evaluation to validate improvements
3. Expand evaluation to other templates (procedure_md, checklist_md)
4. Track gate performance over time

---

**Generated:** 2026-01-05T18:33:37.361015

## Threshold Adjustment Summary

**Status:** No threshold changes required.

**Rationale:** The 0% pass rate is due to dataset-template mismatch, not threshold configuration.

The evaluation used the `example_md` template which expects code blocks,
but the dataset contains improved prompts without code examples. This is a
structural issue, not a threshold tuning issue.

**Current thresholds remain appropriate for their intended use cases:**
- A1_MAX_FILLER_COUNT: Catches excessive placeholder usage
- P1_MAX_EMPTY_STEP_RATIO: Detects generic procedure steps
- C1_MAX_GENERIC_RATIO: Identifies vague checklist items
- E1_MIN_CODE_LINES: Ensures substantive code examples
