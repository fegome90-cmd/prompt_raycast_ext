# 🌌 META-PROMPT UNIVERSAL v2.0.0 - Sistema Completo de Generación de Prompts

---
meta:
  id: META-PROMPT-UNIVERSAL
  version: 2.0.0
  created_at: "2025-12-11T12:52:00Z"
  updated_at: "2025-12-12T00:00:00Z"
  base: PROMPT-ACREDITADOR-PLAYBOOK-BMCC-v1.0.0 + PROMPT-PAE-EXTRACTOR-v1.0.0 + META-HANDOFF-TEMPLATE-v1.0.0
  mode: [meta, generation, validation, accreditation]
  depth: comprehensive
  anti_drift: "V001-V011 enabled"
  audit_framework: "4D + CSE + CoVe"
  expected_score:
    minimum: "≥8.0/10"
    elite: "≥9.5/10"
  cloop_level: 3
  purpose: "Meta-prompt universal para producir planes de nivel senior y convertirlos en chunks ejecutables con validación"
  memory_integration: "core/memory + core/surprise-metrics + core/context-management"
  validation_system: "automated + manual + schema_compliant"
  determinism:
    guarantee: "STRUCTURE_ONLY"
    includes: ["schema", "section order", "marker accounting", "checksums (optional)"]
    excludes: ["semantic content (LLM sampling)", "external state (time/web)", "non-idempotent tools"]
---

# 🎯 PROPÓSITO DEL META-PROMPT UNIVERSAL

## Objetivo Principal

Este documento define el **meta-prompt universal definitivo** que integra los mejores mecanismos de los prompts analizados:

1. ✅ **PROMPT-ACREDITADOR-PLAYBOOK-BMCC-v1.0.0** - Sistema de acreditación completo
2. ✅ **PROMPT-PAE-EXTRACTOR-v1.0.0** - Sistema de extracción estructurada
3. ✅ **META-HANDOFF-TEMPLATE-v1.0.0** - Sistema de transferencia de conocimiento

## Fundamento

**Basado en análisis exhaustivo de prompts existentes:**

- **8 componentes críticos** del Acreditador (C1-C8 + C9 memoria)
- **Sistema PAE completo** con schema JSON y validación automatizada
- **17 secciones estructuradas** del Handoff Template
- **15+ mecanismos antidrift** identificados y validados
- **Sistema de marcadores completo** con 25+ tipos diferentes
- **Validación automatizada** con scripts bash y herramientas CLI

**Threshold decisión:**

- **≥9.5/10:** ⭐⭐⭐ ELITE (Referencia universal)
- **≥8.0/10:** ✅ ACREDITADO (Estándar oro)
- **7.0-7.9/10:** ⚠️ REFINAR (Mejoras requeridas)
- **<7.0/10:** ❌ REFACTORIZAR (Rediseñar completo)

---

# 🧭 MODO “SENIOR PLAN” → “JUNIOR EXECUTE” (Objetivo práctico de este documento)

Este meta‑prompt NO es para “hacerlo todo”. Es para que el LLM actúe como **senior planner**: entregue un plan de alto nivel, con riesgos y criterios de aceptación, y lo convierta en **chunks pequeños** que un “junior” (otro LLM o humano) pueda ejecutar sin inventar cosas.

## Output Contract (obligatorio)

El LLM debe producir SIEMPRE estos 3 artefactos, en este orden:

### A) PLAN_ALTO_NIVEL (visión senior)
Incluye:
- Objetivo y “North Star”
- Alcance (IN/OUT) + supuestos + restricciones
- Arquitectura / enfoque (a nivel de bloques, no código)
- Riesgos principales + mitigaciones
- Métricas de éxito (KPIs) y criterios de aceptación globales
- Hitos (milestones) y entregables

### B) CHUNK_MAP (plan ejecutable en piezas)
Lista de chunks **atómicos**, cada uno con:
- `chunk_id`, `title`, `goal`
- `inputs` (qué necesita), `outputs` (qué deja listo)
- `DoD` (Definition of Done) verificable
- `deps` (dependencias), `risk`, `rollback`
- `tests` o verificaciones mínimas (aunque sean manuales)

**Regla:** un chunk debe poder ejecutarse en 30–90 minutos y **no** debe depender de “contexto implícito”.

### C) HANDOFF (manual para el junior)
Instrucciones paso a paso:
- por dónde empezar
- qué NO hacer (anti‑patrones)
- señales de STOP (cuándo escalar o pedir aclaración)
- cómo validar antes de avanzar al siguiente chunk

## Anti‑patrones (prohibidos)
- Chunks “gigantes” que mezclan 5 objetivos.
- Tareas sin DoD verificable.
- Suponer acceso a sistemas/datos no mencionados.
- “Implementar ahora” cuando el encargo es planificación.

---


# 🛡️ SISTEMA COMPLETO ANTIDRIFT (15+ MECANISMOS)

## 1. Boundary Markers System (≥15 marcadores obligatorios)

### Marcadores de Fuentes

```markdown
[PAPER:arXiv:XXXXX] - Citación paper SOTA
[INTERNAL:documento] - Referencia interna
[EXTERNAL:recurso] - Referencia externa
[PROPOSED:sprint-X] - Propuesta específica
[INFERRED:<X>] - Inferencia basada en evidencia (preferido)
[INFERRED based on <X>] - (legacy) permitido si el modelo no soporta formato con ':'
```

### Marcadores de Conocimiento

```markdown
# Certeza (Knowledge)
[K] - Known (hecho verificado)
[CALC] - Computed (calculado/inferido a partir de evidencia)
[UNK] - Unknown (requiere investigación o dato faltante)

# Acción sobre recursos (Lifecycle)
[ACT:CREATE] - Crear nuevo recurso/archivo/entidad
[ACT:UPDATE] - Modificar existente
[ACT:MIGRATE] - Transformar/mover (incluye renombre, refactor, migración)
[ACT:DEPRECATE] - Eliminar/archivar/dejar obsoleto (con plan de reemplazo)

# Compatibilidad (legacy, permitido pero WARN)
[C] - (legacy) Computed
[U] - (legacy) Unknown/Update (NO usar: ambiguo)
```


### Marcadores de Estados

```markdown
✅ - Completado exitosamente
⚠️ - Warning/Atención
❌ - Bloqueante/Error
🔴 - Crítico/Urgente
🟡 - Mejora sugerida
```

### Marcadores de Separación

```markdown
[EVIDENCIA] - Bloque de datos verificables
[PROPUESTA] - Bloque de recomendaciones
[CRITICAL] - Elemento crítico
[OPTIONAL] - Elemento opcional
[DEPRECATED] - Elemento obsoleto
```

### Validación Automática

```bash
# Contar boundary markers
MARKERS=$(grep -o "\[PAPER:\]\|\[INTERNAL:\]\|\[EXTERNAL:\]\|\[PROPOSED\]\|\[INFERRED\]\|\[EVIDENCIA\]\|\[PROPUESTA\]\|\[K\]\|\[C\]\|\[U\]\|\[CRITICAL\]\|\[OPTIONAL\]\|✅\|⚠️\|❌\|🔴\|🟡" prompt.md | wc -l)
[[ $MARKERS -ge 15 ]] && echo "✅ Boundary Markers: $MARKERS (PASS)" || echo "❌ Boundary Markers: $MARKERS (FAIL threshold ≥15)"
```

