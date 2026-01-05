"""Test that UnifiedPipeline imports work correctly."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_unified_pipeline_imports():
    """Test UnifiedPipeline can be imported and instantiated."""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    assert pipeline is not None
    assert hasattr(pipeline, "dspy_optimizer")
    assert hasattr(pipeline, "example_pool")
    assert hasattr(pipeline, "selector")
    assert hasattr(pipeline, "dataset_loader")


def test_unified_pipeline_has_required_methods():
    """Test UnifiedPipeline has run method."""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    assert hasattr(pipeline, "run")
    assert callable(pipeline.run)
