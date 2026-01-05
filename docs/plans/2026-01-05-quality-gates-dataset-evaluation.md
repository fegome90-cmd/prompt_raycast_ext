# Quality Gates Dataset Evaluation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use @superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute quality gates on real dataset (100-200 outputs) to analyze threshold effectiveness and identify tuning opportunities.

**Architecture:** Python script that reads JSON dataset, runs `evaluate_output()` on each entry, aggregates gate results, and generates statistical analysis with threshold recommendations.

**Tech Stack:** Python 3.14+, pytest, json, statistics (built-in), existing `api.quality_gates` module.

---

## Task 1: Create Dataset Evaluator Script

**Files:**
- Create: `scripts/eval/evaluate_dataset_gates.py`

**Step 1: Write the failing test**

Create `tests/test_dataset_evaluator.py`:

```python
"""Tests for dataset gate evaluation script."""
import pytest
import json
from pathlib import Path

def test_evaluator_exists():
    """Test evaluator script can be imported."""
    from scripts.eval.evaluate_dataset_gates import evaluate_dataset
    assert callable(evaluate_dataset)

def test_evaluator_returns_results():
    """Test evaluator returns results dict with expected keys."""
    from scripts.eval.evaluate_dataset_gates import evaluate_dataset

    results = evaluate_dataset(
        dataset_path="datasets/exports/fewshot-train.json",
        output_field="outputs.improved_prompt",
        template_id="example_md",
        limit=5
    )

    # Check structure
    assert isinstance(results, dict)
    assert "total_evaluated" in results
    assert "v0_1_pass_count" in results
    assert "v0_2_fail_counts" in results
    assert "gate_statistics" in results
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dataset_evaluator.py::test_evaluator_exists -v`

Expected: `ImportError: cannot import name 'evaluate_dataset'`

**Step 3: Write minimal implementation**

Create `scripts/eval/evaluate_dataset_gates.py`:

```python
"""
Evaluate quality gates on dataset for threshold tuning.

Analyzes gate effectiveness across real outputs to identify:
- Distribution of PASS/WARN/FAIL per gate
- Thresholds causing false positives/negatives
- Recommendations for threshold adjustments
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.quality_gates import evaluate_output, DEFAULT_TEMPLATES, GateSeverity


def evaluate_dataset(
    dataset_path: str,
    output_field: str = "outputs.improved_prompt",
    template_id: str = "example_md",
    limit: int = None
) -> Dict[str, Any]:
    """
    Evaluate quality gates on dataset entries.

    Args:
        dataset_path: Path to JSON dataset file
        output_field: Dot-notation path to output field in each entry
        template_id: Template ID to use for evaluation
        limit: Max number of entries to evaluate (None = all)

    Returns:
        Dictionary with evaluation results and statistics
    """
    # Load dataset
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    # Apply limit
    if limit:
        dataset = dataset[:limit]

    results = {
        "total_evaluated": 0,
        "v0_1_pass_count": 0,
        "v0_2_fail_counts": defaultdict(int),
        "v0_2_warn_counts": defaultdict(int),
        "gate_statistics": {},
        "individual_results": []
    }

    # Evaluate each entry
    for idx, entry in enumerate(dataset):
        # Extract output using dot notation
        output = _get_nested_value(entry, output_field)
        if not output:
            continue

        # Run quality gates
        report = evaluate_output(
            output_text=output,
            template_id=template_id,
            template_spec=DEFAULT_TEMPLATES.get(template_id)
        )

        # Aggregate results
        results["total_evaluated"] += 1
        if report.v0_1_pass:
            results["v0_1_pass_count"] += 1

        # Count v0.2 gate results
        for gate_id, gate_result in report.v0_2_gates.items():
            if gate_result.status == GateSeverity.FAIL:
                results["v0_2_fail_counts"][gate_id] += 1
            elif gate_result.status == GateSeverity.WARN:
                results["v0_2_warn_counts"][gate_id] += 1

        # Store individual result (minimal)
        results["individual_results"].append({
            "index": idx,
            "v0_1_pass": report.v0_1_pass,
            "v0_2_fail_count": report.v0_2_fail_count,
            "v0_2_warn_count": report.v0_2_warn_count
        })

    # Calculate statistics
    results["gate_statistics"] = _calculate_statistics(results)

    return results


def _get_nested_value(data: Dict, path: str) -> Any:
    """Get value from dict using dot notation (e.g., 'outputs.improved_prompt')."""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def _calculate_statistics(results: Dict) -> Dict[str, Any]:
    """Calculate statistics from evaluation results."""
    total = results["total_evaluated"]
    if total == 0:
        return {}

    stats = {}

    # Pass rates
    stats["v0_1_pass_rate"] = results["v0_1_pass_count"] / total

    # v0.2 gate failure rates
    for gate_id, fail_count in results["v0_2_fail_counts"].items():
        stats[f"{gate_id}_fail_rate"] = fail_count / total

    # v0.2 gate warning rates
    for gate_id, warn_count in results["v0_2_warn_counts"].items():
        stats[f"{gate_id}_warn_rate"] = warn_count / total

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate quality gates on dataset")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON file")
    parser.add_argument("--output", default="eval/dataset-evaluation-results.json", help="Output path for results")
    parser.add_argument("--limit", type=int, help="Max entries to evaluate")
    parser.add_argument("--template", default="example_md", help="Template ID to use")

    args = parser.parse_args()

    # Run evaluation
    results = evaluate_dataset(
        dataset_path=args.dataset,
        template_id=args.template,
        limit=args.limit
    )

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Evaluation complete: {results['total_evaluated']} entries evaluated")
    print(f"Results saved to: {output_path}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dataset_evaluator.py -v`

