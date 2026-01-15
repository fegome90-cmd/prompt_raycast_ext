"""Test Error ID registry uniqueness and format."""

import pytest
from hemdov.infrastructure.errors.ids import ErrorIds


def test_error_ids_are_unique():
    """Error IDs must be unique for Sentry tracking.

    This prevents two different errors from logging with the same ID,
    which would make debugging impossible in Sentry.
    """
    error_ids = [
        ErrorIds.LLM_CONNECTION_FAILED,
        ErrorIds.LLM_TIMEOUT,
        ErrorIds.LLM_UNKNOWN_ERROR,
        ErrorIds.CACHE_GET_FAILED,
        ErrorIds.CACHE_SET_FAILED,
        ErrorIds.CACHE_UPDATE_FAILED,
        ErrorIds.CACHE_CONSTRAINT_VIOLATION,
        ErrorIds.DATA_CORRUPTION_METRICS,
        ErrorIds.DATA_CORRUPTION_GUARDRAILS,
        ErrorIds.DB_QUERY_FAILED,
        ErrorIds.DB_OPERATIONAL_ERROR,
        ErrorIds.DB_CORRUPTION,
        ErrorIds.DB_PERMISSION_DENIED,
        ErrorIds.DB_INIT_FAILED,
        ErrorIds.MIGRATION_FAILED,
        ErrorIds.FILE_READ_FAILED,
        ErrorIds.FILE_NOT_FOUND,
        ErrorIds.FILE_PERMISSION_DENIED,
        ErrorIds.FILE_UNICODE_ERROR,
    ]

    # Check for duplicates using set property
    unique_ids = set(error_ids)
    assert len(error_ids) == len(unique_ids), (
        f"Duplicate Error IDs found: "
        f"{[eid for eid in error_ids if error_ids.count(eid) > 1]}"
    )


def test_error_id_format():
    """All Error IDs follow PREFIX-NUM format for Sentry compatibility."""
    error_ids = [
        ErrorIds.LLM_CONNECTION_FAILED,
        ErrorIds.LLM_TIMEOUT,
        ErrorIds.LLM_UNKNOWN_ERROR,
        ErrorIds.CACHE_GET_FAILED,
        ErrorIds.CACHE_SET_FAILED,
        ErrorIds.CACHE_UPDATE_FAILED,
        ErrorIds.CACHE_CONSTRAINT_VIOLATION,
        ErrorIds.DATA_CORRUPTION_METRICS,
        ErrorIds.DATA_CORRUPTION_GUARDRAILS,
        ErrorIds.DB_QUERY_FAILED,
        ErrorIds.DB_OPERATIONAL_ERROR,
        ErrorIds.DB_CORRUPTION,
        ErrorIds.DB_PERMISSION_DENIED,
        ErrorIds.DB_INIT_FAILED,
        ErrorIds.MIGRATION_FAILED,
        ErrorIds.FILE_READ_FAILED,
        ErrorIds.FILE_NOT_FOUND,
        ErrorIds.FILE_PERMISSION_DENIED,
        ErrorIds.FILE_UNICODE_ERROR,
    ]

    for error_id in error_ids:
        # Format: LLM-001, CACHE-001, DB-001, IO-001
        assert "-" in error_id, f"{error_id} must contain hyphen"
        parts = error_id.split("-")
        assert len(parts) == 2, f"{error_id} must have exactly one hyphen"
        prefix, number = parts
        assert prefix.isupper(), f"{error_id} prefix must be uppercase"
        assert number.isdigit(), f"{error_id} suffix must be numeric"
