"""
Exception handling utilities for FastAPI endpoints.

Provides consistent error mapping and logging across API endpoints.
"""

import json
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ExceptionMapping:
    """Maps exception types to HTTP status codes and error messages."""

    CALCULATION_ERRORS: tuple[type[Exception], ...] = (
        AttributeError,
        TypeError,
        ZeroDivisionError,
    )

    DATA_ERRORS: tuple[type[Exception], ...] = (
        ValueError,
        KeyError,
    )

    CONNECTION_ERRORS: tuple[type[Exception], ...] = (
        ConnectionError,
        OSError,
        TimeoutError,
    )


def _validate_exception_mapping() -> None:
    """Validate that ExceptionMapping contains only exception types."""
    all_errors = set()
    for attr_name in ['CALCULATION_ERRORS', 'DATA_ERRORS', 'CONNECTION_ERRORS']:
        errors = getattr(ExceptionMapping, attr_name)
        for exc_type in errors:
            if not isinstance(exc_type, type) or not issubclass(exc_type, BaseException):
                raise TypeError(f"{attr_name} contains non-exception type: {exc_type}")
            if exc_type in all_errors:
                raise ValueError(f"Duplicate exception type {exc_type.__name__} in {attr_name}")
            all_errors.add(exc_type)


# Run validation at module load time
_validate_exception_mapping()


def create_exception_handlers():
    """Create FastAPI exception handlers following CLAUDE.md spec.

    Returns:
        Dictionary mapping exception types to handler functions

    Example:
        app = FastAPI()
        handlers = create_exception_handlers()
        for exc_type, handler in handlers.items():
            app.add_exception_handler(exc_type, handler)
    """

    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning(f"ValueError in {request.url.path}: {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid data: {str(exc)}"}
        )

    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        missing_key = str(exc) if exc else "unknown"
        logger.warning(f"KeyError in {request.url.path}: missing key '{missing_key}'")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Missing required data: {missing_key}"}
        )

    async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
        logger.warning(f"TypeError in {request.url.path}: {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid type: {str(exc)}"}
        )

    async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        logger.error(f"RuntimeError in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please contact support."}
        )

    async def attribute_error_handler(request: Request, exc: AttributeError) -> JSONResponse:
        logger.error(f"AttributeError in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please contact support."}
        )

    async def connection_error_handler(request: Request, exc: ConnectionError) -> JSONResponse:
        logger.error(f"ConnectionError in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable"}
        )

    async def os_error_handler(request: Request, exc: OSError) -> JSONResponse:
        logger.error(f"OSError in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable"}
        )

    async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
        # 504 = Gateway Timeout (upstream/LLM provider timeout)
        # 503 = Service Unavailable (server itself is down)
        # For LLM timeouts, 504 is the correct status code
        logger.error(f"TimeoutError in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timeout"}
        )

    async def zero_division_error_handler(request: Request, exc: ZeroDivisionError) -> JSONResponse:
        logger.error(f"ZeroDivisionError in {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Calculation error: division by zero"}
        )

    return {
        ValueError: value_error_handler,
        KeyError: key_error_handler,
        TypeError: type_error_handler,
        RuntimeError: runtime_error_handler,
        AttributeError: attribute_error_handler,
        ConnectionError: connection_error_handler,
        OSError: os_error_handler,
        TimeoutError: timeout_error_handler,
        ZeroDivisionError: zero_division_error_handler,
    }


def handle_file_operation_error(
    exc: Exception,
    component_name: str,
    degradation_flags: dict,
    flag_key: str,
) -> None:
    """
    Handle file operation errors during component initialization.

    Logs appropriate error/warning based on exception type and sets degradation flag.

    Args:
        exc: The caught exception
        component_name: Name of the component being initialized
        degradation_flags: Dictionary to update with degradation flag
        flag_key: Key to set in degradation_flags dictionary

    Example:
        try:
            knn_provider = KNNProvider(catalog_path=path)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
            handle_file_operation_error(e, "KNNProvider", flags, "knn_disabled")
    """
    if isinstance(exc, (FileNotFoundError, PermissionError)):
        logger.warning(
            f"{component_name} file unavailable: {type(exc).__name__}"
        )
    elif isinstance(exc, (json.JSONDecodeError, ValueError, KeyError)):
        logger.warning(
            f"{component_name} data invalid: {type(exc).__name__}"
        )
    else:
        logger.error(
            f"{component_name} initialization error: {type(exc).__name__}: {exc}"
        )

    degradation_flags[flag_key] = True
