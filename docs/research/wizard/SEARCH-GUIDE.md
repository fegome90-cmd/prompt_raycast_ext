# 🗺️ Mapa de Búsqueda - Implementación Prompt Wizard + DSPy

**Propósito:** Guía de referencia rápida para encontrar código, paths e ideas durante la implementación.
**Regla:** Este documento NO replica contenido - solo indica DÓNDE encontrar cada cosa.
**Fecha:** 2026-01-01

---

## 📁 Estructura de Documentos

```
/Users/felipe_gonzalez/Developer/raycast_ext/docs/research/wizard/
├── 00-EXECUTIVE-SUMMARY.md          ← START AQUÍ (Resumen 3 min)
├── 01-wizard-complete-flow.md         ← Flujo completo 6 pasos
├── 02-template-library-analysis.md    ← 174+ templates analizados
├── 03-dspy-integration-guide.md       ← GUÍA PRINCIPAL DSPy
├── 04-prompt-assembly-patterns.md     ← Cómo ensamblar prompts
├── 05-quality-validation-system.md    ← Métricas de calidad
├── 06-dataset-strategy.md             ← Estrategia dataset
├── 07-legacy-prompts-analysis.md      ← MINA DE ORO (NUEVO)
└── DSPy_Audit_Report.md              ← Informe técnico HemDov
```

---

## 🎯 Por Tipo de Información que Necesitas

### Necesitas: **Decisión rápida - ¿Vale la pena?**
→ Ir a: **`00-EXECUTIVE-SUMMARY.md`**
- Líneas 1-50: Resumen del GAP crítico
- Líneas 60-90: Análisis ROI por componente
- Líneas 95-130: Quick Start (Opción A vs B)
- Líneas 140-170: Decision Checklist

### Necesitas: **El código completo del PromptImprover Module**
→ Ir a: **`03-dspy-integration-guide.md`**
- Líneas 306-360: Arquitectura visual de la solución
- Líneas 362-428: **Paso 1 - Signature** (código completo)
- Líneas 430-486: **Paso 2 - Module** (código completo)
- Líneas 488-577: **Paso 3 - Dataset** (ejemplos listos para copiar)
- Líneas 579-665: **Paso 4 - Optimizer** (función `compile_prompt_improver`)
- Líneas 667-771: **Paso 5 - API Endpoint** (FastAPI completo)
- Líneas 773-853: **Paso 6 - Tests** (TDD pattern)
- Líneas 855-898: **Paso 7 - Integración Raycast** (TypeScript client)

### Necesitas: **Entender el flujo actual del Wizard de 6 pasos**
→ Ir a: **`01-wizard-complete-flow.md`**
- Líneas 14-67: **OVERVIEW** - Diagrama del flujo completo
- Líneas 69-120: **Step 0: Discovery** - Búsqueda de templates
- Líneas 122-160: **Step 1: Objective** - Definición de objetivo
- Líneas 162-230: **Step 2: Role** - Sugerencias AI-powered
- Líneas 232-260: **Step 3: Directive** - Directiva core
- Líneas 262-320: **Step 4: Framework** - Selección de razonamiento
- Líneas 322-380: **Step 5: Guardrails** - Restricciones
- Líneas 382-450: **Step 6: Plan View** - Ensamblaje final
- Líneas 452-510: **Validaciones** - Reglas por paso

### Necesitas: **Templates listos para usar como ejemplos**
→ Ir a: **`02-template-library-analysis.md`**
- Líneas 50-120: **SotaTemplateDB Interface** - Estructura de datos
- Líneas 122-200: **Roles (9 componentes)** - Lista completa con código
- Líneas 202-260: **Directives (7 componentes)** - Lista completa
- Líneas 262-310: **Frameworks (2 componentes)** - CoT y ToT
- Líneas 312-380: **Constraints (12 componentes)** - Lista completa
- Líneas 382-480: **Templates Completos** - 4 ejemplos de principio a fin

### Necesitas: **Cómo ensamblar el prompt final**
→ Ir a: **`04-prompt-assembly-patterns.md`**
- Líneas 15-50: **PlanData Structure** - Interface TypeScript
- Líneas 52-100: **Ensamblaje Estándar** - Función `assembleFinalPrompt()`
- Líneas 102-180: **Patrones de Framework** - CoT, ToT, Decomposition, Role-Playing
- Líneas 182-230: **Optimizaciones** - Token efficiency, calidad adaptativa
- Líneas 232-290: **DSPy Integration** - PromptAssembler module

