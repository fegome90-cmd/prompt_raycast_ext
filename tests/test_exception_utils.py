# tests/test_exception_utils.py
"""Tests for api/exception_utils.py exception handlers."""

import json
import pytest
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from unittest.mock import MagicMock

from api.exception_utils import create_exception_handlers


class TestCreateExceptionHandlers:
    """Tests for create_exception_handlers function."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dict with all expected exception type keys."""
        handlers = create_exception_handlers()

        expected_keys = {
            ValueError, KeyError, TypeError, AttributeError,
            ConnectionError, OSError, TimeoutError, ZeroDivisionError,
        }
        assert expected_keys.issubset(handlers.keys())

    def test_includes_request_validation_error(self):
        """Should include RequestValidationError handler."""
        handlers = create_exception_handlers()

        assert RequestValidationError in handlers


class TestValidationErrorHandler:
    """Tests for validation_error_handler (422 → 400 conversion)."""

    @pytest.mark.asyncio
    async def test_returns_400_status(self):
        """Should return 400 status code for validation errors."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "field"), "msg": "Field required", "type": "missing"}
        ]

        result = await handler(mock_request, exc)

        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_includes_field_in_error_message(self):
        """Should include field path in error message."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "mode"), "msg": "Input should be 'legacy' or 'nlac'", "type": "literal_error"}
        ]

        result = await handler(mock_request, exc)
        body = json.loads(result.body)

        assert "body.mode" in body["detail"]

    @pytest.mark.asyncio
    async def test_handles_integer_in_loc(self):
        """Should handle integer elements in loc array (e.g., array indices)."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "items", 0, "name"), "msg": "Field required", "type": "missing"}
        ]

        result = await handler(mock_request, exc)
        body = json.loads(result.body)

        assert "body.items.0.name" in body["detail"]
