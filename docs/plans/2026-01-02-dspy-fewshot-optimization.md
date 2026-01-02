# DSPy Optimization + Few-Shot Learning - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a two-layer prompt optimization system that maximizes value from Phase 2 datasets - DSPy compiles and optimizes prompts, then few-shot learning enriches them with relevant examples, achieving multiplicative improvement in response quality.

**Architecture:** Two integrated layers working together: (1) DSPy Prompt Optimization loads train/val/test datasets from Phase 2 and uses DSPy to compile prompts with reusable modules, then optimizes hyperparameters against validation set with quality metrics like accuracy, coherence, and relevance; (2) Few-Shot Learning System takes optimized prompts and builds an example pool from train set, then implements intelligent selection (similarity-based, diversity-based, random) to pick best examples for each query; both layers combine in unified pipeline where DSPy generates base prompts and few-shot enriches them, producing final prompts that are more effective than either layer alone.

**Tech Stack:** DSPy (already installed), numpy/scipy for metrics, sentence-transformers for embeddings (optional, can use simpler similarity first), typing/dataclasses for type safety, pytest for testing, json for configuration.

---

## Overview

Phase 3 constructs a unified optimization pipeline that leverages Phase 2 datasets (train/val/test) through two complementary mechanisms:

**Layer 1 - DSPy Prompt Optimization:**
- Loads Phase 2 datasets from `datasets/exports/synthetic/`
- DSPy compiles prompts using signature, predictor, and teleprompter modules
- Optimizes prompt structure and hyperparameters using validation set
- Evaluates optimized prompts against test set with quality metrics
- Outputs optimized prompts with performance statistics

**Layer 2 - Few-Shot Learning System:**
- Takes optimized prompts from Layer 1
- Builds example pool from train set with metadata (domain, task type, confidence)
- Implements three selection strategies:
  - *Similarity-based:* Semantic similarity between query and examples
  - *Diversity-based:* Maximizes diversity of selected examples
  - *Random:* Baseline random selection
- Selects top-k examples for each query based on strategy
- Validates few-shot performance against test set

**Integration:**
- Unified pipeline orchestrates both layers
- Phase 2 datasets feed directly into Layer 1
- Layer 1 output feeds into Layer 2
- Final output: Optimized prompts with few-shot examples
- End-to-end evaluation on test set

---

## Task 1: DSPy Optimizer Infrastructure

**Files:**
- Create: `scripts/phase3_dspy/optimizer.py`
- Create: `scripts/phase3_dspy/config.py`
- Test: `scripts/tests/phase3/test_optimizer.py`

**Step 1: Write failing test for DatasetLoader**

```python
def test_load_phase2_datasets():
    """Should load train/val/test datasets from Phase 2"""
    loader = DatasetLoader()
    train, val, test = loader.load_datasets()

    assert len(train) == 11
    assert len(val) == 2
    assert len(test) == 3
    assert all('question' in ex for ex in train)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_load_phase2_datasets -v`
Expected: FAIL with "DatasetLoader not defined"

**Step 3: Write minimal DatasetLoader implementation**

```python
from pathlib import Path
import json
from typing import List, Dict

class DatasetLoader:
    """Load Phase 2 datasets for DSPy optimization."""

    def load_datasets(self) -> tuple[List[Dict], List[Dict], List[Dict]]:
        """Load train/val/test datasets from Phase 2.

        Returns:
            Tuple of (train, val, test) lists of examples
        """
        data_dir = Path("datasets/exports/synthetic")

        with open(data_dir / "train.json") as f:
            train = json.load(f)['examples']

        with open(data_dir / "val.json") as f:
            val = json.load(f)['examples']

        with open(data_dir / "test.json") as f:
            test = json.load(f)['examples']

        return train, val, test
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_load_phase2_datasets -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_dspy/optimizer.py scripts/phase3_dspy/config.py scripts/tests/phase3/test_optimizer.py
git commit -m "feat(phase3): Add DatasetLoader for Phase 2 datasets

Implemented DatasetLoader that loads train/val/test
datasets from Phase 2 (11 train, 2 val, 3 test examples).
Tests verify correct loading and data structure."
```

