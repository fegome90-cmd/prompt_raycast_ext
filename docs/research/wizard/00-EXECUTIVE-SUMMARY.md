# Executive Summary: Prompt Wizard + DSPy Integration

**Fecha:** 2026-01-01
**Fuente:** Auditoría DSPy HemDov + Análisis Architect
**Objetivo:** Decisión de inversión para integración Prompt Wizard con DSPy

---

## 🔴 Hallazgo Crítico

**DSPy HemDov NO implementa "Prompt Improvement" - Es el GAP que debes llenar.**

```
EXISTE (HemDov)              NECESITAS (Raycast)
┌──────────────────┐         ┌──────────────────┐
│ ✅ Tool Selection │         │ ❌ Prompt Improve│
│ ✅ Tool Execution │         │    (GAP CRÍTICO) │
│ ✅ Code Generation │         │ Idea → Better     │
└──────────────────┘         └──────────────────┘
```

---

## ✅ Estado Actual (Repositorio)

El pipeline DSPy + Ollama ya esta operativo en la extension Raycast.

```
Raycast Extension (TS)
     ↓ DSPy-first
FastAPI /api/v1/improve-prompt
     ↓
PromptImprover DSPy Module
     ↓
LiteLLM Adapter → Ollama (HF model)
```

**Nota:** En Raycast, DSPy es obligatorio cuando está habilitado; no hay fallback automático a Ollama. Para usar Ollama directo, desactiva DSPy en preferencias.

Config recomendado (Ollama + HF):

```
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434
```

---

## 📊 Análisis ROI por Componente

| Componente | Estado | Esfuerzo | ROI | Acción |
|------------|-------|----------|-----|--------|
| **PromptImprover Module** | ❌ NO EXISTE | 8-16h | 🔥🔥🔥 **MÁXIMO** | **CREAR** |
| LiteLLMDSPyAdapter | ✅ 100% listo | 0h | - | Reutilizar |
| DSPyOptimizer | ✅ 90% listo | 1h | 🔥🔥 ALTO | Adaptar |
| Test patterns | ✅ 100% listo | 2h | 🔥 MEDIO | Copiar |
| Settings infra | ✅ 100% listo | 0h | - | Reutilizar |

**Conclusión:** Solo necesitas crear el PromptImprover Module. Todo lo demás ya existe en HemDov.

---

## 🎯 Acción Recomendada: Crear PromptImprover

### Qué es exactamente

Un módulo DSPy que hace esto:

```
Input:  "Design ADR process"
Output: Complete SOTA prompt (Role + Directive + Framework + Guardrails)
```

### Arquitectura de la Solución

```
Raycast Extension (Swift/TS)
     ↓ HTTP POST
FastAPI Endpoint: /api/v1/improve-prompt
     ↓
PromptImprover DSPy Module (NUEVO - 8-16h)
     ↓
LiteLLMDSPyAdapter (EXISTE - Reutilizar)
     ↓
Ollama / Gemini / DeepSeek
```

### Esfuerzo por Fase

```
FASE 1: Core (3h) ← MÁXIMO ROI
├─ PromptImproverSignature (1h)
├─ PromptImprover Module (1h)
└─ Tests básicos (1h)

FASE 2: Optimización (4h) ← ROI ALTO
├─ Dataset de ejemplos (2h)
├─ Compilación BootstrapFewShot (1h)
└─ Validación (1h)

FASE 3: API (3h) ← ROI MEDIO
├─ FastAPI endpoint (1h)
├─ Integración adapter (1h)
└─ Tests integración (1h)

TOTAL: 8-16 horas
```

---

## 🚀 Quick Start (Si decides implementar)

### Opción A: Rápida (Zero-shot, sin optimizar)
**Tiempo:** 3-4 horas
**Calidad:** Media-Baja

```python
# 1. Crear Signature (30 min)
class PromptImproverSignature(dspy.Signature):
    original_idea = dspy.InputField(desc="User's raw idea")
    improved_prompt = dspy.OutputField(desc="Improved SOTA prompt")

# 2. Crear Module (30 min)
class PromptImprover(dspy.Module):
    def __init__(self):
        self.improver = dspy.Predict(PromptImproverSignature)

    def forward(self, original_idea: str):
        return self.improver(original_idea=original_idea)

# 3. Crear API endpoint (1-2h)
@app.post("/improve-prompt")
async def improve_prompt(request: ImprovePromptRequest):
    result = improver(original_idea=request.idea)
    return {"improved_prompt": result.improved_prompt}

# 4. Test desde Raycast (30 min)
await improvePrompt("Design ADR process")
```

### Opción B: Optimizada (Con few-shot learning)
**Tiempo:** 8-16 horas
**Calidad:** Alta

Añadir a Opción A:
- Dataset de 10-20 ejemplos (2h)
- Compilación BootstrapFewShot (1h)
- Métricas de calidad (1h)
- Tests completos (2h)

---

## 📁 Archivos Clave del Informe

| Archivo | Contenido Crítica |
|---------|-------------------|
| `/docs/research/wizard/DSPy_Audit_Report.md` | Informe completo auditoría |
| `/docs/research/wizard/03-dspy-integration-guide.md` | Guía actualizada con PromptImprover |
| `/docs/research/wizard/01-wizard-complete-flow.md` | Flujo wizard 6 pasos actual |
| `/docs/research/wizard/02-template-library-analysis.md` | 174+ templates analizados |

---

## ✅ Decision Checklist

Antes de comenzar implementación, verificar:

- [ ] Confirmar que HemDov DSPy está accesible
- [ ] Decidir provider LLM (Ollama local vs Gemini API vs DeepSeek)
- [ ] Definir si necesitas optimización (Opción B) o rápido (Opción A)
- [ ] Confirmar tiempo disponible (3-4h vs 8-16h)
- [ ] Validar que Raycast extension puede hacer HTTP calls

---

## 🎯 Resumen en 3 Puntos

1. **El GAP es claro:** HemDov tiene DSPy para tool execution, necesitas DSPy para prompt improvement
2. **La solución es clara:** Crear PromptImprover Module (8-16h), reutilizar todo lo demás
3. **El ROI es máximo:** Este es el único componente que falta para completar tu wizard de 1 paso

---

**Próximo paso:** Si confirmas que quieres proceder con la implementación, puedo generar el código completo listo para copiar/pegar.
