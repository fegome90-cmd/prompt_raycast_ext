# Audit Critico: Roadmap v1.1 - Prompt Compiler

**Date:** January 5, 2026
**Auditor:** Critical Agent (fail-closed mode)
**Input:** Roadmap Actualizado (Jan 5, 2026)
**Status:** ERRATAS IDENTIFICADAS - CORRECCIONES REQUERIDAS

---

## 1. Dictamen Brutal

El roadmap está ** parcialmente alineado** con simplicidad operable pero contiene **overengineering encubierto** y **metrics sin medición**.

**Problemas críticos identificados:**

1. **Scope creep en Fase 3:** "Firma digital" para command packs es overengineering para v1. No hay amenaza real documentada que justifique criptografía.

2. **KPIs sin instrumentación:** "Copy rate >60%", "DAU >5", "NPS proxy >40", "Retention D7 >40%" - ninguno tiene plan de medición definido. Son aspiraciones, no métricas.

3. **A/B test sin infraestructura:** "A/B test muestra preferencia por fast en 60%+ de casos" - no hay sistema de A/B testing implementado. Es aspiracional.

4. **Time-to-value >90s:** Claim no verificado. No hay medición real del baseline actual. Es una estimación sin datos.

5. **Quality gates sin definición:** "Quality gate pass rate >60%" - no se define qué es un quality gate ni cómo se evalúa.

**Conclusión:** El roadmap tiene la dirección correcta (enfocarse en TTV) pero falla en ejecución: métricas sin medición, overengineering en Fase 3, y aspiraciones presentadas como compromisos.

---

## 2. Tabla de Erratas

| Item | Tipo | Estado | Por qué | Corrección Mínima | Evidencia Requerida |
|------|------|--------|---------|-------------------|-------------------|
| "Time-to-value >90s" | METRIC | **UNVERIFIED** | No hay medición real. Es estimación sin datos. | Medir baseline real antes de claim. | Cronómetro: hotkey → copia exitosa, 10 iteraciones. |
| "Copy rate >60% (actual: 54%)" | METRIC | **UNVERIFIED** | No hay tracking implementado. | Remover o definir plan de medición. | SQLite query: sesiones con copy / sesiones totales. |
| "DAU >5" | METRIC | **UNVERIFIED** | No hay analytics. | Cambiar a "5 usuarios únicos (verificado manualmente)". | Log local de timestamps por sesión. |
| "NPS proxy >40" | METRIC | **UNVERIFIED** | No hay survey implementada. | Remover o definir survey mínima. | Una pregunta post-copy: "¿Recomendarías? (1-10)". |
| "Retention D7 >40%" | METRIC | **UNVERIFIED** | Requiere tracking 7 días. | Cambiar a "Usuario vuelve en misma semana". | Log local: first_seen, last_seen timestamps. |
| "Quality gate pass rate >60%" | METRIC | **UNVERIFIED** | No se define qué es un gate. | Definir 1-2 gates específicos. | JSON parseable AND longitud >100 caracteres. |
| "A/B test muestra preferencia 60%" | METRIC | **ASPIRACIONAL** | No hay infra de A/B. | Cambiar a "experimento manual con 5 usuarios". | Grabación de pantalla + elección. |
| "Confidence score: 87%" | METRIC | **UNVERIFIED** | No se define cómo se calcula. | Definir fórmula o remover. | (few-shot_similarity * 0.5) + (structure_score * 0.5). |
| "{selectedText} placeholder" | ARCH | **UNVERIFIED** | No se verifica si Raycast API soporta esto. | Chequear documentación Raycast API. | Link a docs.raycast.com confirmando API. |
| "Firma digital para packs" | SCOPE | **OVERENGINEER** | Criptografía sin amenaza real documentada. | Remover. Hash SHA-256 suficiente. | Hash del pack en archivo, sin firma criptográfica. |
| "Latency end-to-end <15s" | METRIC | **OK** | Medible con timestamps. | N/A | t_end - t_start en log. |
| "Latency P95 <3s" | METRIC | **OK** | Medible con percentil. | N/A | Percentil 95 de latencias en log. |
| "Quality gates al importar" | SCOPE | **OVERENGINEER** | Importar con gates añade fricción. | Warning opcional, no bloqueo. | Toast de warning, no bloqueo de import. |
| "Sprint 5: Regenerate Simple" | SCOPE | **OUT OF SCOPE** | No reduce TTV ni mejora primer output. | Mover a "later". | Quitar de roadmap v1.1. |
| "Integración Raycast AI" | SCOPE | **OUT OF SCOPE** | No reduce TTV, añade latencia. | Mover a "investigación paralela". | Quitar de roadmap v1.1. |
| "Instalaciones >50" | METRIC | **UNVERIFIED** | No hay analytics de store. | Verificar manualmente o usar Raycast Store stats. | Screenshot de Raycast Store dashboard. |