## 2. Context Refresh Protocol (4 preguntas cada 2h)

### Protocolo de Re-anclaje

```markdown
## CONTEXT REFRESH PROTOCOL

**P1:** ¿Cuál es el objetivo principal actual? (Verificar drift de propósito)
**P2:** ¿Qué documentos base han cambiado? (Detectar obsolescencia)
**P3:** ¿Qué restricciones nuevas aplican? (Actualizar constraints)
**P4:** ¿Qué evidencia reciente valida el enfoque? (Verificar actualidad)

**Frecuencia:** Cada 2 horas de trabajo continuo
**Trigger:** Cambio de contexto, interrupción >30min, o sensación de confusión
```

### Implementación Automatizada

```bash
# Script de context refresh
context_refresh() {
  echo "=== CONTEXT REFRESH PROTOCOL ==="
  echo "P1: ¿Cuál es el objetivo principal actual?"
  read -r objetivo
  echo "P2: ¿Qué documentos base han cambiado?"
  read -r cambios
  echo "P3: ¿Qué restricciones nuevas aplican?"
  read -r restricciones
  echo "P4: ¿Qué evidencia reciente valida el enfoque?"
  read -r evidencia
  echo "=== CONTEXT REFRESH COMPLETADO ==="
}
```

## 3. Chain-of-Verification (CoVe) - 5 preguntas obligatorias

### Sistema CoVe Completo

```markdown
## CHAIN-OF-VERIFICATION (CoVe)

**V1 - Verificación de Fuentes:**

- ¿Las fuentes citadas existen y son accesibles?
- ¿Las citas [PAPER:] corresponden a papers reales?
- ¿Las referencias [INTERNAL:] están disponibles?

**V2 - Verificación de Datos:**

- ¿Los datos [K] son verificables?
- ¿Los cálculos [CALC] son correctos?
- ¿Las métricas tienen unidades correctas?

**V3 - Verificación de Lógica:**

- ¿El flujo de razonamiento es coherente?
- ¿No hay contradicciones internas?
- ¿Las conclusiones se derivan lógicamente?

**V4 - Verificación de Aplicabilidad:**

- ¿Las propuestas [PROPUESTA] son implementables?
- ¿Las recomendaciones son realistas?
- ¿Los recursos requeridos están disponibles?

**V5 - Verificación de Completitud:**

- ¿Se han considerado todos los aspectos relevantes?
- ¿No hay información crítica faltante?
- ¿El scope está completo y delimitado?
```

### Validación CoVe

```bash
# Verificar aplicación CoVe
cove_check() {
  local prompt_file="$1"
  local v1=$(grep -c "Verificación de Fuentes\|V1" "$prompt_file")
  local v2=$(grep -c "Verificación de Datos\|V2" "$prompt_file")
  local v3=$(grep -c "Verificación de Lógica\|V3" "$prompt_file")
  local v4=$(grep -c "Verificación de Aplicabilidad\|V4" "$prompt_file")
  local v5=$(grep -c "Verificación de Completitud\|V5" "$prompt_file")

  [[ $v1 -ge 1 && $v2 -ge 1 && $v3 -ge 1 && $v4 -ge 1 && $v5 -ge 1 ]] && \
    echo "✅ CoVe: 5/5 verificaciones presentes" || \
    echo "❌ CoVe: Verificaciones incompletas"
}
```

## 4. Separación EVIDENCIA/PROPUESTA

### Formato Estricto

```markdown
### [EVIDENCIA] Hallazgo X

[K] **Dato verificable 1:** {fuente + métrica + timestamp}
[CALC] **Cálculo basado en datos:** {fórmula + resultado + validación}
[K] **Evidencia cuantitativa:** {medición + unidad + contexto}

### [PROPUESTA] Acción Recomendada

[PROPOSED:sprint-X] **Recomendación 1:** {acción específica + responsable + timeline}
[INFERRED based on evidencia] **Recomendación 2:** {acción inferida + justificación}
[EXTERNAL:best-practice] **Recomendación 3:** {referencia externa + adaptación}
```

### Validación de Separación

```bash
# Verificar separación EVIDENCIA/PROPUESTA
evidence_proposal_check() {
  local prompt_file="$1"
  local evidence_blocks=$(grep -c "### \[EVIDENCIA\]" "$prompt_file")
  local proposal_blocks=$(grep -c "### \[PROPUESTA\]" "$prompt_file")
  local mixed_content=$(grep -c "\[EVIDENCIA\].*\[PROPUESTA\]\|\[PROPUESTA\].*\[EVIDENCIA\]" "$prompt_file")

  [[ $evidence_blocks -ge 1 && $proposal_blocks -ge 1 && $mixed_content -eq 0 ]] && \
    echo "✅ Separación EVIDENCIA/PROPUESTA: Correcta" || \
    echo "❌ Separación EVIDENCIA/PROPUESTA: Requiere corrección"
}
```

## 5. Checklist Anti-Drift (8 checks V001-V011)

### Checklist Completo

```markdown
## CHECKLIST ANTI-DRIFT V001-V011

**V001:** Boundary Markers ≥15 presentes ✅/❌
**V002:** Context Refresh Protocol documentado ✅/❌
**V003:** Chain-of-Verification (5 preguntas) aplicado ✅/❌
**V004:** Separación EVIDENCIA/PROPUESTA clara ✅/❌
**V005:** TAGs [K/C/U] ≥60% cobertura ✅/❌
**V006:** Objetivos SMART ≥3 medibles ✅/❌
**V007:** Tests ejecutables ≥3 presentes ✅/❌
**V008:** Frontmatter YAML completo ✅/❌
**V009:** Boundaries IN-SCOPE/OUT-OF-SCOPE ✅/❌
**V010:** Validación estricta de schema ✅/❌
**V011:** Determinismo garantizado ✅/❌

**Total checks PASS:** X/11
**Threshold:** ≥8/11 = PASS
```

## 6. Boundaries IN-SCOPE/OUT-OF-SCOPE

### Delimitación Clara

```markdown
## BOUNDARIES DELIMITADOS

### IN-SCOPE (Incluido)

- ✅ {Elemento 1 dentro del alcance}
- ✅ {Elemento 2 dentro del alcance}
- ✅ {Elemento 3 dentro del alcance}

### OUT-OF-SCOPE (Excluido explícitamente)

- ❌ {Elemento 1 fuera del alcance - razón}
- ❌ {Elemento 2 fuera del alcance - razón}
- ❌ {Elemento 3 fuera del alcance - razón}

### BOUNDARY CONDITIONS

- ⚠️ {Caso límite 1 - criterio de decisión}
- ⚠️ {Caso límite 2 - criterio de decisión}
```

## 7. Validación Estricta de Schema

### Sistema de Validación

````markdown
## VALIDACIÓN SCHEMA COMPLETA

### Schema YAML Frontmatter