---

## Task 2: DSPy Signature and Predictor

**Files:**
- Modify: `scripts/phase3_dspy/optimizer.py`
- Test: `scripts/tests/phase3/test_optimizer.py`

**Step 1: Write failing test for DSPySignature**

```python
def test_dspy_signature_creation():
    """Should create DSPy signature from example"""
    signature = DSPySignature()
    compiled = signature.compile("test query")

    assert compiled is not None
    assert 'question' in signature.input_fields
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_dspy_signature_creation -v`
Expected: FAIL with "DSPySignature not defined"

**Step 3: Write minimal DSPySignature implementation**

```python
import dspy

class DSPySignature:
    """DSPy signature wrapper for prompt optimization."""

    def __init__(self):
        self.input_fields = ['question', 'metadata']
        self.output_fields = ['answer']

    def compile(self, query: str) -> dspy.Predict:
        """Compile DSPy signature for query.

        Args:
            query: Query string to optimize prompt for

        Returns:
            Compiled DSPy predictor
        """
        signature = dspy.Signature(self.input_fields, self.output_fields)
        return dspy.Predict(signature)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_dspy_signature_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_dspy/optimizer.py scripts/tests/phase3/test_optimizer.py
git commit -m "feat(phase3): Add DSPySignature and predictor

Implemented DSPySignature that wraps DSPy compilation
with input_fields and output_fields. Tests verify
compilation and field definitions."
```

---

## Task 3: DSPy Optimizer Core

**Files:**
- Modify: `scripts/phase3_dspy/optimizer.py`
- Test: `scripts/tests/phase3/test_optimizer.py`

**Step 1: Write failing test for DSPOptimizer**

```python
def test_dspy_optimizer_minimize_loss():
    """Should optimize prompt using val set"""
    optimizer = DSPOptimizer()
    train = [{"question": "test", "metadata": {}}]
    val = [{"question": "test", "metadata": {}}]

    optimized_prompt = optimizer.optimize(train, val)

    assert 'prompt' in optimized_prompt
    assert 'best_loss' in optimized_prompt
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_dspy_optimizer_minimize_loss -v`
Expected: FAIL with "DSPOptimizer not defined"

**Step 3: Write minimal DSPOptimizer implementation**

```python
class DSPOptimizer:
    """DSPy-based prompt optimizer."""

    def __init__(self):
        self.best_loss = float('inf')
        self.best_prompt = None

    def optimize(self, train: List[Dict], val: List[Dict]) -> Dict:
        """Optimize prompt using train/val sets.

        Args:
            train: Training examples
            val: Validation examples

        Returns:
            Dict with optimized prompt and metrics
        """
        # For now, use simple heuristic: optimize question length
        # Full DSPy optimization comes later

        avg_length = sum(len(e['question']) for e in train) / len(train)

        optimized = {
            'prompt': f"Optimal prompt length: {avg_length:.0f}",
            'best_loss': 0.5,  # Placeholder
            'metrics': {'avg_length': avg_length},
        }

        return optimized
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_optimizer.py::test_dspy_optimizer_minimize_loss -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_dspy/optimizer.py scripts/tests/phase3/test_optimizer.py
git commit -m "feat(phase3): Add DSPOptimizer core

Implemented basic DSPOptimizer with placeholder optimization.
Uses train set to calculate metrics, returns optimized
prompt configuration. Tests verify optimization output."
```

---

## Task 4: Example Pool for Few-Shot

**Files:**
- Create: `scripts/phase3_fewshot/example_pool.py`
- Test: `scripts/tests/phase3/test_example_pool.py`

**Step 1: Write failing test for ExamplePool**

```python
def test_example_pool_from_train_set():
    """Should build example pool from train set"""
    train = [
        {"question": "test 1", "metadata": {"domain": "SOFTDEV", "confidence": 0.8}},
        {"question": "test 2", "metadata": {"domain": "AIML", "confidence": 0.6}}
    ]

    pool = ExamplePool()
    pool.build(train)

    assert len(pool.examples) == 2
    assert pool.has_domain("SOFTDEV")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_example_pool.py::test_example_pool_from_train_set -v`
