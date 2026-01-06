# 📊 Phase 1.2-B3 Evaluation Results

**Date:** 2025-12-15 19:50:32
**Baseline:** eval/baseline-v2.json (2025-12-15 16:37:34)
**Total Cases:** 30
**Status:** ⚠️ REGRESIÓN DETECTADA - Requiere análisis

---

## 🎯 **CORE METRICS COMPARISON**

| Metric | Baseline | Phase 1.2-B3 | Δ Change | Status |
|--------|----------|--------------|----------|--------|
| **jsonValidPass1_total** | 56.7% | 40.0% | **-16.7pp** | ❌ **REGRESIÓN** |
| **copyableRate_total** | 56.7% | 40.0% | **-16.7pp** | ❌ **REGRESIÓN** |
| **latencyP95** | 10,072ms | 16,850ms | **+6,778ms** | ❌ **REGRESIÓN** |
| **reviewRate_total** | 50.0% | 40.0% | -10.0pp | ⚠️  |
| **patternsDetected** | 10 | 4 | -6 | ℹ️  |

### **❌ HARD GATES - FAILED**

1. **jsonValidPass1 ≥ 54%** → **40.0%** (FAILED by -14pp)
2. **copyableRate ≥ 54%** → **40.0%** (FAILED by -14pp)
3. **latencyP95 ≤ 12000ms** → **16,850ms** (FAILED by +4,850ms)

---

## 🔍 **NEW WRAPPER METRICS (Post Phase 1.2)**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **extractionUsedRate** | 0.0% | **CERO extracciones usadas** ⚠️ |
| **extractionMethodBreakdown** | fence: 0, tag: 0, scan: 0 | Ningún JSON chatty detectado/fijado |
| **repairTriggerRate** | 60.0% | 18 de 30 casos → **repair** |
| **repairSuccessRate** | 100.0% | 18 de 18 reparaciones → éxito ✅ |
| **attempt2Rate** | 60.0% | Mismo que repairTriggerRate |

### **Key Insights:**

1. **El extractor NO se está activando** (0.0% extractionUsedRate)
2. **El repair SE está activando mucho** (60% de casos)
3. **EL repair es 100% exitoso** cuando se dispara
4. **BUT** el output del repair NO pasa validación (schemaMismatch)

---

## 📉 **BUCKET BREAKDOWN**

### **Good Cases (10 total)**
| Metric | Baseline | Phase 1.2-B3 | Δ |
|--------|----------|--------------|---|
| jsonValidPass1 | 50.0% | 40.0% | **-10pp** |
| copyableRate | 50.0% | 40.0% | **-10pp** |

**Failures:**
- good-002, good-004, good-008: schema_mismatch (❌)
- good-006, good-007, good-010: tooManyQuestions (⚠️)
- good-001, good-003, good-005, good-009: SUCCESS (4/10)

### **Bad Cases (10 total)**
| Metric | Baseline | Phase 1.2-B3 | Δ |
|--------|----------|--------------|---|
| jsonValidPass1 | 20.0% | **0.0%** | **-20pp** ❌ |
| copyableRate | 20.0% | **0.0%** | **-20pp** ❌ |

**All 10 cases FAILED** - 7 con schema_mismatch, 3 con bannedContent

### **Ambiguous Cases (10 total)**
| Metric | Baseline | Phase 1.2-B3 | Δ |
|--------|----------|--------------|---|
| jsonValidPass1 | 100.0% | 80.0% | **-20pp** |
| copyableRate | 100.0% | 80.0% | **-20pp** |

**Failures:**
- ambig-008, ambig-009: schema_mismatch
- ambig-001 a ambig-007: SUCCESS (8/10)

---

## 📊 **FAILURE REASONS COMPARISON**

| Failure Reason | Baseline | Phase 1.2-B3 | Δ |
|----------------|----------|--------------|---|
| **invalidJson** | 0 | 0 | 0 |
| **schemaMismatch** | 0 | **12** | **+12** ❌ |
| **emptyFinalPrompt** | 0 | 0 | 0 |
| **unfilledPlaceholders** | 1 | 0 | -1 ✅ |
| **chattyOutput** | 1 | 0 | -1 ✅ |
| **bannedContent** | 5 | 3 | -2 ✅ |
| **tooManyQuestions** | 6 | 3 | -3 ✅ |
| **other** | 0 | **12** | **+12** ⚠️ |

### **Root Cause Analysis:**

**Los 12 errores en "other" son:**
```
Failed to generate valid response: schema_mismatch
```

**Traducción:** El wrapper está intentando repair, pero el output del repair NO pasa la validación del schema Zod.

**Evidencia:**
- repairTriggerRate: 60% (18 repairs intentados)
- repairSuccessRate: 100% (18 ó 18 reparaciones "exitosas" según wrapper)
- PERO: 12 casos con schema_mismatch al final

