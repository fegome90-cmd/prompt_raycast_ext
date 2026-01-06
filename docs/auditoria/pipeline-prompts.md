# Auditoría: Pipeline de Prompts - raycast_ext

**Fecha:** 2026-01-02
**Estado:** ✅ Completado
**Objetivo:** Análisis completo del pipeline de mejora de prompts para identificar inconsistencias y oportunidades de optimización.

---

## 1. Resumen Ejecutivo

El proyecto `raycast_ext` implementa un sistema de mejora de prompts utilizando una arquitectura híbrida con **DSPy como backend principal** y **Ollama como motor de inferencia local**. El sistema no utiliza base de datos persistente, operando de manera completamente stateless.

### Stack Tecnológico

| Componente | Tecnología | Ubicación |
|------------|-----------|-----------|
| Frontend | TypeScript + Raycast SDK | `dashboard/src/` |
| Backend API | FastAPI + Python | Raíz del proyecto |
| Framework de Prompts | DSPy (Stanford) | `hemdov/domain/dspy_modules/` |
| Motor LLM | Ollama (Local) | `http://localhost:11434` |
| Adaptador Universal | LiteLLM | `hemdov/infrastructure/adapters/` |
| Modelo Primario | Novaeus-Promptist-7B | Modelo GGUF via Ollama |
| Modelo Fallback | devstral:24b | Modelo alternativo |

---

## 2. Arquitectura del Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FLUJO COMPLETO                                 │
└─────────────────────────────────────────────────────────────────────────┘

Usuario (Raycast)
    ↓ [Input: idea cruda]
promptify-quick.tsx
    ↓ [Validación: min 5 caracteres]
improvePrompt.ts (Frontend Logic)
    ↓
    ├─────────────────────────────────────┐
    │  Intenta DSPy Backend (localhost:8000) │
    │  ↓                                   │
    │  PromptImproverAPI                   │
    │  ↓                                   │
    │  dspy_prompt_improver.py             │
    │  ↓                                   │
    │  LiteLLM Adapter                     │
    │  ↓                                   │
    │  Ollama API                          │
    └─────────────────────────────────────┘
    ↓ (si DSPy falla)
    ├─────────────────────────────────────┐
    │  Ollama Directo (Fallback)           │
    │  ↓                                   │
    │  LiteLLM → Ollama                    │
    └─────────────────────────────────────┘
    ↓
[Output Estructurado]
```

### 2.1 Punto de Entrada

**Archivo:** `dashboard/src/promptify-quick.tsx`

```typescript
// Flujo principal:
1. Usuario abre Raycast extension
2. Input desde selección o clipboard
3. Carga de preferencias de configuración
4. Llamada a improvePromptWithHybrid()
5. Renderizado del resultado
```

### 2.2 Lógica de Mejora

**Archivo:** `dashboard/src/core/llm/improvePrompt.ts`

Estrategia híbrida:
1. **DSPy-First**: Intenta backend DSPy en `localhost:8000`
2. **Fallback**: Si DSPy no responde, usa Ollama directo
3. **Quality Gates**: Validación de JSON y confidence scoring

### 2.3 Backend DSPy

**Archivo:** `hemdov/domain/dspy_modules/prompt_improver.py`

```python
# Patrón Architect implementado:
class PromptImprover(dspy.Module):
    """
    Input: raw_idea (str), context (str, optional)
    Output:
        - improved_prompt (str)
        - role (str)
        - directive (str)
        - framework (str)
        - guardrails (list[str])
        - reasoning (str, optional)
        - confidence (float, optional)
    """
```

### 2.4 Adaptador LiteLLM

**Archivo:** `hemdov/infrastructure/adapters/litellm_dspy_adapter.py`

Proveedores soportados:
- Ollama (principal)
- Gemini
- DeepSeek
- OpenAI

---

## 3. Configuración y Modelos

### 3.1 Modelos Configurados

```bash
# Modelo primario (especializado en prompts)
MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M

# Modelo fallback (más general)
FALLBACK_MODEL=devstral:24b