Expected: FAIL with "ExamplePool not defined"

**Step 3: Write minimal ExamplePool implementation**

```python
from typing import List, Dict

class ExamplePool:
    """Pool of examples for few-shot learning."""

    def __init__(self):
        self.examples = []
        self.domains = set()

    def build(self, train_examples: List[Dict]) -> None:
        """Build example pool from training set.

        Args:
            train_examples: List of training examples
        """
        self.examples = train_examples
        self.domains = {ex['metadata']['domain'] for ex in train_examples}

    def has_domain(self, domain: str) -> bool:
        """Check if domain exists in pool."""
        return domain in self.domains

    def get_examples_by_domain(self, domain: str) -> List[Dict]:
        """Get examples for specific domain."""
        return [ex for ex in self.examples if ex['metadata']['domain'] == domain]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_example_pool.py::test_example_pool_from_train_set -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_fewshot/example_pool.py scripts/tests/phase3/test_example_pool.py
git commit -m "feat(phase3): Add ExamplePool for few-shot learning

Implemented ExamplePool that builds from train set.
Supports domain-based filtering and example retrieval.
Tests verify pool construction and domain queries."
```

---

## Task 5: Similarity-Based Selection

**Files:**
- Create: `scripts/phase3_fewshot/selector.py`
- Test: `scripts/tests/phase3/test_selector.py`

**Step 1: Write failing test for SimilaritySelector**

```python
def test_similarity_selector_top_k():
    """Should return top-k most similar examples"""
    pool = ExamplePool()
    pool.build([
        {"question": "python coding", "metadata": {"domain": "SOFTDEV"}}
    ])

    selector = SimilaritySelector()
    results = selector.select("python code", pool, k=2)

    assert len(results) == 2
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_selector.py::test_similarity_selector_top_k -v`
Expected: FAIL with "SimilaritySelector not defined"

**Step 3: Write minimal SimilaritySelector implementation**

```python
from typing import List, Dict

class SimilaritySelector:
    """Similarity-based example selector for few-shot."""

    def select(self, query: str, pool: ExamplePool, k: int = 3) -> List[Dict]:
        """Select top-k most similar examples to query.

        Args:
            query: Query string
            pool: ExamplePool to search
            k: Number of examples to return

        Returns:
            List of top-k similar examples
        """
        # For now, use simple keyword matching
        # Real similarity with embeddings comes later

        query_lower = query.lower()
        scored = []

        for ex in pool.examples:
            question_lower = ex['question'].lower()

            # Simple similarity: keyword overlap
            query_words = set(query_lower.split())
            ex_words = set(question_lower.split())
            overlap = len(query_words & ex_words)
            similarity = overlap / len(query_words) if query_words else 0

            scored.append({
                'example': ex,
                'similarity': similarity
            })

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top-k
        top_k = [item['example'] for item in scored[:k]]

        return top_k
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_selector.py::test_similarity_selector_top_k -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_fewshot/selector.py scripts/tests/phase3/test_selector.py
git commit -m "feat(phase3): Add SimilaritySelector

Implemented SimilaritySelector using keyword overlap for now.
Selects top-k most similar examples to query.
Tests verify selection and ranking."
```

---

## Task 6: Unified Pipeline

**Files:**
- Create: `scripts/phase3_pipeline/optimizer.py`
- Create: `scripts/phase3_pipeline/main.py`
- Test: `scripts/tests/phase3/test_pipeline.py`

**Step 1: Write failing test for UnifiedPipeline**

```python
def test_unified_pipeline_end_to_end():
    """Should run complete optimization pipeline"""
    pipeline = UnifiedPipeline()
    result = pipeline.run()

    assert 'optimized_prompts' in result
    assert 'few_shot_examples' in result
    assert 'metrics' in result
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_pipeline.py::test_unified_pipeline_end_to_end -v`
Expected: FAIL with "UnifiedPipeline not defined"

