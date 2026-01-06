# tests/test_complexity_analyzer.py
from eval.src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel


def test_complexity_level_enum():
    assert ComplexityLevel.SIMPLE.value == "simple"
    assert ComplexityLevel.MODERATE.value == "moderate"
    assert ComplexityLevel.COMPLEX.value == "complex"


def test_analyzer_simple_by_length():
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze("hola mundo", "")
    assert result == ComplexityLevel.SIMPLE


def test_analyzer_complex_by_length():
    analyzer = ComplexityAnalyzer()
    long_input = "diseña " * 100  # > 150 chars
    result = analyzer.analyze(long_input, "")
    assert result == ComplexityLevel.COMPLEX


def test_analyzer_detects_technical_terms():
    analyzer = ComplexityAnalyzer()
    # Short input but with technical terms should be MODERATE
    result = analyzer.analyze("crea un framework de diseño", "")
    assert result == ComplexityLevel.MODERATE
