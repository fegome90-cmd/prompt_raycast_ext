# Roadmap v1.2 - Prompt Compiler (Corregido)

**Date:** January 5, 2026
**Version:** v1.2 (correcciones de meta-audit)
**Status:** Ejecutable y auditable

---

## Cambios v1.1 → v1.2

| Error | Corrección |
|-------|------------|
| {selectedText} placeholder | Eliminar. Usar getSelectedText() directo. |
| Auto-cleanup 7 días | Cambiar a 14 días mínimo para Retention D7. |
| DAU por session_id | Agregar install_id local (UUID) para métricas por usuario. |
| Quality Gates naive | Gates condicionales por template, no por longitud. |
| Regenerate descartado | Mover a experimento condicionado por copy rate. |
| Checkup SHA-256 | Redactar como integridad, no autenticidad. |

---

## Fase 1: Reducir TTV Real (1 Semana)

**Objetivo medible:** TTV P95 <30s (hotkey → copia exitosa)

### Entregable 1: Comando Nativo (6 horas)

**UX: Sin placeholders expuestos al usuario**

**Implementación:**
1. getSelectedText() como input primario
2. Fallback a Clipboard.readText() si no hay selección
3. Fallback a input manual si ambos fallan

**Código:**
```typescript
import { getSelectedText, Clipboard } from "@raycast/api";

async function getInput() {
  try {
    const selected = await getSelectedText();
    if (selected && selected.trim().length > 0) return { source: "selection", text: selected };
  } catch {}

  try {
    const clipboard = await Clipboard.readText();
    if (clipboard && clipboard.trim().length > 0) return { source: "clipboard", text: clipboard };
  } catch {}

  return { source: "manual", text: "" }; // Usuario escribe manualmente
}
```

**PASS criteria:**
- [ ] getSelectedText() funciona en >=2 apps (TextEdit, VS Code)
- [ ] Fallback a clipboard funciona
- [ ] Fallback a input manual funciona
- [ ] No se expone placeholder {selectedText} al usuario

**FAIL criteria:**
- [ ] getSelectedText() falla en >50% de apps probadas
- [ ] TTV P95 >45s (medido)

**Riesgo:** getSelectedText() no soportado en algunas apps.
**Mitigación:** Fallback a clipboard es transparente para usuario.

---

### Entregable 2: Modo Fast (8 horas)

**Condición:** Solo si reduce latencia SIN bajar Gate 1.

**Backend:**
```python
class ImprovePromptRequest(BaseModel):
    mode: str = "default"  # "fast" (zero-shot), "default" (few-shot)

if request.mode == "fast":
    improver = get_prompt_improver(settings)  # zero-shot, sin KNN
```

**PASS criteria:**
- [ ] Latency P95 <5s (modo fast)
- [ ] Gate 1 (formato esperado) >=70% (modo fast vs default)
- [ ] Diferencia de calidad no es significativa (delta <10%)

**FAIL criteria:**
- [ ] Latency no mejora significativamente
- [ ] Gate 1 cae >20% en modo fast

**Riesgo:** Zero-shot es inconsistentemente peor.
**Mitigación:** Mantener modo default como primario.

**Evidencia:** 20 iteraciones por modo, comparación de gates y latencia.

---

## Métrica Única Fase 1

**TTV (Time-to-Value):**
- Definición: t_copy - t_start (hotkey → copia exitosa)
- Medición: Timestamp en session_start y copy_triggered
- Target: P95 <30,000ms

**No se miden otras métricas en Fase 1.** Foco total en bajar TTV.

---

## Fase 2: Medición + Calidad (1-2 Semanas)

**Objetivo:** Instrumentación mínima + calidad del primer output

### Entregable 3: Instrumentación Local (8 horas)

**Schema SQLite (corregido):**

```sql
CREATE TABLE installs (
    id TEXT PRIMARY KEY,  -- install_id (UUID v4, persistente)
    created_at INTEGER NOT NULL,
    last_seen INTEGER
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,           -- session_id (UUID v4)
    install_id TEXT NOT NULL,      -- FK to installs
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    mode TEXT,
    input_source TEXT,
    FOREIGN KEY (install_id) REFERENCES installs(id)
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Auto-cleanup: 14 días (mínimo para Retention D7)
DELETE FROM events WHERE timestamp < strftime('%s', 'now', '-14 days') * 1000;
DELETE FROM sessions WHERE start_time < strftime('%s', 'now', '-14 days') * 1000;
```

