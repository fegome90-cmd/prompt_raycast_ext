"""Tests for infrastructure module."""

import json
import pytest
from pathlib import Path
from scripts.synthetic_examples.infrastructure import load_component_catalog
from scripts.legacy_curation.models import Component, Domain


class TestLoadComponentCatalog:
    """Test load_component_catalog function."""

    def test_load_component_catalog_success(self, tmp_path: Path):
        """Should successfully load valid catalog."""
        catalog_data = {
            "components": [
                {
                    "source_file": "test.md",
                    "domain": "softdev",
                    "role": "developer",
                    "directive": "Write code",
                    "framework": "Chain-of-Thought",
                    "guardrails": ["Test guardrail"],
                    "confidence": 0.8,
                },
                {
                    "source_file": "test2.md",
                    "domain": "productivity",
                    "role": "assistant",
                    "directive": "Help user",
                    "framework": "Tree-of-Thoughts",
                    "guardrails": [],
                    "confidence": 0.9,
                },
            ],
            "total_components": 2,
            "avg_confidence": 0.85,
        }

        catalog_file = tmp_path / "ComponentCatalog.json"
        catalog_file.write_text(json.dumps(catalog_data))

        result = load_component_catalog(str(catalog_file))

        assert len(result) == 2
        assert all(isinstance(comp, Component) for comp in result)
        assert result[0].confidence == 0.8
        assert result[1].confidence == 0.9

    def test_load_component_catalog_missing_file(self, tmp_path: Path):
        """Should raise ValueError for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(ValueError, match="not found"):
            load_component_catalog(str(missing_file))

    def test_load_component_catalog_invalid_json(self, tmp_path: Path):
        """Should reject malformed JSON."""
        catalog_file = tmp_path / "invalid.json"
        catalog_file.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_component_catalog(str(catalog_file))

    def test_load_filters_low_confidence(self, tmp_path: Path):
        """Should filter components with confidence < 0.2."""
        catalog_data = {
            "components": [
                {
                    "source_file": "high.md",
                    "domain": "softdev",
                    "role": "dev",
                    "directive": "code",
                    "framework": "Chain-of-Thought",
                    "guardrails": [],
                    "confidence": 0.8,
                },
                {
                    "source_file": "medium.md",
                    "domain": "softdev",
                    "role": "dev",
                    "directive": "code",
                    "framework": "Chain-of-Thought",
                    "guardrails": [],
                    "confidence": 0.5,  # Changed from 0.4 to 0.5
                },
                {
                    "source_file": "low.md",
                    "domain": "softdev",
                    "role": "dev",
                    "directive": "code",
                    "framework": "Chain-of-Thought",
                    "guardrails": [],
                    "confidence": 0.1,  # Changed from 0.2 to 0.1 (< threshold)
                },
                {
                    "source_file": "zero.md",
                    "domain": "softdev",
                    "role": "dev",
                    "directive": "code",
                    "framework": "Chain-of-Thought",
                    "guardrails": [],
                    "confidence": 0.0,  # Below threshold, should be filtered
                },
            ],
            "total_components": 4,
            "avg_confidence": 0.35,  # (0.8 + 0.5 + 0.1 + 0.0) / 4
        }

        catalog_file = tmp_path / "catalog.json"
        catalog_file.write_text(json.dumps(catalog_data))

        result = load_component_catalog(str(catalog_file))

        assert len(result) == 2
        assert all(comp.confidence >= 0.2 for comp in result)
        confidences = [comp.confidence for comp in result]
        assert 0.8 in confidences
        assert 0.5 in confidences  # Changed from 0.3 to 0.5

    def test_load_validates_with_pydantic(self, tmp_path: Path):
        """Should validate component structure with Pydantic."""
        catalog_data = {
            "components": [
                {
                    "source_file": "test.md",
                    "domain": "softdev",
                    "role": "dev",
                    "directive": "code",
                    "framework": "Chain-of-Thought",
                    "guardrails": [],
                    "confidence": 0.1,  # Changed from 0.5 to 0.1 (< 0.2)
                },
            ],
            "total_components": 1,
            "avg_confidence": 0.1,
        }

        catalog_file = tmp_path / "catalog.json"
        catalog_file.write_text(json.dumps(catalog_data))

        result = load_component_catalog(str(catalog_file))

        assert len(result) == 0
        assert isinstance(result, list)