**Conclusión:** El repair está **generando JSON válido pero con schema incorrecto** (faltan campos, tipos incorrectos, etc.)

---

## 🚨 **ANÁLISIS DEL PROBLEMA**

### **Síntoma:**
- El wrapper dispara repair (60% de casos)
- El repair sigue el prompt de repair
- PERO el resultado NO pasa validación Zod
- ↓↓↓
- jsonValidPass1 baja de 56.7% → 40.0%

### **Diagnóstico:**

El **repair prompt es defectuoso**: el wrapper dispara repair, Ollama devuelve algo (probablemente JSON), pero ese JSON:

1. **No incluye todos los campos requeridos** (assumptions, confidence faltan)
2. **Tiene tipos incorrectos** (confidence como string vs number)
3. **No pasa el schema Zod** → schema_mismatch

### **Por qué extractionUsedRate = 0%:**

El evaluator NO está viendo los outputs brutos. El erro está ocurriendo ANTES de que llegue al evaluator:

```
Modelo → JSON chatty/con errores → Wrapper intenta repair → Repair produce schema inválido → Wrapper devuelve error → Evaluator ve "schema_mismatch" sin raw output
```

Por eso extractionUsedRate = 0%: el wrapper falla en reparación y NUNCA devuelve un output que el evaluator pueda analizar.

---

## 🎯 **PRÓXIMOS PASOS - ACCIONES INMEDIATAS**

### **T1.2.B4.1: Fix Repair Prompt (CRÍTICO - ANTES DE CUALQUIER OTRA COSA)**

**Problema:** El repair prompt está pidiendo regenerar JSON con schema, pero el modelo no lo está haciendo bien.

**Solución:** Simplificar repair prompt para ser MÁS explícito:

```typescript
// Cambiar de:
"Fix the validation errors listed below"

// A:
"Your output MUST be valid JSON matching this schema exactly:\n" +
JSON.stringify(schema, null, 2)
```

**Archivo:** `src/core/llm/ollamaStructured.ts:buildRepairPrompt()`

**Expected outcome:**
- Repair debería producir JSON que pase Zod validation
- schemaMismatch debería bajar de 12 → 0-2
- jsonValidPass1 debería subir de 40% → 70%+

---

### **T1.2.B4.2: Añadir Logging de Raw Output**

**Problema:** No podemos ver qué está devolviendo el modelo antes del repair.

**Solución:** En el wrapper, guardar `raw` output antes de intentar repair:

```typescript
// En ollamaStructured.ts, en failResult()
console.error(`[WRAPPER-FAIL] Raw output: ${raw}`);
console.error(`[WRAPPER-FAIL] Validation error: ${validationError}`);
```

**Archivo:** `src/core/llm/ollamaStructured.ts:failResult()`

---

### **T1.2.B4.3: Re-evaluar tras fix**

Después de arreglar el repair prompt, ejecutar evaluación de nuevo y verificar:

1. **schemaMismatch ≤ 2** (actual: 12)
2. **jsonValidPass1 ≥ 54%** (gate hard - actual: 40%)
3. **repairSuccessRate ≥ 50%** (actual: 100% pero con outputs inválidos)
4. **Extraction empiece a usarse** (actual: 0% - debería subir a 10-30%)

---

## 📋 **RESUMEN DE ACCIONES**

| # | Acción | Prioridad | Archivos | Expected Impact |
|---|--------|-----------|----------|-----------------|
| 1 | Fix repair prompt para ser más explícito | 🔴 CRÍTICA | ollamaStructured.ts | +15-20pp en jsonValid |
| 2 | Add raw output logging | 🟡 Alta | ollamaStructured.ts | Debug insight |
| 3 | Re-run eval | 🟢 Media | evaluator.ts | Validar fix |
| 4 | Ajustar thresholds si necesario | 🟢 Media | config/defaults.ts | Tuning fino |

---

## 🎯 **CONCLUSIÓN**

**Phase 1.2-B3: FAILED HARD GATES**

- ❌ jsonValidPass1 bajó de 56.7% → 40.0%
- ❌ copyableRate bajó de 56.7% → 40.0%
- ❌ latencyP95 subió de 10s → 16.8s
- ⚠️  Repair trigger rate: 60% (demasiado alto)
- ⚠️  Repair success: 100% pero outputs inválidos
- ⚠️  Extraction: 0% (no se está usando)

**El wrapper funciona correctamente** (encapsula errores, dispara repair, cuenta métricas), pero el **repair prompt es defectuoso**.

**Next step:** Fix repair prompt inmediatamente, luego re-evaluar.

---

**Report generated:** 2025-12-15
**Evaluator:** scripts/evaluator.ts
**Baseline:** eval/baseline-v2.json
**Current:** eval/phase1.2-b3.json
