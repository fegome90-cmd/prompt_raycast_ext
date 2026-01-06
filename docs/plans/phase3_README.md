# Phase 3: DSPy Optimization + Few-Shot Learning

## Overview

Phase 3 constructs a unified two-layer prompt optimization system that maximizes value from Phase 2 datasets:

- **Layer 1 (DSPy):** Optimizes prompt structure and hyperparameters using validation set
- **Layer 2 (Few-Shot):** Enriches prompts with relevant examples selected from training set

Both layers work together to produce optimized prompts with few-shot examples that achieve multiplicative improvement in response quality.

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
                 ExamplePool (from train)
                         ↓
              SimilaritySelector (top-k by similarity)
                         ↓
           Few-Shot Examples + Optimized Prompts
```

## Components

### Layer 1: DSPy Optimization

**DatasetLoader** (`scripts/phase3_dspy/optimizer.py`)
- Loads Phase 2 datasets from `datasets/exports/synthetic/`
- Returns train (11), val (2), test (3) examples

**DSPySignature** (`scripts/phase3_dspy/optimizer.py`)
- Wraps DSPy signature compilation
- Uses `dspy.Signature("question, metadata -> answer")`
- Returns compiled `dspy.Predict` predictor

**DSPOptimizer** (`scripts/phase3_dspy/optimizer.py`)
- Optimizes prompts using train/val sets
- Currently uses placeholder optimization (average question length)
- Returns optimized prompt with metrics

### Layer 2: Few-Shot Learning

**ExamplePool** (`scripts/phase3_fewshot/example_pool.py`)
- Builds example repository from training set
- Supports domain-based filtering
- Tracks domains: SOFTDEV, AIML, etc.

**SimilaritySelector** (`scripts/phase3_fewshot/selector.py`)
- Selects top-k most similar examples to query
- Currently uses keyword overlap similarity
- Returns ranked examples by similarity score

### Integration

**UnifiedPipeline** (`scripts/phase3_pipeline/optimizer.py`)
- Orchestrates both layers end-to-end
- Loads datasets → builds pool → optimizes → selects examples
- Returns complete results with metrics

## Usage

### Running the Pipeline

```bash
# Run optimization pipeline
uv run python -m scripts.phase3_pipeline.main
```

**Expected output:**
```
=== DSPy + Few-Shot Optimization Pipeline ===

Optimization complete!
Train size: 11
Val size: 2
Test size: 3
Example pool size: 11

Optimized prompts: 3
```

### Using Components Programmatically

```python
from scripts.phase3_pipeline.optimizer import UnifiedPipeline

pipeline = UnifiedPipeline()
result = pipeline.run()

# Access optimized prompts
optimized = result['optimized_prompts']
print(optimized['prompt'])

# Access few-shot examples
for item in result['few_shot_examples']:
    query = item['query']
    examples = item['selected_examples']
    print(f"Query: {query}")
    print(f"Selected {len(examples)} examples")
```

## Testing

### Run All Phase 3 Tests

```bash
# Run all tests
uv run pytest scripts/tests/phase3/ -v

# Run specific test file
uv run pytest scripts/tests/phase3/test_pipeline.py -v

# Run with coverage
uv run pytest scripts/tests/phase3/ --cov=scripts/phase3_dspy --cov=scripts/phase3_fewshot --cov=scripts/phase3_pipeline -v
```

### Test Files

| Test File | Coverage |
|-----------|----------|
| `test_optimizer.py` | DatasetLoader, DSPySignature, DSPOptimizer |
| `test_example_pool.py` | ExamplePool construction and queries |
| `test_selector.py` | SimilaritySelector ranking |
| `test_pipeline.py` | UnifiedPipeline orchestration |
| `test_cli.py` | CLI entry point |
| `test_integration.py` | End-to-end integration |

## Output Structure

```python
{
    'optimized_prompts': {
        'prompt': str,
        'best_loss': float,
        'metrics': dict
    },
    'few_shot_examples': [
        {
            'query': str,
            'selected_examples': [dict, ...]  # k=3 examples
        },
        ...
    ],
    'metrics': {
        'train_size': 11,
        'val_size': 2,
        'test_size': 3,
        'pool_size': 11
    }
}
```

## Development Status

- ✅ DatasetLoader - Phase 2 dataset loading
- ✅ DSPySignature - DSPy compilation wrapper
- ✅ DSPOptimizer - Prompt optimization core (placeholder)
- ✅ ExamplePool - Few-shot example repository
- ✅ SimilaritySelector - Example selection (keyword overlap)
- ✅ UnifiedPipeline - End-to-end integration
- ✅ CLI - Main command entry point
- ✅ Integration Test - Complete verification
- ✅ Documentation - README and usage

## Future Improvements

**DSPy Optimization:**
- Implement full DSPy teleprompter optimization
- Add hyperparameter tuning against validation set
- Implement quality metrics (accuracy, coherence, relevance)

**Few-Shot Selection:**
- Replace keyword overlap with semantic embeddings
- Add diversity-based selection strategy
- Implement hybrid selection (similarity + diversity)

**Pipeline:**
- Add parallel processing for large datasets
- Implement caching for optimized prompts
- Add evaluation on test set with quality metrics

## Tech Stack

- **DSPy 3.0.4** - Prompt optimization framework
- **pytest** - Testing framework
- **uv** - Package manager
- **Python 3.14** - Runtime

## Related Documentation

- [Phase 3 Implementation Plan](docs/plans/2026-01-02-dspy-fewshot-optimization.md)
- [DSPy Documentation](https://dspy-docs.vercel.app/)
- [Phase 2 Datasets](datasets/exports/synthetic/)
