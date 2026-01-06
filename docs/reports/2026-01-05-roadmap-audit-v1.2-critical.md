# Auditoría Crítica v1.2 + Plan de Implementación

**Date:** January 5, 2026
**Auditor:** Critical Agent (fail-closed mode)
**Input:** Roadmap v1.2
**Status:** CRÍTICAS IDENTIFICADAS - PLAN TÉCNICO INCLUÍDO

---

## 1. Dictamen Brutal

El roadmap v1.2 está **alineado con "entra texto → sale prompt"** pero aún contiene **overengineering residual** y **métricas sin plan de medición**.

**Problemas críticos:**

1. **Fase 1 (TTV) no tiene plan de medición real:** Se dice "medir TTV P95" pero no se especifica CÓMO se registran los timestamps sin instrumentación formal. Es una aspiración sin método.

2. **Quality Gates v1 requieren sistema de templates:** No existe un sistema de templates en el producto actual. Implementar gates condicionales por `template.type` requiere construir primero un sistema de templates que no existe.

3. **Experimentos manuales A/B/C están descritos en roadmap pero no definidos:** "baseline Raycast AI Command + {selection}" - Raycast AI Commands NO usa `{selection}` como placeholder, usa `{selection}` sin llaves. Confusión de nuevo.

4. **"6 horas" para Entregable 1 es optimista sin conocer el código actual:** No se ha verificado si la arquitectura actual soporta el flujo propuesto.

**Conclusión:** El roadmap tiene la filosofía correcta pero **Fase 1 no es ejecutable sin un plan técnico detallado** y **Fase 2 asume templates que no existen**.

---

## 2. Claims UNVERIFIED

| Claim | Estado | Por qué | Cómo medir |
|-------|--------|---------|------------|
| "TTV P95 <30s" | **UNVERIFIED** | No hay baseline medido. | Cronómetro manual de 10 iteraciones en Fase 1. |
| "getSelectedText() funciona en >=2 apps" | **UNVERIFIED** | No se ha probado. | Test manual en TextEdit, VS Code, Chrome. |
| "Latency P95 <5s (modo fast)" | **UNVERIFIED** | No hay medición de modo fast. | 20 iteraciones en modo fast, calcular P95. |
| "Gate 1 >=70%" | **UNVERIFIED** | No hay sistema de templates. | Definir 3 templates primero, medir sobre 100 outputs. |
| "Gate 2 >=80%" | **UNVERIFIED** | No hay algoritmo validado. | Ejecutar 12 casos de prueba (ver sección 7). |
| "Copy rate >60%" | **UNVERIFIED** | Sin instrumentación, no se puede medir. | Implementar eventos copy_triggered primero. |
| "DAU >5" | **UNVERIFIED** | Sin install_id implementado. | Generar install_id, contar distinct últimos 7 días. |
| "Retention D7 >40%" | **UNVERIFIED** | Requiere 14 días de datos. | Esperar 14 días, calcular users_day0 / users_returned. |
| "Regenerate mejora copy rate >=10pp" | **UNVERIFIED** | Asunción sin datos. | A/B test manual con 5 usuarios. |
| "6 horas" para Entregable 1 | **UNKNOWN** | Sin revisión de código existente. | Revisar `promptify-quick.tsx`, estimar real. |
| "8 horas" para Modo Fast | **UNKNOWN** | Sin revisión de backend. | Revisar `prompt_improver_api.py`, estimar real. |
| "DAU >10 por 2 semanas" (señal Fase 3) | **UNKNOWN** | Umbral arbitrario. | Revisar benchmarks de Raycast Store. |

---

## 3. Riesgos Residuales (Top 8)

