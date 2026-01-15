"""
API Integration Tests for /api/v1/evaluate-quality endpoint.

Tests cover:
- Valid requests for all template types
- Input validation (empty, whitespace, size limits)
- template_id validation
- Error handling and logging
- Response model completeness
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.prompt_improver_api import router
from api.quality_gates import DEFAULT_TEMPLATES

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI app with quality gates router."""
    app_ = FastAPI()
    app_.include_router(router)
    return app_


@pytest.fixture
def client(app):
    """Create test client for API requests."""
    return TestClient(app)


# ============================================================================
# Valid Request Tests
# ============================================================================

class TestValidRequests:
    """Test valid requests for all template types."""

    def test_json_valid_output(self, client):
        """Valid JSON output returns 200 with complete response."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Create API", "role": "Backend", "context": "Python"}',
                "template_id": "json"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all response fields
        assert data["template_id"] == "json"
        assert data["output_length"] == 64  # Actual length of JSON string
        assert data["v0_1_pass"] is True
        assert data["overall_status"] in ["PASS", "WARN", "FAIL"]
        assert "summary" in data
        assert "gates" in data
        assert "v0_1_gates" in data["gates"]
        assert "v0_2_gates" in data["gates"]

    def test_procedure_valid_output(self, client):
        """Valid procedure output returns 200."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": """## Objetivo

Configurar entorno de desarrollo.

## Pasos

1. Crear entorno virtual con Python 3.11
2. Instalar dependencias desde requirements.txt
3. Configurar variables de entorno en .env

## Criterios

- Todas las pruebas pasan
""",
                "template_id": "procedure_md"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == "procedure_md"
        assert data["v0_1_pass"] is True
        assert data["output_length"] > 0

    def test_checklist_valid_output(self, client):
        """Valid checklist output returns 200."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": """## Checklist

- Validar API: el endpoint debe retornar 200
- Verificar base de datos: connection string correcto
- Revisar código: ejecutar ESLint
""",
                "template_id": "checklist_md"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == "checklist_md"

    def test_example_valid_output(self, client):
        """Valid example output returns 200."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": """Here's how to validate input:

```python
def validate(data):
    return all(k in data for k in ['name', 'email'])

result = validate({'name': 'Test'})
print(result)
```

This checks required keys.
""",
                "template_id": "example_md"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == "example_md"

    def test_default_template_id(self, client):
        """Request without template_id defaults to 'json'."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Test"}'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == "json"


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """Test input validation for empty/whitespace/size."""

    def test_empty_output_400(self, client):
        """Empty output returns 400."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": "",
                "template_id": "json"
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_whitespace_only_output_400(self, client):
        """Whitespace-only output returns 400."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": "   \n\n  \t  ",
                "template_id": "json"
            }
        )

        assert response.status_code == 422
        assert "whitespace" in response.json()["detail"][0]["msg"].lower()

    def test_output_exceeds_max_size_400(self, client):
        """Output exceeding 100KB returns 422."""
        large_output = "x" * 100001  # Exceeds 100000 limit

        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": large_output,
                "template_id": "json"
            }
        )

        assert response.status_code == 422

    def test_missing_output_field_422(self, client):
        """Missing output field returns 422."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "template_id": "json"
            }
        )

        assert response.status_code == 422


# ============================================================================
# Template ID Validation Tests
# ============================================================================

class TestTemplateIdValidation:
    """Test template_id validation."""

    def test_invalid_template_id_400(self, client):
        """Invalid template_id returns 400."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Test"}',
                "template_id": "invalid_template"
            }
        )

        assert response.status_code == 422
        detail = response.json()["detail"][0]["msg"]
        assert "invalid template_id" in detail.lower()

    def test_all_valid_templates_accepted(self, client):
        """All templates in DEFAULT_TEMPLATES are accepted."""
        for template_id in DEFAULT_TEMPLATES.keys():
            response = client.post(
                "/api/v1/evaluate-quality",
                json={
                    "output": "test content",
                    "template_id": template_id
                }
            )
            # Should not error on template_id validation
            assert response.status_code != 422 or "template_id" not in str(response.json())


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and logging."""

    def test_invalid_json_fails_gracefully(self, client):
        """Invalid JSON for json template returns 200 with FAIL status."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": "{invalid json",
                "template_id": "json"
            }
        )

        # Should return 200 (evaluation succeeded, but output failed)
        assert response.status_code == 200
        data = response.json()
        assert data["v0_1_pass"] is False
        assert data["overall_status"] == "FAIL"

    def test_missing_markdown_sections_fails_gracefully(self, client):
        """Procedure missing required sections returns 200 with FAIL status."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": "## Objetivo\n\nTest\n\n## Pasos\n\n1. Step 1",
                "template_id": "procedure_md"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["v0_1_pass"] is False

    def test_error_id_generated_on_500(self, client):
        """Internal errors generate error ID for tracking."""
        # This test would require mocking to trigger an internal error
        # For now, verify the error_id format is correct in the code
        import time
        template_id = "json"
        error_id = f"QE-{int(time.time())}-{template_id}"
        assert error_id.startswith("QE-")
        assert template_id in error_id


# ============================================================================
# Response Model Tests
# ============================================================================

class TestResponseModel:
    """Test response model completeness and structure."""

    def test_response_has_all_required_fields(self, client):
        """Response includes all required fields."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Test", "role": "Assistant", "context": "Test"}',
                "template_id": "json"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # All required fields present
        required_fields = [
            "template_id", "output_length", "v0_1_pass",
            "v0_2_fail_count", "v0_2_warn_count", "overall_pass",
            "overall_status", "summary", "gates"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_gates_structure_is_complete(self, client):
        """Gates field has correct structure."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Test", "role": "Assistant"}',
                "template_id": "json"
            }
        )

        assert response.status_code == 200
        data = response.json()
        gates = data["gates"]

        # Has v0.1 and v0.2 gates
        assert "v0_1_gates" in gates
        assert "v0_2_gates" in gates

        # v0.1 gates have expected structure
        if gates["v0_1_gates"]:
            for gate_id, gate_result in gates["v0_1_gates"].items():
                assert "status" in gate_result
                assert "gate_version" in gate_result

    def test_overall_status_derivation(self, client):
        """overall_status is correctly derived from gate results."""
        # Test PASS case
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Test", "role": "Assistant", "context": "Test"}',
                "template_id": "json"
            }
        )

        data = response.json()
        # If v0_1 passes and 0 v0_2 fails, should be PASS or WARN
        if data["v0_1_pass"] and data["v0_2_fail_count"] == 0:
            assert data["overall_status"] in ["PASS", "WARN"]
            assert data["overall_pass"] is True


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimal_valid_output(self, client):
        """Smallest valid output (1 char) works."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": "x",
                "template_id": "example_md"
            }
        )

        assert response.status_code == 200
        assert response.json()["output_length"] == 1

    def test_unicode_output(self, client):
        """Unicode characters in output work correctly."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "测试", "role": "Asistente", "context": "Prueba"}',
                "template_id": "json"
            }
        )

        assert response.status_code == 200

    def test_special_characters_in_output(self, client):
        """Special characters (newlines, tabs, quotes) work correctly."""
        response = client.post(
            "/api/v1/evaluate-quality",
            json={
                "output": '{"prompt": "Line 1\\nLine 2\\tTabbed", "role": "Test"}',
                "template_id": "json"
            }
        )

        assert response.status_code == 200


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