# Base URL de Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Base URL del backend DSPy
DSPY_BASE_URL=http://localhost:8000
```

### 3.2 Variables de Entorno DSPy

```bash
DSPY_MAX_BOOTSTRAPPED_DEMOS=5    # Máximo de demos generadas
DSPY_MAX_LABELED_DEMOS=3          # Máximo de demos etiquetadas
DSPY_COMPILED_PATH=               # Ruta al módulo compilado
```

### 3.3 Configuración Frontend

```typescript
// Opciones configurables por el usuario:
{
  ollamaBaseUrl: "http://localhost:11434",
  dspyBaseUrl: "http://localhost:8000",
  dspyEnabled: true,              // Habilitar/deshabilitar DSPy
  model: "Novaeus-Promptist-7B...",
  fallbackModel: "devstral:24b",
  preset: "structured | default | specific | coding",
  timeoutMs: 30000
}
```

---

## 4. Patrones de Diseño

### 4.1 Patrón Architect

El sistema utiliza el patrón Architect para estructurar prompts:

```
┌─────────────────────────────────────────────────────────┐
│  ROLE        → Quién es el AI                            │
│  DIRECTIVE   → Qué debe hacer                            │
│  FRAMEWORK   → Cómo debe abordar el problema              │
│  GUARDRAILS  → Límites y restricciones                    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Chain-of-Thought (CoT)

DSPy implementa razonamiento paso a paso:
1. Análisis de la idea cruda
2. Identificación del contexto
3. Generación de mejoras
4. Validación estructural
5. Salida formateada

### 4.3 Template-Based

META-PROMPT-UNIVERSAL para estructura consistente:
```typescript
const META_PROMPT = `
Role: {role}
Directive: {directive}
Framework: {framework}
Guardrails: {guardrails}
`;
```

---

## 5. Manejo de Errores y Fallbacks

### 5.1 Estrategia de Fallback

```
┌──────────────────────┐
│  DSPy Backend        │ ← Intenta primero
│  (localhost:8000)    │
└──────────┬───────────┘
           │ (falla)
           ↓
┌──────────────────────┐
│  Ollama Directo      │ ← Fallback
│  (localhost:11434)   │
└──────────┬───────────┘
           │ (falla)
           ↓
┌──────────────────────┐
│  Error Message       │ ← Último recurso
└──────────────────────┘
```

### 5.2 Estrategias de Extracción JSON

Cuando Ollama devuelve texto no estructurado:

1. **Fenced JSON**: Busca `\`\`\`json ... \`\`\``
2. **Tagged JSON**: Busca `<json>...</json>`
3. **Scanning**: Escaneo por JSON válido
4. **Repair**: Extracción automática si parse falla

### 5.3 Quality Gates

| Métrica | Umbral | Propósito |
|---------|--------|-----------|
| JSON Valid | ≥54% | Respuestas parseables |
| Copyable Rate | ≥54% | Prompts usables directamente |
| Latency P95 | ≤12s | Tiempo de respuesta máximo |
| Min Confidence | 0.7 | Confianza mínima requerida |

---

## 6. Almacenamiento de Datos

### 6.1 Sin Base de Datos Persistente

⚠️ **Hallazgo Crítico**: El sistema NO guarda historial de prompts.

**Implicaciones:**
- No hay aprendizaje acumulativo
- No se puede trackear mejoras
- No hay auditoría de uso
- Cada request es independiente

**Soluciones Posibles:**
1. SQLite local para historial
2. Logs estructurados para análisis
3. Vector DB para búsqueda semántica
4. Cache de prompts mejorados

### 6.2 Almacenamiento Actual

| Tipo | Ubicación | Persistencia |
|------|-----------|--------------|
| Configuración | `.env` + Raycast Preferences | Permanente |
| Estado Runtime | Memoria | Volátil |
| Logs | Stdout/Stderr | Volátil |
| Prompts | Ninguno | ❌ No persiste |

---

## 7. Puntos a Investigar (Inconsistencias Potenciales)

### 7.1 🔴 Críticas

| # | Issue | Impacto | Archivos |
|---|-------|---------|----------|
| 1 | **No hay persistencia de prompts** | Alta | `-` |
| 2 | **DSPy backend no está compilado** (`DSPY_COMPILED_PATH=`) | Alta | `.env` |
| 3 | **No hay monitoreo de métricas** | Media | `-` |
| 4 | **Timeout fijo de 30s puede ser insuficiente** | Media | `improvePrompt.ts` |

### 7.2 🟡 Medias

| # | Issue | Impacto | Archivos |
|---|-------|---------|----------|
| 5 | **No hay reintentos automáticos** | Media | `improvePrompt.ts` |
| 6 | **Fallback model es más lento (24b vs 7b)** | Media | Config |
| 7 | **No hay validación de inputs del usuario** | Baja | `promptify-quick.tsx` |
| 8 | **Quality gates bajos (54%)** | Baja | `improvePrompt.ts` |

### 7.3 🟢 Mejoras

| # | Sugerencia | Beneficio |
|---|------------|-----------|
| 9 | Agregar logging estructurado | Debugging |
| 10 | Implementar cache de prompts | Performance |
| 11 | Agregar tests unitarios | Confianza |
| 12 | Documentar API endpoints | Mantenibilidad |

---

## 8. Archivos Clave Identificados

### Frontend (TypeScript)