Expected: All tests pass

**Step 5: Commit**

```bash
git add scripts/eval/evaluate_dataset_gates.py tests/test_dataset_evaluator.py
git commit -m "feat: add dataset gate evaluation script"
```

---

## Task 2: Run Evaluation on Sample Dataset

**Files:**
- Modify: (none - using existing script)

**Step 1: Run evaluation on small sample**

Run: `uv run python scripts/eval/evaluate_dataset_gates.py --dataset datasets/exports/fewshot-train.json --limit 50 --output eval/sample-evaluation.json`

Expected: Script completes, creates `eval/sample-evaluation.json`

**Step 2: Verify output file exists**

Run: `ls -lh eval/sample-evaluation.json`

Expected: File exists with non-zero size

**Step 3: Examine results**

Run: `python3 -c "import json; d=json.load(open('eval/sample-evaluation.json')); print(f\"Total: {d['total_evaluated']}, v0.1 Pass Rate: {d['gate_statistics']['v0_1_pass_rate']:.2%}\")"`

Expected: Shows evaluation statistics

**Step 4: Commit**

```bash
git add eval/sample-evaluation.json
git commit -m "test: add sample dataset evaluation results (50 entries)"
```

---

## Task 3: Create Statistics Analyzer

**Files:**
- Create: `scripts/eval/analyze_thresholds.py`

**Step 1: Write test for analyzer**

Create `tests/test_threshold_analyzer.py`:

```python
"""Tests for threshold analysis script."""
import pytest
import json

def test_analyzer_identifies_threshold_issues():
    """Test analyzer identifies thresholds with high fail rates."""
    from scripts.eval.analyze_thresholds import analyze_thresholds

    # Mock results with high fail rate for P1 gate
    mock_results = {
        "total_evaluated": 100,
        "v0_2_fail_counts": {"P1_steps": 60},  # 60% fail rate
        "gate_statistics": {"P1_steps_fail_rate": 0.6}
    }

    recommendations = analyze_thresholds(mock_results)

    assert "P1_steps" in recommendations
    assert recommendations["P1_steps"]["issue"] == "high_fail_rate"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_threshold_analyzer.py::test_analyzer_identifies_threshold_issues -v`

Expected: `ImportError: cannot import name 'analyze_thresholds'`

**Step 3: Implement threshold analyzer**

Create `scripts/eval/analyze_thresholds.py`:

```python
"""
Analyze quality gate results to identify threshold tuning opportunities.

Identifies gates with:
- High fail rates (potential false positives, threshold too strict)
- High pass rates (potential false negatives, threshold too lenient)
- Recommendations for threshold adjustments
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.quality_gates import GateThresholds


HIGH_FAIL_RATE_THRESHOLD = 0.50  # 50% fail rate = potentially too strict
HIGH_WARN_RATE_THRESHOLD = 0.70  # 70% warn rate = potentially noisy


def analyze_thresholds(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze gate results to identify threshold tuning opportunities.

    Args:
        results: Results dictionary from evaluate_dataset()

    Returns:
        Dictionary with threshold recommendations
    """
    total = results["total_evaluated"]
    if total == 0:
        return {"error": "No data to analyze"}

    recommendations = {}
    stats = results.get("gate_statistics", {})

    # Analyze each gate's fail rate
    for gate_id, fail_rate_key in _get_gate_metric_keys("fail_rate"):
        if fail_rate_key not in stats:
            continue

        fail_rate = stats[fail_rate_key]
        gate_name = gate_id.replace("_fail_rate", "")

        if fail_rate >= HIGH_FAIL_RATE_THRESHOLD:
            recommendations[gate_name] = {
                "issue": "high_fail_rate",
                "current_rate": fail_rate,
                "recommendation": _get_threshold_recommendation(gate_name, "lower"),
                "current_threshold": _get_current_threshold(gate_name)
            }

    # Analyze warn rates
    for gate_id, warn_rate_key in _get_gate_metric_keys("warn_rate"):
        if warn_rate_key not in stats:
            continue

        warn_rate = stats[warn_rate_key]
        gate_name = gate_id.replace("_warn_rate", "")

        if warn_rate >= HIGH_WARN_RATE_THRESHOLD:
            if gate_name not in recommendations:
                recommendations[gate_name] = {
                    "issue": "high_warn_rate",
                    "current_rate": warn_rate,
                    "recommendation": "Review threshold - high warning rate may indicate unclear boundary"
                }

    return recommendations


def _get_gate_metric_keys(metric_type: str) -> List[str]:
    """Get all gate statistic keys for a metric type."""
    # Common gate IDs in v0.2
    gate_ids = ["A1_filler", "A4_repetition", "J1_empty", "P1_steps", "C1_specific", "E1_code"]
    return [f"{gate_id}_{metric_type}" for gate_id in gate_ids]


def _get_threshold_recommendation(gate_name: str, direction: str) -> str:
    """Get specific threshold recommendation for a gate."""
    thresholds = GateThresholds()

    recommendations = {
        "A1_filler": {
            "lower": f"Reduce A1_MAX_FILLER_COUNT from {thresholds.A1_MAX_FILLER_COUNT} to {thresholds.A1_MAX_FILLER_COUNT + 1}",
            "raise": f"Increase A1_MAX_FILLER_COUNT to catch more fillers"
        },
        "P1_steps": {
            "lower": f"Increase P1_MAX_EMPTY_STEP_RATIO from {thresholds.P1_MAX_EMPTY_STEP_RATIO} to {thresholds.P1_MAX_EMPTY_STEP_RATIO + 0.1}",
            "raise": f"Decrease P1_MIN_NON_TRIVIAL_TOKENS to be less strict"
        },
        "C1_specific": {
            "lower": f"Increase C1_MAX_GENERIC_RATIO from {thresholds.C1_MAX_GENERIC_RATIO} to {thresholds.C1_MAX_GENERIC_RATIO + 0.1}",
            "raise": "Decrease C1_MIN_NON_TRIVIAL_TOKENS"
        },
        "E1_code": {
            "lower": f"Decrease E1_MIN_CODE_LINES from {thresholds.E1_MIN_CODE_LINES} to {max(1, thresholds.E1_MIN_CODE_LINES - 1)}",
            "raise": f"Increase E1_MIN_CODE_LINES to ensure more substantive code"
        }
    }

    if gate_name in recommendations and direction in recommendations[gate_name]:
        return recommendations[gate_name][direction]

    return f"Adjust threshold for {gate_name} ({direction})"


def _get_current_threshold(gate_name: str) -> Dict[str, float]:
    """Get current threshold values for a gate."""
    thresholds = GateThresholds()

    threshold_map = {
        "A1_filler": {"A1_MAX_FILLER_COUNT": thresholds.A1_MAX_FILLER_COUNT},
        "P1_steps": {"P1_MAX_EMPTY_STEP_RATIO": thresholds.P1_MAX_EMPTY_STEP_RATIO},
        "C1_specific": {"C1_MAX_GENERIC_RATIO": thresholds.C1_MAX_GENERIC_RATIO},
        "E1_code": {"E1_MIN_CODE_LINES": thresholds.E1_MIN_CODE_LINES}
    }

    return threshold_map.get(gate_name, {})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze threshold effectiveness")
    parser.add_argument("--results", required=True, help="Path to evaluation results JSON")
    parser.add_argument("--output", default="eval/threshold-recommendations.json", help="Output path")

    args = parser.parse_args()

    # Load results
    with open(args.results, 'r') as f:
        results = json.load(f)

    # Analyze
    recommendations = analyze_thresholds(results)

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(recommendations, f, indent=2)

    print(f"Analysis complete: {len(recommendations)} gates identified for tuning")
    print(f"Recommendations saved to: {output_path}")
```