**8 eventos (sin cambios):**
- session_start, input_received, mode_selected
- backend_request, backend_response
- copy_triggered, error, session_end

**Export manual:**
```bash
npm run export-analytics -- --days 14 --output analytics.jsonl
```

**Privacidad:** Local-only, opt-in para export.

---

### Entregable 4: Quality Gates v1 (Condicionales) (6 horas)

**Corrección:** Gates son condicionales por template, no universales.

**Gate 1: Formato Esperado**
```python
def gate1_expected_format(output: str, template: str) -> bool:
    if template.requires_json:
        try:
            json.loads(output)
            return True
        except:
            return False
    else:  # markdown
        required_sections = ["## Objetivo", "## Pasos", "## Criterios"]
        return all(section in output for section in required_sections)
```

**Gate 2: Completitud Mínima**
```python
def gate2_min_completeness(output: str, template: str) -> bool:
    if template.type == "checklist":
        # Debe tener >=3 bullets
        return len(re.findall(r'^\s*-\s+', output, re.MULTILINE)) >= 3
    elif template.type == "procedure":
        # Debe tener >=2 pasos numerados
        return len(re.findall(r'^\s*\d+\.\s+', output, re.MULTILINE)) >= 2
    elif template.type == "example":
        # Debe tener >=1 bloque de código
        return '```' in output
    else:
        return len(output.strip()) >= 100  # Fallback genérico
