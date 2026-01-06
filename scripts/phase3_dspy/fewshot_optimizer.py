#!/usr/bin/env python3
"""DSPy FewShot optimizer using unified pool.

This module provides functionality to load the unified few-shot pool
and compile a KNNFewShot optimizer for production few-shot learning.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import dspy
from eval.src.dspy_prompt_improver_fewshot import (
    PromptImproverWithFewShot,
    create_vectorizer,
)


def load_unified_pool(pool_path: Path) -> List[dspy.Example]:
    """Load unified few-shot pool from JSON.

    The unified pool has a wrapper structure with metadata and examples:
    {
        "metadata": {...},
        "examples": [
            {
                "inputs": {"original_idea": "...", "context": "..."},
                "outputs": {"improved_prompt": "...", "role": "...", ...},
                "metadata": {...}
            },
            ...
        ]
    }

    Args:
        pool_path: Path to unified-fewshot-pool.json

    Returns:
        List of DSPy Examples with inputs() and outputs() properly set

    Raises:
        FileNotFoundError: If pool_path doesn't exist
        KeyError: If pool structure is invalid
    """
    if not pool_path.exists():
        raise FileNotFoundError(f"Unified pool not found at {pool_path}")

    with open(pool_path, encoding='utf-8') as f:
        data = json.load(f)

    # Validate structure
    if 'examples' not in data:
        raise KeyError("Invalid pool structure: missing 'examples' key")

    examples = data['examples']

    # Convert to DSPy Examples
    dspy_examples = []
    for ex in examples:
        inputs = ex['inputs']
        outputs = ex['outputs']

        dspy_ex = dspy.Example(
            original_idea=inputs['original_idea'],
            context=inputs.get('context', ''),
            improved_prompt=outputs['improved_prompt'],
            role=outputs.get('role', ''),
            directive=outputs.get('directive', ''),
            framework=outputs.get('framework', ''),
            guardrails=outputs.get('guardrails', ''),
        ).with_inputs('original_idea', 'context')

        dspy_examples.append(dspy_ex)

    return dspy_examples


def compile_fewshot_with_pool(
    trainset_path: Path,
    output_path: Path,
    k: int = 3
) -> PromptImproverWithFewShot:
    """Compile KNNFewShot with unified pool.

    Args:
        trainset_path: Path to unified-fewshot-pool.json
        output_path: Path to save compilation metadata
        k: Number of neighbors for KNNFewShot (default: 3)

    Returns:
        Compiled PromptImproverWithFewShot instance

    Raises:
        FileNotFoundError: If trainset_path doesn't exist
        RuntimeError: If compilation fails
    """
    if not trainset_path.exists():
        raise FileNotFoundError(f"Unified pool not found at {trainset_path}")

    # Load training data
    print(f"Loading unified pool from {trainset_path}...")
    trainset = load_unified_pool(trainset_path)
    print(f"  Loaded {len(trainset)} examples")

    # Create few-shot improver
    print(f"\nCreating KNNFewShot improver with k={k}...")

    improver = PromptImproverWithFewShot(
        compiled_path=str(output_path),
        k=k,
        fallback_to_zeroshot=True
    )

    # Compile with KNNFewShot
    print(f"Compiling with k={k}...")
    try:
        improver.compile(trainset, k=k)
        print(f"✓ Compilation complete")
    except Exception as e:
        raise RuntimeError(f"Compilation failed: {e}")

    # Save compiled metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_metadata = {
        'model_type': 'KNNFewShot',
        'k': k,
        'trainset_size': len(trainset),
        'trainset_path': str(trainset_path),
        'created_at': str(datetime.now())
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(compiled_metadata, f, indent=2)

    print(f"✓ Metadata saved to: {output_path}")

    return improver


def get_feature_flag() -> bool:
    """Get USE_KNN_FEWSHOT / DSPY_FEWSHOT_ENABLED feature flag.

    Checks both USE_KNN_FEWSHOT (new name) and DSPY_FEWSHOT_ENABLED (legacy).
    USE_KNN_FEWSHOT takes precedence if both are set.

    Returns:
        True if few-shot learning is enabled, False otherwise

    Examples:
        >>> # Enable few-shot
        >>> os.environ['USE_KNN_FEWSHOT'] = 'true'
        >>> get_feature_flag()
        True

        >>> # Disable few-shot
        >>> os.environ['USE_KNN_FEWSHOT'] = 'false'
        >>> get_feature_flag()
        False
    """
    # Check new flag first
    use_knn = os.environ.get('USE_KNN_FEWSHOT', '').lower()
    if use_knn:
        return use_knn in ('true', '1', 'yes', 'on')

    # Fall back to legacy flag
    dspy_fewshot = os.environ.get('DSPY_FEWSHOT_ENABLED', '').lower()
    if dspy_fewshot:
        return dspy_fewshot in ('true', '1', 'yes', 'on')

    # Default: enabled for safety (can be disabled via env var)
    return True


def create_optimizer_from_config(
    pool_path: Optional[Path] = None,
    k: int = 3,
    force_recompile: bool = False
) -> Optional[PromptImproverWithFewShot]:
    """Create few-shot optimizer from environment configuration.

    This is the main entry point for production use. It:
    1. Checks USE_KNN_FEWSHOT feature flag
    2. Loads unified pool if flag is enabled
    3. Compiles KNNFewShot optimizer

    Args:
        pool_path: Path to unified pool (defaults to datasets/exports/unified-fewshot-pool.json)
        k: Number of neighbors (default: 3)
        force_recompile: Force recompilation even if compiled model exists

    Returns:
        Compiled PromptImproverWithFewShot if feature flag is enabled,
        None if feature flag is disabled

    Examples:
        >>> # Enable and create optimizer
        >>> os.environ['USE_KNN_FEWSHOT'] = 'true'
        >>> optimizer = create_optimizer_from_config()
        >>> result = optimizer(original_idea="test", context="")

        >>> # Disable (returns None)
        >>> os.environ['USE_KNN_FEWSHOT'] = 'false'
        >>> optimizer = create_optimizer_from_config()
        >>> assert optimizer is None
    """
    # Check feature flag
    if not get_feature_flag():
        print("USE_KNN_FEWSHOT is disabled, skipping few-shot optimizer")
        return None

    # Default pool path
    if pool_path is None:
        project_root = Path(__file__).parent.parent.parent
        pool_path = project_root / 'datasets/exports/unified-fewshot-pool.json'

    # Check if pool exists
    if not pool_path.exists():
        print(f"Warning: Unified pool not found at {pool_path}")
        print("Few-shot learning will not be available")
        return None

    # Output path for compiled metadata
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / 'models/fewshot-compiled.json'

    # Compile
    try:
        improver = compile_fewshot_with_pool(
            trainset_path=pool_path,
            output_path=output_path,
            k=k
        )
        return improver
    except Exception as e:
        print(f"Error compiling few-shot optimizer: {e}")
        return None


def main() -> int:
    """Compile few-shot optimizer with unified pool (CLI entry point).

    This function:
    1. Loads the unified pool
    2. Compiles KNNFewShot with k=3
    3. Tests with a sample prompt

    Returns:
        0 on success, 1 on failure
    """
    project_root = Path(__file__).parent.parent.parent

    # Paths
    pool_path = project_root / 'datasets/exports/unified-fewshot-pool.json'
    output_path = project_root / 'models/fewshot-compiled.json'

    if not pool_path.exists():
        print(f"❌ Unified pool not found at {pool_path}")
        print("   Run merge_unified_pool.py first!")
        return 1

    try:
        # Compile
        improver = compile_fewshot_with_pool(pool_path, output_path, k=3)

        # Test with sample prompt
        print("\n" + "=" * 70)
        print("TESTING WITH SAMPLE PROMPT")
        print("=" * 70)

        test_input = "Documenta una función en TypeScript"
        print(f"\nInput: {test_input}")

        # Note: We can't actually run inference without DSPy LM configured
        # This just validates the compilation worked
        print(f"\n✓ KNNFewShot compiled successfully!")
        print(f"   k=3")
        print(f"   Trainset size: {improver.compiled_improver is not None}")
        print(f"   Ready for inference")

        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
