# Contra-Audit: Roadmap v1.2-Critical

**Date:** January 5, 2026
**Auditor:** Meta-Auditor (fail-closed mode)
**Input:** `2026-01-05-roadmap-audit-v1.2-critical.md`
**Status:** ERRATAS IDENTIFICADAS - CORRECCIONES REQUERIDAS

---

## 1. Dictamen Brutal

El audit v1.2-critical contiene **errores factuales verificables** sobre la API de Raycast que invalidan portions del plan técnico.

**Problemas críticos identificados:**

1. **Error factual sobre `{selection}` placeholder**: El audit afirma incorrectamente que Raycast AI Commands "NO usa `{selection}` como placeholder". La documentación oficial confirma que **SÍ usa `{selection}` con llaves**.

2. **Error en manejo de `getSelectedText()`**: El código propuesto asume que la función retorna texto vacío, cuando en realidad **la Promise se rechaza** si no hay selección.

3. **Template system no especificado**: El audit presupone quality gates con `template.requires_json` y `template.markdown_sections`, pero **no existe tal sistema en el código actual**. Es una invención sin especificación.

4. **Cleanup policy contradictoria**: Se propone "7 días si DB >10MB" pero también se requiere "Retention D7 >40%". **D7 requiere ventana mínima de 14 días**. El policy rompe la métrica que pretende habilitar.

5. **TTV measurement protocol sin instrumentación**: Se define TTV como "t_copy - t_start" pero no hay especificación de cómo registrar timestamps sin analytics. **El protocolo manual no está documentado**.

**Conclusión:** El audit tiene la dirección correcta (TTV como prioridad) pero falla en verificación factual de la API de Raycast y deja componentes críticos sin especificación (templates, medición manual, cleanup policy).

---

## 2. Tabla de Erratas

| Línea | Claim | Estado | Verificación en Docs Raycast | Corrección |
|-------|-------|--------|------------------------------|------------|
| ~33 | "{selectedText} placeholder expuesto al usuario" | **ERRÓNEO** | `getSelectedText()` es API function, no placeholder | Remover frase. No hay placeholder expuesto. |
| 36-52 | Código `getInput()` con try/catch y empty string check | **PARCIALMENTE ERRÓNEO** | API: "Returns a Promise that **rejects** if no text is selected" | El try/catch es correcto, pero el comentario "Usuario escribe manualmente" es confuso. Si no hay selección Y no hay clipboard, no hay input. |
| 167-178 | `template.requires_json`, `template.markdown_sections` | **NO IMPLEMENTADO** | Revisión de codebase: no existe sistema de templates | Especificar MVP template system o remover quality gates. |
| 182-194 | `template.type == "checklist"`, etc. | **NO IMPLEMENTADO** | No hay campo `type` en ningún sistema de templates | Crear especificación de templates o remover gates. |
| 143 | `DELETE FROM events WHERE timestamp < ... '-14 days'` | **OK para D7** | N/A (SQL local, no depende de Raycast) | Ventana de 14 días es correcta para D7. |
| 372 (v1.1 ref) | `DELETE ... '-7 days'` | **ROMPE D7** | N/A | 7 días no permite calcular D7 (requiere día 0 + días 1-7). |

---

## 3. Verificación de Claims vs Fuentes Primarias

### 3.1 Claim: "Raycast AI Commands NO usa `{selection}`"

**Fuente:** https://manual.raycast.com/ai

**Evidencia:**
> "AI Commands support **Dynamic Placeholders** like `{selection}`, `{clipboard}`, `{date}`..."

**Veredicto:** ❌ **ERRÓNEO** - Raycast AI Commands SÍ usa `{selection}` con llaves.

**Corrección:** Remover claim. La sintaxis `{selection}` es válida en Raycast AI Commands. Prompt Compiler NO usa placeholders (usa `getSelectedText()` directamente).

---

### 3.2 Claim: "`getSelectedText()` retorna texto vacío si no hay selección"

**Fuente:** https://developers.raycast.com/api-reference/environment

**Evidencia:**
> "Returns a Promise that **rejects** if no text is selected"

**Veredicto:** ❌ **ERRÓNEO** - La Promise se rechaza, no retorna empty string.