### Necesitas: **Validar calidad de prompts generados**
→ Ir a: **`05-quality-validation-system.md`**
- Líneas 15-70: **5 Dimensiones de Calidad** - Claridad, Completitud, etc.
- Líneas 72-130: **Fórmulas de Cálculo** - Código de cada métrica
- Líneas 132-200: **Validation Pipeline** - Clase `QualityValidator`
- Líneas 202-270: **Improvement Suggestions** - Clase `PromptImprover`
- Líneas 272-310: **DSPy Integration** - Validador DSPy

### Necesitas: **Estrategia completa del Dataset**
→ Ir a: **`06-dataset-strategy.md`**
- Líneas 9-90: **Inventario Fuentes** - Templates promptass disponibles
- Líneas 92-140: **Estrategia 3 Fases** - Base (10), Expandido (25), Robusto (50+)
- Líneas 142-200: **Proceso Conversión** - Template → Ejemplo DSPy paso a paso
- Líneas 202-270: **Template Ejemplo** - Formato estándar para crear nuevos
- Líneas 272-320: **Criterios Calidad** - Quality gate, validación automática
- Líneas 322-380: **Plan Acción** - Timeline por día para cada fase

### Necesitas: **Mina de Oro de Prompts Legacy**
→ Ir a: **`07-legacy-prompts-analysis.md`** (VERSIÓN CORREGIDA)
- Líneas 10-25: **⚠️ Corrección Crítica** - NO son training data directo
- Líneas 27-48: **GAP Fundamental** - DSPy necesita vs Legacy tiene
- Líneas 50-80: **Inventario CORREGIDO** - Componentes extraíbles reales
- Líneas 84-120: **Tipos de Prompts** - Cómo usar cada uno (CORREGIDO)
- Líneas 122-160: **Uso CORRECTO** - Extraer componentes, no convertir directo
- Líneas 220-320: **Proceso CORREGIDO** - Extracción de componentes paso a paso
- Líneas 334-378: **Ejemplo Real** - Construcción desde componentes
- Líneas 519-540: **Métricas CORREGIDAS** - ROI realista con componentes

### Necesitas: **Detalles técnicos del sistema HemDov DSPy**
→ Ir a: **`DSPy_Audit_Report.md`**
- Líneas 1-50: **Executive Summary** - Estado actual
- Líneas 52-120: **Signatures DSPy** - ExecutorSignature, ToolSelector, etc.
- Líneas 122-180: **Boundaries** - Separación Domain vs Infrastructure
- Líneas 182-240: **Pureza** - Determinismo y hardening
- Líneas 242-300: **Optimización** - BootstrapFewShot implementation
- Líneas 302-380: **Infraestructura** - LiteLLM adapter, Ollama
- Líneas 422-490: **Propuesta Integración** - Opción A (PromptImprover)

---

## 🔍 Búsqueda por Keyword

### Buscas: "¿Cómo creo X?"

| Keyword | Ir a Documento | Líneas | Qué encuentras |
|---------|---------------|--------|-----------------|
| "PromptImproverSignature" | `03-dspy...` | 362-428 | Código completo signature |
| "PromptImprover class" | `03-dspy...` | 430-486 | Código completo module |
| "API endpoint FastAPI" | `03-dspy...` | 667-771 | `@router.post("/improve-prompt")` |
| "load_prompt_improvement_examples" | `03-dspy...` | 488-577 | Dataset con 3 ejemplos |
| "compile_prompt_improver" | `03-dspy...` | 579-665 | Función optimización |
| "assembleFinalPrompt" | `04-prompt...` | 52-100 | Función ensamblaje TypeScript |
| "QualityValidator" | `05-quality...` | 132-200 | Clase validación |
| "PlanData interface" | `04-prompt...` | 15-50 | TypeScript interface |
| "Dataset strategy" | `06-dataset...` | 1-390 | Estrategia completa dataset |
| "Template → Ejemplo DSPy" | `06-dataset...` | 142-200 | Proceso conversión |
| "Quality gate dataset" | `06-dataset...` | 272-320 | Criterios calidad |
| "Legacy prompts" | `07-legacy...` | 1-450 | Mina de oro 1,188 archivos |
| "CodeMachine agents" | `07-legacy...` | 52-120 | 22 agentes conversión directa |
| "Conversión legacy → DSPy" | `07-legacy...` | 202-280 | Proceso conversión legacy |

