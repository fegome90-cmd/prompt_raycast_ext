"""Main CLI entry point for Phase 3 pipeline."""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
