# tests/test_feature_flags.py
"""Tests for hemdov/infrastructure/config/feature_flags.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from hemdov.infrastructure.config.feature_flags import FeatureFlags, _parse_bool


class TestParseBool:
    """Tests for _parse_bool helper."""

    def test_true_values(self):
        """Should return True for truthy strings."""
        assert _parse_bool("true") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("YES") is True
        assert _parse_bool("on") is True
        assert _parse_bool("ON") is True

    def test_false_values(self):
        """Should return False for falsy strings."""
        assert _parse_bool("false") is False
        assert _parse_bool("0") is False
        assert _parse_bool("no") is False
        assert _parse_bool("off") is False

    def test_none_returns_false(self):
        """Should return False for None."""
        assert _parse_bool(None) is False

    def test_empty_string_returns_false(self):
        """Should return False for empty string."""
        assert _parse_bool("") is False

    def test_other_string_returns_false(self):
        """Should return False for unrecognized strings."""
        assert _parse_bool("maybe") is False

    def test_non_string_returns_false(self):
        """Should return False for non-string types."""
        assert _parse_bool(123) is False
        assert _parse_bool(True) is False
        assert _parse_bool([]) is False


class TestFeatureFlagsDefaults:
    """Tests for FeatureFlags default values."""

    def test_default_values(self):
        """Should have correct default values."""
        with patch.dict("os.environ", {}, clear=True):
            flags = FeatureFlags()

            # Defaults from env vars (cleared above)
            assert flags.enable_dspy_embeddings is False
            assert flags.enable_cache is True  # Default is "true"
            assert flags.enable_ifeval is True  # Default is "true"
            assert flags.enable_metrics is True  # Default is "true"
            assert flags.enable_enhanced_rar is False
            assert flags.embedding_provider == "ollama"


class TestFeatureFlagsSave:
    """Tests for FeatureFlags.save()."""

    def test_save_creates_file(self, tmp_path: Path):
        """Should create file with correct JSON structure."""
        # Note: save() creates a new instance with defaults (class method)
        # It saves the default values, not custom instance values
        save_path = tmp_path / "flags.json"

        FeatureFlags.save(save_path)

        assert save_path.exists()
        data = json.loads(save_path.read_text())
        # Check that expected fields exist
        assert "enable_dspy_embeddings" in data
        assert "enable_metrics" in data

    def test_save_includes_all_fields(self, tmp_path: Path):
        """Should include all flag fields in saved JSON."""
        save_path = tmp_path / "flags.json"

        FeatureFlags.save(save_path)

        data = json.loads(save_path.read_text())
        assert "enable_dspy_embeddings" in data
        assert "enable_cache" in data
        assert "enable_ifeval" in data
        assert "enable_metrics" in data
        assert "enable_enhanced_rar" in data
        assert "embedding_provider" in data

    def test_save_creates_single_parent_directory(self, tmp_path: Path):
        """Should create single-level parent directory if it doesn't exist."""
        save_path = tmp_path / "subdir" / "flags.json"

        FeatureFlags.save(save_path)

        assert save_path.exists()


class TestFeatureFlagsLoad:
    """Tests for FeatureFlags.load()."""

    def test_load_missing_file_returns_defaults(self, tmp_path: Path):
        """Should return defaults for non-existent file."""
        load_path = tmp_path / "nonexistent.json"

        flags = FeatureFlags.load(load_path)

        assert flags.enable_dspy_embeddings is False
        assert flags.enable_cache is True

    def test_load_valid_file(self, tmp_path: Path):
        """Should load values from valid JSON file."""
        load_path = tmp_path / "flags.json"
        load_path.write_text(json.dumps({
            "enable_dspy_embeddings": True,
            "enable_cache": False,
            "enable_ifeval": False,
            "enable_metrics": False,
            "enable_enhanced_rar": True,
            "embedding_provider": "openai",
        }))

        flags = FeatureFlags.load(load_path)

        assert flags.enable_dspy_embeddings is True
        assert flags.enable_cache is False
        assert flags.enable_ifeval is False
        assert flags.enable_metrics is False
        assert flags.enable_enhanced_rar is True
        assert flags.embedding_provider == "openai"

    def test_load_invalid_json_raises(self, tmp_path: Path):
        """Should raise on invalid JSON."""
        load_path = tmp_path / "invalid.json"
        load_path.write_text("{ not valid json }")

        with pytest.raises(json.JSONDecodeError):
            FeatureFlags.load(load_path)

    def test_load_partial_file_uses_defaults(self, tmp_path: Path):
        """Should use defaults for missing fields."""
        load_path = tmp_path / "partial.json"
        load_path.write_text(json.dumps({"enable_dspy_embeddings": True}))

        flags = FeatureFlags.load(load_path)

        assert flags.enable_dspy_embeddings is True
        # Other fields should have their defaults
        assert flags.enable_cache is True
        assert flags.embedding_provider == "ollama"


class TestFeatureFlagsStr:
    """Tests for FeatureFlags.__str__()."""

    def test_str_includes_all_flags(self):
        """Should include all flags in string representation."""
        flags = FeatureFlags()
        result = str(flags)

        assert "enable_dspy_embeddings:" in result
        assert "enable_cache:" in result
        assert "enable_ifeval:" in result
        assert "enable_metrics:" in result
        assert "enable_enhanced_rar:" in result
        assert "embedding_provider:" in result
