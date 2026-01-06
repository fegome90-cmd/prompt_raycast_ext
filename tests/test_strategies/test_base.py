# tests/test_strategies/test_base.py
from eval.src.strategies.base import PromptImproverStrategy


def test_base_strategy_is_abstract():
    """Verify base strategy cannot be instantiated."""
    try:
        strategy = PromptImproverStrategy()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        assert True
