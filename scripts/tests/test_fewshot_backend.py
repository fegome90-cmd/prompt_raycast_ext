#!/usr/bin/env python3
"""
Test script for few-shot backend integration.

Tests:
1. Backend with few-shot enabled
2. API response structure
3. Performance comparison (few-shot vs zero-shot)
"""

import os
import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_backend_with_fewshot():
    """Test backend with few-shot mode enabled."""
    print("=" * 60)
    print("Few-Shot Backend Integration Test")
    print("=" * 60)

    # Set environment for few-shot mode
    os.environ["DSPY_FEWSHOT_ENABLED"] = "true"
    os.environ["DSPY_FEWSHOT_TRAINSET_PATH"] = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/merged-trainset.json"
    os.environ["DSPY_FEWSHOT_K"] = "3"

    print("\n🔧 Configuration:")
    print(f"   DSPY_FEWSHOT_ENABLED: {os.getenv('DSPY_FEWSHOT_ENABLED')}")
    print(f"   DSPY_FEWSHOT_TRAINSET_PATH: {os.getenv('DSPY_FEWSHOT_TRAINSET_PATH')}")
    print(f"   DSPY_FEWSHOT_K: {os.getenv('DSPY_FEWSHOT_K')}")

    # Import after setting environment
    import dspy

    from hemdov.infrastructure.config import Settings
    from hemdov.interfaces import container

    settings = container.get(Settings)
    print("\n✓ Settings loaded:")
    print(f"   FEWSHOT_ENABLED: {settings.DSPY_FEWSHOT_ENABLED}")
    print(f"   TRAINSET_PATH: {settings.DSPY_FEWSHOT_TRAINSET_PATH}")
    print(f"   K: {settings.DSPY_FEWSHOT_K}")

    # Configure DSPy LM
    print("\n🔧 Configuring DSPy LM...")
    from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_deepseek_adapter
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.0,
    )
    dspy.configure(lm=lm)
    print(f"   ✓ DSPy configured with {settings.LLM_MODEL}")

    # Test API import
    print("\n📦 Testing API imports...")
    try:
        from api.prompt_improver_api import get_fewshot_improver, get_prompt_improver
        print("   ✓ Imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # Initialize few-shot improver (this will compile with training set)
    print("\n🔧 Initializing few-shot improver (may take a moment)...")
    start = time.time()
    try:
        fewshot_improver = get_fewshot_improver(settings)
        elapsed = time.time() - start
        print(f"   ✓ Few-shot improver initialized in {elapsed:.2f}s")
        print(f"   ✓ Compiled: {fewshot_improver._compiled}")
    except Exception as e:
        print(f"   ✗ Failed to initialize few-shot improver: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test inference
    print("\n🧪 Testing inference...")
    test_idea = "Documenta una función TypeScript que calcula el factorial"

    # Few-shot
    print("\n   Few-shot mode:")
    start = time.time()
    try:
        result_fewshot = fewshot_improver(original_idea=test_idea, context="")
        elapsed_fewshot = time.time() - start
        print(f"   ✓ Latency: {elapsed_fewshot:.2f}s")
        print(f"   ✓ Confidence: {getattr(result_fewshot, 'confidence', 'N/A')}")
        print(f"   ✓ Role: {result_fewshot.role[:50]}..." if len(result_fewshot.role) > 50 else f"   ✓ Role: {result_fewshot.role}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Zero-shot (for comparison)
    print("\n   Zero-shot mode (for comparison):")
    zero_improver = get_prompt_improver(settings)
    start = time.time()
    try:
        result_zero = zero_improver(original_idea=test_idea, context="")
        elapsed_zero = time.time() - start
        print(f"   ✓ Latency: {elapsed_zero:.2f}s")
        print(f"   ✓ Confidence: {getattr(result_zero, 'confidence', 'N/A')}")
        print(f"   ✓ Role: {result_zero.role[:50]}..." if len(result_zero.role) > 50 else f"   ✓ Role: {result_zero.role}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Comparison
    print("\n📊 Comparison:")
    latency_diff = ((elapsed_fewshot - elapsed_zero) / elapsed_zero) * 100
    print(f"   Latency delta: {latency_diff:+.1f}%")

    if hasattr(result_fewshot, 'confidence') and hasattr(result_zero, 'confidence'):
        try:
            conf_zero = float(result_zero.confidence) if isinstance(result_zero.confidence, str) else result_zero.confidence
            conf_fewshot = float(result_fewshot.confidence) if isinstance(result_fewshot.confidence, str) else result_fewshot.confidence
            conf_delta = conf_fewshot - conf_zero
            print(f"   Confidence delta: {conf_delta:+.3f}")
        except (ValueError, TypeError):
            print("   Confidence delta: N/A")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_backend_with_fewshot()
    sys.exit(0 if success else 1)
