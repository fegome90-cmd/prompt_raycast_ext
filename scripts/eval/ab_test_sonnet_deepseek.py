#!/usr/bin/env python3
"""
A/B Test: Sonnet 4.5 vs DeepSeek Chat

Compares prompt improvement quality between:
- Anthropic Claude Sonnet 4.5
- DeepSeek Chat

Usage:
    python scripts/eval/ab_test_sonnet_deepseek.py [--subset N]
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests


# ============================================================================
# Data Models
# ============================================================================

class TestCase:
    def __init__(self, id: str, input: str, asserts: Dict = None):
        self.id = id
        self.input = input
        self.asserts = asserts or {}


class ImprovementResult:
    def __init__(self, **kwargs):
        self.provider = kwargs.get("provider", "")
        self.model = kwargs.get("model", "")
        self.test_id = kwargs.get("test_id", "")
        self.input = kwargs.get("input", "")
        self.improved_prompt = kwargs.get("improved_prompt", "")
        self.role = kwargs.get("role", "")
        self.directive = kwargs.get("directive", "")
        self.framework = kwargs.get("framework", "")
        self.guardrails = kwargs.get("guardrails", [])
        self.reasoning = kwargs.get("reasoning", "")
        self.confidence = kwargs.get("confidence", 0.0)
        self.latency_ms = kwargs.get("latency_ms", 0.0)
        self.error = kwargs.get("error", "")


# ============================================================================
# Test Configuration
# ============================================================================

API_BASE = "http://localhost:8000"

TEST_CASES = [
    TestCase(id="good-001", input="Documenta una función en TypeScript",
             asserts={"minFinalPromptLength": 50, "minConfidence": 0.7}),
    TestCase(id="good-002", input="Escribe un hook de React para manejar formularios",
             asserts={"minFinalPromptLength": 50, "minConfidence": 0.75}),
    TestCase(id="good-003", input="Crea un componente Button con variantes",
             asserts={"minFinalPromptLength": 50, "minConfidence": 0.8}),
    TestCase(id="good-004", input="Implementa un debounce utility en JavaScript",
             asserts={"minFinalPromptLength": 50, "minConfidence": 0.7}),
    TestCase(id="good-005", input="Diseña un schema de Zod para validar usuarios",
             asserts={"minFinalPromptLength": 50, "minConfidence": 0.75}),
]


# ============================================================================
# Provider Switching
# ============================================================================

def switch_provider(provider: str, model: str) -> bool:
    """Switch backend provider by updating .env and restarting.

    Args:
        provider: "anthropic" or "deepseek"
        model: Model name

    Returns:
        True if successful
    """
    env_path = Path(__file__).parent.parent.parent / ".env"

    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update provider and model
    new_lines = []
    for line in lines:
        if line.startswith("LLM_PROVIDER="):
            new_lines.append(f"LLM_PROVIDER={provider}\n")
        elif line.startswith("LLM_MODEL="):
            new_lines.append(f"LLM_MODEL={model}\n")
        else:
            new_lines.append(line)

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)

    # Restart backend using make (static command)
    print(f"  → Switching to {provider}/{model}...")
    subprocess.run(["make", "restart"], capture_output=True, timeout=30)

    # Wait for restart
    time.sleep(3)

    # Verify health
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        data = resp.json()
        if data.get("provider") == provider and data.get("dspy_configured"):
            print(f"  ✓ Switched to {provider}/{model}")
            return True
        else:
            print(f"  ✗ Health check failed: {data}")
            return False
    except Exception as e:
        print(f"  ✗ Health check error: {e}")
        return False


# ============================================================================
# API Client
# ============================================================================

def improve_prompt(idea: str, context: str = "") -> Dict:
    """Call DSPy backend to improve prompt."""
    payload = {"idea": idea, "context": context}

    start = time.time()
    try:
        resp = requests.post(
            f"{API_BASE}/api/v1/improve-prompt",
            json=payload,
            timeout=30
        )
        latency_ms = (time.time() - start) * 1000

        if resp.ok:
            data = resp.json()
            data["latency_ms"] = latency_ms
            return data
        else:
            return {"error": f"HTTP {resp.status}: {resp.text}", "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {"error": str(e), "latency_ms": latency_ms}


# ============================================================================
# Quality Evaluation
# ============================================================================

def evaluate_quality(result: Dict, test_case: TestCase) -> Dict[str, bool]:
    """Evaluate quality gates for a result."""
    gates = {
        "json_valid": True,
        "confidence_ok": False,
        "min_length_ok": False,
        "has_structure": False,
        "no_ai_speak": False,
    }

    if "error" in result:
        return gates

    improved_prompt = result.get("improved_prompt", "")
    confidence = result.get("confidence", 0.0)

    gates["confidence_ok"] = confidence >= test_case.asserts.get("minConfidence", 0.7)

    min_length = test_case.asserts.get("minFinalPromptLength", 50)
    gates["min_length_ok"] = len(improved_prompt) >= min_length

    has_role = bool(result.get("role"))
    has_directive = bool(result.get("directive"))
    has_framework = bool(result.get("framework"))
    gates["has_structure"] = has_role and has_directive and has_framework

    ai_speak_phrases = ["as an ai", "as a language model", "hard rules", "output rules"]
    improved_lower = improved_prompt.lower()
    gates["no_ai_speak"] = not any(phrase in improved_lower for phrase in ai_speak_phrases)

    return gates


# ============================================================================
# Main Test Runner
# ============================================================================

def run_ab_test(subset: int = 5) -> Dict[str, List[ImprovementResult]]:
    """Run A/B test between Sonnet 4.5 and DeepSeek."""
    results = {"sonnet": [], "deepseek": []}
    test_cases = TEST_CASES[:subset]

    # Test Sonnet 4.5
    print("\n" + "="*60)
    print("Testing: Claude Sonnet 4.5")
    print("="*60)

    if not switch_provider("anthropic", "claude-sonnet-4-5-20250929"):
        print("✗ Failed to switch to Sonnet 4.5")
        return results

    for tc in test_cases:
        print(f"\n[{tc.id}] {tc.input[:50]}...")
        result_data = improve_prompt(tc.input)

        result = ImprovementResult(
            provider="anthropic",
            model="claude-sonnet-4-5-20250929",
            test_id=tc.id,
            input=tc.input,
            improved_prompt=result_data.get("improved_prompt", ""),
            role=result_data.get("role", ""),
            directive=result_data.get("directive", ""),
            framework=result_data.get("framework", ""),
            guardrails=result_data.get("guardrails", []),
            reasoning=result_data.get("reasoning", ""),
            confidence=result_data.get("confidence", 0.0),
            latency_ms=result_data.get("latency_ms", 0.0),
            error=result_data.get("error", "")
        )

        gates = evaluate_quality(result_data, tc)

        print(f"  Confidence: {result.confidence:.2f} {'✓' if gates['confidence_ok'] else '✗'}")
        print(f"  Length: {len(result.improved_prompt)} chars {'✓' if gates['min_length_ok'] else '✗'}")
        print(f"  Structure: {'✓' if gates['has_structure'] else '✗'}")
        print(f"  No AI speak: {'✓' if gates['no_ai_speak'] else '✗'}")
        print(f"  Latency: {result.latency_ms:.0f}ms")

        results["sonnet"].append(result)

    # Test DeepSeek
    print("\n" + "="*60)
    print("Testing: DeepSeek Chat")
    print("="*60)

    if not switch_provider("deepseek", "deepseek-chat"):
        print("✗ Failed to switch to DeepSeek")
        return results

    for tc in test_cases:
        print(f"\n[{tc.id}] {tc.input[:50]}...")
        result_data = improve_prompt(tc.input)

        result = ImprovementResult(
            provider="deepseek",
            model="deepseek-chat",
            test_id=tc.id,
            input=tc.input,
            improved_prompt=result_data.get("improved_prompt", ""),
            role=result_data.get("role", ""),
            directive=result_data.get("directive", ""),
            framework=result_data.get("framework", ""),
            guardrails=result_data.get("guardrails", []),
            reasoning=result_data.get("reasoning", ""),
            confidence=result_data.get("confidence", 0.0),
            latency_ms=result_data.get("latency_ms", 0.0),
            error=result_data.get("error", "")
        )

        gates = evaluate_quality(result_data, tc)

        print(f"  Confidence: {result.confidence:.2f} {'✓' if gates['confidence_ok'] else '✗'}")
        print(f"  Length: {len(result.improved_prompt)} chars {'✓' if gates['min_length_ok'] else '✗'}")
        print(f"  Structure: {'✓' if gates['has_structure'] else '✗'}")
        print(f"  No AI speak: {'✓' if gates['no_ai_speak'] else '✗'}")
        print(f"  Latency: {result.latency_ms:.0f}ms")

        results["deepseek"].append(result)

    return results


# ============================================================================
# Summary & Reporting
# ============================================================================

def print_summary(results: Dict[str, List[ImprovementResult]]):
    """Print A/B test summary."""
    print("\n" + "="*60)
    print("A/B TEST SUMMARY")
    print("="*60)

    for provider_name, provider_results in results.items():
        if not provider_results:
            continue

        print(f"\n{provider_name.upper()}:")
        avg_confidence = sum(r.confidence for r in provider_results) / len(provider_results)
        avg_latency = sum(r.latency_ms for r in provider_results) / len(provider_results)
        avg_length = sum(len(r.improved_prompt) for r in provider_results) / len(provider_results)

        pass_confidence = sum(1 for r in provider_results if r.confidence >= 0.7) / len(provider_results)
        pass_length = sum(1 for r in provider_results if len(r.improved_prompt) >= 50) / len(provider_results)
        pass_structure = sum(1 for r in provider_results if r.role and r.directive and r.framework) / len(provider_results)

        print(f"  Avg Confidence: {avg_confidence:.2f} ({pass_confidence*100:.0f}% pass)")
        print(f"  Avg Length: {avg_length:.0f} chars ({pass_length*100:.0f}% pass)")
        print(f"  Structure: {pass_structure*100:.0f}% pass")
        print(f"  Avg Latency: {avg_latency:.0f}ms")

    # Comparison
    if len(results["sonnet"]) > 0 and len(results["deepseek"]) > 0:
        print("\n" + "-"*60)
        print("COMPARISON:")
        sonnet_conf = sum(r.confidence for r in results["sonnet"]) / len(results["sonnet"])
        deepseek_conf = sum(r.confidence for r in results["deepseek"]) / len(results["deepseek"])
        sonnet_lat = sum(r.latency_ms for r in results["sonnet"]) / len(results["sonnet"])
        deepseek_lat = sum(r.latency_ms for r in results["deepseek"]) / len(results["deepseek"])
        print(f"  Confidence: Sonnet {sonnet_conf:.2f} vs DeepSeek {deepseek_conf:.2f}")
        print(f"  Latency: Sonnet {sonnet_lat:.0f}ms vs DeepSeek {deepseek_lat:.0f}ms")


def save_results(results: Dict[str, List[ImprovementResult]]):
    """Save results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(__file__).parent / f"ab_test_sonnet_deepseek_{timestamp}.json"

    def to_dict(r):
        return {
            "provider": r.provider,
            "model": r.model,
            "test_id": r.test_id,
            "input": r.input,
            "improved_prompt": r.improved_prompt,
            "role": r.role,
            "directive": r.directive,
            "framework": r.framework,
            "guardrails": r.guardrails,
            "reasoning": r.reasoning,
            "confidence": r.confidence,
            "latency_ms": r.latency_ms,
            "error": r.error,
        }

    output_data = {
        "timestamp": timestamp,
        "sonnet": [to_dict(r) for r in results["sonnet"]],
        "deepseek": [to_dict(r) for r in results["deepseek"]],
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Results saved to: {output_path}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="A/B Test: Sonnet 4.5 vs DeepSeek")
    parser.add_argument("--subset", type=int, default=5, help="Number of test cases (default: 5)")
    args = parser.parse_args()

    print("A/B Test: Claude Sonnet 4.5 vs DeepSeek Chat")
    print(f"Test Cases: {args.subset}")

    results = run_ab_test(subset=args.subset)
    print_summary(results)
    save_results(results)

    # Switch back to Sonnet 4.5
    print("\n" + "="*60)
    print("Switching back to Sonnet 4.5...")
    switch_provider("anthropic", "claude-sonnet-4-5-20250929")
    print("✓ Done!")


if __name__ == "__main__":
    main()
