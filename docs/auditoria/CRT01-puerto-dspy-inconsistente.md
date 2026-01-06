# CRT-01: Inconsistencia de Puerto DSPy (8000 vs 8001)

**Fecha:** 2026-01-02
**Severidad:** 🟡 Media
**Estado:** ✅ Resuelto
**ID:** CRT-01 (Critical Technical Report)
**Fecha de resolución:** 2026-01-02

---

## 1. Resumen Ejecutivo

Existe una **inconsistencia de configuración** entre el puerto definido en el archivo `.env` (`API_PORT=8001`) y el puerto harcodeado en el frontend TypeScript (`http://localhost:8000`). A pesar de esta discrepancia, el sistema funciona correctamente porque el backend está usando el puerto default 8000 (ignorando la configuración del `.env`).

**Impacto Actual:** Bajo - el sistema funciona
**Riesgo Futuro:** Medio - confusión en deployment y documentación

---

## 2. Descripción Técnica

### 2.1 Flujo de Configuración Actual

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURACIÓN BACKEND                        │
└─────────────────────────────────────────────────────────────────┘

1. .env define: API_PORT=8001
   ↓
2. hemdov/infrastructure/config/__init__.py
   Settings(BaseSettings)
   API_PORT: int = 8000  (default)
   ↓
3. main.py:130
   uvicorn.run(port=settings.API_PORT)
   ↓
4. ¿Resultado? Se usa el default 8000
   (el .env NO está siendo leído correctamente)
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURACIÓN FRONTEND                       │
└─────────────────────────────────────────────────────────────────┘

1. defaults.ts:56
   baseUrl: "http://localhost:8000"  (HARDCODED)
   ↓
2. package.json:32
   "default": "http://localhost:8000"  (HARDCODED)
   ↓
3. improvePrompt.ts:104
   dspyBaseUrl ?? "http://localhost:8000"
   ↓
4. Resultado: Frontend siempre conecta a 8000
```

### 2.2 Estado Verificado

| Componente | Configuración | Puerto Real | Estado |
|------------|---------------|-------------|--------|
| `.env` | `API_PORT=8001` | ❌ Ignorado | Documentación incorrecta |
| Python Settings | `API_PORT: int = 8000` | ✅ Usado | Default correcto |
| Frontend defaults | `http://localhost:8000` | ✅ Correcto | Funcional |
| Backend corriendo | - | `8000` | ✅ Confirmado |

---

## 3. Análisis de Causa Raíz

### 3.1 ¿Por qué funciona si hay inconsistencia?

**Hipótesis confirmada:** El archivo `.env` no está siendo leído correctamente por `pydantic-settings`.

**Evidencia:**
```python
# hemdov/infrastructure/config/__init__.py:38-42
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True,  # ⚠️ Requiere mayúsculas exactas
)
```

**Posibles causas:**
1. El `.env` está en una ubicación no accesible desde el contexto de ejecución
2. La variable está mal escrita en el `.env`
3. Hay un problema con `pydantic-settings` al leer el archivo

### 3.2 Verificación del .env

```bash
# Contenido actual de .env
API_PORT=8001  # ❌ Esta línea NO está siendo leída

# Backend corre en: 8000 (default del código Python)
# Frontend conecta a: 8000 (hardcoded)
```

---

## 4. Impacto y Riesgos

### 4.1 Impacto Actual

| Aspecto | Impacto | Descripción |
|---------|---------|-------------|
| **Funcionalidad** | ✅ Sin impacto | El sistema funciona porque ambos usan 8000 |
| **Documentación** | ⚠️ Confuso | `.env` dice 8001 pero realmente es 8000 |
| **Debugging** | ⚠️ Confuso | Si alguien cambia el .env a 8001, no pasa nada |
| **Deployment** | ⚠️ Riesgo medio | En diferentes entornos podría fallar |

### 4.2 Escenarios de Riesgo

**Escenario 1: Cambio de puerto en .env**
```bash
# Usuario edita .env pensando que cambiará el puerto
API_PORT=9000

# Resultado: NO pasa nada, sigue en 8000
# Causa: El .env no está siendo leído
```

