"""Test ExceptionMapper logging context capture."""

import logging
import pytest
from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds
from hemdov.domain.errors import ErrorCategory


class TestExceptionMapperLogging:
    def test_mapper_captures_structured_logging_context(self, caplog):
        """Verify structured logging context is complete and correct."""
        error = ConnectionError("Network unreachable")

        with caplog.at_level(logging.ERROR):
            result = ExceptionMapper.map_llm_error(
                error,
                provider="anthropic",
                model="claude-haiku-4-5",
                prompt_length=1000
            )

        # Verify log record exists
        assert len(caplog.records) == 1
        log_record = caplog.records[0]

        # Verify extra context is present as attributes on LogRecord
        assert hasattr(log_record, "provider")
        assert hasattr(log_record, "model")
        assert hasattr(log_record, "prompt_length")
        assert hasattr(log_record, "original_exception")
        assert hasattr(log_record, "traceback")

        # Verify all expected values
        assert log_record.provider == "anthropic"
        assert log_record.model == "claude-haiku-4-5"
        assert log_record.prompt_length == "1000"
        assert log_record.original_exception == "ConnectionError"

        # Verify Error ID in message (uses the actual Error ID value, not constant name)
        assert ErrorIds.LLM_CONNECTION_FAILED in log_record.message

    def test_mapper_includes_traceback_in_context(self, caplog):
        """Stack trace should be captured in context for debugging."""
        error = PermissionError("Access denied")

        with caplog.at_level(logging.ERROR):
            result = ExceptionMapper.map_database_error(
                error,
                operation="initialize",
                db_path="/data/metrics.db",
                entity_type="Metrics"
            )

        log_record = caplog.records[0]

        # Verify traceback is present as an attribute (will contain current stack)
        assert hasattr(log_record, "traceback")
        assert len(log_record.traceback) > 0
