"""
Test KNNProvider error context improvements.

Tests that KeyError includes expected vs available keys.
"""

import pytest
from hemdov.domain.services.knn_provider import KNNProvider


def test_missing_key_error_includes_context(caplog):
    """Test that KeyError includes expected vs available keys in log."""
    # Add one invalid example + enough valid examples to keep skip rate below 20%
    examples_data = [
        {
            "inputs": {
                "original_idea": "Test idea",
                "context": ""
            },
            # Missing: outputs (entire section)
            "metadata": {}
        },
        # Add 5 valid examples to keep skip rate at 16.7% (1/6)
        *[
            {
                "inputs": {
                    "original_idea": f"Valid idea {i}",
                    "context": ""
                },
                "outputs": {
                    "improved_prompt": f"Improved {i}",
                    "role": "Developer",
                    "directive": "Write code"
                },
                "metadata": {}
            }
            for i in range(5)
        ]
    ]

    with caplog.at_level("ERROR"):
        # This should log the missing key with context
        provider = KNNProvider(catalog_data=examples_data)

    # Verify error log includes expected keys
    error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_logs) >= 1

    log_message = error_logs[0].message
    assert "Expected keys:" in log_message
    assert "Available keys:" in log_message

    # Verify we loaded the 5 valid examples
    assert len(provider.catalog) == 5


def test_valid_example_data_processes_successfully():
    """Test that valid example data processes without errors."""
    examples_data = [
        {
            "inputs": {
                "original_idea": "Test idea",
                "context": ""
            },
            "outputs": {
                "improved_prompt": "Improved prompt",
                "role": "Developer",
                "directive": "Write code"
            },
            "metadata": {}
        }
    ]

    provider = KNNProvider(catalog_data=examples_data)
    assert len(provider.catalog) == 1
    assert provider.catalog[0].input_idea == "Test idea"
