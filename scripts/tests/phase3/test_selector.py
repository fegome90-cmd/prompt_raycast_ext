"""Tests for similarity selector."""
from pathlib import Path


def test_similarity_selector_top_k():
    """Should return top-k most similar examples"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from scripts.data.fewshot.example_pool import ExamplePool
    from scripts.data.fewshot.selector import SimilaritySelector

    pool = ExamplePool()
    pool.build([
        {"question": "python coding", "metadata": {"domain": "SOFTDEV", "confidence": 0.9}},
        {"question": "machine learning", "metadata": {"domain": "AIML", "confidence": 0.8}},
        {"question": "data structures", "metadata": {"domain": "SOFTDEV", "confidence": 0.7}}
    ])

    selector = SimilaritySelector()
    results = selector.select("python code", pool, k=2)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    # Most similar should be "python coding" due to keyword overlap
    assert results[0]["question"] == "python coding", "Most similar should be 'python coding'"
