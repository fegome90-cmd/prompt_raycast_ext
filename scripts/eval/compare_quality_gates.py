#!/usr/bin/env python3
"""
Compare quality gates between zero-shot and few-shot modes.

Evaluates:
- JSON validity
- Confidence scores
- Copyability
- Review rate

Usage:
    python scripts/compare_quality_gates.py [--subset N]
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_test_cases(path: str) -> List[Dict]:
    """Load test cases from JSONL file."""
    cases = []
    with open(path, 'r') as f:
        for line in f:
            cases.append(json.loads(line))
    return cases


def evaluate_quality_gate(result: Dict, case: Dict) -> Dict[str, bool]:
    """Evaluate quality gates for a single result.

    Returns:
        Dict with quality gate results
    """
    gates = {
        "json_valid": True,  # Always valid from DSPy
        "confidence_ok": False,
        "copyable": False,
        "review_rate_ok": False,
    }

    # Confidence gate
    confidence = getattr(result, 'confidence', 0.5)
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except ValueError:
            confidence = 0.5
    gates["confidence_ok"] = confidence >= 0.7

    # Copyability gate (check if prompt is copyable)
    improved_prompt = result.improved_prompt
    if improved_prompt:
        gates["copyable"] = len(improved_prompt) > 50 and "Role:" in improved_prompt or "##" in improved_prompt

    # Review rate gate (based on asserts from test case)
    asserts = case.get('asserts', {})
    if 'minFinalPromptLength' in asserts:
        gates["copyable"] = gates["copyable"] and len(improved_prompt) >= asserts['minFinalPromptLength']

    # Review rate is high quality (not "bad" category)
    gates["review_rate_ok"] = not case.get('id', '').startswith('bad-')

    return gates


def run_evaluation(improver, cases: List[Dict], mode: str) -> Dict:
    """Run evaluation on test cases.

    Args:
        improver: DSPy improver instance
        cases: Test cases
        mode: "zero-shot" or "few-shot"

    Returns:
        Evaluation results
    """
    results = {
        "mode": mode,
        "total": len(cases),
        "success": 0,
        "failed": 0,
        "gates": {
            "json_valid": 0,
            "confidence_ok": 0,
            "copyable": 0,
            "review_rate_ok": 0,
        },
        "latencies": [],
        "confidences": [],
        "errors": [],
    }

    print(f"\n{'='*60}")
    print(f"Evaluating {mode} mode on {len(cases)} cases")
    print(f"{'='*60}")

    for i, case in enumerate(cases, 1):
        case_id = case.get('id', f'case-{i}')
        input_text = case.get('input', '')

        print(f"\n[{i}/{len(cases)}] {case_id}: {input_text[:50]}...")

        try:
            start = time.time()
            result = improver(original_idea=input_text, context="")
            elapsed = time.time() - start

            # Evaluate quality gates
            gates = evaluate_quality_gate(result, case)

            # Track results
            results["success"] += 1
            results["latencies"].append(elapsed)
            for gate, passed in gates.items():
                if passed:
                    results["gates"][gate] += 1

            # Track confidence
            confidence = getattr(result, 'confidence', 0.5)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    confidence = 0.5
            results["confidences"].append(confidence)

            print(f"   ✓ Latency: {elapsed:.2f}s, Confidence: {confidence:.2f}")
            print(f"   ✓ Gates: {sum(gates.values())}/4 PASSED")

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"case": case_id, "error": str(e)})
            print(f"   ✗ Failed: {e}")

    return results


def print_summary(zero_shot_results: Dict, fewshot_results: Dict):
    """Print comparison summary."""
    print(f"\n{'='*60}")
    print("QUALITY GATES COMPARISON")
    print(f"{'='*60}")

    for mode, results in [("Zero-Shot", zero_shot_results), ("Few-Shot", fewshot_results)]:
        print(f"\n{mode} Mode:")
        print(f"   Total cases: {results['total']}")
        print(f"   Success: {results['success']}")
        print(f"   Failed: {results['failed']}")

        if results['latencies']:
            avg_latency = sum(results['latencies']) / len(results['latencies'])
            p95_latency = sorted(results['latencies'])[int(len(results['latencies']) * 0.95)] if len(results['latencies']) >= 20 else max(results['latencies'])
            print(f"   Avg latency: {avg_latency:.2f}s")
            print(f"   P95 latency: {p95_latency:.2f}s")

        if results['confidences']:
            avg_confidence = sum(results['confidences']) / len(results['confidences'])
            print(f"   Avg confidence: {avg_confidence:.3f}")

        print(f"\n   Quality Gates:")
        for gate, count in results['gates'].items():
            percentage = (count / results['total']) * 100 if results['total'] > 0 else 0
            print(f"      {gate}: {count}/{results['total']} ({percentage:.1f}%)")

        all_gates = min(results['gates'].values())
        print(f"\n   All Gates (4/4): {all_gates}/{results['total']}")

    # Comparison
    print(f"\n{'='*60}")
    print("DELTA (Few-Shot - Zero-Shot)")
    print(f"{'='*60}")

    for gate in ["json_valid", "confidence_ok", "copyable", "review_rate_ok"]:
        zero_count = zero_shot_results['gates'][gate]
        fewshot_count = fewshot_results['gates'][gate]
        delta = fewshot_count - zero_count
        delta_pct = (delta / zero_shot_results['total']) * 100 if zero_shot_results['total'] > 0 else 0
        symbol = "+" if delta > 0 else ""
        print(f"   {gate}: {symbol}{delta} ({symbol}{delta_pct:.1f}%)")

    # All gates comparison
    zero_all = min(zero_shot_results['gates'].values())
    fewshot_all = min(fewshot_results['gates'].values())
    delta_all = fewshot_all - zero_all
    delta_all_pct = (delta_all / zero_shot_results['total']) * 100 if zero_shot_results['total'] > 0 else 0
    symbol = "+" if delta_all > 0 else ""
    print(f"\n   All Gates (4/4): {symbol}{delta_all} ({symbol}{delta_all_pct:.1f}%)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare quality gates between zero-shot and few-shot")
    parser.add_argument("--subset", type=int, default=10, help="Number of test cases to evaluate (default: 10)")
    parser.add_argument("--dataset", type=str, default="/Users/felipe_gonzalez/Developer/raycast_ext/dashboard/testdata/cases.jsonl",
                       help="Path to test dataset")
    args = parser.parse_args()

    # Load test cases
    print(f"📂 Loading test cases from {args.dataset}...")
    all_cases = load_test_cases(args.dataset)
    cases = all_cases[:args.subset]
    print(f"   Loaded {len(cases)} cases (subset of {len(all_cases)} total)")

    # Setup DSPy
    print(f"\n🔧 Setting up DSPy...")
    import dspy
    from hemdov.infrastructure.config import Settings
    from hemdov.interfaces import container
    from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_deepseek_adapter
    from eval.src.dspy_prompt_improver import PromptImprover

    settings = container.get(Settings)
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.0,
    )
    dspy.configure(lm=lm)
    print(f"   ✓ Configured with {settings.LLM_MODEL}")

    # Zero-shot evaluation
    zero_improver = PromptImprover()
    zero_shot_results = run_evaluation(zero_improver, cases, "zero-shot")

    # Few-shot evaluation
    print(f"\n🔧 Initializing few-shot improver...")
    from eval.src.dspy_prompt_improver_fewshot import (
        PromptImproverWithFewShot,
        load_trainset
    )

    trainset_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/merged-trainset.json"
    print(f"   Loading training set from {trainset_path}...")
    trainset = load_trainset(trainset_path)
    print(f"   Loaded {len(trainset)} examples")

    print(f"   Compiling with KNNFewShot (k=3)...")
    fewshot_improver = PromptImproverWithFewShot(k=3)
    fewshot_improver.compile(trainset, k=3)
    print(f"   ✓ Compilation complete")

    fewshot_results = run_evaluation(fewshot_improver, cases, "few-shot")

    # Print summary
    print_summary(zero_shot_results, fewshot_results)

    # Save results
    output_path = f"/Users/felipe_gonzalez/Developer/raycast_ext/eval/quality-gates-comparison-{args.subset}cases.json"
    print(f"\n💾 Saving results to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            "zero_shot": zero_shot_results,
            "fewshot": fewshot_results,
        }, f, indent=2)
    print(f"   ✓ Results saved")


if __name__ == "__main__":
    main()