---

## 3. Roadmap v1.1 (Re-priorizado - Máx 6 Entregables)

**Principio:** Si no reduce TTV o no mejora calidad del primer output, se va a "later".

### Fase 1: Reducir TTV (Semanas 1-1.5)

**Objetivo medible:** TTV P95 <30s (medido desde hotkey hasta copia exitosa)

#### Entregable 1: Placeholder {selection} (4 horas)

**Alcance:**
- Verificar que Raycast API soporta `getSelectedText()`
- Implementar placeholder que expande texto seleccionado
- Graceful degradation si no hay selección

**PASS criteria:**
- [ ] `getSelectedText()` funciona en >=2 apps (TextEdit, VS Code)
- [ ] Placeholder se expande correctamente en <=1s
- [ ] Sin selección = placeholder removido, no error

**FAIL criteria:**
- [ ] `getSelectedText()` no funciona o es inestable
- [ ] Expansión toma >2s

**Riesgo principal:** Raycast API no soporta selección cross-app.
**Mitigación:** Fallback a clipboard si selección falla.

**Evidencia:** Video demo de 30s mostrando expansión en 2 apps.

---

#### Entregable 2: Wrapper Nativo (6 horas)

**Alcance:**
- Nuevo comando `promptify-selected.tsx`
- Hotkey configurable
- Output directamente en Raycast UI (sin browser)

**PASS criteria:**
- [ ] Hotkey → seleccionar texto → improve → copia funciona
- [ ] TTV medido (10 iteraciones) tiene P95 <30s
- [ ] Error handling robusto (backend caído = mensaje claro)

**FAIL criteria:**
- [ ] TTV P95 >45s
- [ ] Más de 20% de intentos fallan

**Riesgo principal:** Backend HTTP no disponible.
**Mitigación:** Mensaje de error con instrucción de `make dev`.

**Evidencia:** Log de 10 iteraciones con TTV medido.

---

#### Entregable 3: Modo Fast (8 horas)

**Alcance:**
- Backend: parámetro `mode=fast` (zero-shot sin few-shot)
- Frontend: toggle o preferencia para activar
- Latency objetivo: P95 <5s (relajado desde 3s irreal)

**PASS criteria:**
- [ ] Latency P95 <5s en modo fast (medido)
- [ ] Output es JSON parseable en >=80% de casos
- [ ] Diferencia con modo default es visible en output

**FAIL criteria:**
- [ ] Latency P95 >8s
- [ ] Menos de 50% JSON parseable

**Riesgo principal:** Zero-shot es inconsistentemente peor que few-shot.
**Mitigación:** Mantener modo default como primary.

**Evidencia:** 20 iteraciones en modo fast, log de latencias y JSON parse rate.

---

### Fase 2: Instrumentación (Semana 2)

**Objetivo:** Poder medir todo sin speculation.

#### Entregable 4: Analytics Minimalista (6 horas)

