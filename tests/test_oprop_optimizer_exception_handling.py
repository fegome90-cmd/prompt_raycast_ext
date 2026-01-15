"""Test OPROOptimizer handles specific exceptions correctly."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from hemdov.domain.dto.nlac_models import PromptObject
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


@pytest.mark.asyncio
async def test_optimizer_handles_runtime_error_from_knn():
    """Optimizer should handle RuntimeError from KNNProvider gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = RuntimeError("Catalog unavailable")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    # Create a simple PromptObject for testing
    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="debug",
        template="Test prompt",
        strategy_meta={"intent": "debug", "complexity": "simple"},
        constraints={"max_tokens": 500},
        created_at=now,
        updated_at=now,
    )

    # Should handle gracefully - KNN error is caught during build_meta_prompt
    result = optimizer.run_loop(prompt_obj)
    # Should complete, just without few-shot examples in meta-prompt
    assert result is not None
    assert result.final_instruction == "Test prompt"


@pytest.mark.asyncio
async def test_optimizer_handles_keyerror_from_knn():
    """Optimizer should handle KeyError from KNNProvider gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyError("missing_key")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    # Create a simple PromptObject for testing
    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="refactor",
        template="Refactor this code",
        strategy_meta={"intent": "refactor", "complexity": "moderate"},
        constraints={"max_tokens": 1000},
        created_at=now,
        updated_at=now,
    )

    # Should handle gracefully
    result = optimizer.run_loop(prompt_obj)
    assert result is not None