| # | Riesgo | Impacto | Probabilidad | Mitigación Mínima |
|---|--------|--------|-------------|-------------------|
| 1 | getSelectedText() falla en >50% de apps | ALTO | MEDIA | **Fallback a clipboard es transparente.** Test en 5 apps, si falla >30%, usar clipboard como primario. |
| 2 | Sistema de templates no existe | ALTO | ALTA | **Construir gates genéricos primero.** Gate 1: JSON parseable (si output parece JSON). Gate 2: longitud >=100 caracteres (fallback). Refinar en Fase 3. |
| 3 | Backend cae (no disponible) | ALTO | MEDIA | **Mensaje claro + instrucción.** "Backend no disponible. Ejecuta `make dev` en terminal." Toast con acción "Open Docs". |
| 4 | Modo fast baja calidad >20% | MEDIO | MEDIA | **Medir ANTES de habilitar modo default.** Si Gate 1 cae >20%, NO exponer modo fast al usuario. |
| 5 | DB SQLite crece >50MB | BAJO | BAJA | **Auto-cleanup agresivo.** 7 días (no 14) si DB >10MB. Trigger: al iniciar sesión, medir tamaño, ejecutar cleanup. |
| 6 | install_id se pierde (reinstalación) | MEDIO | MEDIA | **Regenerar install_id si no existe.** Al iniciar, buscar en localStorage. Si no existe, crear nuevo. No es crítico para retención local. |
| 7 | Quality gates confunden usuario | MEDIO | BAJA | **Opt-in por defecto.** Preferencia `show_gates: false`. Usuario debe activar manualmente para ver gates. |
| 8 | Regenerate se convierte en crutch | MEDIO | BAJA | **Límite duro + cooldown.** Máximo 3 regenerates por sesión. Cooldown de 30s entre regenerates. |

---

## 4. Definition of Done - Fase 1 (TTV)

**Objetivo:** TTV P95 <30s (hotkey → copia exitosa)

### Criterios PASS

1. **Funcionalidad:**
   - [ ] Usuario puede invocar comando vía hotkey
   - [ ] getSelectedText() obtiene texto de >=2 apps (TextEdit, VS Code)
   - [ ] Fallback a clipboard funciona cuando no hay selección
   - [ ] Fallback a input manual funciona cuando clipboard está vacío
   - [ ] Output se muestra en Raycast UI (no browser)

2. **Performance (TTV):**
   - [ ] 10 iteraciones de medición manual completadas
   - [ ] TTV P95 (percentil 95 de 10 mediciones) <30,000ms
   - [ ] TTV promedio <20,000ms

3. **Calidad Mínima:**
   - [ ] Output es copiable al clipboard
   - [ ] Output no está vacío (longitud >=50 caracteres)
   - [ ] Error se maneja gracefully (mensaje claro)

4. **Instrumentación Mínima:**
   - [ ] Timestamps se registran en archivo local (JSONL)
   - [ ] Formato: `{"t0": 1736107200000, "t_copy": 1736107230000, "ttv_ms": 30000}`
   - [ ] Archivo se guarda en `~/Library/Application Support/raycast-ext/ttv-logs.jsonl`

### Criterios FAIL

CUALQUIERA de los siguientes resulta en FAIL:

- [ ] TTV P95 >45,000ms (medido)
- [ ] getSelectedText() falla en >50% de apps probadas
- [ ] Más de 20% de intentos resultan en error visible
- [ ] Usuario no puede copiar output al clipboard
- [ ] Output está vacío o tiene longitud <20 caracteres

### Plan de Medición Fase 1 (Sin Instrumentación Formal)

**Método:** Cronómetro manual + export JSONL

1. **Preparación:**
   - Crear archivo `ttv-measurements.jsonl` vacío
   - Preparar cronómetro (o usar reloj con segundos)

2. **Por cada iteración:**
   - Presionar hotkey (iniciar cronómetro)
   - Esperar output
   - Presionar "Copy to Clipboard" (detener cronómetro)
   - Escribir en papel: `ttv_seconds = tiempo medido`
   - Después de 10 iteraciones, agregar al JSONL:
     ```jsonl
     {"iteration": 1, "ttv_ms": 28000, "source": "selection"}
     {"iteration": 2, "ttv_ms": 35000, "source": "clipboard"}
     ...
     ```

3. **Cálculo de P95:**
   - Ordenar ttv_ms ascendente
   - P95 = valor en posición 9 (de 10)
   - Si P95 <30000ms → PASS

**Evidencia requerida:** JSONL con 10 mediciones + cálculo de P95.

---

## 5. Plan Técnico Fase 1 (1 Página)

### Entregable 1: Comando Nativo Raycast

**Flujo exacto: `getSelectedText() → clipboard → input manual`**