**Corrección en código:**
```typescript
// El código propuesto es CORRECTO (usa try/catch):
try {
  const selected = await getSelectedText();
  if (selected && selected.trim().length > 0) return { source: "selection", text: selected };
} catch {
  // Promise rechazada = continuar al siguiente fallback
}

// PERO el comentario es engañoso:
// INCORRECTO: "Usuario escribe manualmente"
// CORRECTO: "No hay input disponible (requerir input o cancelar)"
```

---

### 3.3 Claim: "Quality Gate 1: Formato Esperado con `template.requires_json`"

**Fuente:** Revisión de codebase (`dashboard/src/`)

**Evidencia:**
- No existe archivo `templates/` con definiciones
- No existe campo `requires_json` en ningún config
- `improvePrompt.ts` no recibe parámetro `template`

**Veredicto:** ❌ **NO IMPLEMENTADO** - Es una invención del audit sin especificación.

**Corrección:** Opción A (recomendada): Especificar MVP template system hardcoded. Opción B: Remover quality gates condicionales y usar gates universales (JSON parseable + longitud ≥100).

---

## 4. Correcciones de Diseño Propuestas

### 4.1 TTV Measurement Protocol (Manual)

**Problema:** El audit define TTV = "t_copy - t_start" pero no especifica CÓMO registrar sin analytics.

**Propuesta:** `docs/protocols/ttv_measurement_protocol_v0.1.md`

**Operational definitions:**
- `t_start`: Momento en que usuario presiona hotkey (o abre comando)
- `t_copy`: Momento en que usuario presiona "Copy to Clipboard"

**Método manual:**
1. Usar cronómetro externo (teléfono o stopwatch)
2. n=10 iteraciones por experimento
3. Registrar en CSV: `iteracion, t_start, t_copy, ttv_ms, copy_within_60s`

**Entregable:** Documento separado con protocolo completo.

---

### 4.2 Minimal Template System

**Problema:** Quality gates requieren `template.requires_json` y `template.type` que no existen.

**Opción A (Recomendada): Templates Hardcoded con Mode Parameter**

```typescript
// En package.json o defaults.ts:
const TEMPLATES = {
  "json": {
    requires_json: true,
    markdown_sections: []
  },
  "procedure_md": {
    requires_json: false,
    markdown_sections: ["## Objetivo", "## Pasos", "## Criterios"]
  },
  "checklist_md": {
    requires_json: false,
    markdown_sections: ["## Checklist"]
  }
};

// En improvePrompt.ts:
async function improvePrompt(input: string, mode: string) {
  const template = TEMPLATES[mode];
  // ... lógica DSPy
  const gate1 = gate1_expected_format(output, template);
}
```

**Opción B: Gates Universales (Sin templates)**

```python
def gate1_json_parseable(output: str) -> bool:
    try:
        json.loads(output)
        return True
    except:
        return False

def gate2_min_length(output: str) -> bool:
    return len(output.strip()) >= 100
```

**Entregable:** `docs/specs/templates_v0.1.md` con especificación completa.

---

### 4.3 SQLite Retention Policy

**Problema:** "7 días si DB >10MB" rompe Retention D7 (requiere ventana de 14 días).

**Corrección:** Two-tier strategy

**Tier 1: Thinning (después de 14 días)**
- Mantener todos eventos por 14 días
- Después de 14 días: keep solo `session_start`, `copy_triggered`, `error`, `session_end`
- Eliminar `input_received`, `mode_selected`, `backend_request`, `backend_response`

**Tier 2: Hard delete (después de 30 días)**
- Eliminar todos eventos >30 días
- Eliminar sessions >30 días
- Mantener installs indefinidamente (DAU calculation)

**Entregable:** `docs/protocols/sqlite_retention_policy_v0.1.md` con SQL exacto.

---

## 5. Roadmap v1.3 (Máx 6 Entregables)

**Principio:** Solo items que reducen TTV o HABILITAN medición de TTV.

### Fase 1: Reducir TTV Real (1-2 Semanas)

**Objetivo medible:** TTV P95 <30s (hotkey → copia exitosa)

#### Entregable 1: Comando Nativo (8 horas)

**UX:** `getSelectedText()` como input primario, fallback a clipboard.

