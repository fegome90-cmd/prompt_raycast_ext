# Handoff: DSPy DeepSeek Optimization

> **Para el próximo agente** - Este documento contiene todo el contexto necesario para continuar la optimización de DSPy con DeepSeek.

## Resumen Ejecutivo

### Completado: CRT-04 - Migración a DeepSeek Chat ✅

**Fecha:** 2026-01-02
**Estado:** COMPLETADO
**Resultado:** CRT-03 resuelto (60-70% failure rate → 0%)

### Problema Resuelto

| Métrica | Antes (Ollama) | Después (DeepSeek) | Mejora |
|---------|-----------------|-------------------|-------------|
| JSON parse success | 30-40% | **70%** | +30-40% |
| JSON failure rate | 60-70% | **0%** | Eliminado |
| Variability (10 runs) | 3/10 success | **10/10** | +233% |
| Latency p95 | ~12s | **4.9s** | ~60% más rápido |
| Quality gates | - | **3/4 PASSED** | ✅ |

## Estado Actual del Sistema

### Backend DSPy (main.py)

**Proveedor activo:** DeepSeek Chat
**Configuración actual:**

```python
# .env (NO trackeado en git)
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-c9fe1a8461104e8ea026cdc4dfe10da0
```

**Temperature por provider (main.py:28-34):**

```python
DEFAULT_TEMPERATURE = {
    "ollama": 0.1,    # Local models need variability
    "gemini": 0.0,    # Deterministic
    "deepseek": 0.0,  # CRITICAL: 0.0 for consistency
    "openai": 0.0,    # Deterministic
}
```

**Validación de API key (main.py:139-173):**
- Valida presencia y formato (sk- prefix)
- Log preview seguro (solo primeros 10 y últimos 4 caracteres)
- Fail-fast en startup si falta API key

### Infraestructura de Testing

**Evaluador con backend DSPy (mergeado en commit 47f5af6):**

```bash
cd dashboard && npm run eval -- \
  --dataset testdata/variance-hybrid.jsonl \
  --output eval/deepseek-eval.json \
  --backend dspy \
  --repeat 5
```

**Componentes clave:**

1. **evaluator.ts** - Soporta `--backend dspy` usando `improvePromptWithHybrid`
2. **improvePrompt.ts** - Función híbrida que intenta DSPy primero, fallback a Ollama
3. **build-variance-datasets.ts** - Generador de datasets híbridos
4. **Test scripts:**
   - `scripts/test-deepseek.sh` - Integración completa
   - `scripts/test-deepseek-variability.sh` - Test de consistencia (10 iteraciones)

### Datasets Disponibles

```bash
dashboard/testdata/
├── cases.jsonl                    # 30 casos base
├── ambiguity-cases.jsonl          # 3 casos ambigüedad
└── variance-hybrid.jsonl          # 73 casos (híbrido)
```

## Worktrees Activos

```bash
git worktree list
# /Users/felipe_gonzalez/Developer/raycast_ext                                    [master] ← ACTUAL
# /Users/felipe_gonzalez/Developer/raycast_ext/.worktrees/dspy-pipeline               [dspy-pipeline]
# /Users/felipe_gonzalez/Developer/raycast_ext/.worktrees/eval-variance-plan          [eval-variance-plan] ← MERGEADO
# /Users/felipe_gonzalez/Developer/raycast_ext/raycast_ext-worktrees/phase3-dspy-fewshot-optimization  [phase3-dspy-fewshot-optimization]
```

**Recomendación:** Los worktrees `dspy-pipeline` y `phase3-dspy-fewshot-optimization` pueden contener trabajo previo relevante.

## Próximos Pasos: Optimización DSPy + DeepSeek

### Oportunidades Identificadas

1. **Few-shot Learning**
   - El worktree `phase3-dspy-fewshot-optimization` tiene implementación de:
     - `DSPOptimizer` - Optimizador de few-shot examples
     - `ExamplePool` - Pool de ejemplos para selección
     - `SimilaritySelector` - Selección semántica de ejemplos
   - **Acción:** Evaluar si estos componentes mejoran la calidad con DeepSeek

2. **DSPy Compilation**
   - Actualmente el backend corre en modo zero-shot (sin compilar)
   - **Acción:** Compilar el `PromptImprover` con few-shot examples
   - **Beneficio:** Mejora consistencia y calidad

3. **Temperature Fine-tuning**
   - DeepSeek usa 0.0 (máxima consistencia)
   - **Acción:** Experimentar con valores bajos (0.0, 0.1, 0.2) para balance consistencia/creatividad

4. **Dataset Sintético**
   - Existe `datasets/exports/synthetic/` con datasets sintéticos
   - **Acción:** Usar para entrenamiento/compilación de DSPy

### Plan Sugerido (Pending Creation)