**Alcance:**
- SQLite local: tabla `events` con 6 columnas (timestamp, event_type, session_id, metadata_json)
- 8 eventos máximo: session_start, input_received, mode_selected, backend_request, backend_response, copy_triggered, error, session_end
- Export manual: `npm run export-analytics` → JSONL

**PASS criteria:**
- [ ] Cada sesión genera >=5 eventos
- [ ] Export genera JSONL válido
- [ ] DB no crece >10MB en 1 semana (auto-cleanup)

**FAIL criteria:**
- [ ] DB crece >50MB en 1 semana
- [ ] Más de 10% de sesiones no tienen eventos

**Riesgo principal:** DB se convierte en bottleneck.
**Mitigación:** Auto-cleanup de eventos >7 días.

**Evidencia:** Export de 1 semana de uso, revisión de schema.

---

### Fase 3: Calidad del Primer Output (Semanas 3-4)

**Objetivo medible:** JSON parseable >=70%, TTV P95 <30s mantenido.

#### Entregable 5: Quality Gates Definidos (4 horas)

**Alcance:**
- Gate 1: JSON parseable (boolean)
- Gate 2: Longitud >=100 caracteres (boolean)
- Mostrar gates en output: "✅ JSON valid" o "❌ Invalid structure"

**PASS criteria:**
- [ ] JSON parse rate >=70% (medido sobre 100 iteraciones)
- [ ] Longitud >=100 en >=90% de casos
- [ ] Gates son visibles en UI

**FAIL criteria:**
- [ ] JSON parse rate <50%
- [ ] Gates confunden al usuario (feedback manual)

**Riesgo principal:** Gates son ruido, no signal.
**Mitigación:** Hacerlos opt-in via preferencia.

**Evidencia:** 100 iteraciones, log de pass/fail por gate.

---

#### Entregable 6: Command Packs (Sin Safeguards) (2 días)

**Alcance:**
- Export: JSON simple con array de prompts
- Import: Leer JSON y cargar en memoria
- **SIN** quality gates al importar
- **SIN** firma digital
- Hash SHA-256 del pack (integridad, no autenticidad)

**Formato minimal:**
```json
{
  "version": "1.0",
  "name": "My Prompts",
  "hash": "sha256:abc123...",
  "prompts": [
    {"input": "...", "output": "...", "timestamp": "2026-01-05T10:00:00Z"}
  ]
}
```

**PASS criteria:**
- [ ] Exportar pack genera JSON válido
- [ ] Importar pack carga prompts en memoria
- [ ] Hash verifica integridad (no autenticidad)

**FAIL criteria:**
- [ ] Import falla >10% de veces
- [ ] Pack corrupto no se detecta

**Riesgo principal:** Packs de mala calidad circulan.
**Mitigación:** Markdown en README explicando que packs son community-curated.

**Evidencia:** Export/import de 5 packs, verificación de hashes.

---

## Características Movidas a "Later" (Sin Fecha)

- ~~Sprint 5: Regenerate Simple~~ (No reduce TTV)
- ~~Integración Raycast AI~~ (No reduce TTV, añade latencia)
- ~~Métricas visibles minimalistas~~ (UX nice-to-have, no critico)
- ~~Refinamiento iterativo~~ (Mejorar primer output primero)
- ~~Firma digital para packs~~ (Overengineering)

---

## 4. Métricas Operables (Definiciones Exactas)

### TTV (Time-to-Value)

**Definición:** Tiempo desde hotkey/command open hasta "Copy to Clipboard" exitoso.

**Evento:** `session_start` (t0) → `copy_triggered` (t1)

**Cálculo:** `ttv_ms = t1 - t0`

**Unidad:** milisegundos

**Target:** P95 <30,000ms

---

### Copy Rate

**Definición:** Porcentaje de sesiones con evento `copy_triggered` dentro de 60s de `session_start`.