### Buscas: "¿Dónde está X?"

| Componente | Documento | Líneas | Path Relativo |
|------------|-----------|--------|--------------|
| **LiteLLM Adapter** | `DSPy_Audit...` | 345-365 | `hemdov/infrastructure/adapters/litellm_dspy_adapter.py` |
| **DSPyOptimizer** | `DSPy_Audit...` | 196-217 | `eval/src/dspy_optimizer.py` |
| **Test Pattern** | `DSPy_Audit...` | 451-470 | `tests/test_dspy_*.py` |
| **Settings** | `DSPy_Audit...` | 112-124 | `hemdov/infrastructure/config/__init__.py` |
| **Role Examples** | `02-template...` | 122-200 | Lista de 9 roles completos |
| **Framework Patterns** | `04-prompt...` | 102-180 | 4 frameworks con diagramas ASCII |
| **Templates Promptass** | `simulation/db.ts` | 105-174 | 4 templates completos |
| **Dataset Fuentes** | `06-dataset...` | 9-90 | Inventario completo fuentes |
| **Legacy Prompts** | `docs/legacy/` | - | 1,188 archivos en inventario |
| **CodeMachine Agents** | `codemachine/agents/` | - | 22 prompts conversión directa |

---

## 📋 Checklists de Implementación

### Checklist Rápida (3-4 horas - Zero-shot)

- [ ] **Leer resumen:** `00-EXECUTIVE-SUMMARY.md` (líneas 95-130)
- [ ] **Copiar Signature:** `03-dspy-integration-guide.md` (líneas 362-428)
- [ ] **Copiar Module:** `03-dspy-integration-guide.md` (líneas 430-486)
- [ ] **Copiar API Endpoint:** `03-dspy-integration-guide.md` (líneas 667-771)
- [ ] **Copiar Tests:** `03-dspy-integration-guide.md` (líneas 773-853)
- [ ] **Copiar Raycast Client:** `03-dspy-integration-guide.md` (líneas 855-898)

### Checklist Completa (8-16 horas - Optimizado)

- [ ] **Fase 1: Core Module** (3h)
  - [ ] Signature: `03-dspy...` líneas 362-428
  - [ ] Module: `03-dspy...` líneas 430-486
  - [ ] Tests: `03-dspy...` líneas 773-853
- [ ] **Fase 2: Optimización** (4h)
  - [ ] Dataset: `03-dspy...` líneas 488-577 (añadir 10+ ejemplos más)
  - [ ] Optimizer: `03-dspy...` líneas 579-665
  - [ ] Métrica: `03-dspy...` líneas 594-630
- [ ] **Fase 3: API** (3h)
  - [ ] Endpoint: `03-dspy...` líneas 667-771
  - [ ] Integración: `03-dspy...` líneas 855-898
  - [ ] Integración tests: `03-dspy...` líneas 845-853

---

## 🎯 Por Componente a Implementar

### Componente 1: PromptImproverSignature

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 362-428
**Qué contiene:**
- Clase `PromptImproverSignature` completa
- Input fields: `original_idea`, `context`, `examples`
- Output fields: `improved_prompt`, `role`, `directive`, `framework`, `guardrails`, `reasoning`, `confidence`

**Copiar:** Todo el bloque de código Python (líneas 366-428)

---

### Componente 2: PromptImprover Module

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 430-486
**Qué contiene:**
- Clase `PromptImprover` con ChainOfThought
- Clase `PromptImproverZeroShot` (alternativa rápida)
- Método `forward()` con implementación completa

**Copiar:** Todo el bloque de código Python (líneas 434-486)

---

### Componente 3: Dataset de Entrenamiento

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 488-577
**Qué contiene:**
- Función `load_prompt_improvement_examples()`
- 3 ejemplos completos listos para copiar
- Estructura `dspy.Example` para cada uno
- Comentario TODO con dominios sugeridos

**Copiar:**
- Función completa (líneas 500-576)
- Añadir 10-20 ejemplos más siguiendo el patrón

---