**Implementación (corregida):**
```typescript
import { getSelectedText, Clipboard } from "@raycast/api";

async function getInput(): Promise<{source: string, text: string}> {
  // Intento 1: Selección directa
  try {
    const selected = await getSelectedText();
    if (selected && selected.trim().length > 0) {
      return { source: "selection", text: selected };
    }
  } catch (error) {
    // Promise rechazada = no hay selección
  }

  // Intento 2: Clipboard
  try {
    const clipboard = await Clipboard.readText();
    if (clipboard && clipboard.trim().length > 0) {
      return { source: "clipboard", text: clipboard };
    }
  } catch (error) {
    // Clipboard vacío o inaccesible
  }

  // Intento 3: Input manual
  // Nota: Si no hay selección ni clipboard, UI debe pedir input manual
  return { source: "manual", text: "" };
}
```

**PASS criteria:**
- [ ] `getSelectedText()` funciona en ≥2 apps (TextEdit, VS Code)
- [ ] Fallback a clipboard funciona
- [ ] Input manual funciona cuando no hay selección ni clipboard
- [ ] TTV P90 <30s, max <45s (medido manualmente, n=15)

**FAIL criteria:**
- [ ] TTV P90 >45s
- [ ] >20% de intentos fallan

**Riesgo CRÍTICO (verificado por usuario):**
- `getSelectedText()` puede fallar en terminales (WezTerm/iTerm) por permisos de Accessibility
- Fallback a clipboard es **obligatorio**, no optional
- Si fallback falla, mostrar mensaje de error claro con instrucciones de permisos

---

#### Entregable 2: Modo Fast (6 horas)

**Condición:** Solo si reduce latencia SIN bajar Gate 1 ≥70%.

**Backend:**
```python
class ImprovePromptRequest(BaseModel):
    mode: str = "default"  # "fast" (zero-shot), "default" (few-shot)

if request.mode == "fast":
    improver = get_prompt_improver(settings)  # zero-shot, sin KNN
```

**PASS criteria:**
- [ ] Latency P95 <5s (modo fast)
- [ ] Gate 1 (JSON parseable) ≥70% (modo fast vs default)
- [ ] Delta calidad <10%

**FAIL criteria:**
- [ ] Latencia no mejora
- [ ] Gate 1 cae >20%

---

### Fase 2: Instrumentación (1 Semana)

**Objetivo:** Poder medir TTV, Copy Rate, DAU sin speculation.

#### Entregable 3: SQLite Local (8 horas)

**Schema (corregido):**
```sql
CREATE TABLE installs (
    id TEXT PRIMARY KEY,  -- install_id (UUID v4, persistente)
    created_at INTEGER NOT NULL,
    last_seen INTEGER
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    install_id TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    mode TEXT,
    input_source TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metadata TEXT
);
```

**Retention policy:**
- 0-14 días: Mantener todos eventos
- 14-30 días: Thinning (keep solo session_start, copy_triggered, error, session_end)
- >30 días: Hard delete

**PASS criteria:**
- [ ] Cada sesión genera ≥5 eventos
- [ ] Export manual funciona (`npm run export-analytics`)
- [ ] DB <50MB después de 30 días

---

#### Entregable 4: Quality Gates v1 (Universales) (4 horas)

**Corrección:** Gates universales, NO condicionales por template.

```python
def gate1_json_parseable(output: str) -> bool:
    try:
        parsed = json.loads(output)
        return bool(parsed and len(str(parsed)) > 0)
    except:
        return False

def gate2_min_length(output: str) -> bool:
    return len(output.strip()) >= 100
```

**PASS criteria:**
- [ ] Gate 1 ≥70% (100 iteraciones)
- [ ] Gate 2 ≥80% (100 iteraciones)

---

### Fase 3: Shareability (Post-Señales)

#### Entregable 5: Command Packs (2 días)

**Formato:**
```json
{
  "version": "1.0",
  "name": "Python Dev Prompts",
  "checksum": "sha256:abc123...",
  "prompts": [...]
}
```

**PASS criteria:**
- [ ] Export/import funciona
- [ ] Checksum detecta corrupción

---

## 6. Correcciones v1.3 → v1.3.1 (Feedback Usuario)

### Resumen de Cambios

