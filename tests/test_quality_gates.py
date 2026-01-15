"""
Minimal unit tests for Quality Gates v0.1 + v0.2

Tests cover:
- v0.1 gates (format + completeness) for each template type
- v0.2 starter set gates (A1, A4, J1, P1, C1, E1)
- Edge cases (empty output, invalid JSON, etc.)
"""

import pytest

from api.quality_gates import (
    DEFAULT_TEMPLATES,
    GateSeverity,
    GateThresholds,
    TemplateSpec,
    evaluate_output,
    gate1_expected_format,
    gate2_min_completeness,
    gate_a1_filler_detector,
    gate_a4_repetition_detector,
    gate_c1_bullet_specificity,
    gate_e1_non_trivial_code,
    gate_j1_empty_value_ratio,
    gate_p1_real_step_content,
    get_template_summary,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def thresholds():
    """Default thresholds for testing"""
    return GateThresholds()


@pytest.fixture
def json_template():
    """JSON template spec"""
    return TemplateSpec.from_dict("json", DEFAULT_TEMPLATES["json"])


@pytest.fixture
def procedure_template():
    """Procedure markdown template spec"""
    return TemplateSpec.from_dict("procedure_md", DEFAULT_TEMPLATES["procedure_md"])


@pytest.fixture
def checklist_template():
    """Checklist markdown template spec"""
    return TemplateSpec.from_dict("checklist_md", DEFAULT_TEMPLATES["checklist_md"])


@pytest.fixture
def example_template():
    """Example markdown template spec"""
    return TemplateSpec.from_dict("example_md", DEFAULT_TEMPLATES["example_md"])


# ============================================================================
# v0.1 Gate Tests - Format
# ============================================================================

class TestV01Gate1Format:
    """Test v0.1 Gate 1: Expected Format"""

    def test_json_valid_passes(self, json_template, thresholds):
        """Valid JSON passes format gate"""
        output = '{"prompt": "Hello", "role": "Assistant"}'
        result = gate1_expected_format(output, json_template, thresholds)
        assert result.status == GateSeverity.PASS
        assert result.details["parsed"] is True

    def test_json_invalid_fails(self, json_template, thresholds):
        """Invalid JSON fails format gate"""
        output = '{"prompt": "Hello", "role": }'
        result = gate1_expected_format(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert "error" in result.details

    def test_json_empty_fails(self, json_template, thresholds):
        """Empty JSON fails format gate"""
        output = '{}'
        result = gate1_expected_format(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert "empty" in result.details["reason"].lower()

    def test_markdown_with_sections_passes(self, procedure_template, thresholds):
        """Markdown with required sections passes"""
        output = "## Objetivo\n\nTest\n\n## Pasos\n\n1. Step 1\n\n## Criterios\n\nDone"
        result = gate1_expected_format(output, procedure_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_markdown_missing_section_fails(self, procedure_template, thresholds):
        """Markdown missing required section fails"""
        output = "## Objetivo\n\nTest\n\n## Pasos\n\n1. Step 1"
        result = gate1_expected_format(output, procedure_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert "criterios" in result.details["missing_sections"][0].lower()

    def test_example_no_sections_required(self, example_template, thresholds):
        """Example template has no required sections"""
        output = "Some text with ```code``` here"
        result = gate1_expected_format(output, example_template, thresholds)
        assert result.status == GateSeverity.PASS


# ============================================================================
# v0.1 Gate Tests - Completeness
# ============================================================================

class TestV01Gate2Completeness:
    """Test v0.1 Gate 2: Minimum Completeness"""

    def test_json_with_2_keys_passes(self, json_template, thresholds):
        """JSON with >=2 keys passes"""
        output = '{"prompt": "Hello", "role": "Assistant"}'
        result = gate2_min_completeness(output, json_template, thresholds)
        assert result.status == GateSeverity.PASS
        assert result.details["key_count"] == 2

    def test_json_with_1_key_fails(self, json_template, thresholds):
        """JSON with <2 keys fails"""
        output = '{"prompt": "Hello"}'
        result = gate2_min_completeness(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert result.details["key_count"] == 1

    def test_procedure_with_2_steps_passes(self, procedure_template, thresholds):
        """Procedure with >=2 numbered steps passes"""
        output = "## Pasos\n\n1. First step\n2. Second step"
        result = gate2_min_completeness(output, procedure_template, thresholds)
        assert result.status == GateSeverity.PASS
        assert result.details["step_count"] == 2

    def test_procedure_with_1_step_fails(self, procedure_template, thresholds):
        """Procedure with <2 steps fails"""
        output = "## Pasos\n\n1. Only step"
        result = gate2_min_completeness(output, procedure_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert result.details["step_count"] == 1

    def test_checklist_with_3_bullets_passes(self, checklist_template, thresholds):
        """Checklist with >=3 bullets passes"""
        output = "## Checklist\n\n- Item 1\n- Item 2\n- Item 3"
        result = gate2_min_completeness(output, checklist_template, thresholds)
        assert result.status == GateSeverity.PASS
        assert result.details["bullet_count"] == 3

    def test_checklist_with_2_bullets_fails(self, checklist_template, thresholds):
        """Checklist with <3 bullets fails"""
        output = "## Checklist\n\n- Item 1\n- Item 2"
        result = gate2_min_completeness(output, checklist_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert result.details["bullet_count"] == 2

    def test_example_with_code_block_passes(self, example_template, thresholds):
        """Example with code block passes"""
        output = "```python\nprint('hello')\n```"
        result = gate2_min_completeness(output, example_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_example_without_code_block_fails(self, example_template, thresholds):
        """Example without code block fails"""
        output = "Just some text without code"
        result = gate2_min_completeness(output, example_template, thresholds)
        assert result.status == GateSeverity.FAIL


# ============================================================================
# v0.2 Gate Tests - Starter Set
# ============================================================================

class TestV02GateA1FillerDetector:
    """Test v0.2 Gate A1: Filler Detector"""

    def test_no_fillers_passes(self, procedure_template, thresholds):
        """Output without fillers passes"""
        output = "This is a valid output with meaningful content"
        result = gate_a1_filler_detector(output, procedure_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_two_fillers_fails(self, procedure_template, thresholds):
        """Output with 2 fillers fails"""
        output = "TODO: implement this feature with TBD logic"
        result = gate_a1_filler_detector(output, procedure_template, thresholds)
        assert result.status == GateSeverity.FAIL

    def test_one_filler_with_low_density_fails(self, procedure_template, thresholds):
        """1 filler + low content density fails"""
        output = "TBD..."  # Low density (3 alnum / 6 total = 0.5 > threshold 0.35)
        # Adjust thresholds for this test
        test_thresholds = GateThresholds(A1_CONTENT_DENSITY_THRESHOLD=0.6)
        result = gate_a1_filler_detector(output, procedure_template, test_thresholds)
        assert result.status == GateSeverity.FAIL


class TestV02GateA4RepetitionDetector:
    """Test v0.2 Gate A4: Repetition Detector"""

    def test_unique_content_passes(self, procedure_template, thresholds):
        """Unique content passes"""
        output = "\n".join([f"Step {i}: Different content here" for i in range(10)])
        result = gate_a4_repetition_detector(output, procedure_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_repetitive_content_fails(self, checklist_template, thresholds):
        """Repetitive content fails"""
        output = "\n".join(["- Generic item"] * 10)
        result = gate_a4_repetition_detector(output, checklist_template, thresholds)
        assert result.status == GateSeverity.FAIL

    def test_short_output_skips(self, procedure_template, thresholds):
        """Output with <6 lines is skipped"""
        output = "\n".join(["Line 1", "Line 2", "Line 3"])
        result = gate_a4_repetition_detector(output, procedure_template, thresholds)
        assert result.status == GateSeverity.SKIP


class TestV02GateJ1EmptyValueRatio:
    """Test v0.2 Gate J1: Empty Value Ratio (JSON)"""

    def test_json_with_values_passes(self, json_template, thresholds):
        """JSON with populated values passes"""
        output = '{"prompt": "Hello", "role": "Assistant", "context": "Test"}'
        result = gate_j1_empty_value_ratio(output, json_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_json_with_empty_values_fails(self, json_template, thresholds):
        """JSON with many empty values fails"""
        output = '{"prompt": "", "role": null, "context": [], "extra": ""}'
        result = gate_j1_empty_value_ratio(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL

    def test_missing_required_key_fails(self, json_template, thresholds):
        """JSON missing required key fails"""
        output = '{"prompt": "Hello"}'  # Missing "role" and "context"
        result = gate_j1_empty_value_ratio(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL
        assert "role" in result.details["missing_required"]


class TestV02GateP1RealStepContent:
    """Test v0.2 Gate P1: Real Step Content (Procedure)"""

    def test_substantive_steps_passes(self, procedure_template, thresholds):
        """Procedure with substantive steps passes"""
        output = """
        1. Implementar la funcion de validacion utilizando Python y expresiones regulares
        2. Configurar el string de conexion a la base de datos PostgreSQL
        3. Ejecutar la suite de pruebas unitarias para verificar la funcionalidad
        """
        result = gate_p1_real_step_content(output, procedure_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_generic_steps_fails(self, procedure_template, thresholds):
        """Procedure with generic steps fails"""
        output = """
        1. TBD
        2. Do the thing
        3. Check stuff
        """
        result = gate_p1_real_step_content(output, procedure_template, thresholds)
        assert result.status == GateSeverity.FAIL


class TestV02GateC1BulletSpecificity:
    """Test v0.2 Gate C1: Bullet Specificity (Checklist)"""

    def test_specific_bullets_passes(self, checklist_template, thresholds):
        """Checklist with specific bullets passes"""
        output = """
        - Validar API: el endpoint debe retornar codigo de estado doscientos
        - Verificar base de datos: el string de conexion debe estar correctamente configurado
        - Revisar codigo: ejecutar ESLint para asegurar que no existen errores de sintaxis
        """
        result = gate_c1_bullet_specificity(output, checklist_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_generic_bullets_fails(self, checklist_template, thresholds):
        """Checklist with generic bullets fails"""
        output = """
        - Check this
        - Do that
        - Verify the thing
        - Item here
        """
        result = gate_c1_bullet_specificity(output, checklist_template, thresholds)
        assert result.status == GateSeverity.FAIL


class TestV02GateE1NonTrivialCode:
    """Test v0.2 Gate E1: Non-Trivial Code (Example)"""

    def test_substantive_code_passes(self, example_template, thresholds):
        """Example with real code passes"""
        output = """
Some explanation text.

```python
def validate_input(data):
    if not data:
        return False
    return all(key in data for key in ['name', 'email'])

result = validate_input({'name': 'Test'})
print(f"Result: {result}")
```

More explanation here.
        """
        result = gate_e1_non_trivial_code(output, example_template, thresholds)
        assert result.status == GateSeverity.PASS

    def test_no_code_fails(self, example_template, thresholds):
        """Example without code blocks fails"""
        output = "Here's an explanation without any code"
        result = gate_e1_non_trivial_code(output, example_template, thresholds)
        assert result.status == GateSeverity.FAIL

    def test_comment_only_code_fails(self, example_template, thresholds):
        """Example with only comments fails"""
        output = """
        ```python
        # This is a comment
        # Another comment
        # No actual code here
        ```
        """
        result = gate_e1_non_trivial_code(output, example_template, thresholds)
        assert result.status == GateSeverity.FAIL


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_output_early_exit(self, procedure_template, thresholds):
        """Empty output fails at v0.1, doesn't reach v0.2"""
        report = evaluate_output("", "procedure_md", DEFAULT_TEMPLATES["procedure_md"], thresholds)
        assert not report.v0_1_pass
        assert len(report.v0_2_gates) == 0  # Early exit, no v0.2 gates run

    def test_whitespace_only_output(self, json_template, thresholds):
        """Whitespace-only output fails"""
        report = evaluate_output("   \n\n  ", "json", DEFAULT_TEMPLATES["json"], thresholds)
        assert not report.v0_1_pass

    def test_json_with_trailing_text(self, json_template, thresholds):
        """JSON with trailing text (common LLM error) fails format"""
        output = '{"prompt": "Hello"}\n\nHere is some extra text'
        result = gate1_expected_format(output, json_template, thresholds)
        assert result.status == GateSeverity.FAIL


# ============================================================================
# Integration Tests - Full evaluate_output()
# ============================================================================

class TestIntegration:
    """Integration tests with full evaluate_output()"""

    def test_json_valid_output(self):
        """Valid JSON output passes all gates"""
        output = '{"prompt": "Create a REST API", "role": "Backend Developer", "context": "Python project"}'
        report = evaluate_output(output, "json", DEFAULT_TEMPLATES["json"])
        assert report.v0_1_pass
        assert report.v0_2_fail_count == 0
        assert report.overall_pass

    def test_procedure_valid_output(self):
        """Valid procedure output passes all gates"""
        output = """
        ## Objetivo

        Configurar el entorno de desarrollo para el proyecto Python.

        ## Pasos

        1. Crear el entorno virtual utilizando Python version tres punto once con el comando pyenv
        2. Instalar todas las dependencias necesarias desde el archivo requirements.txt usando pip
        3. Configurar las variables de entorno en el archivo dotenv para la conexion a base de datos
        4. Ejecutar las migraciones de la base de datos usando el comando alembic upgrade head

        ## Criterios

        - El entorno virtual debe estar activado
        - Todas las pruebas deben pasar
        """
        report = evaluate_output(output, "procedure_md", DEFAULT_TEMPLATES["procedure_md"])
        assert report.v0_1_pass
        assert report.v0_2_fail_count == 0
        assert report.overall_pass

    def test_checklist_valid_output(self):
        """Valid checklist output passes all gates"""
        output = """
        ## Checklist

        - Validar entrada: los datos deben cumplir el schema JSON
        - Verificar permisos: el usuario debe tener rol de admin
        - Probar casos límite: probar con strings vacíos y valores null
        - Documentar cambios: actualizar el README con nueva API
        """
        report = evaluate_output(output, "checklist_md", DEFAULT_TEMPLATES["checklist_md"])
        assert report.v0_1_pass
        assert report.v0_2_fail_count == 0
        assert report.overall_pass

    def test_output_with_warnings(self):
        """Output that passes but has warnings"""
        output = """
        ## Objetivo

        Validar datos de entrada del usuario

        ## Pasos

        1. Leer los datos desde el request
        2. Validar que los campos requeridos esten presentes usando el schema
        3. Retornar error cuatrocientos si la validacion falla

        ## Criterios

        - Validacion correcta de todos los campos
        """
        report = evaluate_output(output, "procedure_md", DEFAULT_TEMPLATES["procedure_md"])
        assert report.v0_1_pass  # Has steps and all required sections
        # P1 gate may WARN or FAIL depending on content, we just need v0.1 to pass

    def test_failing_output(self):
        """Output that fails v0.1"""
        output = "Some random text"
        report = evaluate_output(output, "json", DEFAULT_TEMPLATES["json"])
        assert not report.v0_1_pass
        assert not report.overall_pass


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Test get_template_summary() and other helpers"""

    def test_summary_v01_format_fail(self):
        """Summary for v0.1 format failure"""
        report = evaluate_output("{invalid json", "json", DEFAULT_TEMPLATES["json"])
        summary = get_template_summary(report)
        assert "formato" in summary.lower()

    def test_summary_v02_filler_fail(self):
        """Summary for v0.2 filler failure (using procedure to pass v0.1)"""
        output = """
        ## Objetivo

        Test

        ## Pasos

        1. TBD
        2. TODO implement this

        ## Criterios

        Done
        """
        report = evaluate_output(output, "procedure_md", DEFAULT_TEMPLATES["procedure_md"])
        summary = get_template_summary(report)
        assert "placeholder" in summary.lower() or "tbd" in summary.lower()

    def test_summary_valid_output(self):
        """Summary for valid output"""
        output = '{"prompt": "Hello", "role": "Assistant", "context": "Test"}'
        report = evaluate_output(output, "json", DEFAULT_TEMPLATES["json"])
        summary = get_template_summary(report)
        assert "válido" in summary.lower()


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
