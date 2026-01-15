#!/usr/bin/env python3
"""
Bootstrap IFEval Calibration from Existing Catalog (v2.1 - REAL validation).

This script uses the REAL IFEvalValidator (no mocks) to generate calibration
data from the existing fewshot catalog. The scores are based on actual
constraint evaluation:
1. Minimum length (≥50 chars)
2. Action verbs (create, implement, write, build, develop, add)
3. JSON format validity

Output: data/ifeval-calibration.json with:
- Score distribution statistics
- Calibrated threshold (p50 or p60 based on distribution)
- Individual prompt scores for analysis
"""

import json
import statistics
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hemdov.domain.services.ifeval_validator import IFEvalValidator


def load_calibrated_threshold(calibration_path: Path = Path("data/ifeval-calibration.json")) -> float:
    """
    Load calibrated threshold from calibration data file.

    This function is for use by infrastructure layer code that needs to
    configure the IFEvalValidator with the calibrated threshold.

    Args:
        calibration_path: Path to calibration data file

    Returns:
        Calibrated threshold (0.0-1.0), or 0.7 as default if file not found
    """
    if calibration_path.exists():
        try:
            with open(calibration_path) as f:
                data = json.load(f)
                return data.get("calibrated_threshold", 0.7)
        except (json.JSONDecodeError, OSError):
            pass  # Fall through to default

    return 0.7  # Conservative default


def load_catalog() -> list:
    """
    Load improved prompts from the fewshot catalog.

    Returns:
        List of improved prompt strings
    """
    catalog_path = Path("datasets/exports/unified-fewshot-pool-v2.json")

    if not catalog_path.exists():
        print(f"❌ Catalog not found at {catalog_path}")
        print("   Please ensure the fewshot catalog exists.")
        sys.exit(1)

    with open(catalog_path) as f:
        catalog_data = json.load(f)

    # Extract improved prompts from catalog
    improved_prompts = []
    examples = catalog_data.get("examples", [])

    for ex in examples:
        if "outputs" in ex and "improved_prompt" in ex["outputs"]:
            improved_prompts.append(ex["outputs"]["improved_prompt"])

    print(f"📚 Loaded {len(improved_prompts)} improved prompts from catalog")
    return improved_prompts


