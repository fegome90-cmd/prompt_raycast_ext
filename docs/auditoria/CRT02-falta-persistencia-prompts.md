# CRT-02: Falta de Persistencia de Prompts

**Fecha:** 2026-01-02
**Severidad:** 🔴 Alta
**Estado:** ⚠️ Activo (sin implementar)
**ID:** CRT-02 (Critical Technical Report)

---

## 1. Resumen Ejecutivo

El sistema **no persiste ningún dato** sobre los prompts procesados. Cada request es completamente stateless - no hay historial, no hay logs estructurados, no hay base de datos. Esto imposibilita:

- Análisis de uso y tendencias
- Debugging de problemas posteriores
- Mejora continua basada en datos
- Auditoría de actividad

**Impacto Actual:** Medio - el sistema funciona pero no hay rastro
**Riesgo Futuro:** Alto - imposibilita análisis y mejora

---

## 2. Estado Actual de Persistencia

### 2.1 Matriz de Almacenamiento

| Tipo de Dato | ¿Persiste? | Ubicación | Volatilidad |
|--------------|-----------|-----------|-------------|
| **Configuración** | ✅ Sí | `.env` + Raycast Preferences | Permanente |
| **Prompts de entrada** | ❌ No | - | Se pierde |
| **Prompts mejorados** | ❌ No | - | Se pierde |
| **Métricas de calidad** | ❌ No | - | Se pierde |
| **Logs de errores** | ❌ No | Stdout (temporal) | Se pierde |
| **Backend usado** | ❌ No | - | Se pierde |
| **Latencia** | ❌ No | - | Se pierde |
| **Metadata** | ❌ No | - | Se pierde |

### 2.2 Flujo de Datos Actual

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS (ACTUAL)                     │
└─────────────────────────────────────────────────────────────────┘

Usuario ingresa prompt
    ↓
[Memoria temporal]
    ↓
Procesamiento (DSPy/Ollama)
    ↓
Resultado mostrado al usuario
    ↓
❌ TODO SE PIERDE
    ↓
No hay rastro de lo que pasó
```

**Resultado:** Zero knowledge retention

---

## 3. Impacto y Limitaciones

### 3.1 Impacto Operativo

| Aspecto | Impacto | Descripción |
|---------|---------|-------------|
| **Debugging** | 🔴 Crítico | No se pueden investigar problemas post-hoc |
| **Análisis** | 🔴 Crítico | Imposible saber qué prompts se usan más |
| **Mejora** | 🟡 Alto | No se puede medir mejora over time |
| **Auditoría** | 🟡 Alto | No hay registro de actividad |
| **UX** | 🟢 Bajo | Usuario no nota diferencia |

### 3.2 Casos de Uso Imposibles

**1. Análisis de Tendencias**
```python
# ❌ Imposible actualmente
¿Qué tipos de prompts se usan más?
¿Cuál es el prompt más largo procesado?
¿Cuántos prompts fallaron en la última semana?
```

**2. Debugging Post-Mortem**
```python
# ❌ Imposible actualmente
"El usuario reportó un mal output a las 3pm"
→ No se puede recuperar el request original
→ No se puede reproducir el problema
```

**3. Métricas de Calidad**
```python
# ❌ Imposible actualmente
¿Cuál es el copyableRate real?
¿Cuántos repairs se hicieron hoy?
¿Cuál backend se usa más?
```

**4. A/B Testing**
```python
# ❌ Imposible actualmente
Probar cambio en el prompt de mejora
→ No se puede comparar antes/después
→ No se puede medir impacto
```

---

## 4. Análisis de Requerimientos

### 4.1 Datos que Deberían Persistirse

**Mínimo viable (MVP):**
```sql
CREATE TABLE prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    backend TEXT,              -- 'dspy' | 'ollama'
    model_used TEXT,           -- 'Novaeus-Promptist-7B' | ...
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Ideal (completo):**
```sql
CREATE TABLE prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Input
    input_text TEXT NOT NULL,
    input_length INTEGER,
    input_language TEXT,

    -- Output
    output_text TEXT NOT NULL,
    output_length INTEGER,
    improved_prompt TEXT,
    clarifying_questions TEXT,      -- JSON array
    assumptions TEXT,               -- JSON array
    confidence REAL,

    -- Metadata
    backend TEXT,                   -- 'dspy' | 'ollama'
    model_used TEXT,
    preset TEXT,                    -- 'default' | 'specific' | ...
    temperature REAL,

    -- Quality
    used_extraction BOOLEAN,
    used_repair BOOLEAN,
    attempt INTEGER,
    extraction_method TEXT,

    -- Performance
    latency_ms INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Error handling
    success BOOLEAN,
    error_message TEXT,
    failure_reason TEXT
);

-- Índices para queries comunes
CREATE INDEX idx_backend ON prompt_history(backend);
CREATE INDEX idx_timestamp ON prompt_history(timestamp);
CREATE INDEX idx_success ON prompt_history(success);
CREATE INDEX idx_model ON prompt_history(model_used);
```