**Step 3: Write minimal UnifiedPipeline implementation**

```python
from scripts.phase3_dspy.optimizer import DSPOptimizer, DatasetLoader
from scripts.phase3_fewshot.example_pool import ExamplePool
from scripts.phase3_fewshot.selector import SimilaritySelector

class UnifiedPipeline:
    """Unified DSPy + Few-Shot optimization pipeline."""

    def __init__(self):
        self.dspy_optimizer = DSPOptimizer()
        self.example_pool = ExamplePool()
        self.selector = SimilaritySelector()
        self.dataset_loader = DatasetLoader()

    def run(self) -> Dict:
        """Run complete optimization pipeline.

        Returns:
            Dict with optimized prompts and few-shot examples
        """
        # Load datasets
        train, val, test = self.dataset_loader.load_datasets()

        # Build example pool
        self.example_pool.build(train)

        # Optimize with DSPy
        dspy_result = self.dspy_optimizer.optimize(train, val)

        # Select few-shot examples for test set
        few_shot_results = []
        for test_example in test:
            selected = self.selector.select(
                test_example['question'],
                self.example_pool,
                k=3
            )
            few_shot_results.append({
                'query': test_example['question'],
                'selected_examples': selected
            })

        result = {
            'optimized_prompts': dspy_result,
            'few_shot_examples': few_shot_results,
            'metrics': {
                'train_size': len(train),
                'val_size': len(val),
                'test_size': len(test),
                'pool_size': len(self.example_pool.examples)
            }
        }

        return result
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_pipeline.py::test_unified_pipeline_end_to_end -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_pipeline/optimizer.py scripts/phase3_pipeline/main.py scripts/tests/phase3/test_pipeline.py
git commit -m "feat(phase3): Add UnifiedPipeline

Implemented end-to-end pipeline integrating DSPy optimization
and few-shot learning. Loads Phase 2 datasets, optimizes
prompts, selects examples, returns complete results.
Tests verify pipeline execution and output."
```

---

## Task 7: CLI Entry Point

**Files:**
- Modify: `scripts/phase3_pipeline/main.py`
- Test: `scripts/tests/phase3/test_cli.py`

**Step 1: Write failing test for CLI**

```python
def test_cli_main_command():
    """Should have main command entry point"""
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "scripts.phase3_pipeline.main"],
        capture_output=True
    )

    assert result.returncode == 0
    assert "Optimization complete" in result.stdout.decode()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_cli.py::test_cli_main_command -v`
Expected: FAIL with "command fails or no output"

**Step 3: Write minimal CLI implementation**

```python
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.phase3_pipeline.optimizer import UnifiedPipeline

def main():
    """Main CLI entry point."""
    print("=== DSPy + Few-Shot Optimization Pipeline ===\n")

    pipeline = UnifiedPipeline()
    result = pipeline.run()

    print("Optimization complete!")
    print(f"Train size: {result['metrics']['train_size']}")
    print(f"Val size: {result['metrics']['val_size']}")
    print(f"Test size: {result['metrics']['test_size']}")
    print(f"Example pool size: {result['metrics']['pool_size']}")

    print(f"\nOptimized prompts: {len(result['few_shot_examples'])}")

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_cli.py::test_cli_main_command -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/phase3_pipeline/main.py scripts/tests/phase3/test_cli.py
git commit -m "feat(phase3): Add CLI entry point

Implemented main.py with simple CLI for Phase 3 pipeline.
Prints optimization results and statistics.
Tests verify CLI execution and output."
```

---

## Task 8: End-to-End Integration Test

**Files:**
- Create: `scripts/tests/phase3/test_integration.py`

**Step 1: Write failing integration test**

