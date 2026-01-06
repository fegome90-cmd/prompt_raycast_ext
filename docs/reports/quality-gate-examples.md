# Quality Gates - Examples & Expected Outputs

**Date:** January 5, 2026
**Purpose:** Examples of GateReport outputs for each template type
**Status:** Documentation

---

## Overview

This document shows example outputs from the `/api/v1/evaluate-quality` endpoint for each template type.

---

## 1. JSON Template (`json`)

### 1.1 Valid JSON Output - PASS

**Request:**
```json
{
  "output": "{\"prompt\": \"Create a REST API\", \"role\": \"Backend Developer\", \"context\": \"Python project\"}",
  "template_id": "json"
}
```

**Response:**
```json
{
  "template_id": "json",
  "output_length": 91,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": true,
  "overall_status": "PASS",
  "summary": "Output válido",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {
        "gate_id": "v0.1_gate1_format",
        "gate_version": "0.1",
        "status": "PASS",
        "details": {"format": "json", "parsed": true}
      },
      "gate2_completeness": {
        "gate_id": "v0.1_gate2_completeness",
        "gate_version": "0.1",
        "status": "PASS",
        "details": {"key_count": 3}
      }
    },
    "v0.2_gates": {
      "A1_filler": {
        "gate_id": "A1_filler_detector",
        "gate_version": "0.2",
        "status": "PASS",
        "score": 1.0,
        "details": {"filler_count": 0, "content_density": 0.846, "fillers_found": []}
      },
      "J1_empty": {
        "gate_id": "J1_empty_value_ratio",
        "gate_version": "0.2",
        "status": "PASS",
        "score": 1.0,
        "details": {"empty_ratio": 0.0, "empty_count": 0, "total_count": 3}
      }
    }
  }
}
```

---

### 1.2 JSON with Empty Values - FAIL

**Request:**
```json
{
  "output": "{\"prompt\": \"\", \"role\": null, \"context\": []}",
  "template_id": "json"
}
```

**Response:**
```json
{
  "template_id": "json",
  "output_length": 44,
  "v0_1_pass": true,
  "v0_2_fail_count": 1,
  "v0_2_warn_count": 0,
  "overall_pass": false,
  "overall_status": "FAIL",
  "summary": "Valores vacíos en JSON",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS", "details": {"parsed": true}},
      "gate2_completeness": {"status": "PASS", "details": {"key_count": 3}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "PASS"},
      "J1_empty": {
        "gate_id": "J1_empty_value_ratio",
        "gate_version": "0.2",
        "status": "FAIL",
        "score": 0.0,
        "details": {
          "empty_ratio": 1.0,
          "empty_count": 3,
          "total_count": 3,
          "missing_required": ["role", "context"]
        }
      }
    }
  }
}
```

---

## 2. Procedure Template (`procedure_md`)

### 2.1 Valid Procedure - PASS

**Request:**
```json
{
  "output": "## Objetivo\n\nConfigurar el entorno de desarrollo para el proyecto Python.\n\n## Pasos\n\n1. Crear el entorno virtual utilizando Python version tres punto once con el comando pyenv\n2. Instalar todas las dependencias necesarias desde el archivo requirements.txt usando pip\n3. Configurar las variables de entorno en el archivo dotenv para la conexion a base de datos\n4. Ejecutar las migraciones de la base de datos usando el comando alembic upgrade head\n\n## Criterios\n\n- El entorno virtual debe estar activado\n- Todas las pruebas deben pasar",
  "template_id": "procedure_md"
}
```

**Response:**
```json
{
  "template_id": "procedure_md",
  "output_length": 624,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": true,
  "overall_status": "PASS",
  "summary": "Output válido",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS", "details": {"all_sections_present": true}},
      "gate2_completeness": {"status": "PASS", "details": {"step_count": 4}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "PASS"},
      "A4_repetition": {"status": "PASS"},
      "P1_steps": {"status": "PASS", "score": 1.0}
    }
  }
}
```

---

### 2.2 Procedure with Generic Steps - WARN

**Request:**
```json
{
  "output": "## Objetivo\n\nTest\n\n## Pasos\n\n1. TBD\n2. Do the thing\n3. Check stuff\n\n## Criterios\n\nDone",
  "template_id": "procedure_md"
}
```

**Response:**
```json
{
  "template_id": "procedure_md",
  "output_length": 80,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 1,
  "overall_pass": true,
  "overall_status": "WARN",
  "summary": "Algunos pasos podrían ser más específicos",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS"},
      "gate2_completeness": {"status": "PASS", "details": {"step_count": 3}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "WARN", "details": {"filler_count": 1}},
      "A4_repetition": {"status": "PASS"},
      "P1_steps": {"status": "WARN", "score": 0.33}
    }
  }
}
```

---

## 3. Checklist Template (`checklist_md`)

### 3.1 Valid Checklist - PASS

**Request:**
```json
{
  "output": "## Checklist\n\n- Validar API: el endpoint debe retornar codigo de estado doscientos\n- Verificar base de datos: el string de conexion debe estar correctamente configurado\n- Revisar codigo: ejecutar ESLint para asegurar que no existen errores de sintaxis",
  "template_id": "checklist_md"
}
```