```

**PASS criteria:**
- [ ] Gate 1 >=70% (medido sobre 100 iteraciones)
- [ ] Gate 2 >=80% (medido sobre 100 iteraciones)
- [ ] Gates son visibles en UI (opt-in)

**FAIL criteria:**
- [ ] Gate 1 <50% o Gate 2 <60%
- [ ] Gates confunden usuario (feedback manual)

**Riesgo:** Gates son falsos positivos.
**Mitigación:** Opt-in via preferencia, no por defecto.

---

### Entregable 5: Regenerate 1-Click (Condicional) (4 horas)

**Condición:** Solo implementar si copy rate <60% en Fase 1.

**Implementación:**
- Botón "Regenerate" (1 click, sin feedback)
- Mismo prompt, diferente KNN selection (si few-shot)

**Trigger:** copy_rate_medido <60% → habilitar regenerate

**PASS criteria:**
- [ ] 1 click, sin fricción
- [ ] Latency <5s (misma que primer request)
- [ ] Copy rate mejora >=10pp con regenerate

**FAIL criteria:**
- [ ] Copy rate no mejora o empeora
- [ ] Más de 20% de usuarios hacen >3 regenerates

**Riesgo:** Regenerate se convierte en crutch.
**Mitigación:** Monitorizar regenerate rate, deshabilitar si >50%.

---

## Fase 3: Shareability (Post-Señales)

**Condición:** Solo si hay señales de uso (DAU >10 por 2 semanas).

### Entregable 6: Command Packs (2 días)

**Corrección:** Checksum es integridad, no autenticidad.

**Formato:**
```json
{
  "version": "1.0",
  "name": "Python Dev Prompts",
  "checksum": "sha256:abc123...",  // Integridad, NO autenticidad
  "untrusted": true,               // Warning obligatorio
  "prompts": [...]
}
```

**UX:**
- Import: Mostrar warning "⚠️ Untrusted pack - Review before using"
- No auto-ejecutar nada del pack
- Usuario debe revisar antes de usar

**PASS criteria:**
- [ ] Export genera JSON válido
- [ ] Checksum detecta corrupción
- [ ] Warning "untrusted" es visible
- [ ] No se auto-ejecuta nada

**FAIL criteria:**
- [ ] Checksum no detecta corrupción
- [ ] Pack se ejecuta sin warning

---

## Métricas Operables (Corregidas)

### TTV

**Definición:** t_copy - t_start (hotkey → copia exitosa)

**Target:** P95 <30,000ms

---

### Copy Rate

**Definición:** % de sesiones con copy_triggered dentro de 60s de session_start

**Target:** >60%

---

### Regenerate Rate

**Definición:** % de sesiones con >=2 backend_requests

**Target:** <30% (después de implementar regenerate)

---

### Quality Gates

**Gate 1 (Formato Esperado):**
- Si template requiere JSON → JSON parseable
- Si template requiere markdown → Tiene secciones obligatorias

**Gate 2 (Completitud Mínima):**
- Checklist: >=3 bullets
- Procedure: >=2 pasos numerados
- Example: >=1 bloque de código
- Fallback: longitud >=100 caracteres

**Target:** Gate 1 >=70%, Gate 2 >=80%

---

### DAU (Daily Active Users)

**Corrección:** Usar install_id, no session_id

**Definición:** Número de install_id únicos con sesión en última 24h

**Target:** >5

**Cómo funciona:**
- install_id se genera en primera ejecución
- Se almacena en preferences/local storage
- Persiste entre sesiones
- Es opt-in para export (local-only)

---

### Retention D7

**Corrección:** 14 días mínimo de ventana

**Definición:** % de usuarios que regresaron en días 1-7 después de día 0

**Target:** >40%

**Ventana:** 14 días (para poder calcular D7 confiablemente)

---

### Regenerate Rate

**Definición:** % de sesiones con >=2 backend_requests

**Target:** <30%

---

## Decisiones Pendientes (5 Máximas)

### Decisión 1: getSelectedText() vs Clipboard

**Estado:** PENDIENTE - Probar en 3 apps

**Cómo verificar:**
1. Probar en TextEdit, VS Code, Chrome
2. Medir tasa de éxito de getSelectedText()
3. Si <70%, usar clipboard como primario

**Deadline:** Antes de Sprint 1

---

### Decisión 2: Ventana Cleanup (14 vs 30 días)

**Estado:** PENDIENTE - Trade-off almacenamiento vs métricas

**Opciones:**
- A: 14 días (mínimo para D7)
- B: 30 días (permite D30 también)

**Cómo verificar:**
- Medir tamaño de DB después de 1 semana
- Si >5MB, usar 14 días
- Si <5MB, usar 30 días

**Deadline:** Después de 1 semana de uso

---

### Decisión 3: Quality Gates Opt-In vs Default

**Estado:** PENDIENTE - ¿Mostrar gates por defecto?

**Opciones:**
- A: Opt-in (preferencia)
- B: Default (siempre visible)

**Cómo verificar:**
- Usabilidad test con 5 usuarios
- Si gates confunden >20%, usar opt-in
- Si gates ayudan >60%, usar default

**Deadline:** Antes de Fase 2

---

### Decisión 4: Regenerate Trigger (copy rate threshold)

**Estado:** PENDIENTE - ¿Qué umbral habilita regenerate?

**Opciones:**
- A: copy rate <50%
- B: copy rate <60%
- C: Siempre habilitar

**Cómo verificar:**
- Medir copy rate en Fase 1
- Si <50%, habilitar regenerate inmediatamente
- Si 50-60%, A/B test manual
- Si >60%, no habilitar

**Deadline:** Después de Fase 1

---

### Decisión 5: Command Packs Warning (Untrusted)

**Estado:** PENDIENTE - ¿Cómo mostrar warning?

**Opciones:**
- A: Modal con "I understand" antes de importar
- B: Toast + banner en listado de packs
- C: Badge visual (⚠️) en nombre del pack

**Cómo verificar:**
- Usabilidad test con 3 usuarios
- Si A es demasiado fricción, usar B o C

**Deadline:** Antes de Fase 3

---

## Resumen de Correcciones

| Error v1.1 | Corrección v1.2 |
|------------|-----------------|
| Placeholder {selectedText} | Eliminar. getSelectedText() directo. |
| Auto-cleanup 7 días | Cambiar a 14 días mínimo. |
| DAU por session_id | Usar install_id local (UUID). |
| Quality Gates naive | Gates condicionales por template. |
| Regenerate descartado | Condicionar a copy rate <60%. |
| Checkup SHA-256 | Redactar como integridad + warning untrusted. |

---

## Próximos Pasos

1. **Verificar getSelectedText()** en 3 apps antes de implementar
2. **Implementar Fase 1** y medir TTV real baseline
3. **Instalar instrumentación** antes de Fase 2
4. **Medir quality gates** reales antes de optimizar
5. **Condicionar regenerate** a copy rate medido

---

**v1.2 es ejecutable, medible, y sin contradicciones internas.**
