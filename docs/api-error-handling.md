# API Error Handling

## Overview

This document describes the error handling strategy for the DSPy Prompt Improver API. All errors follow specific patterns to ensure consistent client behavior and proper debugging.

## HTTP Status Codes

| Status | When Used | Example |
|--------|-----------|---------|
| 400 | Invalid input data | Empty idea, invalid filter format |
| 404 | Resource not found | No metrics for comparison group |
| 422 | Validation error | Pydantic validation failure |
| 503 | Service unavailable | Database connection failed, LLM provider unavailable |
| 504 | Gateway timeout | Strategy execution exceeded timeout |
| 500 | Internal error | Unexpected bug (should propagate crashes) |

## Error Response Format

### Standard Error Response

```json
{
  "detail": "Metrics calculation failed: AttributeError"
}
```

### With Error Tracking ID

For quality gate evaluation errors, an error ID is generated for tracking:

```json
{
  "detail": "Internal evaluation error. Reference ID: QE-1736851200-json"
}
```

## Graceful Degradation

### Degradation Flags

The `/improve-prompt` endpoint includes `degradation_flags` in responses to indicate when optional features have failed:

```json
{
  "improved_prompt": "**[ROLE]** ...",
  "metrics_warning": "Metrics calculation skipped: TypeError",
  "degradation_flags": {
    "metrics_failed": true,
    "knn_disabled": false,
    "complex_strategy_disabled": false
  }
}
```

**Flag meanings:**
- `metrics_failed`: Metrics calculation or persistence failed
- `knn_disabled`: KNNProvider initialization failed (NLaC mode)
- `complex_strategy_disabled`: ComplexStrategy initialization failed (legacy mode)

### Metrics Warnings

When metrics fail, a `metrics_warning` field contains the first warning message:

```json
{
  "metrics_warning": "Metrics persistence failed: ConnectionError",
  "degradation_flags": {
    "metrics_failed": true,
    "knn_disabled": false,
    "complex_strategy_disabled": false
  }
}
```

## Exception Types by Category

### Client Errors (400-499)

| Exception Type | HTTP Status | Notes |
|---------------|-------------|-------|
| `ValueError` | 400 | Invalid input data, filter format |
| `TypeError` | 400 | Wrong data type |
| `AttributeError` | 400/500 | Missing attributes (context-dependent) |
| `KeyError` | 400 | Missing required keys |
| `ValidationError` | 422 | Pydantic validation (auto-handled) |

### Service Errors (500-599)

| Exception Type | HTTP Status | Notes |
|---------------|-------------|-------|
| `ConnectionError` | 503 | Database/network unavailable |
| `OSError` | 503 | File system errors |
| `TimeoutError` | 503 | Query timeout |
| `asyncio.TimeoutError` | 504 | Strategy execution timeout |
| `RuntimeError` | 500 | Unexpected bug (may propagate) |
| `MemoryError` | 500 | Out of memory |

## Specific Endpoint Behaviors

### `/api/v1/metrics/*` (Metrics API)

- **Calculation errors** (AttributeError, TypeError, ZeroDivisionError) → 500
- **Data issues** (ValueError, KeyError) → 400
- **Repository errors** (ConnectionError, OSError, TimeoutError) → 503

### `/api/v1/improve-prompt` (Prompt Improver)

- **Strategy timeout** → 504
- **Connection errors** → 503
- **Metrics failures** → 200 with `metrics_warning` and `degradation_flags`
- **Validation errors** → 400

### `/api/v1/evaluate-quality` (Quality Gates)

- **Validation errors** → 400
- **Quality gate errors** → 500
- **Unexpected errors** → 500 with error tracking ID

## Never Catch These Exceptions

The following exceptions should NEVER be caught and should always propagate:

- `KeyboardInterrupt` - Let user/interrupt signals propagate
- `SystemExit` - Let system exit signals propagate
- `Exception` - Use specific exception types instead

## Testing Exception Handling

See test files for examples:
- `tests/test_metrics_api_exception_handling.py`
- `tests/test_prompt_improver_api_exception_handling.py`
- `tests/test_strategy_selector_exception_handling.py`

## Migration Notes

When adding new error handling:

1. **Use specific exceptions** - Never use `except Exception:`
2. **Log with context** - Include exception type and message
3. **Map to appropriate HTTP status** - Follow the table above
4. **Add degradation flags** - For optional feature failures
5. **Write tests first** - Follow TDD RED-GREEN-REFACTOR cycle
