# tests/test_complexity_analyzer.py
from eval.src.complexity_analyzer import ComplexityLevel


def test_complexity_level_enum():
    assert ComplexityLevel.SIMPLE.value == "simple"
    assert ComplexityLevel.MODERATE.value == "moderate"
    assert ComplexityLevel.COMPLEX.value == "complex"
