"""Unified DSPy + Few-Shot optimization pipeline."""
from typing import Dict
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