```
docs/plans/2026-01-02-dspy-fewshot-deepseek-optimization.md
```

**Fases propuestas:**

1. **Fase 1: Evaluación Base**
   - Ejecutar evaluator con `--backend dspy --repeat 10`
   - Medir métricas de ambigüedad
   - Comparar con baseline Ollama

2. **Fase 2: Few-shot Optimization**
   - Revisar implementación en `phase3-dspy-fewshot-optimization`
   - Integrar `ExamplePool` y `SimilaritySelector`
   - Compilar DSPy con dataset de ejemplos

3. **Fase 3: Validación**
   - Ejecutar tests de variabilidad
   - Medir mejora en calidad gates
   - Documentar resultados

## Archivos Clave para el Próximo Agente

### Backend Python
```
/Users/felipe_gonzalez/Developer/raycast_ext/
├── main.py                           # Backend FastAPI con DeepSeek
├── hemdov/
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   └── litellm_dspy_adapter_prompt.py  # DeepSeek adapter (línea 104)
│   │   └── config/
│   │       └── settings.py              # Configuración Pydantic
│   └── interfaces/
│       └── container.py                # Inyección de dependencias
└── api/
    └── prompt_improver_api.py         # FastAPI endpoints
```

### Frontend/Testing (TypeScript)
```
/Users/felipe_gonzalez/Developer/raycast_ext/dashboard/
├── scripts/
│   ├── evaluator.ts                   # Evaluador con --backend dspy
│   ├── build-variance-datasets.ts      # Generador de datasets
│   └── __tests__/
│       ├── evaluator.backend.test.ts   # Tests backend DSPy
│       ├── evaluator.ambiguity.test.ts # Tests ambigüedad
│       └── build-variance-datasets.test.ts
├── src/core/llm/
│   ├── improvePrompt.ts                # improvePromptWithHybrid
│   └── dspyPromptImprover.ts          # Cliente DSPy
└── testdata/
    ├── cases.jsonl
    ├── ambiguity-cases.jsonl
    └── variance-hybrid.jsonl
```

### Documentación
```
docs/auditoria/
├── CRT-03-variabilidad-semantica.md    # Problema original
├── CRT-04-migracion-deepseek-chat.md   # Solución implementada
├── CRT-04-rollback.md                  # Procedimiento de rollback
└── SEGUIMIENTO.md                      # Historial de cambios
```

## Comandos Útiles

### Iniciar Backend DSPy
```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
source .venv/bin/activate
python main.py
# Backend corre en http://localhost:8000
```

### Verificar Health
```bash
curl http://localhost:8000/health
# Debe mostrar: {"provider":"deepseek","model":"deepseek-chat"}
```

### Ejecutar Evaluación
```bash
cd dashboard
npm run eval -- \
  --dataset testdata/variance-hybrid.jsonl \
  --output eval/deepseek-eval.json \
  --backend dspy
```

### Test de Variabilidad
```bash
./scripts/test-deepseek-variability.sh
# 10 iteraciones, mide consistencia
```

## Seguridad

✅ **API Key segura:**
- `.env` está en `.gitignore`
- API key NO está en git history
- Solo placeholder en `.env.example`

⚠️ **ANTES de hacer commits:**
```bash
git check-ignore .env  # Debe retornar .env
git status --porcelain  # NO debe mostrar .env
```

## Rolling Back

Si algo sale mal:

```bash
# 1. Detener backend (Ctrl+C)
# 2. Restaurar Ollama
cp .env.backup.ollama .env
# 3. Reiniciar
python main.py
```

Ver `docs/auditoria/CRT-04-rollback.md` para detalles completos.

## Contexto del Proyecto

**Objetivo principal:** Mejorar la consistencia y calidad del DSPy Prompt Improver usando DeepSeek Chat en lugar de Ollama.

**Hitos clave:**
- ✅ CRT-01: Inconsistencia puerto DSPy (resuelto)
- ✅ CRT-02: Falta persistencia (documentado)
- ✅ CRT-03: Variabilidad semántica (resuelto con DeepSeek)
- ✅ CRT-04: Migración DeepSeek (COMPLETADO)

**Stack:**
- Backend: Python 3.11+, FastAPI, DSPy v3, LiteLLM
- Frontend: TypeScript, Raycast Extension API
- Testing: Vitest
- LLM: DeepSeek Chat (production), Ollama (fallback/local)

## Referencias

- Plan de migración: `docs/plans/2026-01-02-deepseek-chat-migration.md`
- Evaluador DSPy: `docs/claude.md` (líneas 199-203)
- Quickstart DSPy: `docs/backend/quickstart.md`

---

**Última actualización:** 2026-01-02
**Commits relevantes:** `c1719f0` → `bd2063d` (CRT-04 completo)
**Branch:** master
**Working directory:** `/Users/felipe_gonzalez/Developer/raycast_ext`
