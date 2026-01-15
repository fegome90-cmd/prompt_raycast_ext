"""
Test OPROOptimizer separates transient failures from code bugs.

After fix: ConnectionError/TimeoutError/KNNProviderError degrade gracefully.
KeyError/TypeError/ValueError/RuntimeError propagate as code bugs.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.dto.nlac_models import PromptObject
from hemdov.domain.services.knn_provider import KNNProviderError


@pytest.mark.asyncio
async def test_transient_connection_error_tracked_and_degraded():
    """Test that transient ConnectionError is tracked with metadata."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("Network timeout")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="generate",
        template="Write a function",
        strategy_meta={"intent": "generate", "complexity": "simple"},
        constraints={"max_tokens": 500},
        created_at=now,
        updated_at=now,
    )

    # Should not raise - should track and degrade
    result = optimizer.run_loop(prompt_obj)

    # Verify failure was tracked (at least one, since it runs multiple iterations)
    assert len(optimizer._knn_failures) >= 1
    failure = optimizer._knn_failures[0]
    assert failure["error_type"] == "ConnectionError"
    assert failure["is_transient"] is True


@pytest.mark.asyncio
async def test_knn_provider_error_degrades_gracefully():
    """Test that KNNProviderError degrades gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KNNProviderError("KNN service down")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="debug",
        template="Debug this",
        strategy_meta={"intent": "debug", "complexity": "simple"},
        constraints={"max_tokens": 500},
        created_at=now,
        updated_at=now,
    )

    result = optimizer.run_loop(prompt_obj)
    assert len(optimizer._knn_failures) >= 1


@pytest.mark.asyncio
async def test_code_bug_keyerror_propagates_with_tracking():
    """Test that KeyError (code bug) propagates after tracking."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyError("schema_drift")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="debug",
        template="Debug this",
        strategy_meta={"intent": "debug", "complexity": "simple"},
        constraints={"max_tokens": 500},
        created_at=now,
        updated_at=now,
    )

    # Should raise after tracking
    with pytest.raises(KeyError):
        optimizer.run_loop(prompt_obj)

    # Verify bug was tracked
    assert len(optimizer._knn_failures) >= 1
    assert optimizer._knn_failures[0]["is_bug"] is True


@pytest.mark.asyncio
async def test_code_bug_typeerror_propagates_with_tracking():
    """Test that TypeError (code bug) propagates after tracking."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = TypeError("Wrong type")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="refactor",
        template="Refactor this",
        strategy_meta={"intent": "refactor", "complexity": "moderate"},
        constraints={"max_tokens": 1000},
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(TypeError):
        optimizer.run_loop(prompt_obj)

    assert len(optimizer._knn_failures) >= 1
    assert optimizer._knn_failures[0]["is_bug"] is True


@pytest.mark.asyncio
async def test_code_bug_runtime_error_propagates_with_tracking():
    """Test that RuntimeError (code bug) propagates after tracking."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = RuntimeError("Code bug")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="explain",
        template="Explain this",
        strategy_meta={"intent": "explain", "complexity": "complex"},
        constraints={"max_tokens": 1500},
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(RuntimeError):
        optimizer.run_loop(prompt_obj)

    assert len(optimizer._knn_failures) >= 1
    assert optimizer._knn_failures[0]["is_bug"] is True


@pytest.mark.asyncio
async def test_code_bug_value_error_propagates_with_tracking():
    """Test that ValueError (code bug) propagates after tracking."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ValueError("Invalid value")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    now = datetime.now(UTC).isoformat()
    prompt_obj = PromptObject(
        id="test-id",
        version="1.0.0",
        intent_type="generate",
        template="Generate code",
        strategy_meta={"intent": "generate", "complexity": "simple"},
        constraints={"max_tokens": 500},
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(ValueError):
        optimizer.run_loop(prompt_obj)

    assert len(optimizer._knn_failures) >= 1
    assert optimizer._knn_failures[0]["is_bug"] is True