```
Usuario presiona hotkey
    ↓
Comando Raycast se inicia
    ↓
getSelectedText() se ejecuta
    ↓
¿Texto obtenido? ──NO──→ Clipboard.readText()
    ↓                    ↓
   SÍ                  ¿Texto en clipboard?
    ↓                    │
Usar texto obtenido     ──NO──→ Mostrar input field
    ↓                    ↓
Llamar backend DSPy    Usuario escribe manualmente
    ↓                    ↓
Mostrar output en UI   Usuario presiona Enter
    ↓                    ↓
Copiar al clipboard    Llamar backend DSPy
    ↓                    ↓
Usuario ve output     Mostrar output en UI
                         ↓
                         Copiar al clipboard
```

### Manejo de Errores y Degradación

**Caso 1: getSelectedText() falla**
- Error: `getSelectedText() threw error` o retorna texto vacío
- Acción: Fallback silencioso a clipboard
- Log: `{"error": "getSelectedText failed", "fallback": "clipboard"}`

**Caso 2: Clipboard está vacío**
- Error: `Clipboard.readText()` retorna string vacío
- Acción: Mostrar input field con placeholder "Enter your prompt..."
- Log: `{"error": "clipboard empty", "fallback": "manual_input"}`

**Caso 3: Backend no disponible**
- Error: `fetch(http://localhost:8000/api/v1/improve-prompt)` timeout o connection refused
- Acción: Mostrar Detail view con:
  - Título: "Backend Unavailable"
  - Markdown: `## Backend DSPy is not running\n\nStart it:\n\`\`\`bash\ncd /path/to/raycast_ext\nmake dev\n\`\`\``
  - Actions: "Open Terminal" (abre terminal en dir del proyecto), "Retry"
- Log: `{"error": "backend_unavailable", "action": "show_instructions"}`

**Caso 4: Backend retorna error**
- Error: Response status >=500 o response contiene error
- Acción: Mostrar Toast con mensaje del backend
- Log: `{"error": "backend_error", "message": "..."}`

### Contrato de Salida

**Qué muestra:**
- Si output es markdown: `<Detail markdown={output} />`
- Si output es JSON: `<Detail markdown={\`\`\`json\n${output}\n\`\`\`} />`
- Si hay error: `<Detail markdown={error_message} />`

**Qué se copia:**
- Si output es string válido: `Clipboard.copy(output)`
- Si output es objeto con `improved_prompt`: `Clipboard.copy(result.improved_prompt)`
- Si hay error: Nada (no se copia)

**Qué se guarda:**
- Timestamp t0 (session start): `Date.now()`
- Timestamp t_copy (copy triggered): `Date.now()`
- Input source: `"selection"` | `"clipboard"` | `"manual"`
- Output length: `output.length`
- Error (si aplica): `error_type`

### Archivos a Tocar/Crear

**Nuevos archivos:**
1. `dashboard/src/promptify-selected.tsx` - Comando principal
2. `dashboard/src/core/input/getInput.ts` - Función getInput()
3. `dashboard/src/core/errors/handlers.ts` - Manejo de errores

**Archivos a modificar:**
1. `dashboard/package.json` - Agregar nuevo comando al manifest
2. `dashboard/src/core/llm/dspyPromptImprover.ts` - Reutilizar cliente HTTP existente

### Estructura de `promptify-selected.tsx`

