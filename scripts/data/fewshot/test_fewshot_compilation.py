#!/usr/bin/env python3
"""
Test script for DSPy few-shot compilation.

Tests:
1. Load merged training set
2. Compile PromptImproverWithFewShot
3. Run inference on test cases
4. Compare with baseline (zero-shot)
"""

import sys
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "eval"))

from eval.src.dspy_prompt_improver_fewshot import (
    PromptImproverWithFewShot,
    load_trainset,
    create_fewshot_improver
)
from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_deepseek_adapter
from hemdov.interfaces import container
import dspy


def setup_dspy():
    """Initialize DSPy with DeepSeek."""
    print("🔧 Initializing DSPy with DeepSeek...")

    settings = container.get(Settings)
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.0,
    )
    dspy.configure(lm=lm)
    print(f"   ✓ Configured: {settings.LLM_MODEL}")


def test_load_trainset():
    """Test loading merged training set."""
    print("\n📂 Test 1: Load merged training set")

    trainset_path = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/merged-trainset.json"
    trainset = load_trainset(trainset_path)

    print(f"   ✓ Loaded {len(trainset)} examples")

    # Validate first example
    ex = trainset[0]
    assert hasattr(ex, 'original_idea'), "Missing original_idea"
    assert hasattr(ex, 'improved_prompt'), "Missing improved_prompt"
    inputs_dict = ex.inputs()
    assert 'original_idea' in inputs_dict, "Missing original_idea in inputs()"
    assert 'context' in inputs_dict, "Missing context in inputs()"
    print(f"   ✓ Format validated")

    return trainset


def test_compilation(trainset):
    """Test KNNFewShot compilation."""
    print("\n🔧 Test 2: Compile with KNNFewShot")

    improver = PromptImproverWithFewShot(k=3)

    start = time.time()
    improver.compile(trainset, k=3)
    elapsed = time.time() - start

    assert improver._compiled, "Compilation failed"
    print(f"   ✓ Compiled in {elapsed:.2f}s")

    return improver


def test_inference(compiled_improver, zero_shot_improver):
    """Test inference comparison."""
    print("\n🧪 Test 3: Inference comparison")

    test_input = "Documenta una función TypeScript que calcula el factorial"

    # Zero-shot
    print(f"\n   Input: {test_input}")
    print(f"\n   Zero-shot:")
    start = time.time()
    result_zero = zero_shot_improver(original_idea=test_input, context="")
    elapsed_zero = time.time() - start
    print(f"   - Latency: {elapsed_zero:.2f}s")
    print(f"   - Confidence: {getattr(result_zero, 'confidence', 'N/A')}")
    print(f"   - Role: {result_zero.role[:50]}..." if len(result_zero.role) > 50 else f"   - Role: {result_zero.role}")

    # Few-shot
    print(f"\n   Few-shot:")
    start = time.time()
    result_fewshot = compiled_improver(original_idea=test_input, context="")
    elapsed_fewshot = time.time() - start
    print(f"   - Latency: {elapsed_fewshot:.2f}s")
    print(f"   - Confidence: {getattr(result_fewshot, 'confidence', 'N/A')}")
    print(f"   - Role: {result_fewshot.role[:50]}..." if len(result_fewshot.role) > 50 else f"   - Role: {result_fewshot.role}")

    # Comparison
    print(f"\n   📊 Comparison:")
    latency_diff = ((elapsed_fewshot - elapsed_zero) / elapsed_zero) * 100
    print(f"   - Latency delta: {latency_diff:+.1f}%")

    if hasattr(result_zero, 'confidence') and hasattr(result_fewshot, 'confidence'):
        # Handle confidence as string or float
        try:
            conf_zero = float(result_zero.confidence) if isinstance(result_zero.confidence, str) else result_zero.confidence
            conf_fewshot = float(result_fewshot.confidence) if isinstance(result_fewshot.confidence, str) else result_fewshot.confidence
            conf_delta = conf_fewshot - conf_zero
            print(f"   - Confidence delta: {conf_delta:+.3f}")
        except (ValueError, TypeError):
            print(f"   - Confidence delta: N/A (non-numeric value)")


def test_error_handling():
    """Test error handling and fallback."""
    print("\n⚠️  Test 4: Error handling")

    # Test fallback to zero-shot
    improver = PromptImproverWithFewShot(
        k=3,
        fallback_to_zeroshot=True
    )

    # Test with empty trainset (should handle gracefully)
    try:
        empty_trainset = []
        improver.compile(empty_trainset, k=3)
        print(f"   ✓ Handled empty trainset gracefully")
    except Exception as e:
        print(f"   ⚠️  Empty trainset raised: {e}")

    # Test forward without proper compilation
    # (Empty trainset won't work for inference, so we create fresh improver)
    fresh_improver = PromptImproverWithFewShot(
        k=3,
        fallback_to_zeroshot=True
    )
    result = fresh_improver.forward(original_idea="Test input", context="")
    assert result is not None, "Forward without compilation failed"
    print(f"   ✓ Forward without compilation works (fallback to zero-shot)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("DSPy Few-Shot Compilation Tests")
    print("=" * 60)

    # Setup
    setup_dspy()

    # Test 1: Load trainset
    trainset = test_load_trainset()

    # Test 2: Compilation
    compiled_improver = test_compilation(trainset)

    # Test 3: Inference comparison
    zero_shot_improver = PromptImprover()
    test_inference(compiled_improver, zero_shot_improver)

    # Test 4: Error handling
    test_error_handling()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