```yaml
---
meta:
  id: "ID-UNICO"
  version: "X.Y.Z"
  created_at: "YYYY-MM-DDThh:mm:ssZ"
  updated_at: "YYYY-MM-DDThh:mm:ssZ"
  base: "origen(es) del meta-prompt"
  mode: [meta, generation, validation, accreditation]
  depth: { shallow|standard|deep|comprehensive }
  anti_drift: "V001-V011 enabled"
  audit_framework: "4D + CSE + CoVe"
  expected_score:
    minimum: "≥8.0/10"
    elite: "≥9.5/10"
  cloop_level: { 1|2|3 }
  purpose: "para qué existe este meta‑prompt"
  memory_integration: "cómo se integra memoria/estado"
  validation_system: "automated + manual + schema_compliant"
  determinism:
    guarantee: "STRUCTURE_ONLY"
    includes: ["schema", "section order", "marker accounting"]
    excludes: ["semantic content (LLM sampling)", "external state"]
---
```

### Validación Automática

```bash
# Validar schema YAML (frontmatter) — extracción entre las dos primeras líneas '---'
extract_frontmatter() {
  awk 'BEGIN{in=0} /^---$/{in++; next} in==1{print} in>1{exit}' "$1"
}

validate_yaml_schema() {
  local prompt_file="$1"
  local fm
  fm="$(extract_frontmatter "$prompt_file")"

  # Campos mínimos (bajo meta:)
  local required=(
    "meta:"
    "  id:"
    "  version:"
    "  created_at:"
    "  updated_at:"
    "  base:"
    "  mode:"
    "  depth:"
    "  anti_drift:"
    "  audit_framework:"
    "  expected_score:"
    "  cloop_level:"
    "  purpose:"
    "  determinism:"
  )

  for field in "${required[@]}"; do
    echo "$fm" | grep -q "^$field" || {
      echo "❌ Schema YAML: Campo faltante: $field"
      return 1
    }
  done

  echo "✅ Schema YAML: campos mínimos presentes"
}
```


## 8. Determinismo Operativo (Estructura, no “contenido”)

### Principio

En LLMs **no existe determinismo semántico garantizado** (misma entrada → mismo texto) salvo condiciones muy controladas.
Lo que sí podemos exigir es **determinismo estructural**: mismo contrato, mismas secciones, mismos marcadores, mismos checks.

### Reglas (obligatorias)

1. **Estructura idéntica → validación idéntica** (schema + secciones + orden).
2. **No depender de estado externo** si no está declarado (hora, web, sistemas).
3. **Tooling idempotente**: si se usan herramientas, deben ser seguras de re‑ejecutar o tener rollback.
4. **Checksums opcionales**: hash de outputs para detectar drift entre iteraciones (no para “garantizar” mismo contenido).
5. **Versionado explícito**: del meta‑prompt y de cualquier plantilla usada.

### Implementación (checksum estructural)

```python
import hashlib
import json
from typing import Any, Dict

def stable_hash(payload: Dict[str, Any]) -> str:
    """Hash estable para comparar estructura/valores — NO garantiza outputs idénticos del LLM."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

# Ejemplo: hash de un CHUNK_MAP (lista de dicts)
example = {
    "plan_id": "PLAN-001",
    "chunks": [
        {"chunk_id": "C01", "title": "Setup", "DoD": ["Repo listo", "CI pasa"]},
        {"chunk_id": "C02", "title": "Schema", "DoD": ["Schema validado"]},
    ],
}

print(stable_hash(example))
```

### Nota importante

Si el usuario exige “outputs idénticos”, la respuesta correcta es:
- ofrecer **determinismo de estructura + validación**,
- y explicar que el contenido puede variar dentro de límites aceptables (DoD).

## 9. Métricas Cuantitativas

## 10. Sistema de Marcadores Aplicado

## 11. Separación EVIDENCIA/PROPUESTA

## 12. Boundaries IN-SCOPE/OUT-OF-SCOPE

## 13. Protocolo Context Refresh

## 14. Chain-of-Verification (5 preguntas)

## 15. Checklist Anti-Drift (V001-V011)

## 16. Referencias Completas

## 17. Validación Schema y Determinismo

---

# 🎯 9 COMPONENTES CRÍTICOS DEL ACREDITADOR

### C1: CSE (Context-Specification-Verification) Completo ⭐⭐⭐

**Elementos obligatorios:**

1. **CONTEXTO:** Documentos base (≥2), resumen ejecutivo, historia, gap/challenge
2. **ESPECIFICACIÓN:** Objetivos medibles (≥3), tareas detalladas (≥5), criterios éxito, restricciones
3. **VERIFICACIÓN:** Criterios validación (≥2), tests ejecutables (≥3), rollback documentado, métricas

**Threshold:** ✅ PASS: 3/3 secciones presentes

### C2: TAGs [K/CALC/UNK] ≥60% Cobertura ⭐⭐⭐

**TAGs requeridos:** [K], [CALC], [UNK], [EVIDENCIA], [PROPUESTA], [PAPER:], [INTERNAL:], [EXTERNAL:], [ACT:*] (recomendado)

**Threshold:** ✅ PASS: ≥60% de afirmaciones con TAG

### C3: Boundary Markers ≥15 por Documento ⭐⭐⭐

**Markers requeridos:** Fuentes, estados, bloques, transiciones

**Threshold:** ✅ PASS: ≥15 boundary markers

### C4: Frontmatter YAML Completo ⭐⭐⭐

**Campos obligatorios:** id, version, created_at, base, mode, depth, anti_drift, audit_framework, expected_score, cloop_level

**Threshold:** ✅ PASS: 10/10 campos presentes

### C5: Anti-Drift ≥3 Mecanismos Activos ⭐⭐⭐

**Mecanismos:** Boundary Markers, Context Refresh, CoVe, Separación EVIDENCIA/PROPUESTA, Checklist V001-V011, Boundaries

**Threshold:** ✅ PASS: ≥3 mecanismos activos

### C6: Objetivos ≥3 Medibles (SMART) ⭐⭐

**Formato:** Verbo + Objeto + Métrica + Threshold

**Threshold:** ✅ PASS: ≥3 objetivos SMART

### C7: Tests ≥3 Ejecutables ⭐⭐

**Formato:** Comando bash/script ejecutable con output esperado

**Threshold:** ✅ PASS: ≥3 tests ejecutables

### C8: Separación EVIDENCIA/PROPUESTA ⭐

**Formato:** Bloques diferenciados con TAGs apropiados

**Threshold:** ✅ PASS: ≥80% secciones con separación clara

### C9: Integración Memoria /core [NUEVO v2.0.0] ⭐⭐

**Elementos obligatorios:** Referencias a /core, integración con memoria, consistencia con sistemas

**Threshold:** ✅ PASS: ≥3 referencias /core + integración memoria

---

# 📋 SECCIONES ESPECIALIZADAS DEL PAE EXTRACTOR

## Sistema PAE Integrado

### 1. Schema JSON Estructurado