### 4.2 Consultas Comunes Necesarias

```sql
-- 1. Prompts recientes
SELECT * FROM prompt_history
ORDER BY timestamp DESC
LIMIT 50;

-- 2. Tasas de éxito por backend
SELECT
    backend,
    COUNT(*) as total,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    CAST(SUM(CASE WHEN success THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate
FROM prompt_history
GROUP BY backend;

-- 3. Latencia promedio (P50, P95, P99)
SELECT
    backend,
    AVG(latency_ms) as avg_latency,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95
FROM prompt_history
WHERE success = TRUE
GROUP BY backend;

-- 4. Prompts fallidos recientes
SELECT * FROM prompt_history
WHERE success = FALSE
ORDER BY timestamp DESC
LIMIT 20;

-- 5. Modelos más usados
SELECT
    model_used,
    COUNT(*) as usage_count
FROM prompt_history
GROUP BY model_used
ORDER BY usage_count DESC;
```

---

## 5. Soluciones Propuestas

### 5.1 Opción 1: SQLite Local (Recomendada)

**Ventajas:**
- ✅ Zero configuración
- ✅ Embedded en la aplicación
- ✅ Performance excelente para este caso de uso
- ✅ Portabilidad (archivo único)
- ✅ SQL completo para análisis

**Desventajas:**
- ⚠️ Solo acceso local
- ⚠️ Concurrency limitado (1 writer)

**Implementación:**

```python
# backend/db/prompt_history.py
import sqlite3
from datetime import datetime
from typing import Optional
import json

class PromptHistory:
    def __init__(self, db_path: str = "prompt_history.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                backend TEXT,
                model_used TEXT,
                latency_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def log_prompt(self, data: dict):
        """Log a prompt processing event."""
        self.conn.execute("""
            INSERT INTO prompt_history (
                input_text, output_text, backend, model_used,
                latency_ms, success, error_message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["input_text"],
            data["output_text"],
            data.get("backend"),
            data.get("model_used"),
            data.get("latency_ms"),
            data.get("success", True),
            data.get("error_message"),
            json.dumps(data.get("metadata", {}))
        ))
        self.conn.commit()

# Uso en main.py
from backend.db.prompt_history import PromptHistory

history = PromptHistory()

@app.post("/api/v1/improve-prompt")
async def improve_prompt(request: PromptRequest):
    start = time.time()
    try:
        result = await process_prompt(request)
        latency = (time.time() - start) * 1000

        # Log al historial
        history.log_prompt({
            "input_text": request.raw_idea,
            "output_text": result.improved_prompt,
            "backend": "dspy",
            "model_used": settings.LLM_MODEL,
            "latency_ms": latency,
            "success": True,
            "metadata": {
                "confidence": result.confidence,
                "framework": result.framework
            }
        })
        return result
    except Exception as e:
        latency = (time.time() - start) * 1000
        history.log_prompt({
            "input_text": request.raw_idea,
            "output_text": "",
            "backend": "dspy",
            "latency_ms": latency,
            "success": False,
            "error_message": str(e)
        })
        raise
```

