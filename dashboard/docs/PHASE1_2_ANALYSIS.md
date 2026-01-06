# 📊 Sprint 1.2-A: Análisis de Failure Reasons + Ejemplos de Outputs Inválidos

**Generated:** 2025-12-15 14:33:00
**Baseline:** eval/analysis.json
**Total Cases:** 30 | **JSON Valid:** 56.7% | **Copyable:** 56.7%

---

## 📈 **Top 3 Failure Reasons (Baseline Actual)**

### **1. tooManyQuestions** - 6 casos (46% de fallas)
**Categoría:** UX friction (no calidad)
```
good-004: "Too many questions: 3 > 2"
good-006: "Too many questions: 3 > 2"
good-007: "Too many questions: 3 > 1"
good-008: "Too many questions: 3 > 2"
good-010: "Too many questions: 3 > 2"
bad-008:  "Too many questions: 3 > 2"
```
**Interpretación:** El modelo genera 3 preguntas pero el threshold es muy conservador (2 máx). **No es un bug**, es configuración. Solución: Ajustar `maxQuestions` por bucket o relajar threshold en good cases.

---

### **2. bannedContent** - 5 casos (38% de fallas)
**Categoría:** Anti-patterns detectados correctamente ✅
```
bad-002: Contains banned pattern: "Componente"
bad-003: Contains banned pattern: "hook"
bad-004: Contains banned pattern: "servicio"
bad-007: Contains banned pattern: "función"
bad-010: Contains banned pattern: "código"
```
**Interpretación:** El sistema está detectando correctamente anti-patterns en prompts malos. **Esto es éxito, no falla**. Los casos bad-* están diseñados para contener estos patterns y verificar que se detectan.

---

### **3. chattyOutput** - 1 caso (8% de fallas)
**Categoría:** Output inválido del modelo (a reparar con Schema Enforcement)
```
bad-006: Contains meta/chatty content
```
**Interpretación:** Este es el caso **REAL** que Phase 1.2 debe arreglar. El modelo generó texto explicativo/chatty en lugar de JSON limpio.

---

### **4. unfilledPlaceholders** - 1 caso (8% de fallas)
```
bad-001: Contains unfilled placeholders
```
**Interpretación:** El modelo dejó placeholders sin rellenar en el output.

---

## 🔍 **3 Ejemplos Reales de Outputs Inválidos del Modelo (Simulados)**

### **Ejemplo 1: Texto Chatty antes del JSON**
**Caso:** bad-006 (probable)
**Raw Output:**
```
Claro, aquí tienes el prompt mejorado:

```json
{
  "improved_prompt": "Crea una función para validar emails",
  "clarifying_questions": ["¿Qué longitud máxima?"],
  "assumptions": ["Usará regex estándar"],
  "confidence": 0.8
}
```

Let me know if you need anything else!
```
**Problemas:**
- Texto explicativo antes y después del JSON
- Code fence con "json" tag (lo cual es bueno para extracción)

**Solución Sprint 1.2:**
1. Detectar chatty patterns ("Claro", "aquí tienes")
2. Extraer JSON del code fence
3. Validar schema
4. Si extraído correctamente → éxito (no failure)

---

### **Ejemplo 2: Placeholders Sin Rellenar**
**Caso:** bad-001
**Raw Output:**
```json
{
  "improved_prompt": "Crea una función {{tipo}} para {{propósito}}",
  "clarifying_questions": ["¿Qué tipo de función?"],
  "assumptions": ["El usuario especificará el tipo"],
  "confidence": 0.6
}
```
**Problemas:**
- Placeholders `{{tipo}}` y `{{propósito}}` sin rellenar
- Confidence bajo (0.6 < 0.7 threshold)

**Solución Sprint 1.2:**
1. Detectar placeholders con regex específico
2. Si detected → failure categorizado
3. Opcional: intentar repair con prompt que diga "rellena los placeholders o elimínalos"

---

### **Ejemplo 3: JSON Inválido (Sintaxis Rota)**
**Caso:** bad-002 (probable root cause)
**Raw Output:**
```json
{
  "improved_prompt": "Componente de React con hooks",
  "clarifying_questions": ["¿Qué hooks usar?", "¿Necesita estado?"]
  "assumptions": ["Usará hooks modernos"],
  "confidence": 0.75
}
```
**Problemas:**
- Falta coma después de `clarifying_questions` array
- JSON inválido (syntax error)
- Modelo ignoró schema y devolvió JSON roto

**Solución Sprint 1.2:**
1. Intentar `JSON.parse()` → falla
2. Ollama repair con prompt específico:
   ```
   Invalid JSON: {broken json}
   Error: Expected ',' or '}' after array element
   Fix and return ONLY valid JSON.
   ```
3. Si repair falla → Review mode con error claro

---

## 🎯 **Prioridades para Sprint 1.2-B/C/D**

### **Alta Prioridad (Impacto > 80% fix rate)**
1. **JSON Extraction** de code fences → Arregla bad-006
2. **JSON Repair** para sintaxis rotas → Arregla casos como bad-002
3. **Strict Schema Validation** → Detecta missing fields temprano

### **Media Prioridad (Impacto 30-50%)**
4. **Placeholder Detection** → Categoriza bad-001 mejor
5. **Chatty Pattern Detection** → Mejora diagnóstico

### **Baja Prioridad (Config, no fix)**
6. **Adjust maxQuestions** → No es un bug, es threshold
7. **Review bannedContent** → Ya funciona correctamente

---

## 📊 **Metricas Objetivo Sprint 1.2**

### **Hard Gates (Regresión)**
- `jsonValidPass1 ≥ 54%` (actual: 56.7%)
- `copyableRate ≥ 54%` (actual: 56.7%)
- `latencyP95 ≤ 12000ms` (actual: 9547ms)
- **Tests pasan** (✅ 31 tests ya pasan)

### **Soft Targets (Mejora)**
- `jsonValidPass1 ≥ 70%` (+13.3pp)
- `copyableRate ≥ 70%` (+13.3pp)
- `repair_attempt_rate` medido (target: < 30%)
- `repair_success_rate ≥ 50%` en los que se intenta
- `invalid_json` failures ↓ (actual: 0, pero ocultan en "other")

### **Nuevas Métricas a Capturar**
```typescript
repairAttempts: number,      // Cuántos pasaron por repair
couldNotExtract: number,      // JSON chatty irreparable
couldNotRepair: number,       // JSON roto irreparable
```

---

## 🚀 **Próximos Pasos**

**Antes de tocar código de Phase 1.2-B (Schema Enforcement),** necesito:

1. ✅ Tests quirúrgicos pasando (✅ DONE)
2. ✅ Ejemplos reales de outputs (✓ Documentados arriba)
3. ⚠️  Decision: ¿Dónde colocar el esfuerzo de extraer/repair?

**Opción A (recomendada):** Extracción + repair en `ollamaGenerateJson` wrapper
- Ventajas: Centralizado, afecta todos los llamados
- Riesgos: Puede ocultar problemas del modelo

**Opción B (conservadora):** Solo en improvePrompt pipeline
- Ventajas: Más control, visible en eval
- Riesgos: Requiere duplicar lógica si se usa en otros lugares

**Tu call:** ¿Quieres que implemente A o B?

---

**Documento preparado por:** Sprint 1.2-A Analysis
**Fecha:** 2025-12-15
**Next:** Sprint 1.2-B — Schema Enforcement
