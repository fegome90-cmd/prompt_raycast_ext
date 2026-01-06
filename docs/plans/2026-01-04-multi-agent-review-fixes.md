# Plan de Corrección - Análisis Multi-Agente PR Review

**Fecha:** 2026-01-04
**Agentes utilizados:** 4 (code-reviewer, silent-failure-hunter, pr-test-analyzer, type-design-analyzer)
**Total issues encontrados:** 41

---

## 📊 Resumen Ejecutivo

| Categoría | Críticos | Altos | Medios | Total |
|-----------|----------|-------|--------|-------|
| Calidad de Código | 3 | 11 | - | 14 |
| Error Handling | 6 | 2 | 4 | 12 |
| Tests Faltantes | 3 | 3 | - | 6 |
| Diseño de Tipos | 2 | 4 | 3 | 9 |
| **TOTAL** | **14** | **20** | **7** | **41** |

---

## 🔴 FASE 1: Críticos - HOY (Bloqueantes)

### 1.1 Remover `node-fetch` - Raycast conectividad ⭐⭐⭐
**Archivo:** `dashboard/src/core/llm/dspyPromptImprover.ts:26`

**Estado:** ✅ COMPLETADO (2026-01-04)

**Problema:** Import innecesario que rompe el fetch nativo de Raycast.

```typescript
- import fetch from "node-fetch";
```

**Acción:** Eliminar línea 26

**Resolución:** Migración completa a native fetch implementada en `docs/plans/2026-01-04-remove-node-fetch.md`

---

### 1.2 Agregar handler de Anthropic en main.py ⭐⭐⭐
**Archivo:** `main.py:71-89`

**Problema:** El adapter existe pero no se usa. App crashea con `LLM_PROVIDER=anthropic`.

```python
elif provider == "anthropic":
    lm = create_anthropic_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.ANTHROPIC_API_KEY or settings.HEMDOV_ANTHROPIC_API_KEY,
        temperature=temp,
    )
```

**Acción:** Agregar el handler en el lifespan

---

### 1.3 Fix circuit breaker paradox ⭐⭐⭐
**Archivo:** `api/prompt_improver_api.py:252-259`

**Problema:** `record_success()` dentro del try-except causa paradoja éxito/fracaso.

```python
# Mover FUERA del try-except
try:
    await _circuit_breaker.record_success()
except Exception as cb_error:
    logger.error(f"Failed to record success: {cb_error}")
```

---

### 1.4 Framework validation fix ⭐⭐⭐
**Archivo:** `hemdov/domain/entities/prompt_history.py:56-63`

**Problema:** Validación estricta causa error 500 cuando el LLM devuelve framework descriptivo.

**Opción A:** Relajar validación (normalizar después)
**Opción B:** Agregar fallback a "chain-of-thought" si no coincide

```python
def __post_init__(self):
    # Validate framework is allowed value (with fallback)
    allowed_frameworks = {
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing"
    }
    if self.framework not in allowed_frameworks:
        logger.warning(f"Unknown framework '{self.framework}', defaulting to 'chain-of-thought'")
        object.__setattr__(self, 'framework', 'chain-of-thought')
```

---

### 1.5 SQLite JSON deserialization error handling ⭐⭐⭐
**Archivo:** `sqlite_prompt_repository.py:220`

```python
try:
    guardrails = json.loads(row["guardrails"])
except (json.JSONDecodeError, TypeError) as e:
    logger.error(f"Corrupted guardrails in record {row['id']}: {e}")
    guardrails = []
```

---

### 1.6 SQLite connection leak on init ⭐⭐⭐
**Archivo:** `sqlite_prompt_repository.py:34-42`

```python
try:
    self._connection = await aiosqlite.connect(self.db_path)
    await self._configure_connection(self._connection)
except Exception:
    if self._connection:
        await self._connection.close()
        self._connection = None
    raise
```

---

## 🟡 FASE 2: Importantes - Esta Semana

### 2.1 Fix confidence type coercion
**Archivo:** `api/prompt_improver_api.py:244`

**Problema:** `confidence` llega como string, validación espera float.

```python
confidence = getattr(result, "confidence", None)
# Convert to float if string
if isinstance(confidence, str):
    try:
        confidence = float(confidence)
    except ValueError:
        confidence = None
```

---

### 2.2 Literal types para framework
**Archivo:** `api/prompt_improver_api.py` (modelos Pydantic)

```python
from typing import Literal

class ImprovePromptResponse(BaseModel):
    framework: Literal["chain-of-thought", "tree-of-thoughts", "decomposition", "role-playing"]
```

---

### 2.3 TypeScript Zod validation
**Archivo:** `dashboard/src/core/llm/dspyPromptImprover.ts`

```typescript
import { z } from 'zod';

const DSPyResponseSchema = z.object({
  framework: z.enum(["chain-of-thought", "tree-of-thoughts", "decomposition", "role-playing"]),
  guardrails: z.array(z.string()).min(1),
  confidence: z.number().min(0).max(1).optional(),
});

// En improvePrompt:
const data = DSPyResponseSchema.parse(await response.json());
```

---

### 2.4 Better error messages en SQLite
**Archivos:** `sqlite_prompt_repository.py`, `migrations.py`

Agregar error IDs y logging estructurado:
```python
logger.error(
    f"Failed to connect to database {self.db_path}: {e}",
    extra={"error_id": "sqlite_connect_failed", "db_path": str(self.db_path)}
)
```