### Componente 4: Optimizer (BootstrapFewShot)

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 579-665
**Qué contiene:**
- Función `prompt_improver_metric()` (líneas 594-630)
- Función `compile_prompt_improver()` (líneas 631-665)
- Setup de optimizer con métricas custom

**Copiar:** Todo el bloque (líneas 583-665)

---

### Componente 5: API Endpoint

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 667-771
**Qué contiene:**
- FastAPI router completo
- Pydantic models: `ImprovePromptRequest`, `ImprovePromptResponse`
- Endpoint `POST /api/v1/improve-prompt`
- Error handling y validaciones

**Copiar:** Todo el bloque (líneas 667-771)

---

### Componente 6: Tests

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 773-853
**Qué contiene:**
- `TestPromptImprover` class (unit tests)
- `TestPromptImproverIntegration` class (integration tests)
- Tests RED-GREEN siguiendo patrón HemDov

**Copiar:** Todo el bloque (líneas 777-853)

---

### Componente 7: Raycast Client

**Dónde:** `03-dspy-integration-guide.md`
**Líneas:** 855-898
**Qué contiene:**
- Interfaces TypeScript
- Función `improvePrompt()` async
- Ejemplo de uso

**Copiar:** Todo el bloque (líneas 859-898)

---

## 🔗 Referencias Cruzadas

### De Template Library a DSPy

**Si necesitas ejemplos para el Dataset:**

1. Ir a: `02-template-library-analysis.md`
2. Líneas 382-480: Templates completos
3. Copiar estructura: **original_idea** (descripción) → **improved_prompt** (contenido completo)

**Mapeo:**
- `template.description` → `original_idea`
- `template.components.role.content` → `role`
- `template.components.directive.content` → `directive`
- `template.components.framework.content` → `framework`
- `template.components.constraints` → `guardrails`

### De Dataset Strategy a Implementación

**Si necesitas construir el dataset:**

1. Ir a: `06-dataset-strategy.md`
2. Líneas 9-90: Inventario de fuentes disponibles en promptass
3. Líneas 142-200: Proceso conversión Template → Ejemplo DSPy
4. Líneas 202-270: Template listo para copiar/pegar
5. Líneas 322-380: Plan de acción día por día

**Conversión:**
- `simulation/db.ts` templates: 4 ejemplos base listos
- Combinar componentes: 9 roles × 7 directives × 2 frameworks = 126+ combinaciones posibles
- Quality gate: Solo ejemplos con score ≥ 0.7 pasan

### De Legacy Prompts a Dataset DSPy

**Si necesitas convertir prompts legacy:**

1. Ir a: `07-legacy-prompts-analysis.md`
2. Líneas 52-120: Inventario completo por tipo (CodeMachine, Agentes, Sprints)
3. Líneas 202-280: Proceso conversión Legacy → DSPy paso a paso
4. Líneas 282-340: Ejemplo real de conversión (Architecture Agent)
5. Líneas 342-380: Top 10 prioridades para convertir primero

**Fuentes Legacy (CORREGIDO):**
- CodeMachine Agents: 22 agentes = fuentes de componentes production-proven
- Agentes Especializados: 15 agentes = componentes especializados
- Sprint Prompts: 45 prompts = metadata y frameworks
- **Total potencial:** Componentes para 50-100 ejemplos sintéticos de ALTA calidad
- **⚠️ IMPORTANTE:** NO son training data directo, son FUENTE DE COMPONENTES

**Path Legacy:**
`/Users/felipe_gonzalez/Developer/promtassss-main/docs/legacy/inventario-documental-collection`

**Uso Recomendado:**
1. Extraer components (role, directive, framework, guardrails)
2. Generar inputs realistas basados en propósito del agente
3. Construir ejemplos sintéticos con components production-proven
4. Validar calidad de cada ejemplo construido

---

## 💡 Tips de Búsqueda Rápida

### Para encontrar código rápido

1. **Abrir** el documento relevante (ver tabla arriba)
2. **Usar** búsqueda del editor (Ctrl+F / Cmd+F)
3. **Buscar:** "class PromptImprover" o "def compile_prompt"
4. **Copiar** el bloque completo de código

### Para entender patrones

