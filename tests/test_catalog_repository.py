"""Tests for CatalogRepository - TDD approach."""
import os

import pytest

from hemdov.infrastructure.repositories.catalog_repository import (
    FileSystemCatalogRepository,
)


def test_repository_loads_valid_catalog(tmp_path):
    """Given: Valid catalog file with examples
    When: Load catalog
    Then: Returns list of example dictionaries"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": [{"inputs": {"original_idea": "test"}, "outputs": {"improved_prompt": "improved"}}]}')

    repo = FileSystemCatalogRepository(catalog_file)
    data = repo.load_catalog()

    assert len(data) == 1
    assert data[0]["inputs"]["original_idea"] == "test"


def test_repository_raises_on_missing_file(tmp_path):
    """Given: Catalog file doesn't exist
    When: Load catalog
    Then: Raises FileNotFoundError"""
    repo = FileSystemCatalogRepository(tmp_path / "nonexistent.json")

    with pytest.raises(FileNotFoundError):
        repo.load_catalog()


def test_repository_handles_list_format(tmp_path):
    """Given: Catalog in list format (no wrapper)
    When: Load catalog
    Then: Returns list correctly"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('[{"inputs": {"original_idea": "test"}, "outputs": {"improved_prompt": "improved"}}]')

    repo = FileSystemCatalogRepository(catalog_file)
    data = repo.load_catalog()

    assert len(data) == 1


def test_repository_raises_on_invalid_format(tmp_path):
    """Given: Catalog with invalid format
    When: Load catalog
    Then: Raises ValueError with 'Invalid catalog format'"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"invalid": "format"}')

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(ValueError, match="Invalid catalog format"):
        repo.load_catalog()


def test_repository_handles_permission_error(tmp_path):
    """Given: Catalog file with no read permissions
    When: Load catalog
    Then: Raises PermissionError (original exception exposed)"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": []}')
    os.chmod(catalog_file, 0o000)

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(PermissionError):
        repo.load_catalog()


def test_repository_handles_json_decode_error(tmp_path):
    """Given: Catalog file with invalid JSON
    When: Load catalog
    Then: Raises ValueError with JSON decode info"""
    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text('{"examples": [invalid json}')

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(ValueError, match="JSON"):
        repo.load_catalog()


def test_repository_handles_unicode_decode_error(tmp_path):
    """Given: Catalog file with encoding issues
    When: Load catalog
    Then: Raises ValueError with encoding info"""
    catalog_file = tmp_path / "test-catalog.json"
    # Write invalid UTF-8 bytes
    with open(catalog_file, 'wb') as f:
        f.write(b'{"examples": [\xff\xfe]}')

    repo = FileSystemCatalogRepository(catalog_file)

    with pytest.raises(ValueError, match="Encoding"):
        repo.load_catalog()


def test_knn_provider_with_repository(tmp_path):
    """Given: KNNProvider with repository
    When: Initialize and use KNNProvider
    Then: Works correctly with repository"""
    from hemdov.domain.services.knn_provider import KNNProvider

    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text(
        '{"examples": ['
        '{"inputs": {"original_idea": "debug code"}, "outputs": {"improved_prompt": "add logging"}},'
        '{"inputs": {"original_idea": "refactor function"}, "outputs": {"improved_prompt": "extract method"}}'
        ']}'
    )

    repo = FileSystemCatalogRepository(catalog_file)
    provider = KNNProvider(repository=repo, k=2)

    examples = provider.find_examples(intent="debug", complexity="simple", k=2)

    assert len(examples) <= 2
    assert all(hasattr(ex, 'input_idea') for ex in examples)


def test_knn_provider_backward_compatibility(tmp_path):
    """Given: KNNProvider with catalog_path (legacy)
    When: Initialize and use KNNProvider
    Then: Works correctly with backward compatibility"""
    from hemdov.domain.services.knn_provider import KNNProvider

    catalog_file = tmp_path / "test-catalog.json"
    catalog_file.write_text(
        '{"examples": ['
        '{"inputs": {"original_idea": "debug code"}, "outputs": {"improved_prompt": "add logging"}}'
        ']}'
    )

    # Legacy API - should still work
    provider = KNNProvider(catalog_path=catalog_file, k=1)

    examples = provider.find_examples(intent="debug", complexity="simple", k=1)

    assert len(examples) <= 1
    assert all(hasattr(ex, 'input_idea') for ex in examples)


def test_knn_provider_with_catalog_data():
    """Given: KNNProvider with pre-loaded catalog_data
    When: Initialize and use KNNProvider
    Then: Works correctly without file I/O"""
    from hemdov.domain.services.knn_provider import KNNProvider

    catalog_data = [
        {"inputs": {"original_idea": "debug code"}, "outputs": {"improved_prompt": "add logging"}},
        {"inputs": {"original_idea": "refactor function"}, "outputs": {"improved_prompt": "extract method"}},
    ]

    provider = KNNProvider(catalog_data=catalog_data, k=2)

    examples = provider.find_examples(intent="debug", complexity="simple", k=2)

    assert len(examples) <= 2
    assert all(hasattr(ex, 'input_idea') for ex in examples)