```typescript
import {
  getSelectedText,
  Clipboard,
  Detail,
  ActionPanel,
  Action,
  showToast,
  Toast
} from "@raycast/api";

import { improvePromptWithHybrid } from "./core/llm/improvePrompt";
import { getInput } from "./core/input/getInput";
import { handleBackendError } from "./core/errors/handlers";

export default async function Command() {
  const t0 = Date.now();

  try {
    // Paso 1: Obtener input
    const input = await getInput();

    if (!input.text || input.text.trim().length < 5) {
      await showToast({
        style: Toast.Style.Failure,
        title: "No input found",
        message: "Select text or copy to clipboard first"
      });
      return <Detail markdown="## No Input\n\nSelect text in any app, then try again." />;
    }

    await showToast({ style: Toast.Style.Animated, title: "Improving prompt..." });

    // Paso 2: Llamar backend
    const result = await improvePromptWithHybrid({
      rawInput: input.text,
      // ... config
    });

    // Paso 3: Mostrar output
    const t_copy = Date.now();
    const ttv_ms = t_copy - t0;

    // Guardar log local
    await logTtvMeasurement({
      t0,
      t_copy,
      ttv_ms,
      source: input.source,
      output_length: result.improved_prompt.length
    });

    // Copiar al clipboard automáticamente
    await Clipboard.copy(result.improved_prompt);

    return (
      <Detail
        markdown={result.improved_prompt}
        actions={
          <ActionPanel>
            <Action.CopyToClipboard
              title="Copy Improved Prompt"
              content={result.improved_prompt}
            />
          </ActionPanel>
        }
      />
    );

  } catch (error) {
    return handleBackendError(error, t0);
  }
}

async function logTtvMeasurement(data: TtvLog) {
  // Guardar en JSONL local
  const fs = require('fs');
  const path = require('path');
  const logPath = path.join(
    require('os').homedir(),
    'Library/Application Support/raycast-ext/ttv-logs.jsonl'
  );
  const logEntry = JSON.stringify({ ...data, timestamp: Date.now() }) + '\n';
  await fs.promises.appendFile(logPath, logEntry);
}
```

### Acceptance Tests Reproducibles

**Test 1: getSelectedText() funciona**
```bash
# PASO: En TextEdit, escribir "test prompt for email validation"
# ACCIÓN: Seleccionar texto, presionar hotkey
# EXPECTED: Output se muestra, ttv <30s
# FAIL: Output vacío o error
```

**Test 2: Fallback clipboard**
```bash
# PASO: Copiar "test prompt" al clipboard, NO seleccionar nada
# ACCIÓN: Presionar hotkey
# EXPECTED: Output se muestra, source="clipboard"
# FAIL: Pide input manual
```

**Test 3: Fallback manual**
```bash
# PASO: NO seleccionar nada, clipboard vacío
# ACCIÓN: Presionar hotkey
# EXPECTED: Input field aparece, usuario escribe, presiona Enter
# FAIL: Error o no pasa a input manual
```

**Test 4: Backend caído**
```bash
# PASO: Asegurar que backend NO está corriendo
# ACCIÓN: Presionar hotkey con texto seleccionado
# EXPECTED: Mensaje "Backend Unavailable" con instrucciones
# FAIL: Crashea o error genérico
```

**Test 5: TTV P95 <30s**
```bash
# PASO: Ejecutar comando 10 veces, medir con cronómetro
# ACCIÓN: Calcular P95
# EXPECTED: P95 <30000ms
# FAIL: P95 >45000ms
```

---

## 6. Schema de Instrumentación SQLite (Fase 2)

### DDL Completo

```sql
-- Tabla installs (una fila por instalación)
CREATE TABLE IF NOT EXISTS installs (
    id TEXT PRIMARY KEY,              -- install_id (UUID v4)
    created_at INTEGER NOT NULL,     -- Unix timestamp (ms)
    last_seen INTEGER,                -- Unix timestamp (ms) de última sesión
    metadata TEXT                    -- JSON string opcional
);

-- Tabla sessions (una fila por sesión)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,              -- session_id (UUID v4)
    install_id TEXT NOT NULL,         -- FK to installs
    start_time INTEGER NOT NULL,      -- Unix timestamp (ms)
    end_time INTEGER,                 -- Unix timestamp (ms) o NULL si está activa
    mode TEXT,                       -- "fast", "default", "fewshot"
    input_source TEXT,                -- "selection", "clipboard", "manual"
    output_length INTEGER,            -- Longitud del output en caracteres
    gate1_pass INTEGER,              -- 0 = fail, 1 = pass, NULL = no ejecutado
    gate2_pass INTEGER,              -- 0 = fail, 1 = pass, NULL = no ejecutado
    FOREIGN KEY (install_id) REFERENCES installs(id)
);

-- Tabla events (una fila por evento)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,       -- Unix timestamp (ms)
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,         -- "session_start", "backend_request", "copy_triggered", etc.
    metadata TEXT,                   -- JSON string opcional
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Índices mínimos (4)
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_install ON sessions(install_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
```

### Queries para Métricas

