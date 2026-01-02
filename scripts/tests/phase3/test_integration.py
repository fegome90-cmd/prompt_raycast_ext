"""End-to-end integration test for Phase 3 pipeline."""
from pathlib import Path


def test_phase3_integration_e2e():
    """Should run complete Phase 3 pipeline"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    result = pipeline.run()

    # Verify pipeline components
    assert 'optimized_prompts' in result, "Result should contain 'optimized_prompts'"
    assert 'few_shot_examples' in result, "Result should contain 'few_shot_examples'"
    assert 'metrics' in result, "Result should contain 'metrics'"

    # Verify metrics match Phase 2 dataset sizes
    metrics = result['metrics']
    assert metrics['train_size'] == 11, f"Expected 11 train examples, got {metrics['train_size']}"
    assert metrics['val_size'] == 2, f"Expected 2 val examples, got {metrics['val_size']}"
    assert metrics['test_size'] == 3, f"Expected 3 test examples, got {metrics['test_size']}"
    assert metrics['pool_size'] == 11, f"Expected pool size 11, got {metrics['pool_size']}"

    # Verify few-shot results
    few_shot = result['few_shot_examples']
    assert len(few_shot) == 3, f"Expected 3 few-shot results, got {len(few_shot)}"

    # Verify each test example has selected examples
    for item in few_shot:
        assert 'query' in item, "Each result should have 'query'"
        assert 'selected_examples' in item, "Each result should have 'selected_examples'"
        assert len(item['selected_examples']) == 3, f"Expected k=3 examples, got {len(item['selected_examples'])}"

    # Verify optimized prompts structure
    optimized = result['optimized_prompts']
    assert 'prompt' in optimized, "Optimized result should have 'prompt'"
    assert 'best_loss' in optimized, "Optimized result should have 'best_loss'"
    assert 'metrics' in optimized, "Optimized result should have 'metrics'"