### 5.2 Opción 2: JSON Lines (Simple)

**Ventajas:**
- ✅ Súper simple
- ✅ Human-readable
- ✅ Fácil de importar a otras herramientas

**Desventajas:**
- ⚠️ No hay queries
- ⚠️ Performance pobre para datasets grandes
- ⚠️ No hay índices

**Implementación:**

```python
# backend/logging/jsonl_logger.py
import json
from datetime import datetime
from pathlib import Path

class JSONLLogger:
    def __init__(self, log_path: str = "logs/prompts.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, data: dict):
        """Append to JSONL file."""
        data["timestamp"] = datetime.utcnow().isoformat()
        with open(self.log_path, "a") as f:
            f.write(json.dumps(data) + "\n")

# Uso
logger = JSONLLogger()
logger.log({
    "input": request.raw_idea,
    "output": result.improved_prompt,
    "backend": "dspy",
    "latency_ms": latency,
    "success": True
})
```

### 5.3 Opción 3: Vector DB (Overkill para ahora)

**No recomendado** hasta que se necesite búsqueda semántica.

---

## 6. Comparación de Soluciones

| Aspecto | SQLite | JSONL | Vector DB |
|---------|--------|-------|-----------|
| **Complejidad** | Media | Baja | Alta |
| **Queries** | ✅ SQL completo | ❌ Ninguna | ✅ Búsqueda semántica |
| **Performance** | ✅ Excelente | ⚠️ Pobre | ✅ Buena |
| **Configuración** | ✅ Zero | ✅ Zero | ⚠️ Requiere setup |
| **Escalabilidad** | ⚠️ 1 writer | ✅ ilimitado | ✅ Distribuido |
| **Portabilidad** | ✅ 1 archivo | ✅ Texto | ⚠️ Complejo |
| **Recomendado** | ✅ Sí | Para logging | Futuro |

---

## 7. Plan de Implementación

### 7.1 Fase 1: MVP con SQLite (Sprint 1)

**Objetivo:** Persistencia básica funcional

- [ ] Crear tabla `prompt_history`
- [ ] Implementar `PromptHistory.log_prompt()`
- [ ] Integrar en endpoint `/api/v1/improve-prompt`
- [ ] Agregar migración inicial
- [ ] Test básico de persistencia

**Archivos a crear:**
```
backend/
├── db/
│   ├── __init__.py
│   ├── prompt_history.py      # ORM simple
│   └── migrations/
│       └── 001_initial.sql    # CREATE TABLE
```

**Archivos a modificar:**
```
main.py                         # Integrar logging
api/prompt_improver_api.py      # Log en endpoint
```

### 7.2 Fase 2: Analytics Dashboard (Sprint 2)

**Objetivo:** Visualizar datos históricos

- [ ] Endpoint `/api/v1/analytics/summary`
- [ ] Endpoint `/api/v1/analytics/recent`
- [ ] Endpoint `/api/v1/analytics/failures`
- [ ] Dashboard simple en Raycast

### 7.3 Fase 3: Advanced Features (Sprint 3)

**Objetivo:** Búsqueda y filtrado

- [ ] Búsqueda por texto en input/output
- [ ] Filtros por backend, modelo, rango de fechas
- [ ] Export a CSV/JSON
- [ ] Cleanup automático de datos viejos

---

## 8. Consideraciones de Privacy

### 8.1 Datos Sensibles

⚠️ **Importante:** Los prompts pueden contener información sensible:

- Código propietario
- Información corporativa
- Ideas no publicadas
- Datos personales