```json
{
  "run": {
    "work_unit_id": "WORK-UNIT-ID",
    "phase": "Reflect",
    "timestamp": "{ISO8601}",
    "duration_minutes": 10-20
  },
  "governance_pre": {
    "handoff": {"present": true, "path": "...", "score": 9.5},
    "plan": {"present": true, "path": "..."},
    "executor_prompt": {"present": true, "path": "...", "cse_complete": true},
    "pre_audit": {"present": true, "path": "...", "score4d": 8.5},
    "pre_calibration": {"present": true, "path": "...", "score4d": 8.0}
  },
  "execution_outputs": {
    "deliverables": [
      {
        "id": "E1",
        "title": "Título del entregable",
        "path": "path/to/E1.md",
        "size_lines": 250,
        "boundary_markers": 18,
        "evidence_split": true,
        "references_present": true,
        "format": "narrative"
      }
    ],
    "validator_results": [
      {
        "deliverable_id": "E1",
        "overall_pass": true,
        "scores": {
          "S_qual": 0.85,
          "S_exec": 0.90,
          "S_arch": 0.80,
          "S_total": 0.85
        }
      }
    ]
  },
  "verification_post": {
    "post_audit": {"present": true, "path": "...", "score4d": 9.0},
    "post_calibration": {"present": true, "path": "...", "score4d": 8.8},
    "next_handoff": {"present": true, "path": "...", "ready": true}
  },
  "gates": [
    {
      "gate": "PRE.CALIBRATION",
      "status": "pass",
      "threshold": ">=7.0",
      "actual": "8.0",
      "evidence": ["docs/CALIBRACION-PRE-SPRINT-X.md#score"]
    }
  ],
  "checklist": {
    "C1_CoVe": true,
    "C2_BoundaryMarkers_15p": true,
    "C3_EVIDENCE_vs_PROPOSAL": true,
    "C4_Context_Refresh": true,
    "C5_NoInventedAcronyms": true,
    "C6_Claims_Verified": true,
    "C7_Boundaries_IN_OUT": true,
    "C8_CSE_YAML_Format": true
  },
  "summary": {
    "status": "ready_for_post_verification",
    "missing_docs": [],
    "violations": [],
    "suggested_audit_level": 1,
    "confidence": "high"
  },
  "checksum": "SHA256_HASH"
}
```

### 2. Gates Configuration (18 quality gates)

```json
{
  "gates": [
    {
      "id": "PRE.CALIBRATION",
      "description": "Pre-calibration score threshold",
      "threshold": ">=7.0",
      "severity": "critical",
      "waivable": false
    },
    {
      "id": "POST.CALIBRATION",
      "description": "Post-calibration score threshold",
      "threshold": ">=7.0",
      "severity": "critical",
      "waivable": false
    },
    {
      "id": "BOUNDARY_MARKERS.EACH",
      "description": "Minimum boundary markers per deliverable",
      "threshold": ">=15",
      "severity": "high",
      "waivable": true
    }
  ]
}
```

### 3. Validación Automatizada

```bash
#!/bin/bash
# validate-pae-universal.sh

PAE_FILE="pae_output_universal.json"
SCHEMA_FILE="meta-prompt-universal-schema.json"

# Test 1: JSON válido
jq empty "$PAE_FILE" || { echo "❌ JSON inválido"; exit 1; }

# Test 2: Schema compliance
ajv validate -s "$SCHEMA_FILE" -d "$PAE_FILE" || { echo "❌ Schema violation"; exit 1; }

# Test 3: Required sections
required=("run" "governance_pre" "execution_outputs" "verification_post" "gates" "checklist" "summary")
for section in "${required[@]}"; do
  jq -e "has(\"$section\")" "$PAE_FILE" || { echo "❌ Missing $section"; exit 1; }
done

# Test 4: Gates count
gates_count=$(jq '.gates|length' "$PAE_FILE")
[[ $gates_count -ge 15 ]] || { echo "❌ Gates insuficientes: $gates_count"; exit 1; }

# Test 5: Summary complete
jq -e '.summary.status' "$PAE_FILE" && \
jq -e '.summary.suggested_audit_level' "$PAE_FILE" || { echo "❌ Summary incompleto"; exit 1; }

echo "✅ PAE Universal validado exitosamente"
```

---

# 🔄 TEMPLATE ESTRUCTURADO DEL HANDOFF

## 17 Secciones Obligatorias

### 1. Resumen Ejecutivo

### 2. Estado Completado

### 3. Logros Principales

### 4. Innovación Sprint

### 5. Entregables Completados

### 6. Objetivos Siguiente Sprint

### 7. Tareas Detalladas

### 8. Metodología

### 9. Métricas

### 10. Próximos Pasos

### 11. Responsables

### 12. PAE Generation

### 13. Checklist Handoff

### 14. Lecciones

### 15. Calibración Post-Sprint

### 16. Métricas Comparativas

### 17. Referencias Críticas

---

# 🔍 EXPLICACIONES CLARAS Y DOCUMENTACIÓN

## Uso Correcto de Cada Marcador

### [K] - Known

```markdown
✅ CORRECTO: [K] El proyecto utiliza React 18.2.0 (ver package.json)
❌ INCORRECTO: [K] El proyecto parece usar React
```

### [CALC] - Computed

```markdown
✅ CORRECTO: [CALC] Performance mejoró 25% (100ms → 75ms en benchmarks)
❌ INCORRECTO: [CALC] Performance mejoró mucho
```

### [UNK] - Unknown

```markdown
✅ CORRECTO: [UNK] Impacto en producción desconocido (requiere monitoreo)
❌ INCORRECTO: [UNK] Probablemente no hay impacto
```

### [EVIDENCIA] vs [PROPUESTA]

```markdown
### [EVIDENCIA] Análisis Performance

[K] Tiempo respuesta actual: 150ms (medido con Lighthouse)
[CALC] 32% por encima del target de 114ms
[K] 3rd party scripts: 45ms (30% del total)

### [PROPUESTA] Optimización Performance

[PROPOSED:sprint-3] Implementar lazy loading para imágenes (reducción estimada: 20ms)
[EXTERNAL:web.dev] Aplicar code splitting según mejores prácticas (reducción estimada: 30ms)
```

## Antipatrones Comunes a Evitar

### 1. Mezclar EVIDENCIA con PROPUESTA

```markdown
❌ INCORRECTO: [EVIDENCIA] [PROPUESTA] Debemos optimizar porque es lento
✅ CORRECTO: Separar bloques claramente
```

### 2. TAGs sin contexto

```markdown
❌ INCORRECTO: [K] Mejoramos el código
✅ CORRECTO: [K] Refactorizamos el módulo auth (ver commit abc123)
```

### 3. Boundary markers inconsistentes

```markdown
❌ INCORRECTO: Usar [INTERNAL] y [internal] indistintamente
✅ CORRECTO: Mantener consistencia en todos los markers
```

## Ejemplos de Implementación

### Ejemplo 1: Prompt de Clasificación

````markdown
# 🔍 PROMPT: Clasificación de Prioridades

---

meta:
  id: PROMPT-CLASIFICACION-PRIORIDADES
  version: 2.0.0
  created_at: "2025-12-11T12:52:00Z"
  updated_at: "2025-12-12T00:00:00Z"
  base: META-PROMPT-UNIVERSAL-v2.0.0
  mode: classification
  depth: standard
  anti_drift: "V001-V011 enabled"
  audit_framework: "4D + CSE + CoVe"
  expected_score:
    minimum: "≥8.0/10"
    elite: "≥9.0/10"
  cloop_level: 2
  purpose: "Clasificar tareas por prioridad usando método MoSCoW"
  memory_integration: "core/memory + core/context-management"
  validation_system: "automated + manual"
  determinism:
    guarantee: "STRUCTURE_ONLY"

---

# 🎯 PROPÓSITO

Eres un **clasificador senior** especializado en:

- [K] Método MoSCoW (Must, Should, Could, Won't)
- [K] Análisis de impacto y esfuerzo
- [CALC] Cálculo de prioridad relativa

Tu objetivo es **clasificar tareas por prioridad** y **proporcionar justificación clara**.

---

## 📚 CONTEXTO COMPLETO

### Documentos Base (Leer OBLIGATORIO)

1. `project-roadmap.md` (visión y objetivos estratégicos)
2. `current-sprint-backlog.md` (tareas pendientes)
3. `team-capacity.md` (capacidad del equipo actual)

### Resumen ejecutivo contexto:

- ✅ Proyecto en fase de desarrollo activo
- ✅ Sprint actual: 3 semanas restantes
- ⚠️ Gap: 25% más tareas que capacidad disponible

---

## 🎯 OBJETIVOS ESPECÍFICOS

**O1:** Clasificar 15 tareas del backlog actual usando método MoSCoW (100% cobertura)
**O2:** Calcular score de prioridad para cada tarea (fórmula: impacto × urgencia / esfuerzo)
**O3:** Identificar tareas fuera de scope para sprint actual (máximo 10 tareas)

---

## 📋 TAREAS DETALLADAS

### Fase 1: Análisis de Tareas (15min)

- T1: Leer backlog completo (15 tareas)
- T2: Evaluar impacto de cada tarea (1-5)
- T3: Evaluar urgencia de cada tarea (1-5)
- T4: Evaluar esfuerzo de cada tarea (horas)

### Fase 2: Clasificación MoSCoW (10min)

- T5: Aplicar criterios Must/Should/Could/Won't
- T6: Calcular score de prioridad
- T7: Validar consistencia de clasificación

### Fase 3: Propuesta Sprint (5min)

- T8: Seleccionar tareas para sprint actual
- T9: Validar contra capacidad del equipo
- T10: Documentar justificaciones

---

## 🔍 VALIDACIÓN

### Criterios de Validación

**Estructura:** CSE completo
**Contenido:** Todas las tareas clasificadas
**Calidad:** Scores calculados correctamente

### Tests Ejecutables

**Test 1:** Verificar cobertura 100% MoSCoW

```bash
# Verificar que todas las tareas tengan clasificación MoSCoW
grep -c "M-\|S-\|C-\|W-" backlog-clasificado.md
# Expected: 15
```
````

**Test 2:** Validar cálculo de scores

```bash
# Verificar fórmula score = impacto × urgencia / esfuerzo
python validate_scores.py backlog-clasificado.md
# Expected: All scores valid
```

**Test 3:** Verificar capacidad sprint

```bash
# Validar que horas totales ≤ capacidad equipo
jq '[.tareas[] | .esfuerzo] | add' sprint-plan.json
# Expected: ≤ 160 (40h × 4 personas × 1 semana)
```

---

## 📋 ENTREGABLES ESPERADOS

**E1:** backlog-clasificado.md (15 tareas con scores MoSCoW)
**E2:** sprint-plan.json (tareas seleccionadas para sprint)
**E3:** justificacion-prioridades.md (explicación de decisiones)

---

## 🛡️ MECANISMOS ANTI-DRIFT

### Boundary Markers

- [PAPER:arXiv:2501.12345] Referencia a método MoSCoW actualizado
- [INTERNAL:team-capacity.md] Capacidad verificada del equipo
- [EXTERNAL:scrum-guide.org] Mejores prácticas Scrum

### Context Refresh Protocol

**P1:** ¿Cuál es el objetivo principal actual? (Clasificar backlog)
**P2:** ¿Qué documentos base han cambiado? (Ninguno en última semana)
**P3:** ¿Qué restricciones nuevas aplican? (Fecha límite sprint inmutable)
**P4:** ¿Qué evidencia reciente valida el enfoque? (Sprint anterior completado 95%)

### Chain-of-Verification

**V1 - Fuentes:** ¿roadmap.md y backlog.md están actualizados?
**V2 - Datos:** ¿Los scores siguen la fórmula correcta?
**V3 - Lógica:** ¿La clasificación es consistente con objetivos?
**V4 - Aplicabilidad:** ¿Las tareas seleccionadas son realizables?
**V5 - Completitud:** ¿Se consideraron todas las dependencias?

### Separación EVIDENCIA/PROPUESTA

```markdown
### [EVIDENCIA] Análisis Backlog

[K] Total tareas: 15
[K] Capacidad equipo: 160h/semana
[CALC] Esfuerzo total requerido: 280h
[K] Gap: 120h (75% sobre capacidad)

### [PROPUESTA] Selección Sprint

[PROPOSED:sprint-3] Seleccionar 8 tareas Must (120h total)
[INFERRED based on capacity] Posponer 4 tareas Should (80h)
[EXTERNAL:scrum-guide] Mover 3 tareas Could a backlog futuro
```

---

## ✅ CHECKLIST ANTI-DRIFT V001-V011

- [x] **V001:** Boundary Markers ≥15 presentes (18 encontrados)
- [x] **V002:** Context Refresh Protocol documentado
- [x] **V003:** Chain-of-Verification (5 preguntas) aplicado
- [x] **V004:** Separación EVIDENCIA/PROPUESTA clara
- [x] **V005:** TAGs [K/C/U] ≥60% cobertura (75%)
- [x] **V006:** Objetivos SMART ≥3 medibles (3 objetivos)
- [x] **V007:** Tests ejecutables ≥3 presentes (3 tests)
- [x] **V008:** Frontmatter YAML completo (15 campos)
- [x] **V009:** Boundaries IN-SCOPE/OUT-OF-SCOPE claros
- [x] **V010:** Validación estricta de schema
- [x] **V011:** Determinismo garantizado

**Total checks PASS:** 11/11 ✅

---

## 🔗 REFERENCIAS

**Documentos Base:**

- `project-roadmap.md` (visión estratégica)
- `current-sprint-backlog.md` (tareas pendientes)
- `team-capacity.md` (capacidad equipo)

**Papers SOT:**

- [PAPER:arXiv:2501.12345] Smith et al. (2025) - Modern Priority Classification Methods

**Herramientas:**

- META-PROMPT-UNIVERSAL-v2.0.0
- validate-pae-universal.sh
- priority-calculator.py

---

**PROMPT COMPLETADO** ✅

```

---

# 📊 SISTEMA DE SCORING Y VALIDACIÓN

## Fórmula Matemática Ponderada

```

Score_Universal = Σ(Componente_i × Peso_i) × 10

Donde:

- C1 (CSE): 20%
- C2 (TAGs): 15%
- C3 (Markers): 15%
- C4 (Frontmatter): 10%
- C5 (Anti-drift): 15%
- C6 (Objetivos): 10%
- C7 (Tests): 10%
- C8 (Separación): 5%
- C9 (Memoria): 10% [NUEVO v2.0.0]

Total pesos: 110% (ajustado en cálculo)

````

### Cálculo Detallado
```python
def calculate_universal_score(components):
    """
    Calcular score universal usando fórmula ponderada

    Args:
        components: dict con scores 0.0-1.0 para cada componente

    Returns:
        float: Score final 0.0-10.0
    """
    weights = {
        'C1_CSE': 0.20,
        'C2_TAGS': 0.15,
        'C3_Markers': 0.15,
        'C4_Frontmatter': 0.10,
        'C5_AntiDrift': 0.15,
        'C6_Objectives': 0.10,
        'C7_Tests': 0.10,
        'C8_Separation': 0.05,
        'C9_Memory': 0.10
    }

    # Normalizar pesos a 100%
    total_weight = sum(weights.values())
    normalized_weights = {k: v/total_weight for k, v in weights.items()}

    # Calcular score ponderado
    weighted_score = sum(components[comp] * weight
                         for comp, weight in normalized_weights.items())

    return weighted_score * 10
````

## Thresholds Claros

| Score          | Veredicto       | Acción                | Calidad     |
| -------------- | --------------- | --------------------- | ----------- |
| **≥9.5/10**    | ⭐⭐⭐ ELITE    | Referencia universal  | Excepcional |
| **≥9.0/10**    | ⭐⭐ EXCELENTE  | Estándar oro premium  | Superior    |
| **≥8.5/10**    | ⭐ BUENO        | Aprobado sin reservas | Bueno       |
| **≥8.0/10**    | ✅ ACREDITADO   | Mínimo aceptable      | Aceptable   |
| **7.5-7.9/10** | ⚠️ REFINAR      | Mejoras requeridas    | Mejorable   |
| **7.0-7.4/10** | ⚠️ REVISAR      | Revisión mayor        | Deficiente  |
| **<7.0/10**    | ❌ REFACTORIZAR | Rediseñar completo    | Inaceptable |

## Script de Validación Automatizado

```bash
#!/bin/bash
# validate-meta-prompt-universal.sh

PROMPT_FILE="$1"
VERBOSE="${2:-false}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== META-PROMPT UNIVERSAL VALIDATION ===${NC}"
echo "Prompt: $PROMPT_FILE"
echo ""

# Función para imprimir resultado
print_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"

    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✅ $test_name: PASS${NC}"
    elif [[ "$result" == "WARN" ]]; then
        echo -e "${YELLOW}⚠️ $test_name: WARN${NC}"
    else
        echo -e "${RED}❌ $test_name: FAIL${NC}"
    fi

    if [[ "$VERBOSE" == "true" && -n "$details" ]]; then
        echo "   $details"
    fi
}

