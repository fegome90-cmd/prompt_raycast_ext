# TTV Measurement Protocol v0.1

**Date:** January 5, 2026
**Purpose:** Manual measurement of Time-to-Value without analytics instrumentation
**Status:** Executable protocol

---

## 1. Operational Definitions

### 1.1 TTV (Time-to-Value)

**Definition:** Time from user initiation to successful copy action.

**Formula:** `TTV_ms = t_copy - t_start`

### 1.2 Event Definitions

| Event | Operational Definition | Notes |
|-------|----------------------|-------|
| `t_start` | Moment user presses hotkey OR opens command | Use stopwatch/phone timer |
| `t_copy` | Moment user presses "Copy to Clipboard" button | Use stopwatch/phone timer |
| `copy_within_60s` | Boolean: `TTV_ms < 60000` | Yes/No |

---

## 2. Manual Measurement Equipment

**Required:**
- Stopwatch (phone app or physical stopwatch)
- Spreadsheet (CSV template below)
- Test environment: Raycast extension running

**Optional:**
- Screen recording (for verification)

---

## 3. Experimental Setup

### 3.1 Test Cases

**Experiment A: Selection Input**
1. Open TextEdit (or any text editor)
2. Select text: "Write a function to validate email addresses"
3. Press hotkey for Prompt Compiler
4. Wait for output
5. Press "Copy to Clipboard"

**Experiment B: Clipboard Input**
1. Copy text to clipboard: "Debug this Python code"
2. Press hotkey for Prompt Compiler
3. Wait for output
4. Press "Copy to Clipboard"

**Experiment C: Manual Input**
1. Press hotkey for Prompt Compiler
2. Type: "Create a React component for a modal"
3. Press Enter/Submit
4. Wait for output
5. Press "Copy to Clipboard"

---

## 4. Data Collection Template

### 4.1 CSV Format

```csv
experiment,iteration,t_start_iso,t_copy_iso,ttv_ms,copy_within_60s,notes
A,1,2026-01-05T10:00:00.000Z,2026-01-05T10:00:25.500Z,25500,true,
A,2,2026-01-05T10:01:00.000Z,2026-01-05T10:01:28.300Z,28300,true,
...
```

### 4.2 Field Descriptions

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `experiment` | string | "A" | Test case identifier (A, B, or C) |
| `iteration` | integer | 1 | Iteration number (1-10 per experiment) |
| `t_start_iso` | ISO 8601 | "2026-01-05T10:00:00.000Z" | Start timestamp |
| `t_copy_iso` | ISO 8601 | "2026-01-05T10:00:25.500Z" | Copy timestamp |
| `ttv_ms` | integer | 25500 | Calculated: `(t_copy - t_start)` in milliseconds |
| `copy_within_60s` | boolean | true | `ttv_ms < 60000` |
| `notes` | string (optional) | "Backend slow" | Free text for anomalies |

---

## 5. Statistical Analysis

### 5.1 Sample Size

**Minimum:** n=15 iterations per experiment

**Recommended:** n=20 iterations per experiment for more stable estimates

**Rationale:** With n=15-20, P90 is more stable. P95 with small samples is essentially the maximum and provides little additional information.

### 5.2 Percentile Calculations

**Method:** Order statistics (non-parametric)

**Report:** P50, P90, and max

**DO NOT report P95 with n<30** - it's statistically indistinguishable from max.

**Steps:**
1. Sort `ttv_ms` values in ascending order
2. Calculate indices:
   - `k_P50 = ceil(0.50 * n)` - median
   - `k_P90 = ceil(0.90 * n)` - 90th percentile
   - `max = n` - worst case

**Example (n=15):**
```
Sorted TTVs: [22000, 24500, 25300, 26000, 27100, 28300, 29500, 30000, 31000, 32500, 34000, 36000, 38000, 42000, 45000]

k_P50 = ceil(0.50 * 15) = ceil(7.5) = 8
k_P90 = ceil(0.90 * 15) = ceil(13.5) = 14
max = 15

P50 = 30000 ms (30 seconds)
P90 = 42000 ms (42 seconds)
max = 45000 ms (45 seconds)
```

**NOTE:** With n=15, P95 would be `ceil(0.95 * 15) = 15`, which equals max. This provides no additional information over reporting max directly.

### 5.3 When to Report P95

**Report P95 only when:**
- n ≥ 30 (stable estimate)
- OR when using automated instrumentation (hundreds of samples)

**With manual measurement (n=15-20):** Report P50, P90, max

---

## 6. Success Criteria

### 6.1 Primary Metrics

**TTV P90:** <30,000 ms (30 seconds) for n=15-20 manual measurements
**TTV max:** <45,000 ms (45 seconds) worst case

**Rationale:** P90 is more stable than P95 for small samples. Max ensures no unacceptable outliers.

**Secondary check:** TTV P50 should be <20,000 ms (20 seconds) for acceptable median performance.

### 6.2 Target for Production (Post-Instrumentation)

Once SQLite analytics are implemented (n≥100):

**TTV P95:** <30,000 ms (30 seconds) - this becomes the target with large sample size

### 6.2 Secondary Metrics

| Metric | Target | Calculation |
|--------|--------|-------------|
| Copy Rate (within 60s) | >60% | `count(copy_within_60s=true) / n * 100` |
| TTV P50 | <20,000 ms | Median of all TTVs |
| Failure Rate | <10% | Iterations with error / n |

---

## 7. Execution Checklist

**Pre-Experiment:**
- [ ] Backend running (`make health` returns 200)
- [ ] Ollama/LLM provider accessible
- [ ] Stopwatch ready
- [ ] CSV template created

**Per Iteration:**
- [ ] Start stopwatch at `t_start`
- [ ] Stop stopwatch at `t_copy`
- [ ] Record times in CSV
- [ ] Note any anomalies (errors, timeouts, etc.)

**Post-Experiment:**
- [ ] Calculate P95, P50, copy rate
- [ ] Compare against targets
- [ ] Document findings

---

## 8. Troubleshooting

### 8.1 Common Issues

| Issue | Cause | Mitigation |
|-------|-------|------------|
| TTV >60s | Backend slow or LLM timeout | Check backend logs, increase timeout |
| "Copy" button never appears | Output generation failed | Check error logs, verify LLM availability |
| High variance (P95 >> P50) | Inconsistent backend performance | Check LLM provider rate limits |

### 8.2 Data Quality Checks

**Valid CSV:**
- All `ttv_ms` values >0
- All `t_copy_iso` > `t_start_iso`
- `copy_within_60s` matches `ttv_ms < 60000`

**Invalid data indicators:**
- Negative `ttv_ms` → Error in timestamp recording
- `ttv_ms` = 0 → Copy button pressed immediately (invalid)
- Missing iterations → Not completed protocol

---

## 9. Example Results

**Experiment A (Selection Input), n=10:**

| iteration | ttv_ms | copy_within_60s |
|-----------|--------|-----------------|
| 1 | 22,500 | true |
| 2 | 24,800 | true |
| 3 | 25,300 | true |
| 4 | 26,100 | true |
| 5 | 27,200 | true |
| 6 | 28,400 | true |
| 7 | 29,600 | true |
| 8 | 31,000 | true |
| 9 | 32,500 | true |
| 10 | 45,000 | true |

**Statistics:**
- P50 = 27,800 ms
- P95 = 45,000 ms
- Copy Rate = 100%

**Assessment:** ❌ FAIL (P95 = 45s > 30s target)

---

**Protocol v0.1 - Ready for execution**
