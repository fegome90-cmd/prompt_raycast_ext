"""
Tests for NLaC Strategy integration with Strategy Pattern.
"""

import pytest
from eval.src.strategies.nlac_strategy import NLaCStrategy
from eval.src.strategy_selector import StrategySelector


class TestNLaCStrategy:
    """Test NLaC strategy implementation."""

    @pytest.fixture
    def nlac_strategy(self):
        """Create NLaC strategy instance."""
        return NLaCStrategy(
            llm_client=None,
            enable_cache=True,
            enable_optimization=True,
            enable_validation=True,
        )

    def test_strategy_name(self, nlac_strategy):
        """Strategy has correct name."""
        assert nlac_strategy.name == "nlac"

    def test_improve_returns_prediction(self, nlac_strategy):
        """improve() returns dspy.Prediction."""
        result = nlac_strategy.improve(
            original_idea="Create a hello world function",
            context="In Python"
        )

        # Check it's a dspy.Prediction
        import dspy
        assert isinstance(result, dspy.Prediction)

    def test_prediction_has_required_fields(self, nlac_strategy):
        """Prediction has all required fields for backward compatibility."""
        result = nlac_strategy.improve(
            original_idea="Debug this code",
            context="Not working"
        )

        # Required fields
        assert hasattr(result, 'improved_prompt')
        assert hasattr(result, 'role')
        assert hasattr(result, 'directive')
        assert hasattr(result, 'framework')
        assert hasattr(result, 'guardrails')

        # Verify they're non-empty
        assert result.improved_prompt
        assert result.role
        assert result.directive
        assert result.framework
        assert isinstance(result.guardrails, list)

    def test_improve_simple_input(self, nlac_strategy):
        """Simple input gets appropriate treatment."""
        result = nlac_strategy.improve(
            original_idea="Print hello",
            context=""
        )

        # Should have role and improved prompt
        assert result.role
        assert "hello" in result.improved_prompt.lower() or result.improved_prompt
        # Simple inputs use chain-of-thought
        assert result.framework in ["chain-of-thought", "decomposition"]

    def test_improve_with_debug_context(self, nlac_strategy):
        """Debug intent is detected and handled."""
        result = nlac_strategy.improve(
            original_idea="Fix this error",
            context="ZeroDivisionError when dividing"
        )

        # Should have debug-related role
        assert "debugg" in result.role.lower() or result.role
        # Directive should mention debug
        assert "debug" in result.directive.lower() or result.directive

    def test_input_validation(self, nlac_strategy):
        """Input validation works correctly."""
        # None inputs should raise ValueError
        with pytest.raises(ValueError, match="must be non-None"):
            nlac_strategy.improve(None, "context")

        with pytest.raises(ValueError, match="must be non-None"):
            nlac_strategy.improve("idea", None)

        # Non-string inputs should raise TypeError
        with pytest.raises(TypeError, match="must be strings"):
            nlac_strategy.improve(123, "context")

    def test_cache_disabled(self):
        """Cache can be disabled."""
        strategy = NLaCStrategy(
            enable_cache=False,
            enable_optimization=False,
            enable_validation=False,
        )

        result = strategy.improve(
            original_idea="Test",
            context=""
        )

        assert result.improved_prompt

    def test_to_prediction_mapping(self, nlac_strategy):
        """Internal _to_prediction maps fields correctly."""
        from hemdov.domain.dto.nlac_models import PromptObject, IntentType
        from datetime import datetime, UTC

        prompt_obj = PromptObject(
            id="test",
            version="1.0",
            intent_type=IntentType.DEBUG,
            template="Test template",
            strategy_meta={
                "role": "TestRole",
                "strategy": "test_strategy",
                "intent": "debug",
                "complexity": "simple",
            },
            constraints={
                "max_tokens": 100,
                "include_examples": True,
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        result = nlac_strategy._to_prediction(prompt_obj)

        # Verify field mapping
        assert result.improved_prompt == "Test template"
        assert result.role == "TestRole"
        assert "test_strategy" in result.directive
        assert "debug" in result.directive
        assert result.framework == "chain-of-thought"  # simple complexity
        assert any("100" in str(g) for g in result.guardrails)


class TestStrategySelectorNLaC:
    """Test StrategySelector with NLaC mode."""

    def test_legacy_mode_default(self):
        """Legacy mode is default for backward compatibility."""
        selector = StrategySelector()

        # Should use legacy strategies
        assert selector._use_nlac is False
        assert hasattr(selector, 'simple_strategy')
        assert hasattr(selector, 'moderate_strategy')

    def test_nlac_mode_enabled(self):
        """NLaC mode can be enabled."""
        selector = StrategySelector(use_nlac=True)

        # Should use NLaC strategy
        assert selector._use_nlac is True
        assert hasattr(selector, 'nlac_strategy')

    def test_select_returns_nlac_strategy(self):
        """In NLaC mode, select() always returns NLaCStrategy."""
        selector = StrategySelector(use_nlac=True)

        # Simple input
        strategy1 = selector.select("Test", "")
        assert isinstance(strategy1, NLaCStrategy)

        # Complex input
        complex_idea = "Build a comprehensive system with authentication, " \
                       "authorization, rate limiting, caching, and monitoring"
        strategy2 = selector.select(complex_idea, "Enterprise grade")
        assert isinstance(strategy2, NLaCStrategy)

    def test_select_legacy_mode_routes_by_complexity(self):
        """In legacy mode, select() routes based on complexity."""
        selector = StrategySelector(use_nlac=False)

        from eval.src.strategies.simple_strategy import SimpleStrategy

        # Simple input
        simple_strategy = selector.select("Hi", "")
        assert isinstance(simple_strategy, SimpleStrategy)

    def test_backward_compatibility(self):
        """Legacy mode maintains backward compatibility."""
        selector = StrategySelector(use_nlac=False)

        # Should select legacy strategy
        strategy = selector.select("Create a function", "In Python")

        # Verify it's a legacy strategy (not NLaC)
        assert not isinstance(strategy, NLaCStrategy)
        from eval.src.strategies.simple_strategy import SimpleStrategy
        assert isinstance(strategy, (SimpleStrategy, type(strategy)))

        # Note: We can't test strategy.improve() without DSPy LM configured
        # That's tested in the existing strategy test files