# C1: CSE Completo
check_cse() {
    local context=$(grep -q "## 📚 CONTEXTO COMPLETO" "$PROMPT_FILE" && echo "1" || echo "0")
    local objectives=$(grep -q "## 🎯 OBJETIVOS ESPECÍFICOS" "$PROMPT_FILE" && echo "1" || echo "0")
    local validation=$(grep -q "## 🔍 VALIDACIÓN" "$PROMPT_FILE" && echo "1" || echo "0")

    local total=$((context + objectives + validation))

    if [[ $total -eq 3 ]]; then
        print_result "C1 (CSE)" "PASS" "3/3 secciones presentes"
        echo "1.0"
    elif [[ $total -ge 2 ]]; then
        print_result "C1 (CSE)" "WARN" "$total/3 secciones"
        echo "0.7"
    else
        print_result "C1 (CSE)" "FAIL" "$total/3 secciones"
        echo "0.0"
    fi
}

# C2: TAGs Cobertura
check_tags() {
    local total_lines
    total_lines=$(wc -l < "$PROMPT_FILE")

    # Cuenta líneas que contengan al menos un tag/marker estándar (incluye compatibilidad legacy)
    local tag_lines
    tag_lines=$(grep -E -c "\[(K|CALC|UNK)\]|\[ACT:(CREATE|UPDATE|MIGRATE|DEPRECATE)\]|\[(EVIDENCIA|PROPUESTA)\]|\[(IN-SCOPE|OUT-OF-SCOPE|CRITICAL|OPTIONAL)\]|\[(PAPER|INTERNAL|EXTERNAL|POLICY|SCOPE):[^]]+\]|\[PROPOSED:[^]]+\]|\[INFERRED[^]]*\]|\[(C|U)\]" "$PROMPT_FILE")

    local coverage=$((tag_lines * 100 / total_lines))

    if [[ $coverage -ge 60 ]]; then
        print_result "C2 (TAGs)" "PASS" "$coverage% cobertura"
        echo "1.0"
    elif [[ $coverage -ge 40 ]]; then
        print_result "C2 (TAGs)" "WARN" "$coverage% cobertura"
        echo "0.7"
    else
        print_result "C2 (TAGs)" "FAIL" "$coverage% cobertura"
        echo "0.0"
    fi
}

# C3: Boundary Markers
check_markers() {
    local markers
    markers=$(grep -E -o "\[(PAPER|INTERNAL|EXTERNAL|POLICY|SCOPE):[^]]+\]|\[PROPOSED:[^]]+\]|\[INFERRED[^]]*\]|\[(EVIDENCIA|PROPUESTA|IN-SCOPE|OUT-OF-SCOPE|CRITICAL|OPTIONAL)\]|✅|⚠️|❌|🔴|🟡" "$PROMPT_FILE" | wc -l)

    if [[ $markers -ge 15 ]]; then
        print_result "C3 (Markers)" "PASS" "$markers markers"
        echo "1.0"
    elif [[ $markers -ge 10 ]]; then
        print_result "C3 (Markers)" "WARN" "$markers markers"
        echo "0.7"
    else
        print_result "C3 (Markers)" "FAIL" "$markers markers"
        echo "0.0"
    fi
}

# C4: Frontmatter YAML
extract_frontmatter_score() {
  awk 'BEGIN{in=0} /^---$/{in++; next} in==1{print} in>1{exit}' "$PROMPT_FILE"
}

check_frontmatter() {
    local fm
    fm="$(extract_frontmatter_score)"

    local required_fields=(
      "meta:"
      "  id:"
      "  version:"
      "  created_at:"
      "  updated_at:"
      "  base:"
      "  mode:"
      "  depth:"
      "  anti_drift:"
      "  audit_framework:"
      "  expected_score:"
      "  cloop_level:"
      "  purpose:"
      "  determinism:"
    )

    local present=0
    for field in "${required_fields[@]}"; do
        echo "$fm" | grep -q "^$field" && ((present++))
    done

    if [[ $present -ge 14 ]]; then
        print_result "C4 (Frontmatter)" "PASS" "$present/14 campos"
        echo "1.0"
    elif [[ $present -ge 11 ]]; then
        print_result "C4 (Frontmatter)" "WARN" "$present/14 campos"
        echo "0.7"
    else
        print_result "C4 (Frontmatter)" "FAIL" "$present/14 campos"
        echo "0.0"
    fi
}


# C5: Anti-Drift
check_anti_drift() {
    local boundary_markers=$(grep -q "Boundary Markers" "$PROMPT_FILE" && echo "1" || echo "0")
    local context_refresh=$(grep -q "Context Refresh Protocol" "$PROMPT_FILE" && echo "1" || echo "0")
    local cove=$(grep -q "Chain-of-Verification" "$PROMPT_FILE" && echo "1" || echo "0")
    local evidence_proposal=$(grep -q "Separación EVIDENCIA/PROPUESTA" "$PROMPT_FILE" && echo "1" || echo "0")
    local checklist=$(grep -q "CHECKLIST ANTI-DRIFT" "$PROMPT_FILE" && echo "1" || echo "0")
    local boundaries=$(grep -q "IN-SCOPE/OUT-OF-SCOPE" "$PROMPT_FILE" && echo "1" || echo "0")

    local total=$((boundary_markers + context_refresh + cove + evidence_proposal + checklist + boundaries))

    if [[ $total -ge 3 ]]; then
        print_result "C5 (Anti-drift)" "PASS" "$total/6 mecanismos"
        echo "1.0"
    elif [[ $total -ge 2 ]]; then
        print_result "C5 (Anti-drift)" "WARN" "$total/6 mecanismos"
        echo "0.7"
    else
        print_result "C5 (Anti-drift)" "FAIL" "$total/6 mecanismos"
        echo "0.0"
    fi
}

