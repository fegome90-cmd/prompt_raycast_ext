"""
Generate markdown report from evaluation results.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_markdown_report(
    results_path: str,
    recommendations_path: str,
    output_path: str
):
    """Generate markdown report from evaluation results."""

    # Load data with error handling
    try:
        with open(results_path) as f:
            results = json.load(f)
    except FileNotFoundError:
        logger.error(f"Results file not found: {results_path}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        raise SystemExit(1)

    try:
        with open(recommendations_path) as f:
            recommendations = json.load(f)
    except FileNotFoundError:
        logger.error(f"Recommendations file not found: {recommendations_path}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in recommendations file: {e}")
        raise SystemExit(1)

    # Validate structure
    if "gate_statistics" not in results:
        logger.error("Missing 'gate_statistics' in results")
        raise SystemExit(1)

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
    report += f"""
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

    # Write report with error handling
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            f.write(report)
    except IOError as e:
        logger.error(f"Failed to write report: {e}")
        raise SystemExit(1)

    logger.info(f"Report generated: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate markdown report")
    parser.add_argument("--results", required=True, help="Path to evaluation results")
    parser.add_argument("--recommendations", required=True, help="Path to threshold recommendations")
    parser.add_argument("--output", default="docs/reports/dataset-evaluation-report.md", help="Output path")

    args = parser.parse_args()

    generate_markdown_report(args.results, args.recommendations, args.output)