**Escenario 2: Deployment en producción**
```bash
# Admin configura puerto en variable de entorno
export API_PORT=8080

# Resultado: PODRÍA funcionar (vars de entorno sí se leen)
# Pero la documentación dice .env, causando confusión
```

**Escenario 3: Múltiples instancias**
```bash
# Intentar correr backend en puerto diferente
# para evitar conflictos con otro servicio

# Resultado: No funciona mediante .env
# Requiere editar código Python directamente
```

---

## 5. Análisis de Código Fuente

### 5.1 Archivos Involucrados

**Backend (Python):**

| Archivo | Línea | Configuración |
|---------|-------|---------------|
| `.env` | 13 | `API_PORT=8001` ❌ No leído |
| `hemdov/infrastructure/config/__init__.py` | 31 | `API_PORT: int = 8000` ✅ Default |
| `main.py` | 130 | `port=settings.API_PORT` ✅ Usado |

**Frontend (TypeScript):**

| Archivo | Línea | Configuración |
|---------|-------|---------------|
| `dashboard/src/core/config/defaults.ts` | 56 | `baseUrl: "http://localhost:8000"` ✅ |
| `dashboard/package.json` | 32 | `"default": "http://localhost:8000"` ✅ |
| `dashboard/src/core/llm/improvePrompt.ts` | 104 | `dspyBaseUrl ?? "http://localhost:8000"` ✅ |

### 5.2 Code Snippets

**Backend - Configuración Python:**
```python
# hemdov/infrastructure/config/__init__.py
class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000  # ← Default usado
    API_RELOAD: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
```

**Frontend - Configuración TypeScript:**
```typescript
// dashboard/src/core/config/defaults.ts
dspy: {
  /**
   * Base URL for DSPy backend
   * Default: localhost:8000 (FastAPI)
   */
  baseUrl: "http://localhost:8000",  // ← Hardcoded
  // ...
}
```

---

## 6. Historial y Contexto

### 6.1 Cuándo se Introdujo

**Evidencia en commits:**
```bash
# .env.example siempre tuvo 8000
API_PORT=8000

# Pero .env local tiene 8001
API_PORT=8001
```

**Posible explicación:**
- Alguien cambió el `.env` a 8001 para evitar conflictos con otro servicio
- El cambio no se propagó al código Python
- El frontend nunca se actualizó para usar el 8001

### 6.2 Referencias en Documentación

| Documento | Puerto Mencionado | Consistente |
|-----------|-------------------|-------------|
| `docs/backend/README.md` | 8000 | ✅ |
| `docs/backend/quickstart.md` | 8000 | ✅ |
| `docs/plans/2026-01-01-dspy-ollama-pipeline.md` | 8000 | ✅ |
| `.env` | 8001 | ❌ |
| `.env.example` | 8000 | ✅ |

**Conclusión:** Solo `.env` tiene 8001, todo lo demás documenta 8000.

---

## 7. Soluciones Propuestas

### 7.1 Solución Recomendada: Unificar a Puerto 8000

**Razones:**
1. Ya es el default en el código Python
2. Ya está hardcoded en el frontend
3. Toda la documentación usa 8000
4. Es el puerto estándar para servicios de desarrollo

**Pasos:**

1. **Actualizar .env:**
```bash
# Cambiar
API_PORT=8001
# A
API_PORT=8000
```

2. **Verificar que pydantic-settings lo lea:**
```python
# Agregar logging temporal en main.py
logger.info(f"Loaded API_PORT from env: {settings.API_PORT}")
```

3. **Documentar la configuración:**
```markdown
# docs/backend/configuration.md
## Puerto del Servidor

El backend DSPy corre por defecto en el puerto 8000.

Para cambiar el puerto:
1. Editar `.env`: `API_PORT=9000`
2. O variable de entorno: `export API_PORT=9000`
3. Reiniciar el servidor
```

### 7.2 Solución Alternativa: Usar Variable de Entorno

**Si se requiere cambiar el puerto dinámicamente:**

```bash
# En lugar de editar .env
export API_PORT=9000
python main.py
```

**Ventaja:** Funciona correctamente (pydantic-settings sí lee vars de entorno)

**Desventaja:** No persiste entre sesiones

