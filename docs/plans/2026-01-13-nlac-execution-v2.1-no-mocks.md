# Plan: Ejecución NLaC Pipeline v3.0 - Para Otro Agente

> **Fecha:** 2026-01-13
> **Objetivo:** Planificar ejecución completa del NLaC Pipeline v3.0 para implementar en otra sesión
> **Referencia:** docs/plan/2026-01-13-nlac-pipeline-improvements.md (v3.0)
> **Instrucciones:** docs/plan/INSTRUCTIONS-FOR-AGENT.md

> **🎯 Cambio v2.1:** Se eliminaron mocks. IFEvalValidator se implementa en Fase 0 con validación REAL (3 constraints básicos).

---

## 🎯 Objetivo de la Sesión Futura

Implementar las 4 fases del NLaC Pipeline v3.0 usando el documento `INSTRUCTIONS-FOR-AGENT.md` como guía de ejecución.

**Estado previo:** ✅ Fixes críticos aplicados y mergeados (PR #3)

---

## 📋 Estructura del Plan

El plan `INSTRUCTIONS-FOR-AGENT.md` tiene 7 partes:

| Parte | Descripción | Tiempo Estimado | Estado Previo |
|-------|-------------|-----------------|----------------|
| **Part 1** | Worktree Setup | 30 min | ✅ Completado |
| **Part 2** | Fase 0 (5 tareas) | 4-6 horas | ⏳ Pendiente |
| **Part 3** | Fase 0 Completion | 30 min | ⏳ Pendiente |
| **Part 4** | Go/No-Go Points | - | ⏳ Pendiente |
| **Part 5** | Troubleshooting | - | ⏳ Pendiente |
| **Part 6** | Worktree Cleanup | 30 min | ⏳ Pendiente |

---

## 🚀 Plan de Ejecución para Otro Agente

### Pre-requisitos para el Agente

**Antes de iniciar:**
1. Tener acceso a `docs/plan/INSTRUCTIONS-FOR-AGENT.md`
2. Tener Ollama instalado o poder instalarlo
3. Ubicación preferida: `.worktrees/` directorio

### Batch 1: Setup Inicial (30 min)

**Tareas:**
1. Verificar que `.worktrees/` existe y está en `.gitignore`
2. Crear worktree: `git worktree add .worktrees/nlac-pipeline -b feature/nlac-pipeline-implementation`
3. Instalar dependencias: `uv sync`
4. Verificar baseline: `make test` (debe pasar sin errores nuevos)

**Checkpoint:** Tests pasando, worktree listo

### Batch 2: Fase 0 - Task 0.1 (1 hora)

**Tarea:** Setup Ollama nomic-embed-text

**Pasos:**
```bash
# 1. Verificar/instalar Ollama
which ollama || curl -fsSL https://ollama.com/install.sh | sh

# 2. Iniciar servicio
pgrep -x ollama || ollama serve &

# 3. Descargar modelo
ollama pull nomic-embed-text

# 4. Validar
ollama run nomic-embed-text "test query"
```

**Checkpoint:** Ollama corriendo con nomic-embed-text (768 dimensions)

### Batch 3: Fase 0 - Task 0.2a (1-2 horas)

**Tarea:** Implement IFEvalValidator Básico (SIN Mocks)

**Pasos:**
1. Crear `hemdov/domain/services/ifeval_validator.py` con validación real
2. Implementar 3 constraints básicas:
   - Longitud mínima del prompt (≥50 caracteres)
   - Presencia de verbos de acción (create, implement, write, etc.)
   - Formato JSON válido
3. Ejecutar: `uv run python -c "from hemdov.domain.services.ifeval_validator import IFEvalValidator; v = IFEvalValidator(); print(v.validate('Create a function to sort a list'))"`

**Checkpoint:** IFEvalValidator validando prompts reales

---

### Batch 4: Fase 0 - Task 0.2b (2-3 horas)

**Tarea:** Bootstrap IFEval Calibration con Validación REAL

**Pasos:**
1. Crear `scripts/bootstrap_ifeval_calibration.py` (usa IFEvalValidator real)
2. Ejecutar: `uv run python scripts/bootstrap_ifeval_calibration.py`
3. Verificar output: `cat data/ifeval-calibration.json | jq .calibrated_threshold`
4. Analizar distribución de scores y ajustar threshold si es necesario

**Checkpoint:** `data/ifeval-calibration.json` con scores REALES del catálogo

### Batch 5: Fase 0 - Task 0.3 (1-2 horas)

**Tarea:** Baseline Measurement Script

**Pasos:**
1. Crear `scripts/measure_baseline.py` (desde INSTRUCTIONS-FOR-AGENT.md líneas 298-408)
2. Ejecutar: `uv run python scripts/measure_baseline.py`
3. Verificar: `cat data/baseline-v3.0.json | jq .results`

**Checkpoint:** Baseline metrics guardadas

### Batch 6: Fase 0 - Task 0.4 (1-2 horas)

**Tarea:** Feature Flags Infrastructure

**Pasos:**
1. Crear `hemdov/infrastructure/config/feature_flags.py` (líneas 436-528)
2. Crear directorio: `mkdir -p hemdov/infrastructure/config`
3. Crear `__init__.py`: `touch hemdov/infrastructure/config/__init__.py`
4. Agregar a `.env.local` (líneas 509-521)
5. Verificar: `uv run python -c "from hemdov.infrastructure.config.feature_flags import FeatureFlags; print(FeatureFlags.enable_dspy_embeddings)"`

**Checkpoint:** Feature flags funcionando, devuelve `False`

### Batch 7: Fase 0 - Task 0.5 (1 hora)

**Tarea:** Define Missing Ports

**Pasos:**
1. Crear `hemdov/domain/ports/cache_port.py` (líneas 559-596)
2. Crear `hemdov/domain/ports/vectorizer_port.py` (líneas 598-646)
3. Crear `hemdov/domain/ports/metrics_port.py` (líneas 648-717)
4. Crear `hemdov/domain/ports/__init__.py` (líneas 719-728)
5. Verificar imports: `uv run python -c "from hemdov.domain.ports import CachePort, VectorizerPort, MetricsPort"`

**Checkpoint:** Todos los ports importan correctamente

### Batch 8: Fase 0 Completion (30 min)

**Verificación:**
```bash
# 1. Ollama running
curl -s http://localhost:11434/api/tags | jq '.models[] | select(.name | contains("nomic"))'

# 2. IFEval calibration existe
cat data/ifeval-calibration.json | jq .statistics

# 3. Baseline medido
cat data/baseline-v3.0.json | jq .results

# 4. Feature flags configurados
cat config/feature_flags.json | jq .

# 5. Ports definidos
ls -la hemdov/domain/ports/

# 6. Tests pasando
make test
```

**Checkpoint:** Fase 0 completa, listo para Fase 1-4

---

## 📦 Archivos a Crear

| Archivo | Ubicación | Descripción |
|--------|-----------|-------------|
| `ifeval_validator.py` | hemdov/domain/services/ | **NUEVO: Validación real sin mocks** |
| `bootstrap_ifeval_calibration.py` | scripts/ | Usa IFEvalValidator real |
| `measure_baseline.py` | scripts/ | Métricas baseline |
| `feature_flags.py` | hemdov/infrastructure/config/ | Feature flags |
| `cache_port.py` | hemdov/domain/ports/ | Cache protocol |
| `vectorizer_port.py` | hemdov/domain/ports/ | Vectorizer protocol |
| `metrics_port.py` | hemdov/domain/ports/ | Metrics protocol |

---

## ✅ Verificación Final

Después de completar todos los batches:

```bash
# Resumen de Fase 0
echo "✅ FASE 0 COMPLETA"
echo "- Ollama: nomic-embed-text listo"
echo "- Calibration: threshold calibrado"
echo "- Baseline: métricas guardadas"
echo "- Feature flags: infraestructura lista"
echo "- Ports: 3 ports definidos"
```

---

## 🚦 Go/No-Go Decision Points

### Después de Fase 0

**Auto-Go si:**
- ✅ Ollama instalado y validado
- ✅ Calibration bootstrapped
- ✅ Baseline medido
- ✅ Feature flags creadas
- ✅ Ports definidos
- ✅ Tests pasando

### Antes de Fase 3

**MUST ejecutar PoC script:**
```bash
uv run python scripts/poc_ollama_embeddings.py
# Expected: All 4 criteria PASS
```

---

## 📊 Timeline (Actualizado: SIN Mocks)

| Batch | Tarea | Tiempo | Acumulado |
|-------|-------|--------|-----------|
| 1 | Setup | 30 min | 30 min |
| 2 | Task 0.1: Ollama | 1 hora | 1.5 horas |
| 3a | Task 0.2a: IFEvalValidator | 1-2 horas | 2.5-3.5 horas |
| 3b | Task 0.2b: Calibration REAL | 2-3 horas | 4.5-6.5 horas |
| 4 | Task 0.3: Baseline | 1-2 horas | 5.5-8.5 horas |
| 5 | Task 0.4: Feature flags | 1-2 horas | 6.5-10.5 horas |
| 6 | Task 0.5: Ports | 1 hora | 7.5-11.5 horas |
| 7 | Completion | 30 min | **8-12 horas total** |

**Cambio clave:** +1 hora por implementar IFEvalValidator real en lugar de usar mocks

---

## 🎯 Instrucciones para el Agente

**Usar skill:** `superpowers:executing-plans`

**Workflow:**
1. Cargar este plan
2. Ejecutar batches 1-7 en orden
3. Reportar después de cada batch
4. Usar `superpowers:finishing-a-development-branch` al final

**Si encuentra blocker:**
- Stop y reportar
- No adivinar
- Pedir clarificación

---

**Plan Version:** 2.1 (Ejecución NLaC Pipeline - SIN Mocks)
**Status:** ✅ Ready for Another Session
**Estimated Time:** 8-12 horas (Fase 0 completa con IFEvalValidator REAL)