**Step 4: Run tests to verify it passes**

Run: `uv run pytest tests/test_threshold_analyzer.py -v`

Expected: All tests pass

**Step 5: Commit**

```bash
git add scripts/eval/analyze_thresholds.py tests/test_threshold_analyzer.py
git commit -m "feat: add threshold analysis script"
```

---

## Task 4: Run Full Dataset Evaluation

**Files:**
- Create: `eval/full-dataset-evaluation.json`

**Step 1: Run evaluation on full dataset**

Run: `uv run python scripts/eval/evaluate_dataset_gates.py --dataset datasets/exports/fewshot-train.json --limit 200 --output eval/full-dataset-evaluation.json`

Expected: Script processes 200 entries, generates results

**Step 2: Run threshold analysis**

Run: `uv run python scripts/eval/analyze_thresholds.py --results eval/full-dataset-evaluation.json --output eval/threshold-recommendations.json`

Expected: Generates recommendations JSON

**Step 3: View summary**

Run: `python3 -c "
import json
r = json.load(open('eval/full-dataset-evaluation.json'))
recs = json.load(open('eval/threshold-recommendations.json'))
print(f'Total Evaluated: {r[\"total_evaluated\"]}')
print(f'v0.1 Pass Rate: {r[\"gate_statistics\"][\"v0_1_pass_rate\"]:.1%}')
print(f'Gates Needing Tuning: {len(recs)}')
for gate, data in recs.items():
    print(f'  - {gate}: {data[\"issue\"]} ({data[\"current_rate\"]:.1%})')
"`

Expected: Shows summary statistics

**Step 4: Commit**

```bash
git add eval/full-dataset-evaluation.json eval/threshold-recommendations.json
git commit -m "eval: run full dataset evaluation (200 entries) with threshold analysis"
```

---

## Task 5: Generate Markdown Report

**Files:**
- Create: `docs/reports/2026-01-05-dataset-evaluation-report.md`

**Step 1: Create report generation script**

Create `scripts/eval/generate_report.py`:

