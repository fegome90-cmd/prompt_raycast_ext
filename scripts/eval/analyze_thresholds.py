"""
Analyze quality gate results to identify threshold tuning opportunities.

Identifies gates with:
- High fail rates (potential false positives, threshold too strict)
- High pass rates (potential false negatives, threshold too lenient)
- Recommendations for threshold adjustments
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

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
    # Validate results structure
    if "gate_statistics" not in results:
        logger.error("Missing 'gate_statistics' in results")
        return {"error": "Invalid results format - missing gate_statistics"}

    total = results.get("total_evaluated", 0)
    if total == 0:
        logger.warning("No data to analyze - total_evaluated is 0")
        return {"error": "No data to analyze"}

    recommendations = {}
    stats = results.get("gate_statistics", {})

    # Analyze each gate's fail rate
    for fail_rate_key in _get_gate_metric_keys("fail_rate"):
        if fail_rate_key not in stats:
            continue

        fail_rate = stats[fail_rate_key]
        gate_name = fail_rate_key.replace("_fail_rate", "")

        if fail_rate >= HIGH_FAIL_RATE_THRESHOLD:
            recommendations[gate_name] = {
                "issue": "high_fail_rate",
                "current_rate": fail_rate,
                "recommendation": _get_threshold_recommendation(gate_name, "more_lenient"),
                "current_threshold": _get_current_threshold(gate_name)
            }

    # Analyze warn rates
    for warn_rate_key in _get_gate_metric_keys("warn_rate"):
        if warn_rate_key not in stats:
            continue

        warn_rate = stats[warn_rate_key]
        gate_name = warn_rate_key.replace("_warn_rate", "")

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
    """Get specific threshold recommendation for a gate.

    Args:
        gate_name: Name of the gate (e.g., "A1_filler")
        direction: "more_lenient" (reduce false positives) or "more_strict" (reduce false negatives)

    Returns:
        Human-readable recommendation string
    """
    thresholds = GateThresholds()

    recommendations = {
        "A1_filler": {
            "more_lenient": f"Increase A1_MAX_FILLER_COUNT from {thresholds.A1_MAX_FILLER_COUNT} to {thresholds.A1_MAX_FILLER_COUNT + 1} (allows more filler words)",
            "more_strict": f"Decrease A1_MAX_FILLER_COUNT from {thresholds.A1_MAX_FILLER_COUNT} to {max(0, thresholds.A1_MAX_FILLER_COUNT - 1)} (catches more filler words)"
        },
        "P1_steps": {
            "more_lenient": f"Increase P1_MAX_EMPTY_STEP_RATIO from {thresholds.P1_MAX_EMPTY_STEP_RATIO} to {thresholds.P1_MAX_EMPTY_STEP_RATIO + 0.1} (allows more empty steps)",
            "more_strict": f"Decrease P1_MAX_EMPTY_STEP_RATIO from {thresholds.P1_MAX_EMPTY_STEP_RATIO} to {max(0.0, thresholds.P1_MAX_EMPTY_STEP_RATIO - 0.1)} (requires more substantive steps)"
        },
        "C1_specific": {
            "more_lenient": f"Increase C1_MAX_GENERIC_RATIO from {thresholds.C1_MAX_GENERIC_RATIO} to {thresholds.C1_MAX_GENERIC_RATIO + 0.1} (allows more generic phrases)",
            "more_strict": f"Decrease C1_MAX_GENERIC_RATIO from {thresholds.C1_MAX_GENERIC_RATIO} to {max(0.0, thresholds.C1_MAX_GENERIC_RATIO - 0.1)} (requires more specific content)"
        },
        "E1_code": {
            "more_lenient": f"Decrease E1_MIN_CODE_LINES from {thresholds.E1_MIN_CODE_LINES} to {max(1, thresholds.E1_MIN_CODE_LINES - 1)} (requires less code)",
            "more_strict": f"Increase E1_MIN_CODE_LINES from {thresholds.E1_MIN_CODE_LINES} to {thresholds.E1_MIN_CODE_LINES + 1} (requires more substantive code)"
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

    # Load results with error handling
    try:
        with open(args.results, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        logger.error(f"Results file not found: {args.results}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        raise SystemExit(1)

    # Analyze
    recommendations = analyze_thresholds(results)

    # Save with error handling
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump(recommendations, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to write recommendations: {e}")
        raise SystemExit(1)

    logger.info(f"Analysis complete: {len(recommendations)} gates identified for tuning")
    logger.info(f"Recommendations saved to: {output_path}")