1. **Flujo Wizard:** `01-wizard-complete-flow.md` (leer secciones relevantes)
2. **Templates:** `02-template-library-analysis.md` (leer ejemplos)
3. **Dataset:** `06-dataset-strategy.md` (ver estrategia completa)
4. **Legacy Prompts:** `07-legacy-prompts-analysis.md` (mina de oro 1,188 archivos)
5. **Ensamblaje:** `04-prompt-assembly-patterns.md` (ver patrón que necesitas)
6. **DSPy:** `03-dspy-integration-guide.md` (copiar código)

### Para troubleshooting

1. **Error en DSPy:** `DSPy_Audit_Report.md` (líneas 380-420 - infraestructura)
2. **Error en tests:** `DSPy_Audit_Report.md` (líneas 422-470 - test patterns)
3. **Error en calidad:** `05-quality-validation-system.md` (líneas 132-200 - fórmulas)
4. **Dataset pobre:** `06-dataset-strategy.md` (líneas 272-320 - quality gate)
5. **Uso de legacy:** `07-legacy-prompts-analysis.md` (líneas 10-25 - corrección crítica) ⭐ NUEVO

---

## 📊 Matriz de Decisión

```
                  +------------------+------------------+
                  |  Tiempo Disponible |   Calidad Meta   |
                  +------------------+------------------+
                  |  3-4h (rápido)   |  8-16h (óptimo)  |
+-----------------+------------------+------------------+
│ Prompt simple   |  Opción A (3-4h)   |  Opción A (3-4h)   |
│ Baja complejidad |  Zero-shot        |  Zero-shot        |
+-----------------+------------------+------------------+
│ Prompt complejo |  Opción A (3-4h)   |  Opción B (8-16h)  |
│ Alta complejidad |  Riesgo calidad    |  Con optimización   |
+-----------------+------------------+------------------+
│ Production-ready |  Opción B (8-16h)  |  Opción B (8-16h)  |
| Requiere robustez |  Con optimización   |  Con optimización   |
+-----------------+------------------+------------------+
```

---

## 🎯 Roadmap de Lectura (Ordenado por Prioridad)

### Lectura Mínima (15 min) - Para decidir si implementar
1. `00-EXECUTIVE-SUMMARY.md` - Todo
2. `DSPy_Audit_Report.md` - Líneas 1-50 (Executive Summary)
3. `03-dspy-integration-guide.md` - Líneas 306-360 (El Problema)

### Lectura Técnica (45 min) - Para implementar
1. `03-dspy-integration-guide.md` - Líneas 362-898 (Todo el código)
2. `04-prompt-assembly-patterns.md` - Líneas 52-100 (Función ensamblaje)
3. `02-template-library-analysis.md` - Líneas 382-480 (Ejemplos para dataset)
4. `06-dataset-strategy.md` - Líneas 9-90 (Fuentes disponibles)
5. `07-legacy-prompts-analysis.md` - Líneas 52-120 (Inventario legacy)

### Lectura Profunda (2h) - Para entender arquitectura
1. `01-wizard-complete-flow.md` - Todo (flujo 6 pasos)
2. `02-template-library-analysis.md` - Todo (174+ templates)
3. `04-prompt-assembly-patterns.md` - Todo (patrones de framework)
4. `05-quality-validation-system.md` - Todo (métricas)
5. `06-dataset-strategy.md` - Todo (estrategia dataset)
6. `07-legacy-prompts-analysis.md` - Todo (mina de oro legacy)
7. `DSPy_Audit_Report.md` - Todo (auditoría técnica completa)

---

## 🚀 Quick Start Commands

### Si decides implementar Opción Rápida (3-4h):

```bash
# 1. Crear archivos (siguiendo estructura HemDov)
mkdir -p hemdov/domain/dspy_modules
mkdir -p eval/src
mkdir -p tests

# 2. Copiar código desde 03-dspy-integration-guide.md:
#    - Líneas 362-428 → prompt_improver.py
#    - Líneas 430-486 → dspy_prompt_improver.py
#    - Líneas 667-771 → prompt_improver_api.py
#    - Líneas 773-853 → test_dspy_prompt_improver.py

# 3. Crear dataset mínimo (3 ejemplos ya listos en líneas 488-577)

# 4. Testar manual
python -c "from eval.src.dspy_prompt_improver import PromptImprover; improver = PromptImprover(); print(improver(original_idea='Test'))"
```