```python
"""
Generate markdown report from evaluation results.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_markdown_report(
    results_path: str,
    recommendations_path: str,
    output_path: str
):
    """Generate markdown report from evaluation results."""

    # Load data
    with open(results_path) as f:
        results = json.load(f)

    with open(recommendations_path) as f:
        recommendations = json.load(f)

    # Generate report
    report = f"""# Quality Gates Dataset Evaluation Report

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Dataset:** fewshot-train.json (sample of {results['total_evaluated']} entries)
**Template:** example_md
**Purpose:** Analyze gate effectiveness and identify threshold tuning opportunities

---

## Executive Summary

- **Total Entries Evaluated:** {results['total_evaluated']}
- **v0.1 Pass Rate:** {results['gate_statistics']['v0_1_pass_rate']:.1%}
- **Gates Requiring Tuning:** {len(recommendations)}

---

## Gate Performance Summary

| Gate | Fail Rate | Warn Rate | Status |
|------|-----------|-----------|--------|
"""

    # Add gate statistics
    for gate_id in ["A1_filler", "P1_steps", "C1_specific", "E1_code"]:
        fail_rate = results['gate_statistics'].get(f'{gate_id}_fail_rate', 0)
        warn_rate = results['gate_statistics'].get(f'{gate_id}_warn_rate', 0)

        if fail_rate > 0.5:
            status = "⚠️ NEEDS TUNING"
        elif warn_rate > 0.7:
            status = "⚠️ HIGH WARN RATE"
        else:
            status = "✅ GOOD"

        report += f"| {gate_id} | {fail_rate:.1%} | {warn_rate:.1%} | {status} |\n"

    # Add recommendations section
    report += "\n---\n\n## Threshold Recommendations\n\n"

    if recommendations:
        for gate_name, data in recommendations.items():
            report += f"### {gate_name}\n\n"
            report += f"**Issue:** {data['issue']} ({data['current_rate']:.1%})\n\n"
            report += f"**Recommendation:** {data.get('recommendation', 'N/A')}\n\n"
            if data.get('current_threshold'):
                report += f"**Current Threshold:** `{data['current_threshold']}`\n\n"
            report += "---\n\n"
    else:
        report += "No threshold adjustments needed - all gates performing well.\n\n"

    # Add methodology
    report += """
---

## Methodology

This evaluation used the following approach:

1. **Sample Selection:** Random sample of {results['total_evaluated']} entries from fewshot-train.json
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

**Generated:** {datetime.now().isoformat()}
"""

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(report)

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate markdown report")
    parser.add_argument("--results", required=True, help="Path to evaluation results")
    parser.add_argument("--recommendations", required=True, help="Path to threshold recommendations")
    parser.add_argument("--output", default="docs/reports/dataset-evaluation-report.md", help="Output path")

    args = parser.parse_args()

    generate_markdown_report(args.results, args.recommendations, args.output)
```

**Step 2: Generate report**

Run: `uv run python scripts/eval/generate_report.py --results eval/full-dataset-evaluation.json --recommendations eval/threshold-recommendations.json`

Expected: Creates markdown report

**Step 3: View report**

Run: `cat docs/reports/2026-01-05-dataset-evaluation-report.md`

Expected: Shows formatted report with tables and recommendations

**Step 4: Commit**

```bash
git add scripts/eval/generate_report.py docs/reports/2026-01-05-dataset-evaluation-report.md
git commit -m "docs: add dataset evaluation report with threshold recommendations"
```

---

## Task 6: Update Thresholds Based on Findings

**Files:**
- Modify: `api/quality_gates.py` (if needed based on recommendations)

**Step 1: Review current thresholds**

Run: `python3 -c "from api.quality_gates import GateThresholds; t = GateThresholds(); print('P1_MAX_EMPTY_STEP_RATIO:', t.P1_MAX_EMPTY_STEP_RATIO)"`

Expected: Shows current threshold value

**Step 2: If recommendations suggest changes, update thresholds**

Only do this if the evaluation identified specific gates needing tuning.

Example (if P1 has 60% fail rate):

Edit `api/quality_gates.py` around line 70-80:

```python
@dataclass
class GateThresholds:
    """Centralized threshold configuration for all gates"""
    # Relaxed for MVP - may need further tuning based on production data
    P1_MAX_EMPTY_STEP_RATIO: float = 0.40  # Increased from 0.30 to reduce false positives
    P1_MIN_NON_TRIVIAL_TOKENS: int = 4     # Kept stable
    # ... other thresholds
```

**Step 3: Re-run tests to ensure no regression**

Run: `uv run pytest tests/test_quality_gates.py tests/test_v02_trampa_cases.py -v`

Expected: All tests still pass

**Step 4: Commit**

```bash
git add api/quality_gates.py
git commit -m "feat: adjust P1 threshold based on dataset evaluation"
```

---

## Completion Checklist

Before marking PROMPT 3 complete, verify:

- [ ] Dataset evaluator script created and tested
- [ ] Evaluation run on 200+ entries
- [ ] Threshold analysis completed
- [ ] Markdown report generated
- [ ] Thresholds updated if needed (with rationale documented)
- [ ] All tests still passing after changes
- [ ] Report includes methodology, findings, and recommendations

---

**Next:** PROMPT 4 - Design UI spec for WARN display