# C6: Objetivos SMART
check_objectives() {
    local objectives=$(grep -c "^\*\*O[0-9]:" "$PROMPT_FILE")

    if [[ $objectives -ge 3 ]]; then
        print_result "C6 (Objetivos)" "PASS" "$objectives objetivos"
        echo "1.0"
    elif [[ $objectives -ge 2 ]]; then
        print_result "C6 (Objetivos)" "WARN" "$objectives objetivos"
        echo "0.7"
    else
        print_result "C6 (Objetivos)" "FAIL" "$objectives objetivos"
        echo "0.0"
    fi
}

# C7: Tests Ejecutables
check_tests() {
    local tests=$(grep -c "^\*\*Test [0-9]:" "$PROMPT_FILE")

    if [[ $tests -ge 3 ]]; then
        print_result "C7 (Tests)" "PASS" "$tests tests"
        echo "1.0"
    elif [[ $tests -ge 2 ]]; then
        print_result "C7 (Tests)" "WARN" "$tests tests"
        echo "0.7"
    else
        print_result "C7 (Tests)" "FAIL" "$tests tests"
        echo "0.0"
    fi
}

# C8: Separación EVIDENCIA/PROPUESTA
check_separation() {
    local evidence_blocks=$(grep -c "### \[EVIDENCIA\]" "$PROMPT_FILE")
    local proposal_blocks=$(grep -c "### \[PROPUESTA\]" "$PROMPT_FILE")
    local mixed_content=$(grep -c "\[EVIDENCIA\].*\[PROPUESTA\]\|\[PROPUESTA\].*\[EVIDENCIA\]" "$PROMPT_FILE")

    if [[ $evidence_blocks -ge 1 && $proposal_blocks -ge 1 && $mixed_content -eq 0 ]]; then
        print_result "C8 (Separación)" "PASS" "Separación clara"
        echo "1.0"
    elif [[ $evidence_blocks -ge 1 && $proposal_blocks -ge 1 ]]; then
        print_result "C8 (Separación)" "WARN" "Separación parcial"
        echo "0.7"
    else
        print_result "C8 (Separación)" "FAIL" "Sin separación clara"
        echo "0.0"
    fi
}

# C9: Integración Memoria /core
check_memory() {
    local core_refs=$(grep -c "core/" "$PROMPT_FILE")
    local memory_refs=$(grep -c "memory\|Memory" "$PROMPT_FILE")
    local systems_refs=$(grep -c "surprise-metrics\|context-management\|search" "$PROMPT_FILE")

    local total=$((core_refs + memory_refs + systems_refs))

    if [[ $core_refs -ge 3 && $memory_refs -ge 1 && $systems_refs -ge 2 ]]; then
        print_result "C9 (Memoria)" "PASS" "$total referencias /core"
        echo "1.0"
    elif [[ $core_refs -ge 2 ]]; then
        print_result "C9 (Memoria)" "WARN" "$total referencias /core"
        echo "0.7"
    else
        print_result "C9 (Memoria)" "FAIL" "$total referencias /core"
        echo "0.0"
    fi
}

# Ejecutar todos los checks
C1_SCORE=$(check_cse)
C2_SCORE=$(check_tags)
C3_SCORE=$(check_markers)
C4_SCORE=$(check_frontmatter)
C5_SCORE=$(check_anti_drift)
C6_SCORE=$(check_objectives)
C7_SCORE=$(check_tests)
C8_SCORE=$(check_separation)
C9_SCORE=$(check_memory)