### Si decides implementar Opción Optimizada con Legacy (14-30h):

```bash
# Mismos pasos que Opción Rápida, PLUS:

# 5. Convertir prompts legacy (usar 07-legacy-prompts-analysis.md)
#    Top 10 prioridades: CodeMachine agents + MemTech agent
#    Ver líneas 342-380 para lista completa

# 6. Script de conversión (crear: scripts/convert_legacy_to_dspy.py)
#    - identify_prompt_type()
#    - extract_components()
#    - convert_to_dspy_example()

# 7. Batch conversion (45-200 ejemplos)
python scripts/convert_legacy_to_dspy.py \
    --source /Users/felipe_gonzalez/Developer/promtassss-main/docs/legacy/inventario-documental-collection \
    --target eval/src/prompt_improvement_dataset.py \
    --top 50  # Convertir top 50 prompts por prioridad

# 8. Correr tests completos
pytest tests/test_dspy_prompt_improver.py -v

# 9. Integrar con API
# (ver líneas 667-771 para endpoint)
```

---

## 📞 Referencias a Archivos Externos

### Sistema HemDov (referenciado en auditoría)

```
/Users/felipe_gonzalez/[path-to-hemdov]/
├── hemdov/
│   ├── domain/dspy_modules/
│   │   └── code_generator.py          ← Estructura reference
│   └── infrastructure/
│       ├── adapters/
│       │   ├── litellm_dspy_adapter.py  ← REUTILIZAR (100%)
│       │   └── dspy_executor_adapter.py
│       └── config/
│           └── __init__.py                ← Settings reference
├── eval/src/
│   ├── dspy_signatures.py               ← ExecutorSignature reference
│   ├── dspy_optimizer.py               ← Optimizer reference
│   └── dspy_dataset.py                ← Dataset reference
└── tests/
    └── test_dspy_*.py                   ← Test patterns
```

**Nota:** Paths son relativos a la ubicación de HemDov en tu sistema.

### Prompts Legacy (mina de oro - 1,188 archivos)

```
/Users/felipe_gonzalez/Developer/promtassss-main/docs/legacy/inventario-documental-collection/
├── files/
│   ├── codemachine-cli/prompts/
│   │   └── templates/codemachine/
│   │       ├── agents/                   ← 22 agentes conversión directa
│   │       │   ├── 01-architecture-agent.md
│   │       │   ├── 05-code-generation-agent.md
│   │       │   └── ...
│   │       └── workflows/                ← 18 workflows
│   ├── agents/
│   │   ├── memtech/prompt.md             ← Agente especializado
│   │   ├── guardian/                     ← Agente de seguridad
│   │   └── prompting/                    ← Agente de prompting
│   └── core/surprise-metrics/            ← 45 sprint prompts
│       ├── PROMPT-SPRINT-13-MEMTECH-AGENT-v1.0.0.md
│       ├── PROMPT-SPRINT-15-REFINAMIENTO-MEMTECH-v1.0.0.md
│       └── ...
└── _metadata.json                        ← Inventario completo
```

**Nota:** Ver `07-legacy-prompts-analysis.md` para estrategia de conversión.

---

## ✅ Última Verificación

Antes de comenzar implementación, verificar:

- [ ] Leí `00-EXECUTIVE-SUMMARY.md` completo
- [ ] Entiendo el GAP: necesito crear PromptImprover Module
- [ ] Sé cuál opción implementar:
  - [ ] Opción Rápida (3-4h): 10 ejemplos sintéticos
  - [ ] Opción Optimizada (8-16h): 25 ejemplos sintéticos
  - [ ] Opción con Componentes Legacy (14 días): 25 ejemplos con components production-proven ⭐ RECOMENDADA
- [ ] Tengo acceso a código HemDov (para reutilizar LiteLLM adapter)
- [ ] Tengo Ollama o provider LLM configurado
- [ ] Sé dónde crear archivos (siguiendo estructura HemDov)
- [ ] **Si elijo Legacy:** Entiendo que NO son training data directo ⭐ CRÍTICO
- [ ] **Si elijo Legacy:** Sé que debo extraer COMPONENTES y construir ejemplos ⭐ CRÍTICO

---

**Fin del Mapa de Búsqueda**

*Este documento es tu guía de navegación. Para implementar, sigue las referencias a los documentos fuente.*
