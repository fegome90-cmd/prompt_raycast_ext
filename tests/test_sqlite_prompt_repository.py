# tests/test_sqlite_prompt_repository.py
"""
Unit tests for SQLitePromptRepository.

Tests cover CRUD operations, validation, quality score calculation,
and repository lifecycle management.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from hemdov.infrastructure.config import Settings
from hemdov.domain.entities.prompt_history import PromptHistory


@pytest.fixture
def settings(temp_db_path: str) -> Settings:
    """Provide test Settings with temporary database path."""
    return Settings(
        SQLITE_DB_PATH=temp_db_path,
        SQLITE_WAL_MODE=True,
    )


@pytest_asyncio.fixture
async def repository(settings: Settings) -> SQLitePromptRepository:
    """Create repository instance with clean database."""
    repo = SQLitePromptRepository(settings)
    yield repo
    await repo.close()


@pytest.fixture
def sample_prompt() -> PromptHistory:
    """Provide sample PromptHistory for testing."""
    return PromptHistory(
        original_idea="Write a function to sort data",
        context="Python development",
        improved_prompt="Create a Python function that sorts a list using the Timsort algorithm",
        role="Python Developer",
        directive="Implement efficient sorting",
        framework="chain-of-thought",
        guardrails=["handle edge cases", "include type hints"],
        reasoning="Timsort provides O(n log n) complexity",
        confidence=0.85,
        backend="zero-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=1500,
        created_at=datetime.utcnow().isoformat(),
    )


@pytest.mark.asyncio
async def test_save_prompt_history(repository: SQLitePromptRepository, sample_prompt: PromptHistory):
    """Test saving a prompt history record."""
    # Act
    history_id = await repository.save(sample_prompt)

    # Assert
    assert history_id > 0
    assert isinstance(history_id, int)

    # Verify record was saved
    retrieved = await repository.find_by_id(history_id)
    assert retrieved is not None
    assert retrieved.original_idea == sample_prompt.original_idea
    assert retrieved.improved_prompt == sample_prompt.improved_prompt
    assert retrieved.confidence == sample_prompt.confidence
    assert retrieved.backend == sample_prompt.backend


@pytest.mark.asyncio
async def test_find_by_id(repository: SQLitePromptRepository, sample_prompt: PromptHistory):
    """Test finding a prompt history by ID."""
    # Arrange
    history_id = await repository.save(sample_prompt)

    # Act - Find existing record
    found = await repository.find_by_id(history_id)

    # Assert
    assert found is not None
    assert found.original_idea == sample_prompt.original_idea
    assert found.improved_prompt == sample_prompt.improved_prompt
    assert found.role == sample_prompt.role
    assert found.directive == sample_prompt.directive
    assert found.framework == sample_prompt.framework
    assert found.guardrails == sample_prompt.guardrails
    assert found.reasoning == sample_prompt.reasoning
    assert found.confidence == sample_prompt.confidence
    assert found.backend == sample_prompt.backend
    assert found.model == sample_prompt.model
    assert found.provider == sample_prompt.provider
    assert found.latency_ms == sample_prompt.latency_ms

    # Act - Find non-existent record
    not_found = await repository.find_by_id(99999)

    # Assert
    assert not_found is None


@pytest.mark.asyncio
async def test_find_recent(repository: SQLitePromptRepository):
    """Test finding recent prompts with pagination."""
    # Arrange - Create multiple prompts with different timestamps
    prompts = []
    for i in range(5):
        prompt = PromptHistory(
            original_idea=f"Idea {i}",
            context=f"Context {i}",
            improved_prompt=f"Improved prompt {i}",
            role="Developer",
            directive="Write code",
            framework="chain-of-thought",
            guardrails=["be safe"],
            confidence=0.8 + (i * 0.02),
            backend="zero-shot" if i % 2 == 0 else "few-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1000 + (i * 100),
            created_at=(datetime.utcnow() - timedelta(hours=i)).isoformat(),
        )
        prompts.append(prompt)
        await repository.save(prompt)

    # Act - Get recent without filters
    recent = await repository.find_recent(limit=3)

    # Assert
    assert len(recent) == 3
    # Should be ordered by created_at DESC (most recent first)
    assert recent[0].original_idea == "Idea 0"
    assert recent[1].original_idea == "Idea 1"
    assert recent[2].original_idea == "Idea 2"

    # Act - Get with offset
    recent_offset = await repository.find_recent(limit=2, offset=2)

    # Assert
    assert len(recent_offset) == 2
    assert recent_offset[0].original_idea == "Idea 2"
    assert recent_offset[1].original_idea == "Idea 3"

    # Act - Filter by backend
    zero_shot = await repository.find_recent(backend="zero-shot")

    # Assert
    assert len(zero_shot) == 3
    assert all(p.backend == "zero-shot" for p in zero_shot)

    # Act - Filter by provider
    openai = await repository.find_recent(provider="openai")

    # Assert
    assert len(openai) == 5
    assert all(p.provider == "openai" for p in openai)


@pytest.mark.asyncio
async def test_delete_old_records(repository: SQLitePromptRepository):
    """Test deleting old records."""
    # Arrange - Create old and new records
    old_prompt = PromptHistory(
        original_idea="Old idea",
        context="Old context",
        improved_prompt="Old improved prompt",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["be safe"],
        confidence=0.8,
        backend="zero-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=1000,
        # Create a record that's 35 days old
        created_at=(datetime.utcnow() - timedelta(days=35)).isoformat(),
    )
    await repository.save(old_prompt)

    new_prompt = PromptHistory(
        original_idea="New idea",
        context="New context",
        improved_prompt="New improved prompt",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["be safe"],
        confidence=0.9,
        backend="few-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=1000,
        # Create a record that's 10 days old
        created_at=(datetime.utcnow() - timedelta(days=10)).isoformat(),
    )
    new_id = await repository.save(new_prompt)

    # Act - Delete records older than 30 days
    deleted_count = await repository.delete_old_records(days=30)

    # Assert
    assert deleted_count == 1

    # Old record should be deleted
    old_record = await repository.find_by_id(1)
    assert old_record is None

    # New record should still exist
    new_record = await repository.find_by_id(new_id)
    assert new_record is not None
    assert new_record.original_idea == "New idea"


@pytest.mark.asyncio
async def test_quality_score_calculation(repository: SQLitePromptRepository):
    """Test quality score property calculation."""
    # Arrange - Test with high confidence, low latency
    prompt_high = PromptHistory(
        original_idea="Test idea",
        context="Test context",
        improved_prompt="Test improved prompt",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["be safe"],
        confidence=0.95,
        backend="zero-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=100,  # Very low latency (1% penalty)
    )
    await repository.save(prompt_high)

    # Act
    high_quality_score = prompt_high.quality_score

    # Assert - High confidence, low latency = high quality
    # 0.95 - (100/10000) = 0.95 - 0.01 = 0.94
    assert high_quality_score > 0.93
    assert high_quality_score <= 1.0

    # Arrange - Test with low confidence, high latency
    prompt_low = PromptHistory(
        original_idea="Test idea 2",
        context="Test context 2",
        improved_prompt="Test improved prompt 2",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["be safe"],
        confidence=0.6,
        backend="zero-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=8000,  # High latency (80% penalty, capped at 30%)
    )
    await repository.save(prompt_low)

    # Act
    low_quality_score = prompt_low.quality_score

    # Assert - Lower score due to low confidence and high latency
    # 0.6 - min(0.8, 0.3) = 0.6 - 0.3 = 0.3
    assert low_quality_score < 0.4
    assert low_quality_score >= 0.0

    # Test edge cases
    # No confidence (defaults to 0.5) + high latency
    prompt_no_conf = PromptHistory(
        original_idea="Test idea 3",
        context="Test context 3",
        improved_prompt="Test improved prompt 3",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["be safe"],
        confidence=None,  # No confidence
        backend="zero-shot",
        model="gpt-4",
        provider="openai",
        latency_ms=15000,  # Very high latency (150% penalty, capped at 30%)
    )

    # Act
    no_conf_score = prompt_no_conf.quality_score

    # Assert - Should have penalty due to high latency
    # 0.5 - min(1.5, 0.3) = 0.5 - 0.3 = 0.2
    assert no_conf_score < 0.3
    assert no_conf_score >= 0.0


@pytest.mark.asyncio
async def test_validation_empty_original_idea(repository: SQLitePromptRepository):
    """Test validation for empty original_idea."""
    # Arrange & Act & Assert - Empty string
    with pytest.raises(ValueError, match="original_idea cannot be empty"):
        PromptHistory(
            original_idea="",
            context="Context",
            improved_prompt="Improved prompt",
            role="Developer",
            directive="Write code",
            framework="chain-of-thought",
            guardrails=["be safe"],
            confidence=0.8,
            backend="zero-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1000,
        )

    # Arrange & Act & Assert - Whitespace only
    with pytest.raises(ValueError, match="original_idea cannot be empty"):
        PromptHistory(
            original_idea="   ",
            context="Context",
            improved_prompt="Improved prompt",
            role="Developer",
            directive="Write code",
            framework="chain-of-thought",
            guardrails=["be safe"],
            confidence=0.8,
            backend="zero-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1000,
        )


@pytest.mark.asyncio
async def test_validation_invalid_confidence(repository: SQLitePromptRepository):
    """Test validation for invalid confidence values."""
    base_prompt = {
        "original_idea": "Test idea",
        "context": "Test context",
        "improved_prompt": "Test improved prompt",
        "role": "Developer",
        "directive": "Write code",
        "framework": "chain-of-thought",
        "guardrails": ["be safe"],
        "backend": "zero-shot",
        "model": "gpt-4",
        "provider": "openai",
        "latency_ms": 1000,
    }

    # Test confidence > 1.0
    with pytest.raises(ValueError, match="Confidence must be 0-1"):
        PromptHistory(**base_prompt, confidence=1.5)

    # Test confidence < 0.0
    with pytest.raises(ValueError, match="Confidence must be 0-1"):
        PromptHistory(**base_prompt, confidence=-0.1)

    # Test confidence exactly at boundaries (should pass)
    prompt_min = PromptHistory(**base_prompt, confidence=0.0)
    assert prompt_min.confidence == 0.0

    prompt_max = PromptHistory(**base_prompt, confidence=1.0)
    assert prompt_max.confidence == 1.0


@pytest.mark.asyncio
async def test_search(repository: SQLitePromptRepository):
    """Test searching prompts by text content."""
    # Arrange - Create searchable prompts
    prompts = [
        PromptHistory(
            original_idea="Create a sorting function",
            context="Python development",
            improved_prompt="Implement quicksort in Python",
            role="Developer",
            directive="Write code",
            framework="chain-of-thought",
            guardrails=["handle edge cases"],
            confidence=0.8,
            backend="zero-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1000,
        ),
        PromptHistory(
            original_idea="Write database query",
            context="SQL optimization",
            improved_prompt="Create efficient SQL query with indexes",
            role="DBA",
            directive="Optimize query",
            framework="decomposition",
            guardrails=["use parameterized queries"],
            confidence=0.9,
            backend="few-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1500,
        ),
    ]
    for prompt in prompts:
        await repository.save(prompt)

    # Act - Search in original_idea
    results = await repository.search("sorting")

    # Assert
    assert len(results) == 1
    assert "sorting" in results[0].original_idea.lower()

    # Act - Search in improved_prompt
    results = await repository.search("efficient")

    # Assert
    assert len(results) == 1
    assert "efficient" in results[0].improved_prompt.lower()

    # Act - Search with no matches
    results = await repository.search("nonexistent")

    # Assert
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_statistics(repository: SQLitePromptRepository):
    """Test getting usage statistics."""
    # Arrange - Create multiple prompts
    prompts = [
        PromptHistory(
            original_idea=f"Idea {i}",
            context=f"Context {i}",
            improved_prompt=f"Improved {i}",
            role="Developer",
            directive="Write code",
            framework="chain-of-thought",
            guardrails=["be safe"],
            confidence=0.6 + (i * 0.08),
            backend="zero-shot" if i % 2 == 0 else "few-shot",
            model="gpt-4",
            provider="openai",
            latency_ms=1000 + (i * 500),
        )
        for i in range(5)
    ]
    for prompt in prompts:
        await repository.save(prompt)

    # Act
    stats = await repository.get_statistics()

    # Assert
    assert stats["total_count"] == 5
    assert 0.7 <= stats["average_confidence"] <= 1.0
    assert stats["average_latency_ms"] > 0
    assert "zero-shot" in stats["backend_distribution"]
    assert "few-shot" in stats["backend_distribution"]
    assert stats["backend_distribution"]["zero-shot"] == 3
    assert stats["backend_distribution"]["few-shot"] == 2
