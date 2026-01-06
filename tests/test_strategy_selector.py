# tests/test_strategy_selector.py
from eval.src.strategy_selector import StrategySelector
from eval.src.strategies.simple_strategy import SimpleStrategy
from eval.src.strategies.moderate_strategy import ModerateStrategy
from eval.src.strategies.complex_strategy import ComplexStrategy
from eval.src.complexity_analyzer import ComplexityLevel


def test_selector_returns_simple_for_short_input():
    """Test StrategySelector returns SimpleStrategy for short inputs."""
    selector = StrategySelector()
    strategy = selector.select("hola", "")
    assert isinstance(strategy, SimpleStrategy)


def test_selector_returns_moderate_for_medium_input():
    """Test StrategySelector returns ModerateStrategy for medium inputs."""
    selector = StrategySelector()
    strategy = selector.select("crea un prompt para evaluar calidad de software con métricas", "")
    assert isinstance(strategy, ModerateStrategy)


def test_selector_returns_complex_for_long_input():
    """Test StrategySelector returns ComplexStrategy for long inputs."""
    selector = StrategySelector()
    long_input = "diseña una arquitectura de microservicios completa para una plataforma de e-commerce escalable " * 10
    strategy = selector.select(long_input, "con alta disponibilidad y tolerancia a fallos")
    # Will be ModerateStrategy if ComplexStrategy unavailable (no trainset)
    assert isinstance(strategy, (ComplexStrategy, ModerateStrategy))


def test_selector_validates_inputs():
    """Test StrategySelector validates input parameters."""
    selector = StrategySelector()

    # Test None inputs
    try:
        selector.select(None, "")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be non-None strings" in str(e)

    # Test non-string inputs
    try:
        selector.select(123, "")
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "must be strings" in str(e)


def test_selector_get_complexity():
    """Test StrategySelector.get_complexity returns correct level."""
    selector = StrategySelector()

    # Simple
    complexity = selector.get_complexity("hola", "")
    assert complexity == ComplexityLevel.SIMPLE

    # Moderate (exceeds 50 chars, has technical terms)
    moderate_input = "crea un prompt para evaluar la calidad de software con métricas"
    complexity = selector.get_complexity(moderate_input, "")
    assert complexity == ComplexityLevel.MODERATE

    # Complex (very long >300 chars auto-triggers COMPLEX)
    long_input = "a" * 400
    complexity = selector.get_complexity(long_input, "")
    assert complexity == ComplexityLevel.COMPLEX