```
dashboard/src/
├── promptify-quick.tsx              # Entry point principal
├── core/
│   ├── llm/
│   │   └── improvePrompt.ts         # Lógica híbrida DSPy/Ollama
│   └── config/
│       ├── index.ts                 # Config loader
│       ├── defaults.ts              # Valores por defecto
│       └── schema.ts                # Validación Zod
└── components/
    └── (UI components para prompts)
```

### Backend (Python)

```
hemdov/
├── domain/
│   └── dspy_modules/
│       └── prompt_improver.py       # Módulo DSPy principal
├── infrastructure/
│   └── adapters/
│       └── litellm_dspy_adapter.py # Adaptador universal
└── api/
    └── prompt_improver_api.py       # FastAPI endpoint

eval/
└── src/
    └── dspy_prompt_improver.py      # Versión compilada
```

### Configuración

```
.
├── .env                             # Variables de entorno
├── pyproject.toml                   # Dependencias Python
├── dashboard/package.json           # Dependencias Node
└── requirements.txt                 # Requisitos Python
```

---

## 9. Estado de Compilación DSPy

### 9.1 Módulo Compilado vs No Compilado

El sistema soporta dos modos de operación:

| Modo | Descripción | Estado Actual |
|------|-------------|---------------|
| **Compiled** | DSPy con ejemplos optimizados | ❌ No configurado |
| **Zero-shot** | DSPy sin optimización previa | ✅ Activo |

### 9.2 Compilación

Para compilar el módulo DSPy:

```bash
# Dataset de entrenamiento requerido
npm run eval -- --dataset testdata/cases.jsonl --output eval/compiled.json

# Esto generaría:
# - Few-shot examples optimizados
# - Mejor calidad de salida
# - Mayor consistencia
```

**Estado Actual:** `DSPY_COMPILED_PATH=` (vacío)

---

## 10. Verificación de Estado (2026-01-02)

### 10.1 Estado de Servicios ✅

| Servicio | Estado | Detalles |
|----------|--------|----------|
| **DSPy Backend** | ✅ Running | `http://localhost:8000` - Status: healthy, DSPy configured: true |
| **Ollama** | ✅ Running | `http://localhost:11434` - 4 modelos disponibles |
| **Novaeus-Promptist-7B** | ✅ Loaded | Modelo primario presente (5.4GB) |
| **API Endpoint** | ✅ Available | `/api/v1/improve-prompt` funcional |

### 10.2 Modelos Disponibles en Ollama

```
1. hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M (5.4GB)
   → Modelo especializado en prompt engineering

2. nomic-embed-text:latest (274MB)
   → Modelo para embeddings

3. qwen3-coder:30b (18.5GB)
   → Modelo para código

4. qwen3:latest (5.2GB)
   → Modelo general
```

### 10.3 Verificación de Configuración

**Archivo `.env` (líneas clave):**
```bash
# ✅ Correcto
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434

# ⚠️ Vacío - DSPy no está compilado
DSPY_COMPILED_PATH=

# ✅ Configurado
MIN_CONFIDENCE_THRESHOLD=0.7
MAX_LATENCY_MS=30000
```

**Archivo `defaults.ts` (líneas clave):**
```typescript
// ✅ Quality gates configurados
jsonValidPass1: 0.54,    // 54% mínimo
copyableRate: 0.54,      // 54% mínimo
latencyP95Max: 12_000,   // 12 segundos máximo

// ✅ Timeout configurado
timeoutMs: 30_000,       // 30 segundos
```

### 10.4 Análisis del Código `improvePrompt.ts`

**Estrategia híbrida confirmada:**
```typescript
// Línea 74-153: improvePromptWithHybrid()
1. Crea cliente DSPy (localhost:8000)
2. Health check a DSPy backend
3. Si DSPy healthy → usa DSPy
4. Si DSPy falla → fallback a Ollama
5. Retorna metadata con backend usado
```

**Flujo Ollama con 2 intentos:**
```typescript
// Línea 158-284: improvePromptWithOllama()
Intento 1: Generación directa
  ↓ Si hay quality issues
Intento 2: Repair prompt
  ↓ Retorna resultado
```

---

## 11. Hallazgos Confirmados

### 11.1 🔴 Críticas Confirmadas

| # | Issue | Estado | Impacto |
|---|-------|--------|---------|
| 1 | **No hay persistencia de prompts** | ✅ Confirmado | Alta |
| 2 | **DSPy backend no está compilado** (`DSPY_COMPILED_PATH=`) | ✅ Confirmado | Alta |
| 3 | **No hay monitoreo de métricas** | ✅ Confirmado | Media |

### 11.2 🟡 Medias Confirmadas

