# Roadmap Actualizado: Oportunidades de Mejora - Prompt Compiler

**Date:** January 5, 2026
**Status:** Updated with subagent analysis
**Sources:** 4 parallel agent analyses (Technical, Integrations, UX/Product, Architecture)

---

## Executive Summary

Basado en el análisis exhaustivo con subagentes paralelos, el roadmap se **re-prioriza** para atacar el problema crítico identificado en el audit competitivo: **time-to-value >90s**.

**Hallazgo clave:** El 80% de las oportunidades analizadas son **postergables** hasta resolver la fricción fundamental de adopción.

---

## Matriz de Decisión Consolidada

| Oportunidad | Complejidad | Esfuerzo | Riesgo | Valor | **Decisión** |
|-------------|-------------|----------|--------|-------|--------------|
| **Wrapper nativo Raycast** | 2/5 | 3-4h | Bajo | ALTO | ✅ PRIORITARIA |
| **Placeholder {selectedText}** | 1/5 | 1-2h | Ninguno | ALTO | ✅ PRIORITARIA |
| **Modo Fast (sin few-shot)** | 2/5 | 4-6h | Bajo | MEDIO | ✅ PRIORITARIA |
| **Métricas visibles (minimal)** | 1/5 | 1h | Bajo | MEDIO | ⏳ MANTENER (fase 2) |
| **Command Pack Exportable** | 2/5 | 2d | Medio | MEDIO | ⏳ MANTENER (fase 3) |
| **Refinamiento iterativo** | 3/5 | 3d | Medio | MEDIO | ⏳ POSTERGAR |
| **Integración Prompt Stash** | 4/5 | 1d | Alto | BAJO | ❌ DESCARTAR |
| **Modo Evaluar** | 5/5 | 4d | Alto | BAJO | ❌ DESCARTAR |
| **Raycast AI post-procesador** | 4/5 | 4d | Alto | INCIERTO | ⚠️ ARRIESGADO |
| **LangChain Hub integración** | N/A | N/A | N/A | N/A | ❌ NO APLICA |

---

## Fase 1: Resolver Time-to-Value (CRÍTICO - 30 días)

**Objetivo:** Reducir time-to-first-improve de 90s+ a <30s

### Sprint 1: Placeholder {selectedText} (1-2 horas)

**Archivos:**
- `dashboard/src/promptify-quick.tsx`

**Implementación:**
```typescript
const expandSelectedTextPlaceholder = async (text: string): Promise<string> => {
  if (text.includes("{selectedText}")) {
    try {
      const selected = await getSelectedText();
      return text.replace("{selectedText}", selected);
    } catch {
      return text.replace("{selectedText}", "");
    }
  }
  return text;
};
```

**PASS criteria:**
- [ ] Usuario puede escribir "Improve this: {selectedText}"
- [ ] Funciona sin selección (graceful degradation)
- [ ] Maneja selección multilinea

---

### Sprint 2: Wrapper Nativo (3-4 horas)

**Archivos:**
- Nuevo: `dashboard/src/promptify-selected.tsx`
- Modificar: `dashboard/package.json`

**Implementación:**
```typescript
import { getSelectedText, Clipboard, Detail, ActionPanel } from "@raycast/api";

export default async function Command() {
  const selectedText = await getSelectedText();
  const result = await improvePromptWithHybrid({
    rawInput: selectedText,
    // ... config
  });
  return <Detail markdown={result.improved_prompt} actions={...} />;
}
```

**PASS criteria:**
- [ ] Hotkey directo desde selección funciona
- [ ] Latency end-to-end <15s
- [ ] Error handling robusto

---

### Sprint 3: Modo Fast (4-6 horas)

**Archivos:**
- `api/prompt_improver_api.py` - agregar parámetro `mode`
- `dashboard/src/core/llm/dspyPromptImprover.ts` - enviar `mode`

**Implementación:**
```python
class ImprovePromptRequest(BaseModel):
    mode: str = "default"  # "fast", "default", "fewshot"

if request.mode == "fast":
    improver = get_prompt_improver(settings)  # zero-shot
```

**PASS criteria:**
- [ ] Latency P95 <3s en modo fast
- [ ] Quality gates pass rate >50%
- [ ] A/B test muestra preferencia por fast en 60%+ de casos

---

## Fase 2: Simplificar (Post Time-to-Value - 60 días)

**Objetivo:** Añadir valor sin añadir fricción

### Sprint 4: Métricas Visibles Minimalistas (1 hora)

**Formato recomendado:**
```
✅ JSON Valid: 98%
⚡ Latency: 2.3s
🎯 Confidence: 87%
```

**NO mostrar:**
- ~~JSON Valid Pass 1~~ (técnico)
- ~~Copyable Rate~~ (obvio para usuario)
- ~~Backend name~~ (implementación detail)

**PASS criteria:**
- [ ] Solo 3 métricas visibles
- [ ] Formato semáforo (🟢/🟡/🔴)
- [ ] Usuario entiende sin explicación

---

### Sprint 5: Regenerate Simple (opcional)

**Implementación:**
- Un botón "Regenerate" (sin feedback)
- Usa misma semilla DSPy pero diferente KNN selection

**PASS criteria:**
- [ ] 1 click vs 3-4 del refinamiento
- [ ] Latency <5s
- [ ] Tasa de satisfacción >70%

---

## Fase 3: Shareability (Post Validación - 90 días)

**Objetivo:** Crecimiento orgánico vía compartir