**TTV P95:**
```sql
SELECT
  (e_end.timestamp - e_start.timestamp) as ttv_ms
FROM events e_start
JOIN events e_end ON e_start.session_id = e_end.session_id
WHERE e_start.event_type = 'session_start'
  AND e_end.event_type = 'copy_triggered'
ORDER BY ttv_ms ASC
LIMIT 1 OFFSET 9;  -- P95 de 10 = posición 9 (0-indexed)
```

**Copy Rate:**
```sql
SELECT
  COUNT(DISTINCT s.id) as total_sessions,
  COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END) as sessions_with_copy,
  (CAST(COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END) AS FLOAT) / COUNT(DISTINCT s.id)) * 100 as copy_rate
FROM sessions s
LEFT JOIN events e ON s.id = e.session_id
WHERE s.start_time > strftime('%s', 'now', '-1 days') * 1000;
```

**DAU:**
```sql
SELECT COUNT(DISTINCT s.install_id) as dau
FROM sessions s
WHERE s.start_time > strftime('%s', 'now', '-1 days') * 1000;
```

**Gate Pass Rate:**
```sql
SELECT
  AVG(gate1_pass) as gate1_pass_rate,
  AVG(gate2_pass) as gate2_pass_rate
FROM sessions
WHERE gate1_pass IS NOT NULL;
```

### Política de Cleanup 14 Días

**Estrategia:** Cleanup al inicio de cada sesión (no cron)

```typescript
// Al iniciar comando, antes de cualquier otra cosa
async function cleanupOldEvents() {
  const cutoff = Date.now() - (14 * 24 * 60 * 60 * 1000); // 14 días en ms

  await db.execute(
    `DELETE FROM events WHERE timestamp < ?`,
    [cutoff]
  );

  await db.execute(
    `DELETE FROM sessions WHERE start_time < ?`,
    [cutoff]
  );
}
```

**SQL exacto:**
```sql
DELETE FROM events WHERE timestamp < (strftime('%s', 'now', '-14 days') * 1000);
DELETE FROM sessions WHERE start_time < (strftime('%s', 'now', '-14 days') * 1000);
```

### Comandos de Export

```bash
# Exportar últimos 7 días
npm run export-analytics -- --days 7 --output analytics-7d.jsonl

# Exportar últimos 14 días
npm run export-analytics -- --days 14 --output analytics-14d.jsonl
```

**Implementación:**
```typescript
// scripts/export-analytics.ts
import fs from 'fs';
import path from 'path';
import sqlite3 from 'better-sqlite3';

function exportAnalytics(days: number, outputPath: string) {
  const dbPath = path.join(
    require('os').homedir(),
    'Library/Application Support/raycast-ext/analytics.db'
  );
  const db = new sqlite3(dbPath);

  const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);

  const rows = db.prepare(`
    SELECT
      e.timestamp,
      s.id as session_id,
      s.install_id,
      e.event_type,
      s.mode,
      s.input_source,
      s.output_length,
      s.gate1_pass,
      s.gate2_pass
    FROM events e
    JOIN sessions s ON e.session_id = s.id
    WHERE e.timestamp >= ?
    ORDER BY e.timestamp ASC
  `).all(cutoff);

  const jsonl = rows.map(row => JSON.stringify(row)).join('\n');
  fs.writeFileSync(outputPath, jsonl);

  console.log(`Exported ${rows.length} events to ${outputPath}`);
}
```

---

## 7. Quality Gates v1 (Contratos Ejecutables)

### Especificación de Templates (Mínimo 3)

**Template 1: JSON Prompt**
```json
{
  "id": "json-default",
  "name": "JSON Output",
  "requires_json": true,
  "markdown_sections": null,
  "type": "generic"
}
```

**Template 2: Markdown Procedure**
```json
{
  "id": "markdown-procedure",
  "name": "Step-by-Step Procedure",
  "requires_json": false,
  "markdown_sections": ["## Objetivo", "## Pasos", "## Criterios"],
  "type": "procedure"
}
```

**Template 3: Markdown Checklist**
```json
{
  "id": "markdown-checklist",
  "name": "Action Checklist",
  "requires_json": false,
  "markdown_sections": ["## Tareas", "## Notas"],
  "type": "checklist"
}
```

### Algoritmo de Validación Gate 1