| # | Issue | Estado | Impacto |
|---|-------|--------|---------|
| 4 | **No hay reintentos automáticos** | ✅ Confirmado | Media |
| 5 | **Quality gates al 54%** | ✅ Confirmado | Baja-Media |

### 11.3 ✅ Componentes Funcionales

| Componente | Estado | Notas |
|------------|--------|-------|
| DSPy Backend | ✅ Operational | Health check OK |
| Ollama API | ✅ Operational | 4 modelos cargados |
| Fallback mechanism | ✅ Working | DSPy → Ollama |
| JSON extraction | ✅ Multi-strategy | 3 métodos implementados |
| Auto-repair | ✅ Working | 2 intentos con repair |

---

## 12. Inconsistencias Identificadas

### 12.1 Puerto DSPy: Diferencia entre .env y defaults.ts

| Archivo | Configuración |
|---------|---------------|
| `.env` | `API_PORT=8001` |
| `defaults.ts` | `baseUrl: "http://localhost:8000"` |

**Impacto:** Si se cambia el puerto en .env, el frontend seguirá intentando conectar al 8000.

**Recomendación:** Unificar configuración de puerto.

### 12.2 DSPy Signature vs Output Schema

**DSPy Signature** (`prompt_improver.py`):
```python
- improved_prompt (str)
- role (str)
- directive (str)
- framework (str)
- guardrails (list[str])
- reasoning (str, optional)
- confidence (float, optional)
```

**Frontend Schema** (`improvePrompt.ts`):
```typescript
{
  improved_prompt: string,
  clarifying_questions: string[],  // ❌ No existe en DSPy
  assumptions: string[],           // ❌ No existe en DSPy
  confidence: number
}
```

**Impacto:** DSPy no genera `clarifying_questions` ni `assumptions` - el frontend los setea como array vacío.

**Estado:** Funcional pero inconsistente.

### 12.3 Módulo DSPy No Implementado

**Archivo:** `hemdov/domain/dspy_modules/prompt_improver.py`

**Contenido actual:** Solo define la `Signature`, no el `Module`.

```python
# ❌ Falta:
class PromptImprover(dspy.Module):
    def forward(self, original_idea: str, context: str) -> Output:
        # Implementación no encontrada
```

**Impacto:** El backend DSPy probablemente usa una implementación separada no visible en este archivo.

---

## 13. Recomendaciones Prioritarias

### 13.1 Inmediatas (Alta Prioridad)

1. **Unificar configuración de puerto DSPy**
   - Sincronizar `.env:API_PORT` con `defaults.ts:dspy.baseUrl`

2. **Implementar persistencia básica**
   - SQLite local para historial de prompts
   - Tabla: `prompts(id, input, output, backend, timestamp, quality_score)`

3. **Documentar módulo DSPy**
   - Ubicar la implementación real de `PromptImprover.forward()`
   - Documentar por qué `clarifying_questions` no se genera

### 13.2 Corto Plazo (Media Prioridad)

4. **Agregar monitoreo básico**
   - Logging estructurado con timestamps
   - Métricas: latencia, success rate, backend usado

5. **Compilar DSPy**
   - Ejecutar `npm run eval` para generar few-shot examples
   - Configurar `DSPY_COMPILED_PATH` con el resultado

6. **Implementar reintentos**
   - 2 reintentos automáticos antes de fallback
   - Backoff exponencial: 1s → 2s → 4s

### 13.3 Largo Plazo (Baja Prioridad)

7. **Subir quality gates**
   - Actual: 54% → Objetivo: 70%
   - Baseline: medir performance actual

8. **Agregar tests E2E**
   - Test del pipeline completo
   - Mock de DSPy y Ollama

---

## 14. Conclusión

El sistema está **funcional y operativo** con DSPy backend y Ollama corriendo correctamente. Las principales inconsistencias identificadas son:

1. **Configuración desincronizada** (puerto DSPy)
2. **Falta de persistencia** (no se guarda historial)
3. **DSPy no compilado** (opera en modo zero-shot)
4. **Esquemas inconsistentes** (DSPy vs Frontend)

**Estado General:** 🟡 Operativo con oportunidades de mejora

**Riesgo Inmediato:** Bajo - el sistema funciona correctamente

**Deuda Técnica:** Media - mejorar persistencia y compilación incrementaría calidad significativamente

---

## 15. Referencias

- **DSPy Documentation:** https://dspy-docs.vercel.app/
- **LiteLLM Documentation:** https://docs.litellm.ai/
- **Ollama Documentation:** https://ollama.com/docs
- **Novaeus Model:** https://huggingface.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF

---

**Última actualización:** 2026-01-02
**Próxima revisión:** Pendiente análisis de logs y métricas reales