---

### 2.5 Container shutdown error handling
**Archivo:** `interfaces.py:56-62`

```python
async def shutdown(self):
    for i, hook in enumerate(reversed(self._cleanup_hooks)):
        try:
            if iscoroutinefunction(hook):
                await hook()
            else:
                hook()
        except Exception as e:
            logger.error(f"Cleanup hook {i} failed: {e}")
```

---

## 🟢 FASE 3: Tests - Próxima Sprint

### 3.1 Circuit breaker tests
**Archivo nuevo:** `tests/test_circuit_breaker.py`

```python
@pytest.mark.asyncio
async def test_circuit_breaker_full_trip_cycle():
    """Test closed -> open -> half-open -> closed."""
    breaker = CircuitBreaker(max_failures=3, timeout_seconds=1)
    assert await breaker.should_attempt() is True
    for _ in range(3):
        await breaker.record_failure()
    assert await breaker.should_attempt() is False
    await asyncio.sleep(1.1)
    assert await breaker.should_attempt() is True

@pytest.mark.asyncio
async def test_circuit_breaker_concurrent_access():
    """Test thread-safety under concurrent access."""
    breaker = CircuitBreaker(max_failures=10, timeout_seconds=60)
    tasks = [breaker.record_failure() if i % 2 == 0 else breaker.should_attempt()
             for i in range(20)]
    results = await asyncio.gather(*tasks)
    assert await breaker.should_attempt() is not None
```

---

### 3.2 SQLite concurrent writes
**Archivo nuevo:** `tests/test_sqlite_concurrent.py`

```python
@pytest.mark.asyncio
async def test_concurrent_saves(repository: SQLitePromptRepository):
    """Test that concurrent saves are handled correctly."""
    prompts = [PromptHistory(...) for _ in range(10)]
    tasks = [repository.save(p) for p in prompts]
    ids = await asyncio.gather(*tasks)
    assert len(set(ids)) == 10
```

---

### 3.3 Anthropic adapter tests
**Archivo nuevo:** `tests/test_anthropic_adapter.py`

```python
def test_anthropic_adapter_key_fallback():
    """Test fallback to HEMDOV_ANTHROPIC_API_KEY."""
    with patch.dict(os.environ, {"HEMDOV_ANTHROPIC_API_KEY": "sk-test"}):
        adapter = create_anthropic_adapter()
        assert adapter.api_key == "sk-test"
```

---

### 3.4 API success when DB fails
**Archivo:** `tests/test_api_persistence.py`

```python
def test_improve_prompt_succeeds_when_save_fails(client):
    """Test that prompt succeeds even if persistence fails."""
    mock_repo = AsyncMock()
    mock_repo.save.side_effect = Exception("DB error")
    # Should still return 200
    response = client.post("/api/v1/improve-prompt", json={"idea": "test"})
    assert response.status_code == 200
```

---

### 3.5 PromptHistory validation tests
**Archivo:** `tests/test_prompt_history_validation.py`

```python
def test_validation_invalid_framework():
    with pytest.raises(ValueError, match="Invalid framework"):
        PromptHistory(..., framework="invalid")

def test_validation_empty_guardrails():
    with pytest.raises(ValueError, match="guardrails cannot be empty"):
        PromptHistory(..., guardrails=[])
```

---

### 3.6 Migration idempotency
**Archivo:** `tests/test_migrations.py`

```python
@pytest.mark.asyncio
async def test_migration_is_idempotent():
    """Test running migrations twice doesn't cause errors."""
    conn1 = await aiosqlite.connect(db_path)
    await run_migrations(conn1)
    await conn1.close()

    conn2 = await aiosqlite.connect(db_path)
    await run_migrations(conn2)  # Should not fail
```

---

## 📋 Checklist de Implementación

### Fase 1 - Hoy [ ]
- [ ] Remover `import fetch from "node-fetch"` (dspyPromptImprover.ts:26)
- [ ] Agregar handler de Anthropic en main.py
- [ ] Fix circuit breaker paradox (mover record_success)
- [ ] Framework validation con fallback
- [ ] JSON deserialization error handling
- [ ] SQLite connection leak fix

### Fase 2 - Esta semana [ ]
- [ ] Fix confidence type coercion
- [ ] Literal types para framework en Pydantic
- [ ] Zod validation en TypeScript
- [ ] Error IDs y structured logging
- [ ] Container shutdown error handling

### Fase 3 - Tests [ ]
- [ ] Circuit breaker full cycle test
- [ ] Circuit breaker concurrent access test
- [ ] SQLite concurrent saves test
- [ ] Anthropic adapter key fallback test
- [ ] API success when DB fails test
- [ ] PromptHistory validation edge cases
- [ ] Migration idempotency test

---

## 🎯 Success Criteria

- [ ] Backend corre sin errores 500
- [ ] Raycast se conecta correctamente al backend
- [ ] Todos los tests nuevos pasan
- [ ] Coverage de tests >80% para código nuevo
- [ ] No hay silent failures
- [ ] Circuit breaker funciona correctamente

---

## 📝 Notas

- **Priority:** Fase 1 bloquea el uso de Raycast
- **Risk:** Cambios de validación pueden afectar datos existentes en SQLite
- **Dependencies:** Algunos fixes dependen de otros (ej: confidence coercion antes de guardar en DB)

**Estado actual:**
- ✅ Backend corriendo con DeepSeek
- ⏳ Esperando implementación de Fase 1