### Sprint 6: Command Pack Exportable (2 días)

**Formato:**
```json
{
  "version": "1.0",
  "name": "Python Dev Prompts",
  "prompts": [
    {
      "input": "validate email",
      "output": "...",
      "role": "Python Developer",
      "confidence": 0.87
    }
  ]
}
```

**Safeguards críticos:**
- [ ] Quality gates al importar (pass rate >60%)
- [ ] Warning si prompts son de baja calidad
- [ ] Firma digital para verificar fuente

**PASS criteria:**
- [ ] Exportar/importar funciona
- [ ] Al menos 1 pack creado por usuario externo
- [ ] Quality gates se mantienen >60%

---

## Características POSTERGADAS (Sin fecha)

### Refinamiento Iterativo

**Razón para postergar:**
- Añade 3-4 clicks al flow
- Complejidad UX media (3/5)
- Solo es valioso si el primer output es subóptimo
- **Mejor:** Resolver calidad del primer output antes

**Implementación futura (si se justifica):**
- Quick feedback tags: "Shorter", "More examples", "More formal"
- NO texto libre (demasiado complejo)

---

### Integración Raycast AI (AI Extension con Tool)

**Veredicto:** ARRIESGADO - Proceder con cautela

**Razones:**
- ✅ Técnicamente viable como AI Extension
- ⚠️ No hay hooks para interceptar output nativo
- ⚠️ Latencia añadida (+3-5s)
- ⚠️ Requiere Raycast Pro ($8/mes)

**Estrategia híbrida recomendada:**
1. Mantener modo standalone (actual)
2. Añadir AI Extension como opción secundaria
3. Fallback automático si backend falla
4. Medir agresivamente (primeros 30 días)

**Criterio PASS/FAIL:**
- ✅ PASS: Latency P95 <8s Y Quality >60%
- ❌ FAIL: Latency >10s O Quality <50% → PIVOT

---

## Caracterías DESCARTADAS

### Integración Prompt Stash

**Razón:**
- Storage no es diferenciador
- Usuario puede exportar manualmente
- Complejidad técnica media-alta
- Valor estratégico bajo

**Alternativa:** Usuario copia output y guarda manualmente

---

### Modo Evaluar (Comparación vs Baseline)

**Razón:**
- Complejidad UX muy alta (5/5)
- Usuario NO quiere "evaluar", quiere "usar"
- Es feature de marketing, no de producto
- ROI negativo: 4 días para feature que <5% usará

**Alternativa:** Mostrar benchmarks en página web (marketing)

---

### LangChain Hub Integration

**Aclaración:** NO es una integración de producto

**Uso real:**
- Source de datos para encontrar candidatos a prompts
- Se usa en entrenamiento, no en runtime
- Los prompts se validan y agregan al dataset propio curado

**Acción:** Continuar usando como source, no como feature

---

## Resumen de Esfuerzo

| Fase | Características | Esfuerzo Total | Valor Estratégico |
|------|----------------|----------------|-------------------|
| **Fase 1** | Wrapper, Placeholder, Fast | 8-12 horas | CRÍTICO |
| **Fase 2** | Métricas minimal, Regenerate | 2 horas | ALTO |
| **Fase 3** | Command Packs | 2 días | MEDIO |
| **Postergrado** | Refinamiento, Raycast AI | 7 días | INCIERTO |
| **Descartadas** | Prompt Stash, Evaluar | 0 ahorrados | N/A |

**Total para 30 días:** ~12 horas de desarrollo

---

## Criterios de Éxito Actualizados

### Hitos 30 Días

**PASS:**
- ✅ Time-to-value <30s (actual: 90s+)
- ✅ Copy rate >60% (actual: 54%)
- ✅ DAU >5

**FAIL:**
- ❌ Time-to-value >45s
- ❌ Copy rate <50%
- ❌ DAU <3

### Hitos 60 Días

**PASS:**
- ✅ Regenerate rate <30%
- ✅ NPS proxy >40

**FAIL:**
- ❌ Regenerate rate >45%
- ❌ NPS <20

### Hitos 90 Días

**PASS:**
- ✅ Instalaciones >50
- ✅ Retention D7 >40%
- ✅ Quality gate pass rate >60%

**FAIL:**
- ❌ Instalaciones <20
- ❌ Retention D7 <20
- ❌ Quality gate pass rate <50%

---

## Archivos Clave Identificados

```
Backend Python:
├── main.py:76 - Configuración DSPy
├── api/prompt_improver_api.py - Endpoint /improve-prompt
├── eval/src/dspy_prompt_improver.py - Zero-shot
└── eval/src/dspy_prompt_improver_fewshot.py - Few-shot

Frontend TypeScript:
├── dashboard/src/promptify-quick.tsx - Comando actual
├── dashboard/src/core/llm/improvePrompt.ts - Lógica mejora
└── dashboard/src/core/llm/dspyPromptImprover.ts - Cliente HTTP

Nuevos archivos a crear:
├── dashboard/src/promptify-selected.tsx - Wrapper nativo
└── dashboard/src/promptify-regenerate.tsx - Regenerate simple
```

---

## Fuentes

- **Análisis Técnico:** Agent ID a621933
- **Análisis Integraciones:** Agent ID a0342ce
- **Análisis UX/Producto:** Agent ID ad63737
- **Análisis Arquitectura:** Agent ID ad54408
- **Audit Competitivo:** `docs/reports/competitive_audit_prompt_compiler.md`

---

**Próxima revisión:** February 5, 2026 (30 días)