**Cálculo:** `copy_rate = count(copy_triggered within 60s) / count(session_start) * 100`

**Unidad:** porcentaje

**Target:** >60%

---

### Regenerate Rate

**Definición:** Porcentaje de sesiones con >=2 eventos `backend_request` (misma sesión).

**Cálculo:** `regenerate_rate = count(sessions with >=2 backend_requests) / count(session_start) * 100`

**Unidad:** porcentaje

**Target:** <30%

---

### Quality Gate Pass Rate

**Gate 1 (JSON Parseable):**
```python
import json
def gate1_json_parseable(output: str) -> bool:
    try:
        json.loads(output)
        return True
    except:
        return False
```

**Gate 2 (Longitud Mínima):**
```python
def gate2_min_length(output: str) -> bool:
    return len(output.strip()) >= 100
```

**Pass Rate:** `gate_pass_rate = count(gate1=True AND gate2=True) / count(total_outputs) * 100`

**Target:** >70%

---

### DAU (Daily Active Users)

**Definición:** Número de `session_id` únicos con `session_start` en última ventana de 24h.

**Cálculo:** `dau = count(distinct session_id where session_start in last 24h)`

**Unidad:** conteo

**Target:** >5

**Privacidad:** Todo local, sin telemetry a server. Opt-in para export manual.

---

### Retention D7

**Definición:** Porcentaje de usuarios que regresaron en una fecha posterior dentro de 7 días.

**Cálculo:**
```
users_day_0 = distinct session_id where session_start in day_0
users_returned = distinct session_id where session_start in day_1_to_7 AND session_id in users_day_0
retention_d7 = count(users_returned) / count(users_day_0) * 100
```

**Unidad:** porcentaje

**Target:** >40%

---

## 5. Plan de Instrumentación (Minimalista)