```python
import json
import re

def gate1_expected_format(output: str, template: dict) -> bool:
    """
    Gate 1: Formato esperado del output
    Retorna True si el output cumple el formato, False si no
    """

    if template.get("requires_json", False):
        # Output debe ser JSON válido
        try:
            parsed = json.loads(output)
            # Validar que no es JSON vacío
            return bool(parsed and len(str(parsed)) > 0)
        except (json.JSONDecodeError, ValueError):
            return False

    else:
        # Output debe ser markdown con secciones específicas
        required_sections = template.get("markdown_sections", [])
        if not required_sections:
            # Sin secciones requeridas, pasa por default
            return True

        # Verificar que todas las secciones estén presentes
        output_lower = output.lower()
        for section in required_sections:
            if section.lower() not in output_lower:
                return False

        return True
```

### Algoritmo de Validación Gate 2

```python
import re

def gate2_min_completeness(output: str, template: dict) -> bool:
    """
    Gate 2: Completitud mínima del output
    Retorna True si el output tiene elementos suficientes, False si no
    """

    template_type = template.get("type", "generic")

    if template_type == "checklist":
        # Debe tener >=3 bullets (líneas que empiezan con "-")
        bullets = re.findall(r'^\s*-\s+', output, re.MULTILINE)
        return len(bullets) >= 3

    elif template_type == "procedure":
        # Debe tener >=2 pasos numerados
        steps = re.findall(r'^\s*\d+\.\s+', output, re.MULTILINE)
        return len(steps) >= 2

    elif template_type == "example":
        # Debe tener >=1 bloque de código (triple backticks)
        return '```' in output

    else:
        # Fallback genérico: longitud mínima de 100 caracteres
        return len(output.strip()) >= 100