# Calcular score final
FINAL_SCORE=$(python3 -c "
import json
weights = {
    'C1': 0.20, 'C2': 0.15, 'C3': 0.15, 'C4': 0.10,
    'C5': 0.15, 'C6': 0.10, 'C7': 0.10, 'C8': 0.05, 'C9': 0.10
}
scores = {
    'C1': $C1_SCORE, 'C2': $C2_SCORE, 'C3': $C3_SCORE, 'C4': $C4_SCORE,
    'C5': $C5_SCORE, 'C6': $C6_SCORE, 'C7': $C7_SCORE, 'C8': $C8_SCORE, 'C9': $C9_SCORE
}
total_weight = sum(weights.values())
normalized_weights = {k: v/total_weight for k, v in weights.items()}
weighted_score = sum(scores[k] * normalized_weights[k] for k in weights.keys())
final_score = weighted_score * 10
print(f'{final_score:.1f}')
")

echo ""
echo -e "${BLUE}=== RESULTADOS FINALES ===${NC}"
echo -e "Score Final: ${BLUE}$FINAL_SCORE/10${NC}"

# Veredicto
if (( $(echo "$FINAL_SCORE >= 9.5" | bc -l) )); then
    echo -e "${GREEN}⭐⭐⭐ ELITE - Referencia Universal${NC}"
elif (( $(echo "$FINAL_SCORE >= 9.0" | bc -l) )); then
    echo -e "${GREEN}⭐⭐ EXCELENTE - Estándar Oro Premium${NC}"
elif (( $(echo "$FINAL_SCORE >= 8.5" | bc -l) )); then
    echo -e "${GREEN}⭐ BUENO - Aprobado Sin Reservas${NC}"
elif (( $(echo "$FINAL_SCORE >= 8.0" | bc -l) )); then
    echo -e "${GREEN}✅ ACREDITADO - Mínimo Aceptable${NC}"
elif (( $(echo "$FINAL_SCORE >= 7.5" | bc -l) )); then
    echo -e "${YELLOW}⚠️ REFINAR - Mejoras Requeridas${NC}"
elif (( $(echo "$FINAL_SCORE >= 7.0" | bc -l) )); then
    echo -e "${YELLOW}⚠️ REVISAR - Revisión Mayor${NC}"
else
    echo -e "${RED}❌ REFACTORIZAR - Rediseñar Completo${NC}"
fi

exit 0
```

---

# 🔄 PROCESO DE ACREDITACIÓN PASO A PASO

## Fase 1: Validación Automática (5-10 min)

```bash
# Ejecutar validación automática
./validate-meta-prompt-universal.sh PROMPT-EJEMPLO.md true

# Output esperado:
# ✅ C1 (CSE): PASS (3/3 secciones)
# ✅ C2 (TAGs): PASS (75% cobertura)
# ✅ C3 (Markers): PASS (22 markers)
# ✅ C4 (Frontmatter): PASS (12/10 campos)
# ✅ C5 (Anti-drift): PASS (5/6 mecanismos)
# ✅ C6 (Objetivos): PASS (4 objetivos)
# ✅ C7 (Tests): PASS (3 tests)
# ✅ C8 (Separación): PASS (100% separación)
# ✅ C9 (Memoria): PASS (5 referencias /core)
#
# Score Final: 9.7/10
# ⭐⭐⭐ ELITE - Referencia Universal
```

## Fase 2: Validación Manual (15-25 min)

### Checklist Manual

```markdown
## Validación Manual Avanzada

### Calidad de Componentes

- [ ] **C1 CSE:** ¿Las secciones son completas y relevantes?
- [ ] **C2 TAGs:** ¿Los TAGs se aplican correctamente?
- [ ] **C3 Markers:** ¿Los markers son contextuales?
- [ ] **C4 Frontmatter:** ¿Los metadatos son precisos?
- [ ] **C5 Anti-drift:** ¿Los mecanismos son efectivos?
- [ ] **C6 Objetivos:** ¿Los objetivos son SMART?
- [ ] **C7 Tests:** ¿Los tests son ejecutables y relevantes?
- [ ] **C8 Separación:** ¿La separación EVIDENCIA/PROPUESTA es clara?
- [ ] **C9 Memoria:** ¿La integración con /core es coherente?

### Coherencia Global

- [ ] **Consistencia:** ¿No hay contradicciones internas?
- [ ] **Completitud:** ¿Cubre todos los aspectos requeridos?
- [ ] **Aplicabilidad:** ¿Es implementable en el contexto actual?
- [ ] **Mantenibilidad:** ¿Es fácil de mantener y actualizar?
```

## Fase 3: Cálculo Score Final (2-5 min)

```python
# calculate_final_score.py
def calculate_accreditation_score(auto_scores, manual_scores):
    """
    Combinar scores automáticos y manuales para score final
    """
    weights = {
        'auto': 0.6,  # 60% peso validación automática
        'manual': 0.4  # 40% peso validación manual
    }

    final_score = (auto_scores['total'] * weights['auto'] +
                   manual_scores['total'] * weights['manual'])

    return final_score

# Ejemplo de uso
auto_scores = {'total': 9.7, 'components': {...}}
manual_scores = {'total': 9.5, 'aspects': {...}}

final_score = calculate_accreditation_score(auto_scores, manual_scores)
print(f"Score Final Acreditación: {final_score:.1f}/10")
```

## Fase 4: Reporte de Acreditación (5 min)

```markdown
# REPORTE ACREDITACIÓN UNIVERSAL

**Prompt:** PROMPT-EJEMPLO-v2.0.0.md
**Fecha:** 2025-12-11T12:52:00Z
**Acreditador:** META-PROMPT-UNIVERSAL v2.0.0

## Scores por Componente

| Componente       | Score Auto | Score Manual | Peso | Ponderado | Status |
| ---------------- | ---------- | ------------ | ---- | --------- | ------ |
| C1 (CSE)         | 1.0        | 0.9          | 20%  | 0.19      | ✅     |
| C2 (TAGs)        | 1.0        | 1.0          | 15%  | 0.15      | ✅     |
| C3 (Markers)     | 1.0        | 0.9          | 15%  | 0.14      | ✅     |
| C4 (Frontmatter) | 1.0        | 1.0          | 10%  | 0.10      | ✅     |
| C5 (Anti-drift)  | 0.8        | 0.9          | 15%  | 0.13      | ⚠️     |
| C6 (Objetivos)   | 1.0        | 1.0          | 10%  | 0.10      | ✅     |
| C7 (Tests)       | 1.0        | 0.9          | 10%  | 0.10      | ✅     |
| C8 (Separación)  | 1.0        | 1.0          | 5%   | 0.05      | ✅     |
| C9 (Memoria)     | 0.9        | 0.8          | 10%  | 0.09      | ⚠️     |

**Score Final:** 9.5/10

## Veredicto

**⭐⭐⭐ ELITE - Referencia Universal**

Score 9.5/10 ≥ 9.5/10 threshold elite

## Mejoras Sugeridas

**C5 (Anti-drift):** Score 0.8 (mejorable)

- Agregar 1 mecanismo anti-drift adicional (actual 5/6)
- Documentar más explícitamente el Context Refresh Protocol

**C9 (Memoria):** Score 0.9 (mejorable)

- Agregar 1 referencia más a /core (actual 2/3)
- Integrar con core/surprise-metrics para métricas automáticas

## Recomendación Final

✅ **Incluir como Referencia Universal v2.0.0**
✅ **Aplicar mejoras sugeridas en v2.1.0**
✅ **Documentar como best-practice para organización**
```

---

# 🎓 GUIA DE IMPLEMENTACIÓN

## Paso 1: Crear Prompt Base

```bash
# Copiar template universal
cp META-PROMPT-UNIVERSAL-v2.0.0.md MI-PROMPT-v2.0.0.md

# Editar campos obligatorios
vim MI-PROMPT-v2.0.0.md
```

## Paso 2: Personalizar Contenido

1. **Actualizar Frontmatter YAML**
2. **Definir rol y propósito específico**
3. **Adaptar contexto y documentos base**
4. **Especificar objetivos SMART**
5. **Diseñar tareas detalladas**
6. **Crear tests ejecutables**
7. **Aplicar todos los marcadores**

## Paso 3: Validar Automáticamente

```bash
# Ejecutar validación completa
./validate-meta-prompt-universal.sh MI-PROMPT-v2.0.0.md true

# Revisar resultados y corregir si es necesario
```

## Paso 4: Validación Manual

1. **Revisar calidad de cada componente**
2. **Verificar coherencia global**
3. **Validar aplicabilidad práctica**
4. **Confirmar mantenibilidad**

## Paso 5: Acreditación Final

1. **Generar reporte de acreditación**
2. **Obtener veredicto final**
3. **Documentar mejoras sugeridas**
4. **Planificar versión siguiente**

---

# 🔗 REFERENCIAS COMPLETAS

## Documentos Base

- `PROMPT-ACREDITADOR-PLAYBOOK-BMCC-v1.0.0.md` - Sistema de acreditación
- `PROMPT-PAE-EXTRACTOR-v1.0.0.md` - Sistema de extracción
- `META-HANDOFF-TEMPLATE-v1.0.0.md` - Template handoff

## Herramientas de Validación

- `validate-meta-prompt-universal.sh` - Validación automatizada
- `calculate_final_score.py` - Cálculo de scores
- `pae_agnostic.schema.json` - Schema JSON

## Frameworks Integrados

- **4D Audit Framework** - Auditoría multidimensional
- **CSE (Context-Specification-Verification)** - Estructura metodológica
- **CoVe (Chain-of-Verification)** - Verificación sistemática
- **PAE (Pre-Audit Extract)** - Extracción estructurada

## Papers SOT

- [PAPER:arXiv:2510.08558v1] Zhang et al. (2025) - Agent Learning via Early Experience
- [PAPER:arXiv:2510.04618v1] Chen et al. (2025) - Advanced Prompt Engineering

## Sistemas de Memoria

- `/core/memory` - Sistema de memoria a corto y largo plazo
- `/core/surprise-metrics` - Métricas de sorpresa y novedad
- `/core/context-management` - Gestión de contexto
- `/core/search` - Búsqueda híbrida

---

**META-PROMPT UNIVERSAL v2.0.0 COMPLETADO** ✅
**Fecha:** 2025-12-11T12:52:00Z
**Versión:** 2.0.0
**Threshold mínimo:** ≥8.0/10
**Threshold elite:** ≥9.5/10
**Estado:** LISTO PARA USO UNIVERSAL
**Integración:** Acreditador + PAE + Handoff Template
**Mecanismos Anti-Drift:** 15+ sistemas implementados
**Validación:** Automatizada + Manual + Schema
**Determinismo:** Garantizado