### Schema SQLite

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,  -- Unix timestamp ms
    session_id TEXT NOT NULL,     -- UUID v4
    event_type TEXT NOT NULL,     -- session_start, input_received, etc.
    metadata TEXT,                -- JSON string opcional
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,           -- session_id (UUID v4)
    start_time INTEGER NOT NULL,   -- Unix timestamp ms
    end_time INTEGER,              -- Unix timestamp ms (nullable)
    mode TEXT,                     -- "fast", "default", "fewshot"
    input_source TEXT,             -- "selection", "clipboard", "typed"
    metadata TEXT                  -- JSON string opcional
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_sessions_start ON sessions(start_time);
```

### Eventos (8 máximo)

| Event Type | Trigger | Metadata (JSON) |
|------------|---------|----------------|
| `session_start` | Comando abierto | `{"source": "hotkey" \| "menu"}` |
| `input_received` | Input del usuario | `{"length": 123, "source": "selection" \| "clipboard"}` |
| `mode_selected` | Usuario elige modo | `{"mode": "fast" \| "default"}` |
| `backend_request` | Request a backend | `{"mode": "fast", "input_length": 123}` |
| `backend_response` | Response de backend | `{"latency_ms": 2500, "json_parseable": true}` |
| `copy_triggered` | Usuario copia output | `{"output_length": 456}` |
| `error` | Cualquier error | `{"error_type": "backend_unavailable", "message": "..."}` |
| `session_end` | Sesión cerrada | `{"duration_ms": 30000, "events_count": 7}` |

### Auto-Cleanup

```python
# Correr diariamente via cron o al iniciar sesión
DELETE FROM events WHERE timestamp < strftime('%s', 'now', '-7 days') * 1000;
DELETE FROM sessions WHERE start_time < strftime('%s', 'now', '-7 days') * 1000;
```

### Export Manual

```bash
npm run export-analytics -- --days 7 --output analytics-7d.jsonl
```

Output (JSONL):
```json
{"timestamp": 1736107200000, "session_id": "abc-123", "event_type": "session_start", "metadata": {"source": "hotkey"}}
{"timestamp": 1736107200500, "session_id": "abc-123", "event_type": "input_received", "metadata": {"length": 45}}
```

### Privacidad

- Todo local (SQLite en `~/Library/Application Support/raycast-ext/`)
- Sin telemetry a server externo
- Export es manual (user-triggered)
- Opt-in para compartir analytics

---

## 6. Decisiones Pendientes (5 Máximo)

### Decisión 1: {selectedText} Placeholder

**Estado:** PENDIENTE - Verificar API Raycast

**Cómo verificar:**
1. Ir a https://developers.raycast.com/api-reference/get-selected-text
2. Confirmar que `getSelectedText()` existe y es estable
3. Probar en 2 apps (TextEdit, VS Code)

**Deadline:** Antes de Sprint 1 (Entregable 1)

**Fallback:** Si API no existe, usar clipboard como source.

---

### Decisión 2: Calcular Confidence Score

**Estado:** PENDIENTE - Definir fórmula

**Opciones:**
- A: `confidence = (few-shot_similarity * 0.5) + (json_parseable * 0.5)`
- B: `confidence = json_parseable ? 1.0 : 0.0` (binario)
- C: Remover confidence score (no mostrar al usuario)

**Cómo verificar:**
- Implementar A en 10 iteraciones
- Medir si correlaciona con satisfacción manual
- Si no correlaciona, usar B o C

**Deadline:** Antes de Fase 3 (Entregable 5)

---

### Decisión 3: Hash vs Firma Digital para Packs

**Estado:** DECIDIDO - Hash SHA-256 suficiente

**Razón:**
- Sin amenaza real documentada de packs maliciosos
- Firma criptográfica añade complejidad (key management)
- Hash detecta corrupción accidental (suficiente para v1)

**Implementación:**
```python
import hashlib
pack_json = json.dumps(pack, sort_keys=True)
pack_hash = hashlib.sha256(pack_json.encode()).hexdigest()
```

---

### Decisión 4: Medir DAU sin Analytics

**Estado:** PENDIENTE - Verificar Raycast Store stats

**Opciones:**
- A: Raycast Store tiene dashboard de installs
- B: Log local con opt-in del usuario
- C: Remover métrica DAU (no medible sin telemetría)

**Cómo verificar:**
1. Loguearse a Raycast Store dashboard
2. Ver si "Installs" está disponible
3. Si no, usar opción B o C

**Deadline:** Antes de hito 30 días

---

### Decisión 5: NPS Proxy sin Survey

**Estado:** PENDIENTE - Definir proxy medible

**Opciones:**
- A: "Repeat rate" - % sesiones que regresan en 7 días
- B: "Share rate" - % sesiones que exportan pack
- C: Remover NPS (no medible sin survey real)

**Cómo verificar:**
- Implementar A o B en instrumentación
- Medir baseline por 1 semana
- Si varía <10%, no es signal útil

**Deadline:** Antes de hito 60 días

---

## Resumen de Cambios v1.0 → v1.1

| Cambio | Razón |
|--------|-------|
| Remover "Firma digital" | Overengineering sin amenaza real |
| Remover "Quality gates al importar" | Añade fricción innecesaria |
| Remover Sprint 5 (Regenerate) | No reduce TTV |
| Remover Integración Raycast AI | No reduce TTV, añade latencia |
| Remover "A/B test 60%" claim | Sin infra, es aspiracional |
| Remover "DAU >5" como PASS | No medible sin Raycast Store stats |
| Cambiar "P95 <3s" a "P95 <5s" | Más realista |
| Añadir "Instrumentación" como Fase 2 | Poder medir sin speculation |
| Definir 2 quality gates solo | JSON parseable + longitud mínima |
| Reducir de 8 a 6 entregables | Foco en TTV y calidad primer output |

---

**Siguiente paso:** Ejecutar Fase 1 y medir baseline real de TTV antes de cualquier otro claim.
