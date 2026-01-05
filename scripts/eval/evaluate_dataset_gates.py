"""
Evaluate quality gates on dataset for threshold tuning.

Analyzes gate effectiveness across real outputs to identify:
- Distribution of PASS/WARN/FAIL per gate
- Thresholds causing false positives/negatives
- Recommendations for threshold adjustments
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

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
    # Load dataset with error handling
    try:
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {dataset_path}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in dataset file: {e}")
        raise SystemExit(1)

    # Apply limit
    if limit:
        dataset = dataset[:limit]

    results = {
        "total_evaluated": 0,
        "skipped_count": 0,
        "skipped_indices": [],
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
            results["skipped_count"] += 1
            results["skipped_indices"].append(idx)
            logger.debug(f"Skipping entry {idx}: empty output at '{output_field}'")
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
    parser.add_argument("--output-field", default="outputs.improved_prompt", help="Dot-notation path to output field")
    parser.add_argument("--limit", type=int, help="Max entries to evaluate")
    parser.add_argument("--template", default="example_md", help="Template ID to use")

    args = parser.parse_args()

    # Run evaluation
    results = evaluate_dataset(
        dataset_path=args.dataset,
        output_field=args.output_field,
        template_id=args.template,
        limit=args.limit
    )

    # Save results with error handling
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise SystemExit(1)

    logger.info(f"Evaluation complete: {results['total_evaluated']} entries evaluated")
    if results['skipped_count'] > 0:
        logger.info(f"Skipped: {results['skipped_count']} entries (indices: {results['skipped_indices'][:10]}{'...' if len(results['skipped_indices']) > 10 else ''})")
    logger.info(f"Results saved to: {output_path}")
