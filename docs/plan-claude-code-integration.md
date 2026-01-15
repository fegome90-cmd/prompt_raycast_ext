# Instrucciones para Agente Ejecutor

## Contexto

Este documento contiene las instrucciones para que un agente ejecute el plan de integración de HemDov Prompt Improver con Claude Code.

## Plan Aprobado

**Archivo del plan:** `/Users/felipe_gonzalez/.claude/plans/tingly-zooming-lerdorf.md`

## Resumen Ejecutivo

Integrar el backend de HemDov Prompt Improver con Claude Code usando **llamadas HTTP directas** a través de un comando personalizado.

**Enfoque:** HTTP directo (sin MCP, sin plugins) para uso personal.

## Archivo Crítico: Limitación del Backend

⚠️ **IMPORTANTE:** El backend actual NO soporta `mode="auto"`.

En `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py:113-116`, el validator solo acepta `"legacy"` o `"nlac"`:

```python
@field_validator("mode")
@classmethod
def validate_mode(cls, v):
    """Validate mode is either 'legacy' or 'nlac'."""
    if v not in ("legacy", "nlac"):
        raise ValueError("mode must be 'legacy' or 'nlac'")
    return v
```

**El comando debe usar `mode="legacy"` por defecto** (o `mode="nlac"` si el usuario lo especifica).

## Tareas a Ejecutar

### 1. Crear directorio `.claude/commands`

```bash
mkdir -p /Users/felipe_gonzalez/Developer/raycast_ext/.claude/commands
```

### 2. Crear archivo `improve-prompt.md`

**Ruta:** `/Users/felipe_gonzalez/Developer/raycast_ext/.claude/commands/improve-prompt.md`

**Contenido completo:**

```markdown
---
name: improve_prompt
description: Improve a prompt using the HemDov Prompt Improver backend
parameters:
  - name: idea
    type: string
    required: true
    description: The raw prompt idea to improve
  - name: context
    type: string
    required: false
    description: Additional context about the task
  - name: mode
    type: string
    required: false
    enum: ["legacy", "nlac"]
    default: "legacy"
    description: "legacy" is fast DSPy mode (~30s), "nlac" is high-quality NLaC mode (~60s)
---

## Improve Prompt Command

This command calls the HemDov Prompt Improver backend to enhance a raw prompt into a structured, high-quality prompt.

### How it works

1. Sends the prompt to the backend at `http://localhost:8000/api/v1/improve-prompt`
2. Backend processes using the selected mode:
   - **legacy** (default): DSPy framework with few-shot learning (~30s)
   - **nlac**: NLaC pipeline with iterative optimization (~60s)
3. Returns an improved prompt with:
   - `role`: Expert persona (e.g., "Senior Software Engineer")
   - `directive`: Core mission statement
   - `framework`: Reasoning approach (CoT, ReAct, etc.)
   - `guardrails`: 3-5 constraints
   - `improved_prompt`: Complete structured prompt

### Example Usage

**Fast mode (DSPy, ~30s):**
```
> /improve_prompt "Fix the login bug"
```

**High-quality mode (NLaC, ~60s):**
```
> /improve_prompt "Design microservices architecture" mode:"nlac"
```

**With context:**
```
> /improve_prompt "Add authentication" context:"FastAPI backend with JWT"
```

### Prerequisites

The backend must be running:
```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
make dev
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### Mode Selection

- **legacy** (default): Fast, uses DSPy with few-shot learning. Best for simple to moderate complexity prompts.
- **nlac**: High-quality, uses NLaC pipeline with OPRO optimization. Best for complex prompts requiring maximum quality.
```

### 3. Verificar backend está corriendo

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
make health
# Debe devolver: {"status":"healthy",...}
```

### 4. Verificar archivo creado

```bash
cat /Users/felipe_gonzalez/Developer/raycast_ext/.claude/commands/improve-prompt.md
```

## Verificación Final

Después de crear los archivos, el agente debe verificar:

1. ✅ Directorio `.claude/commands/` existe
2. ✅ Archivo `improve-prompt.md` existe con el contenido correcto
3. ✅ Backend responde a `/health`

## Testing (opcional)

Si el usuario lo solicita, probar con:

```bash
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "Fix the login bug", "context": "", "mode": "legacy"}'
```

## Archivos de Referencia

| Archivo | Propósito |
|---------|-----------|
| `api/prompt_improver_api.py:106-117` | Backend request/response models |
| `api/prompt_improver_api.py:215-402` | Endpoint `/improve-prompt` |
| `hemdov/domain/services/complexity_analyzer.py` | Complexity analysis logic |
| `eval/src/strategy_selector.py` | Strategy routing (DSPy vs NLaC) |

## Notas Importantes

1. **NO modificar el backend** - el usuario eligió modo manual
2. **El command usa `mode="legacy"` por defecto** - no usar `mode="auto"`
3. **El backend debe estar corriendo** para que funcione el comando