```

### Suite de 12 Casos de Prueba

| # | Input | Template | Gate 1 Esperado | Gate 2 Esperado | Resultado |
|---|-------|----------|-----------------|-----------------|----------|
| 1 | `{}` (válido) | JSON | PASS | PASS (len>100) | **PASS PASS** |
| 2 | `{...} "trailing text` | JSON | FAIL (no es JSON) | - | **FAIL** |
| 3 | `## Objetivo\n\nHacer algo` | Markdown Procedure | FAIL (falta ## Pasos) | FAIL (no pasos) | **FAIL FAIL** |
| 4 | `- Tarea 1\n- Tarea 2\n- Tarea 3` | Checklist | PASS (no secciones req) | PASS (3 bullets) | **PASS PASS** |
| 5 | `1. Paso 1\n2. Paso 2` | Procedure | FAIL (falta ## Objetivo) | PASS (2 pasos) | **FAIL PASS** |
| 6 | `Ejemplo:\n\`\`\`code\`\`\`` | Example | PASS (no secciones req) | PASS (1 bloque) | **PASS PASS** |
| 7 | `texto corto` (50 chars) | Generic | PASS | FAIL (len<100) | **PASS FAIL** |
| 8 | `texto lo suficientemente largo para pasar` (150 chars) | Generic | PASS | PASS (len>=100) | **PASS PASS** |
| 9 | `- Solo 2 bullets` | Checklist | PASS | FAIL (solo 2 bullets) | **PASS FAIL** |
| 10 | `## Objetivo\n\nValidar email\n\n## Pasos\n\nUsar regex` | Procedure | PASS | FAIL (no pasos numerados) | **PASS FAIL** |
| 11 | `{}` | JSON | PASS | FAIL (JSON vacío) | **PASS FAIL** |
| 12 | ```json\n{}\n``` con trailing | JSON | FAIL (no es JSON puro) | - | **FAIL** |

**Criterio de Fallback SIN usar longitud salvo último recurso:**
- Longitud >=100 caracteres SOLO se usa para template.type == "generic"
- Para JSON, se valida que no es vacío (no se usa longitud)
- Para markdown específico, NO se usa longitud, se usan secciones y/o elementos

---

## 8. Plan de Medición TTV (3 Experimentos Manuales - 7 Días)

### Experimento A: Baseline Raycast AI Command

**Hipótesis:** Raycast AI nativo con `{selection}` tiene TTV P95 <20s

**Pasos exactos:**
1. Abrir Raycast (⌘ + Space)
2. Escribir "Translate {selection} to Spanish" (o cualquier comando nativo)
3. Seleccionar texto en TextEdit (ejemplo: "Hello world")
4. Presionar Enter
5. Medir tiempo desde Enter hasta que aparezca output
6. Repetir 10 veces

**Muestra mínima:** n=5 (si 5 iteraciones son consistentes, n=10 es opcional)

**Métrica primaria:** TTV P95 (percentil 95 de latencias)

**Métrica secundaria:** Copy within 60s (binario: ¿copió el output dentro de 60s?)

**Registro manual:**
```jsonl
{"experiment": "A", "iteration": 1, "ttv_ms": 3500, "copied": true, "notes": ""}
{"experiment": "A", "iteration": 2, "ttv_ms": 4000, "copied": true, "notes": ""}
...
```

**PASS:** TTV P95 <20,000ms
**FAIL:** TTV P95 >30,000ms

---

### Experimento B: Prompt Compiler Comando Nativo (Selección Automática)

**Hipótesis:** Prompt Compiler con getSelectedText() tiene TTV P95 <30s

**Pasos exactos:**
1. Asegurar que backend DSPy está corriendo (`make dev`)
2. Seleccionar texto en VS Code (ejemplo: "write a python function to validate email")
3. Presionar hotkey de Prompt Compiler (configurado en Raycast)
4. Esperar output
5. Medir tiempo desde hotkey hasta que aparezca output (hasta que se pueda copiar)
6. Repetir 10 veces

**Muestra mínima:** n=5

**Métrica primaria:** TTV P95

**Métrica secundaria:** Copy within 60s

**Registro manual:**
```jsonl
{"experiment": "B", "iteration": 1, "ttv_ms": 25000, "copied": true, "source": "selection", "notes": ""}
...
```

**PASS:** TTV P95 <30,000ms
**FAIL:** TTV P95 >45,000ms

---

### Experimento C: Prompt Compiler con Fallback Clipboard/Input

**Hipótesis:** Prompt Compiler con fallback clipboard/input tiene TTV P95 <35s

**Pasos exactos:**
1. NO seleccionar nada
2. Copiar "write a python function to validate email" al clipboard
3. Presionar hotkey de Prompt Compiler
4. Medir tiempo desde hotkey hasta output
5. Repetir 10 veces

**Muestra mínima:** n=5

**Métrica primaria:** TTV P95

**Métrica secundaria:** Copy within 60s

**Registro manual:**
```jsonl
{"experiment": "C", "iteration": 1, "ttv_ms": 32000, "copied": true, "source": "clipboard", "notes": ""}
...
```

**PASS:** TTV P95 <35,000ms
**FAIL:** TTV P95 >50,000ms

---

### Análisis Comparativo (7 Días)

**Después de 7 días, comparar:**

| Experimento | TTV P95 | Copy Rate | Veredicto |
|-------------|---------|-----------|----------|
| A: Raycast AI nativo | ? ms | ?% | Baseline |
| B: Prompt Compiler (selección) | ? ms | ?% | ¿Mejora baseline? |
| C: Prompt Compiler (fallback) | ? ms | ?% | ¿Es viable? |

**Decisión:**
- Si B TTV P95 < A TTV P95 + 10,000ms → Prompt Compiler es más lento, reconsiderar arquitectura
- Si B Copy Rate > A Copy Rate + 20pp → Prompt Compiler añade valor significativo
- Si C TTV P95 > 45,000ms → Eliminar fallback manual, simplificar flujo

---

## Resumen de Cambios Requeridos al Roadmap

| Item | Roadmap v1.2 | Corrección Auditoría |
|------|--------------|---------------------|
| TTV P95 <30s | Claim sin medición | Agregar: medición manual de 10 iteraciones |
| getSelectedText() funciona | Claim sin prueba | Agregar: test en 3 apps antes de implementar |
| Quality Gates | System requerido | Agregar: gates genéricos primero, templates después |
| 6 horas para Entregable 1 | Estimación optimista | Agregar: revisión de código primero |
| Experiments A/B/C | No definidos | Agregar: pasos exactos, n=5, registros JSONL |

---

**v1.2 + Auditoría = Plan ejecutable con evidencias requeridas.**
