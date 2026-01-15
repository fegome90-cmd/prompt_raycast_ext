"""Error ID registry for Sentry tracking.

Each error has a unique ID that appears in logs and Sentry.
Format: PREFIX-NUM where PREFIX is the error category and NUM is a sequence.
"""


class ErrorIds:
    """Centralized Error ID registry.

    All Error IDs must be unique for Sentry tracking.
    Format: PREFIX-NUM (e.g., LLM-001, CACHE-001, DB-001, IO-001)
    """

    # LLM Provider Errors
    LLM_CONNECTION_FAILED = "LLM-001"
    LLM_TIMEOUT = "LLM-002"
    LLM_UNKNOWN_ERROR = "LLM-003"

    # Cache Errors
    CACHE_GET_FAILED = "CACHE-001"
    CACHE_SET_FAILED = "CACHE-002"
    CACHE_UPDATE_FAILED = "CACHE-003"
    CACHE_CONSTRAINT_VIOLATION = "CACHE-004"

    # Data Corruption Errors
    DATA_CORRUPTION_METRICS = "DATA-001"
    DATA_CORRUPTION_GUARDRAILS = "DATA-002"

    # Database Errors
    DB_QUERY_FAILED = "DB-001"
    DB_OPERATIONAL_ERROR = "DB-002"
    DB_CORRUPTION = "DB-003"
    DB_PERMISSION_DENIED = "DB-004"
    DB_INIT_FAILED = "DB-005"
    MIGRATION_FAILED = "DB-006"

    # File I/O Errors
    FILE_READ_FAILED = "IO-001"
    FILE_NOT_FOUND = "IO-002"
    FILE_PERMISSION_DENIED = "IO-003"
    FILE_UNICODE_ERROR = "IO-004"