def bootstrap_calibration() -> dict:
    """
    Bootstrap IFEval calibration using REAL IFEvalValidator.

    Returns:
        Calibration data dictionary
    """
    print("=" * 60)
    print("🔬 IFEval Calibration Bootstrap (v2.1 - REAL validation)")
    print("=" * 60)

    # Load catalog
    prompts = load_catalog()

    if not prompts:
        print("❌ No prompts found in catalog")
        sys.exit(1)

    # Initialize validator with default threshold (will be overridden)
    validator = IFEvalValidator(threshold=0.7)

    # Validate all prompts
    print(f"\n🔍 Validating {len(prompts)} prompts against 3 constraints...")
    results = []

    for i, prompt in enumerate(prompts):
        result = validator.validate(prompt)
        results.append({
            "prompt_length": len(prompt),
            "score": result.score,
            "passed": result.passed,
        })

        # Progress indicator
        if (i + 1) % 20 == 0 or i == 0:
            print(f"   Progress: {i + 1}/{len(prompts)}")

    # Analyze score distribution
    scores = [r["score"] for r in results]

    print("\n📊 Score Distribution Analysis:")
    print(f"   Count: {len(scores)}")
    print(f"   Min: {min(scores):.2f}")
    print(f"   Max: {max(scores):.2f}")
    print(f"   Mean: {statistics.mean(scores):.2f}")
    print(f"   Median: {statistics.median(scores):.2f}")
    print(f"   Std Dev: {statistics.stdev(scores) if len(scores) > 1 else 0:.3f}")

    # Calculate score distribution buckets
    print("\n📈 Score Distribution:")
    buckets = {
        "0.0": 0,
        "0.33": 0,
        "0.67": 0,
        "1.0": 0,
    }

    for score in scores:
        if score == 0.0:
            buckets["0.0"] += 1
        elif score == 1/3:
            buckets["0.33"] += 1
        elif score == 2/3:
            buckets["0.67"] += 1
        elif score == 1.0:
            buckets["1.0"] += 1
        else:
            # Shouldn't happen with 3 constraints, but handle it
            rounded = round(score, 2)
            key = str(rounded)
            buckets[key] = buckets.get(key, 0) + 1

    for score_val, count in sorted(buckets.items()):
        pct = count / len(scores) * 100
        print(f"   {score_val}: {count:3d} ({pct:5.1f}%)")

    # Calculate calibrated threshold
    # Use p60 (60th percentile) as threshold - conservative but not too strict
    sorted_scores = sorted(scores)
    percentile_60 = sorted_scores[int(len(sorted_scores) * 0.6)]
    percentile_50 = statistics.median(scores)

    # Choose threshold based on distribution
    if percentile_60 >= 0.67:
        # Most prompts score well, use higher threshold
        calibrated_threshold = 0.67
        print(f"\n💡 High-quality distribution detected (p60={percentile_60:.2f})")
        print("   Using threshold: 0.67")
    elif percentile_50 >= 0.5:
        # Median is good, use it
        calibrated_threshold = round(percentile_50, 2)
        print(f"\n💡 Moderate distribution detected (median={percentile_50:.2f})")
        print(f"   Using threshold: {calibrated_threshold}")
    else:
        # Low scores, use conservative threshold
        calibrated_threshold = 0.5
        print(f"\n⚠️  Low-score distribution detected (median={percentile_50:.2f})")
        print("   Using conservative threshold: 0.5")

    pass_count = sum(1 for r in results if r["score"] >= calibrated_threshold)
    pass_rate = pass_count / len(results)

    print("\n✅ Calibration Results:")
    print(f"   Threshold: {calibrated_threshold}")
    print(f"   Pass rate: {pass_count}/{len(results)} ({pass_rate:.1%})")

    # Check for score distribution issues
    if len(buckets) <= 2:
        print("\n⚠️  WARNING: Narrow score distribution!")
        print(f"   Only {len(buckets)} unique score values detected.")
        print("   Consider adjusting constraints for better discrimination.")

    # Save calibration data
    calibration_output = Path("data/ifeval-calibration.json")
    calibration_output.parent.mkdir(exist_ok=True)

    calibration_data = {
        "threshold_tested": 0.7,
        "calibrated_threshold": calibrated_threshold,
        "results": results,
        "statistics": {
            "count": len(scores),
            "min": min(scores),
            "max": max(scores),
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "pass_rate_at_threshold": pass_rate,
            "percentile_50": percentile_50,
            "percentile_60": percentile_60,
        },
        "distribution": buckets,
        "metadata": {
            "validator_version": "2.1-no-mocks",
            "constraints": [
                "min_length_constraint (≥50 chars)",
                "action_verbs_constraint (create, implement, write, build, develop, add)",
                "json_format_constraint (valid JSON)",
            ],
            "catalog_path": "datasets/exports/unified-fewshot-pool-v2.json",
        },
    }

    with open(calibration_output, "w") as f:
        json.dump(calibration_data, f, indent=2)

    print(f"\n💾 Calibration saved to {calibration_output}")
    print("\n📋 Sample prompt scores (first 5):")
    for i, result in enumerate(results[:5]):
        status = "✅" if result["score"] >= calibrated_threshold else "❌"
        print(f"   {status} Prompt {i+1}: score={result['score']:.2f}, length={result['prompt_length']}")

    return calibration_data


if __name__ == "__main__":
    try:
        bootstrap_calibration()
        print("\n✅ Calibration complete!")
    except Exception as e:
        print(f"\n❌ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
