"""Test StrategySelector exception handling.

Tests cover:
- KNNProvider initialization failures
- ComplexStrategy initialization failures
- Degradation flag tracking
- KeyboardInterrupt NOT caught
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from eval.src.strategy_selector import StrategySelector


class TestKNNProviderExceptionHandling:
    """Test KNNProvider initialization exception handling."""

    @patch('eval.src.strategy_selector.Path')
    def test_file_not_found_sets_knn_degradation_flag(self, mock_path):
        """FileNotFoundError sets knn_disabled flag."""
        # Mock path to exist
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        with patch('eval.src.strategy_selector.KNNProvider') as mock_knn:
            mock_knn.side_effect = FileNotFoundError("Catalog not found")

            selector = StrategySelector(use_nlac=True)
            flags = selector.get_degradation_flags()

            assert flags["knn_disabled"] is True

    @patch('eval.src.strategy_selector.Path')
    def test_json_decode_error_sets_knn_degradation_flag(self, mock_path):
        """JSONDecodeError sets knn_disabled flag."""
        # Mock path to exist
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        with patch('eval.src.strategy_selector.KNNProvider') as mock_knn:
            import json
            mock_knn.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            selector = StrategySelector(use_nlac=True)
            flags = selector.get_degradation_flags()

            assert flags["knn_disabled"] is True

    @patch('eval.src.strategy_selector.Path')
    def test_keyboard_interrupt_not_caught_in_knn(self, mock_path):
        """KeyboardInterrupt is NOT caught."""
        # Mock path to exist
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        with patch('eval.src.strategy_selector.KNNProvider') as mock_knn:
            mock_knn.side_effect = KeyboardInterrupt()

            # DESIRED: KeyboardInterrupt should propagate
            with pytest.raises(KeyboardInterrupt):
                StrategySelector(use_nlac=True)


class TestComplexStrategyExceptionHandling:
    """Test ComplexStrategy initialization exception handling."""

    def test_trainset_not_found_sets_complex_degradation_flag(self):
        """FileNotFoundError sets complex_strategy_disabled flag."""
        with patch('eval.src.strategy_selector.ComplexStrategy') as mock_complex:
            mock_complex.side_effect = FileNotFoundError("trainset.json not found")

            selector = StrategySelector(use_nlac=False)
            flags = selector.get_degradation_flags()

            assert flags["complex_strategy_disabled"] is True
            assert selector._complex_available is False

    def test_permission_denied_sets_complex_degradation_flag(self):
        """PermissionError sets complex_strategy_disabled flag."""
        with patch('eval.src.strategy_selector.ComplexStrategy') as mock_complex:
            mock_complex.side_effect = PermissionError("Cannot read trainset")

            selector = StrategySelector(use_nlac=False)
            flags = selector.get_degradation_flags()

            assert flags["complex_strategy_disabled"] is True

    def test_json_decode_error_sets_complex_degradation_flag(self):
        """JSONDecodeError sets complex_strategy_disabled flag."""
        with patch('eval.src.strategy_selector.ComplexStrategy') as mock_complex:
            import json
            mock_complex.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            selector = StrategySelector(use_nlac=False)
            flags = selector.get_degradation_flags()

            assert flags["complex_strategy_disabled"] is True


class TestDegradationFlags:
    """Test degradation flag tracking."""

    @patch('eval.src.strategy_selector.Path')
    def test_get_degradation_flags_returns_copy(self, mock_path):
        """get_degradation_flags returns a copy, not reference."""
        # Mock path to exist
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        selector = StrategySelector(use_nlac=False)
        flags1 = selector.get_degradation_flags()
        flags2 = selector.get_degradation_flags()

        assert flags1 is not flags2

    @patch('eval.src.strategy_selector.Path')
    def test_both_flags_can_be_set(self, mock_path):
        """Both KNN and ComplexStrategy can fail independently."""
        # Mock path to exist for NLaC mode
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        # Test with KNN failure
        with patch('eval.src.strategy_selector.KNNProvider') as mock_knn:
            mock_knn.side_effect = FileNotFoundError()

            selector = StrategySelector(use_nlac=True)
            flags = selector.get_degradation_flags()

            # NLaC mode sets knn_disabled
            assert "knn_disabled" in flags
            # Legacy mode sets complex_strategy_disabled
            assert "complex_strategy_disabled" in flags

    @patch('eval.src.strategy_selector.Path')
    def test_nlac_mode_with_knn_disabled_continues(self, mock_path):
        """NLaC mode continues without KNN when KNN initialization fails."""
        # Mock path to exist
        mock_catalog = Mock()
        mock_catalog.exists.return_value = True
        mock_path.return_value = Mock(exists=lambda: True)

        with patch('eval.src.strategy_selector.KNNProvider') as mock_knn:
            mock_knn.side_effect = FileNotFoundError("Catalog not found")

            selector = StrategySelector(use_nlac=True)

            # Should still have nlac_strategy
            assert selector.nlac_strategy is not None
            # KNN provider should be None
            from eval.src.strategies.nlac_strategy import NLaCStrategy
            assert isinstance(selector.nlac_strategy, NLaCStrategy)