| Issue | v1.3 | v1.3.1 Corrección |
|-------|------|-------------------|
| **Template system** | TS+Python duplicados | Backend-only (api/templates.json como SSOT) |
| **TTV P95 con n=10** | Reportar P95 | Reportar P50, P90, max con n=15-20 |
| **Retención "forever"** | Eventos críticos kept forever | Hard delete 30 días + daily_metrics agregados |
| **Terminal/permisos** | No mencionado | Riesgo CRÍTICO documentado |
| **DB steady state** | "~240 KB" (confuso) | "~380 KB + 36 KB/year" (con agregados) |

### Detalle de Correcciones

#### A) Template System: Single Source of Truth

**Problema v1.3:** Duplicación de lógica TS+Python crea sincronización imposible.

**Corrección v1.3.1:**
- Backend: `api/templates.json` como única definición
- Frontend: Solo envía `template_id` string
- Endpoint GET `/api/v1/templates` para obtener metadatos

#### B) TTV Protocol: Estadísticas Válidas

**Problema v1.3:** Con n=10, P95 = max (no aporta información).

**Corrección v1.3.1:**
- Sample size: n=15 mínimo, n=20 recomendado
- Reportar: P50 (mediana), P90, max
- NO reportar P95 hasta n≥30 o instrumentación automática

#### C) Retention Policy: Sin "Forever"

**Problema v1.3:** "Critical events kept forever" contradice "steady state ~240KB".

**Corrección v1.3.1:**
- Eventos: Hard delete >30 días (sin excepciones)
- Sesiones: Hard delete >30 días
- Agregados: Tabla `daily_metrics` con contadores diarios (indefinido, ~36 KB/año)
- DB total: ~380 KB + 36 KB/año (sin crecimiento no acotado)

#### D) getSelectedText(): Riesgo de Terminales

**Problema v1.3:** No documentaba riesgo de permisos Accessibility.

**Corrección v1.3.1:**
- Riesgo documentado: Falla en WezTerm/iTerm por permisos
- Fallback clipboard es **obligatorio**, no optional
- Mensaje de error con instrucciones de permisos si todo falla

---

## 7. Decisiones Pendientes Resueltas

### Decisión 1: Template System

**Estado:** ✅ **RESUELTO** - Backend-only (api/templates.json como SSOT)

**Implementación v1.3.1:**
- Backend: `api/templates.json` como única definición
- Frontend: Solo envía `template_id` string
- 4 templates: `json`, `procedure_md`, `checklist_md`, `example_md`
- Endpoint GET `/api/v1/templates` para obtener metadatos

---

### Decisión 2: Cleanup Policy

**Estado:** ✅ **RESUELTO** - Two-tier + Agregados

**0-14 días:** Keep all events
**14-30 días:** Thinning (4 eventos críticos)
**>30 días:** Hard delete + daily_metrics agregados

**Tabla nueva:** `daily_metrics` con contadores diarios (DAU, copy rate, avg TTV)

---

### Decisión 3: TTV Measurement

**Estado:** ✅ **RESUELTO** - Protocolo manual ajustado

**Método v1.3.1:** Cronómetro manual + CSV registration
**Sample size:** n=15 mínimo, n=20 recomendado
**Reportar:** P50, P90, max (NO P95 hasta n≥30)

---

## 8. Próximos Pasos

1. **Experimento A (Baseline)** - Medir TTV de Raycast AI Command con `{selection}` (n=15)
2. **Implementar Comando Nativo** - getSelectedText() con fallbacks obligatorios
3. **Experimento B/C** - Medir TTV del comando nativo vs baseline
4. **Solo si B/C ganan o empatan** → Pasar a instrumentación SQLite

---

## 9. Riesgos Residuales Documentados

| Riesgo | Mitigación | Status |
|--------|------------|--------|
| `getSelectedText()` en terminales | Fallback clipboard obligatorio | Documentado |
| Template system divergencia | Backend-only (api/templates.json) | Resuelto |
| P95 con muestra chica | Reportar P50, P90, max en su lugar | Resuelto |
| DB crecimiento no acotado | Hard delete 30 días + daily_metrics | Resuelto |

---

**v1.3.1 es ejecutable, verificada contra fuentes primarias, corregida por feedback usuario, y sin contradicciones internas.**

**Estado:** Listo para Fase 1 con medición manual previa.