**Requisitos:**
1. **Local-only:** La DB nunca debe salir de la máquina del usuario
2. **Encryption opcional:** Permitir encryptar la DB
3. **Clear data:** Botón para borrar todo el historial
4. **Explicit consent:** Informar al usuario que se guardan datos

### 8.2 Configuración de Privacidad

```typescript
// dashboard/src/core/config/schema.ts
export const configSchema = z.object({
  // ...
  privacy: z.object({
    enableHistory: z.boolean().default(true),
    encryptDatabase: z.boolean().default(false),
    autoCleanupDays: z.number().optional(),
    anonymizeData: z.boolean().default(false),  // Remover texto real
  }),
});
```

---

## 9. Testing y Validación

### 9.1 Tests de Persistencia

```python
# tests/test_prompt_history.py
def test_prompt_persistence():
    """Verify prompts are saved to DB."""
    history = PromptHistory(":memory:")

    history.log_prompt({
        "input_text": "test input",
        "output_text": "test output",
        "backend": "dspy",
        "success": True
    })

    # Verify
    rows = history.get_recent(10)
    assert len(rows) == 1
    assert rows[0]["input_text"] == "test input"

def test_error_logging():
    """Verify errors are saved."""
    history = PromptHistory(":memory:")

    history.log_prompt({
        "input_text": "bad input",
        "output_text": "",
        "success": False,
        "error_message": "Failed to process"
    })

    failures = history.get_failures(limit=10)
    assert len(failures) == 1
    assert failures[0]["error_message"] is not None
```

### 9.2 Tests de Performance

```python
def test_bulk_insert_performance():
    """Verify DB can handle 1000 inserts."""
    history = PromptHistory(":memory:")

    start = time.time()
    for i in range(1000):
        history.log_prompt({
            "input_text": f"test {i}",
            "output_text": f"output {i}",
            "success": True
        })
    elapsed = time.time() - start

    # Should be < 1 second for 1000 inserts
    assert elapsed < 1.0
```

---

## 10. Alternativas Consideradas

### 10.1 No Persistir (Status Quo)

**Ventajas:**
- ✅ Zero complejidad
- ✅ Zero storage overhead
- ✅ Maximum privacy

**Desventajas:**
- ❌ Imposible analizar uso
- ❌ Imposible debuggear
- ❌ Imposible mejorar

**Veredicto:** No es viable a largo plazo

### 10.2 Cloud Storage

**No considerado** por:
- Violación de principio "local-first"
- Costos de infraestructura
- Latencia de red
- Privacy concerns

---

## 11. Roadmap de Decisión

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION TREE                            │
└─────────────────────────────────────────────────────────────┘

¿Necesitas buscar prompts semánticamente?
│
├─ NO → Usar SQLite (recomendado)
│        │
│        └─ ¿Necesitas análisis complejo?
│             ├─ SÍ → SQLite + queries SQL
│             └─ NO → SQLite básico
│
└─ SÍ → Vector DB (Chroma, FAISS, etc.)
          (Futuro - cuando haya 10k+ prompts)
```

**Recomendación actual:** SQLite MVP

---

## 12. Conclusión

**Estado:** 🔴 Sin implementar

**Impacto:**
- **Actual:** Medio - sistema funciona pero "ciego"
- **Futuro:** Alto - imposibilita análisis y mejora

**Resolución:** Compleja pero manejable
- Implementar SQLite MVP (1-2 días)
- Agregar endpoints de analytics (1 día)
- Considerar privacy desde el inicio

**Prioridad:** Alta
- Bloquea análisis de uso
- Bloquea debugging post-mortem
- Bloquea medición de mejora continua

**Beneficios de implementar:**
1. ✅ Visibilidad total del uso
2. ✅ Capacity para debugging
3. ✅ Data-driven improvements
4. ✅ Auditoría de actividad

---

**Reportado por:** Auditoría de Pipeline
**Revisado por:** Pendiente
**Aprobado por:** Pendiente
**Fecha de revisión:** Pendiente