**Response:**
```json
{
  "template_id": "checklist_md",
  "output_length": 245,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": true,
  "overall_status": "PASS",
  "summary": "Output válido",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS"},
      "gate2_completeness": {"status": "PASS", "details": {"bullet_count": 3}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "PASS"},
      "A4_repetition": {"status": "PASS"},
      "C1_specific": {"status": "PASS", "score": 1.0}
    }
  }
}
```

---

### 3.2 Checklist with Generic Bullets - FAIL

**Request:**
```json
{
  "output": "## Checklist\n\n- Check this\n- Do that\n- Verify the thing\n- Item here",
  "template_id": "checklist_md"
}
```

**Response:**
```json
{
  "template_id": "checklist_md",
  "output_length": 60,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 1,
  "overall_pass": true,
  "overall_status": "WARN",
  "summary": "Algunos bullets podrían ser más específicos",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS"},
      "gate2_completeness": {"status": "PASS", "details": {"bullet_count": 4}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "PASS"},
      "A4_repetition": {"status": "PASS"},
      "C1_specific": {"status": "WARN", "score": 0.75}
    }
  }
}
```

---

## 4. Example Template (`example_md`)

### 4.1 Valid Example with Code - PASS

**Request:**
```json
{
  "output": "Here's how to validate input:\n\n```python\ndef validate_input(data):\n    if not data:\n        return False\n    return all(key in data for key in ['name', 'email'])\n\nresult = validate_input({'name': 'Test'})\nprint(f\"Result: {result}\")\n```\n\nThis function checks if all required keys are present.",
  "template_id": "example_md"
}
```

**Response:**
```json
{
  "template_id": "example_md",
  "output_length": 235,
  "v0_1_pass": true,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": true,
  "overall_status": "PASS",
  "summary": "Output válido",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS"},
      "gate2_completeness": {"status": "PASS", "details": {"has_code_block": true}}
    },
    "v0.2_gates": {
      "A1_filler": {"status": "PASS"},
      "A4_repetition": {"status": "PASS"},
      "E1_code": {"status": "PASS", "score": 1.0, "details": {"code_blocks": 1, "code_lines": 6}}
    }
  }
}
```

---

### 4.2 Example without Code - FAIL

**Request:**
```json
{
  "output": "Here's an explanation without any code block",
  "template_id": "example_md"
}
```

**Response:**
```json
{
  "template_id": "example_md",
  "output_length": 47,
  "v0_1_pass": false,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": false,
  "overall_status": "FAIL",
  "summary": "Example has no code block",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {"status": "PASS"},
      "gate2_completeness": {"status": "FAIL", "details": {"reason": "Example has no code block"}}
    },
    "v0.2_gates": {}
  }
}
```

---

## 5. Early Exit Examples

### 5.1 Invalid JSON - Early Exit (no v0.2 gates)

**Request:**
```json
{
  "output": "{invalid json",
  "template_id": "json"
}
```

**Response:**
```json
{
  "template_id": "json",
  "output_length": 14,
  "v0_1_pass": false,
  "v0_2_fail_count": 0,
  "v0_2_warn_count": 0,
  "overall_pass": false,
  "overall_status": "FAIL",
  "summary": "Formato inválido",
  "gates": {
    "v0.1_gates": {
      "gate1_format": {
        "status": "FAIL",
        "details": {"reason": "Invalid JSON", "error": "Expecting value"}
      }
    },
    "v0.2_gates": {}
  }
}
```

**Note:** v0.2_gates is empty because of early exit - v0.1 failed, so v0.2 gates were not executed.

---

## Summary Table

| Template | Output Type | v0.1 | v0.2 | Overall | Summary |
|----------|-------------|------|------|---------|---------|
| json | Valid JSON | PASS | 0 FAIL | PASS | Output válido |
| json | Empty values | PASS | 1 FAIL | FAIL | Valores vacíos en JSON |
| json | Invalid JSON | FAIL | - | FAIL | Formato inválido |
| procedure_md | Valid procedure | PASS | 0 FAIL | PASS | Output válido |
| procedure_md | Generic steps | PASS | 1 WARN | WARN | Pasos podrían ser más específicos |
| checklist_md | Valid checklist | PASS | 0 FAIL | PASS | Output válido |
| checklist_md | Generic bullets | PASS | 1 WARN | WARN | Bullets podrían ser más específicos |
| example_md | With code | PASS | 0 FAIL | PASS | Output válido |
| example_md | No code | FAIL | - | FAIL | Example has no code block |

---

## Usage in Frontend

### Display Logic

```typescript
function renderQualityGates(report: GateReport) {
  if (!report.v0_1_pass) {
    // Show error: "Formato inválido" or "Contenido incompleto"
    return <ErrorBanner message={report.summary} disableCopy />;
  }

  if (report.v0_2_fail_count > 0) {
    // Show error: "Valores vacíos en JSON", etc.
    return <ErrorBanner message={report.summary} disableCopy />;
  }

  if (report.v0_2_warn_count > 0) {
    // Show warning: allow copy but display subtle warning
    return <WarningBanner message={report.summary} allowCopy />;
  }

  // All good - show success
  return <SuccessBanner message="Output listo para usar" />;
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