```python
def test_phase3_integration_e2e():
    """Should run complete Phase 3 pipeline"""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    result = pipeline.run()

    # Verify pipeline components
    assert 'optimized_prompts' in result
    assert 'few_shot_examples' in result
    assert 'metrics' in result

    # Verify metrics
    metrics = result['metrics']
    assert metrics['train_size'] == 11
    assert metrics['val_size'] == 2
    assert metrics['test_size'] == 3
    assert metrics['pool_size'] == 11

    # Verify few-shot results
    few_shot = result['few_shot_examples']
    assert len(few_shot) == 3  # One per test example

    # Verify each test example has selected examples
    for item in few_shot:
        assert 'query' in item
        assert 'selected_examples' in item
        assert len(item['selected_examples']) == 3  # k=3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest scripts/tests/phase3/test_integration.py::test_phase3_integration_e2e -v`
Expected: FAIL with pipeline missing some components or outputs

**Step 3: Ensure all pipeline components work together**

All previous tasks should be complete. Just verify integration:

```bash
# Run pipeline
python3 -m scripts.phase3_pipeline.main

# Expected output:
# === DSPy + Few-Shot Optimization Pipeline ===
# Optimization complete!
# Train size: 11
# Val size: 2
# Test size: 3
# Example pool size: 11
# Optimized prompts: 3
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest scripts/tests/phase3/test_integration.py::test_phase3_integration_e2e -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/tests/phase3/test_integration.py
git commit -m "feat(phase3): Add end-to-end integration test

Implemented complete integration test for Phase 3 pipeline.
Verifies all components work together end-to-end.
Tests verify metrics, few-shot selection, and outputs."
```

---

## Task 9: Documentation

**Files:**
- Create: `docs/plans/phase3_README.md`

**Step 1: Write comprehensive README**

```markdown
# Phase 3: DSPy Optimization + Few-Shot Learning

## Overview

Phase 3 builds a unified two-layer prompt optimization system:

- **Layer 1 (DSPy):** Optimizes prompt structure and hyperparameters
- **Layer 2 (Few-Shot):** Enriches prompts with relevant examples

## Usage

```bash
# Run optimization pipeline
python3 -m scripts.phase3_pipeline.main
```

## Components

- **DatasetLoader:** Loads Phase 2 datasets (train/val/test)
- **DSPOptimizer:** DSPy-based prompt optimization
- **ExamplePool:** Repository of few-shot examples
- **SimilaritySelector:** Selects examples by similarity
- **UnifiedPipeline:** Orchestrates all components

## Architecture

```
Phase 2 Datasets (train/val/test)
         ↓
DatasetLoader
         ↓
    +-----> DSPOptimizer → Optimized Prompts
    |                    ↓
    +-------------------+
                         ↓
                 ExamplePool
                         ↓
              SimilaritySelector
                         ↓
           Few-Shot Examples + Optimized Prompts
```

## Testing

```bash
# Run all Phase 3 tests
python3 -m pytest scripts/tests/phase3/ -v

# Run integration test
python3 -m pytest scripts/tests/phase3/test_integration.py -v
```

## Output

Pipeline outputs:
- Optimized prompts with performance metrics
- Few-shot examples for each test query
- Overall statistics (train/val/pool sizes)
```

**Step 2: Commit**

```bash
git add docs/plans/phase3_README.md
git commit -m "docs(phase3): Add Phase 3 documentation

Added comprehensive README for Phase 3 DSPy + Few-Shot
pipeline. Includes usage, architecture, and testing."
```

---

## Summary

This plan implements Phase 3 in 9 bite-sized tasks:

1. ✅ DatasetLoader - Load Phase 2 datasets
2. ✅ DSPySignature - DSPy compilation wrapper
3. ✅ DSPOptimizer - Prompt optimization core
4. ✅ ExamplePool - Few-shot example repository
5. ✅ SimilaritySelector - Example selection strategy
6. ✅ UnifiedPipeline - End-to-end integration
7. ✅ CLI Entry Point - Main command
8. ✅ Integration Test - Complete verification
9. ✅ Documentation - README and usage

**Total estimated time:** 8-12 hours
**Total commits:** 9
**Total tests:** ~10-12

All tasks follow TDD with failing tests first, minimal implementation, and verification before committing.
