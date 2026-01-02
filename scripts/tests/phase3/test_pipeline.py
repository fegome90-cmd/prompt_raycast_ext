"""Tests for unified pipeline."""
from pathlib import Path


def test_unified_pipeline_end_to_end():
    """Should run complete optimization pipeline"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    result = pipeline.run()

    assert 'optimized_prompts' in result, "Result should contain 'optimized_prompts'"
    assert 'few_shot_examples' in result, "Result should contain 'few_shot_examples'"
    assert 'metrics' in result, "Result should contain 'metrics'"

    # Verify metrics
    metrics = result['metrics']
    assert 'train_size' in metrics, "Metrics should contain 'train_size'"
    assert 'val_size' in metrics, "Metrics should contain 'val_size'"
    assert 'test_size' in metrics, "Metrics should contain 'test_size'"
    assert 'pool_size' in metrics, "Metrics should contain 'pool_size'"