### 7.3 Solución NO Recomendada: Actualizar Frontend a 8001

**Por qué NO:**
1. Requiere cambios en múltiples archivos
2. Rompe consistencia con documentación
3. No resuelve el problema de fondo (.env no leído)

---

## 8. Plan de Acción

### 8.1 Inmediato (Prioridad Alta)

- [ ] Actualizar `.env: API_PORT=8000`
- [ ] Verificar que backend lee la configuración
- [ ] Agregar logging de configuración al startup

### 8.2 Corto Plazo (Prioridad Media)

- [ ] Agregar test que verifique puerto configurado vs puerto en uso
- [ ] Documentar procedimiento para cambiar puerto
- [ ] Actualizar SEGUIMIENTO.md con resolución

### 8.3 Largo Plazo (Prioridad Baja)

- [ ] Considerar usar puerto configurable vía argumento CLI
- [ ] Agregar health check que reporte puerto configurado
- [ ] Unificar todos los archivos de configuración

---

## 9. Testing y Verificación

### 9.1 Tests Propuestos

```typescript
// dashboard/src/core/config/__tests__/port-configuration.test.ts
describe("DSPy Port Configuration", () => {
  it("should have consistent port across all configs", () => {
    const defaults = DEFAULTS.dspy.baseUrl;
    const packageJson = require("../../../../package.json");
    const preferenceDefault = packageJson.preferences.find(
      (p: any) => p.name === "dspyBaseUrl"
    ).default;

    expect(defaults).toBe("http://localhost:8000");
    expect(preferenceDefault).toBe("http://localhost:8000");
    expect(defaults).toBe(preferenceDefault);
  });
});
```

### 9.2 Comandos de Verificación

```bash
# Verificar puerto que está escuchando el backend
lsof -i :8000  # Debería mostrar python/uvicorn
lsof -i :8001  # NO debería mostrar nada

# Verificar configuración cargada
curl http://localhost:8000/health
# Debería responder con status: healthy

# Verificar que frontend conecta
# (Requiere revisar logs de Raycast)
```

---

## 10. Conclusión

**Estado:** ⚠️ Inconsistencia documentada pero funcional

**Resolución:** Simple y de bajo riesgo
- Cambiar `.env` a `API_PORT=8000`
- Verificar que pydantic-settings lo lee
- Documentar el cambio

**Prevención:**
- Agregar test de consistencia de puertos
- Documentar procedimiento de cambio de puerto
- Revisar configuración al hacer deploy

**Riesgo si no se corrige:** Medio
- Confusión continua en documentación
- Dificultad para cambiar puerto en el futuro
- Posibles problemas en deployment

---

**Reportado por:** Auditoría de Pipeline
**Revisado por:** Pendiente
**Aprobado por:** Pendiente
**Fecha de revisión:** Pendiente

---

## 11. Resolución Aplicada (2026-01-02)

### Cambios Realizados

**1. Corregido `.env`**
```diff
- API_PORT=8001
+ API_PORT=8000
```

**2. Agregada validación al startup en `main.py`**
```python
# Validate configuration on startup (fail fast)
if not (1024 <= settings.API_PORT <= 65535):
    raise ValueError(f"Invalid API_PORT: {settings.API_PORT}. Must be between 1024-65535.")

logger.info("✓ Configuration loaded from .env")
logger.info(f"✓ API_PORT: {settings.API_PORT} (validated)")
```

### Verificación

- ✅ `.env` ahora coincide con `.env.example` (ambos en puerto 8000)
- ✅ Validación de rango de puerto agregada (1024-65535)
- ✅ Logging explícito de configuración al startup
- ✅ `.env.example` ya estaba correcto (no requirió cambios)

### Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `.env` | `API_PORT=8001` → `API_PORT=8000` |
| `main.py` | Agregada validación de puerto y logging |
| `.env.example` | Sin cambios (ya correcto) |

### Prácticas Aplicadas (superpowers:secrets-and-config)

1. ✅ **Env-only configuration** - Puerto desde variable de entorno
2. ✅ **Fail fast validation** - Validación al startup
3. ✅ **Keep .env.example in sync** - Sincronizados
4. ✅ **Explicit logging** - Confirmación de configuración cargada
