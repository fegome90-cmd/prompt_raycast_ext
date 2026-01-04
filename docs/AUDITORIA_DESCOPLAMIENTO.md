# AUDITORÍA DE DESACOPLAMIENTO
**Para migración a core/ independiente**

**Fecha:** 2025-01-01
**Objetivo:** Identificar puntos de acoplamiento para separar lógica de negocio de infraestructura Raycast

---

## 1. IDENTIFICACIÓN DE DEPENDENCIAS DE INFRAESTRUCTURA

### 1.1 Dependencias de `@raycast/api`

| Archivo | Línea | Tipo | Detalle |
|---------|-------|------|---------|
| `config/index.ts` | 6 | Import | `import { getPreferenceValues } from "@raycast/api";` |
| `config/index.ts` | 39 | Llamada | `const rawPrefs = getPreferenceValues<RawPreferences>();` |
| `config/index.ts` | 94 | Llamada | `const prefs = getPreferenceValues<RawPreferences>();` |

**HECHO:** No se detectan importaciones de `@raycast/api` en:
- `ollamaStructured.ts`
- `improvePrompt.ts`
- `ollamaRaw.ts`
- `jsonExtractor.ts`

**Conclusión:** El único punto de acoplamiento con Raycast es el cargador de configuración.

---

## 2. DETECCIÓN DE "INFECCIÓN" POR PREFERENCIAS

### 2.1 Funciones que llaman a `getPreferenceValues()`

| Función | Archivo | Líneas | Acoplamiento |
|---------|---------|--------|--------------|
| `loadConfig()` | `config/index.ts` | 31-70 | **ALTO** - Lee preferencias directamente |
| `isSafeMode()` | `config/index.ts` | 92-104 | **MEDIO** - Lee preferencias para override manual |
| `getConfigSource()` | `config/index.ts` | 118-121 | **BAJO** - Solo retorna metadata |

**HECHO:** `loadConfig()` es la única función que requiere reemplazo completo.

**Flujo actual:**
```
getPreferenceValues() → loadConfig() → promptify-quick.tsx (UI)
```

**Flujo propuesto:**
```
ConfigProvider (inyectado) → PromptEngine → CLI/MCP/Raycast
```

---

## 3. AISLAMIENTO DE LÓGICA PURA

### 3.1 Funciones que NO tienen dependencias externas

#### `jsonExtractor.ts` (100% movible a core/)

| Función | Líneas | Dependencias externas |
|---------|--------|----------------------|
| `extractJsonFromText()` | 22-33 | Ninguna |
| `extractFromFence()` | 39-57 | Ninguna |
| `extractFromTag()` | 62-79 | Ninguna |
| `extractFirstJsonObject()` | 85-138 | Ninguna |
| `validateExtractedJson()` | 146-176 | Solo Zod (librería externa, no Raycast) |

#### `ollamaRaw.ts` (100% movible a core/)

| Función | Líneas | Dependencias externas |
|---------|--------|----------------------|
| `fetchTransport()` | 27-71 | Native fetch (Node 18+) (migrated from node-fetch@3.2.10 on 2026-01-04) |
| `makeOllamaGenerateRaw()` | 76-79 | Ninguna |

#### `ollamaStructured.ts` (95% movible a core/)

| Función | Líneas | Dependencias externas | Notas |
|---------|--------|----------------------|-------|
| `ollamaGenerateStructured()` | 62-131 | Solo Zod | **Core business logic** |
| `tryParseJson()` | 137-197 | Ninguna | Pura |
| `sanitizeStructuredOutput()` | 203-220 | Ninguna | Pura |
| `coerceStringArray()` | 226-231 | Ninguna | Pura |
| `parseAndValidateAttempt2()` | 237-278 | Solo Zod | Pura |
| `summarizeZodError()` | 415-427 | Solo Zod | Pura |
| `getSchemaFields()` | 434-471 | Solo Zod | Pura |
| `buildRepairPrompt()` | 362-408 | Ninguna | Pura |
| `isOllamaTransport()` | 354-356 | Ninguna | Type guard |
| `getTransportInstance()` | 338-349 | Ninguna | Factory pattern |
| `failResult()` | 476-503 | `console.error()` | Efecto secundario menor (logging) |

#### `improvePrompt.ts` (98% movible a core/)

| Función | Líneas | Dependencias externas | Notas |
|---------|--------|----------------------|-------|
| `improvePromptWithOllama()` | 66-176 | Solo `ollamaGenerateStructured` | **Core entry point** |
| `callImprover()` | 178-228 | Solo `ollamaGenerateStructured` | Pura (inyecta transport) |
| `buildImprovePromptUser()` | 230-267 | Ninguna | Pura - prompt engineering |
| `buildRepairPrompt()` | 269-308 | Ninguna | Pura - prompt engineering |
| `presetToRules()` | 310-333 | Ninguna | Pura - constantes de dominio |
| `normalizeImproverOutput()` | 335-370 | Ninguna | Pura - post-procesamiento |
| `qualityIssues()` | 372-412 | Ninguna | Pura - validación de dominio |
| `looksLikeQuestion()` | 414-419 | Ninguna | Pura - heurística |
| `dedupePreserveOrder()` | 421-431 | Ninguna | Pura - algoritmo |

---

## 4. ANÁLISIS DE EFECTOS SECUNDARIOS

### 4.1 Llamadas a `showToast`, `Clipboard`, `Toast` dentro de core/

**HECHO:** **No se detectan** llamadas a efectos secundarios de UI en:
- `core/llm/ollamaStructured.ts`
- `core/llm/improvePrompt.ts`
- `core/llm/ollamaRaw.ts`
- `core/llm/jsonExtractor.ts`

**Ubicación de efectos secundarios:**
| Archivo | Función | Efecto |
|---------|---------|--------|
| `promptify-quick.tsx` | `handleGenerateFinal()` | `showToast()`, `Clipboard.copy()` |
| `promptify-quick.tsx` | `PromptPreview()` | `ActionPanel`, `Detail` |

**Conclusión:** La capa `core/` ya está aislada de efectos secundarios de UI.

---

## 5. DEFINICIÓN DE CONTRATOS (INTERFACES)

### 5.1 Interfaz propuesta para `PromptEngine`

Basado en el análisis de `improvePrompt.ts:66-176` y tipos existentes:

```typescript
/**
 * Contrato agnóstico a infraestructura para el motor de prompts
 */
export interface PromptEngineConfig {
  /** Ollama base URL */
  baseUrl: string;
  /** Nombre del modelo Ollama */
  model: string;
  /** Timeout en milisegundos */
  timeoutMs: number;
}

export type PromptPreset = "default" | "specific" | "structured" | "coding";

/**
 * Resultado de mejora de prompt con metadatos de telemetría
 */
export interface PromptImprovementResult {
  /** El prompt mejorado */
  improved_prompt: string;
  /** Preguntas que el usuario debe responder */
  clarifying_questions: string[];
  /** Suposiciones que el LLM hizo */
  assumptions: string[];
  /** Confianza del LLM en el resultado (0-1) */
  confidence: number;
  /** Metadatos internos de ejecución */
  _metadata?: {
    usedExtraction: boolean;
    usedRepair: boolean;
    attempt: 1 | 2;
    extractionMethod?: string;
    latencyMs: number;
  };
}

/**
 * Contrato principal del motor de prompts
 */
export interface PromptEngine {
  /**
   * Mejora un prompt crudo usando el modelo configurado
   *
   * @throws {ImprovePromptError} Con metadata de fallo si hay errores
   */
  improve(args: {
    rawInput: string;
    preset: PromptPreset;
  }): Promise<PromptImprovementResult>;
}

/**
 * Error del motor con metadata de debugging
 */
export class ImprovePromptError extends Error {
  constructor(
    message: string,
    readonly cause?: unknown,
    public readonly meta?: {
      wrapper?: {
        attempt: 1 | 2;
        usedRepair: boolean;
        usedExtraction: boolean;
        failureReason?: string;
        latencyMs: number;
        validationError?: string;
        extractionMethod?: string;
      };
    },
  ) {
    super(message);
    this.name = "ImprovePromptError";
  }
}
```

### 5.2 Interfaz para Provider de Configuración

```typescript
/**
 * Abstracción para fuente de configuración
 * Permite inyectar configuración desde cualquier fuente (CLI args, env vars, Raycast prefs)
 */
export interface ConfigProvider {
  getConfig(): PromptEngineConfig;
}

/**
 * Implementación para Raycast
 */
export class RaycastConfigProvider implements ConfigProvider {
  getConfig(): PromptEngineConfig {
    // Usa getPreferenceValues() internamente
    // Esta es la única parte que permanece en dashboard/
  }
}

/**
 * Implementación para CLI
 */
export class CliConfigProvider implements ConfigProvider {
  getConfig(): PromptEngineConfig {
    // Lee de process.argv, .env file, o defaults
    // Parte de nueva implementación CLI
  }
}
```

---

## 6. VARIABLES DE ENTORNO/CONFIGURACIÓN

### 6.1 Constantes de dominio (movibles a core/)

| Valor | Fuente | Naturaleza |
|-------|--------|------------|
| `bannedSnippets` | `defaults.ts:79-90` | **DOMINIO** - Reglas de validación de calidad |
| `metaLineStarters` | `defaults.ts:96` | **DOMINIO** - Patrones de detección de meta-instrucciones |
| `maxQuestions: 3` | `defaults.ts:50` | **DOMINIO** - Límite de UX del producto |
| `maxAssumptions: 5` | `defaults.ts:56` | **DOMINIO** - Límite de UX del producto |
| `minConfidence: 0.7` | `defaults.ts:73` | **DOMINIO** - Threshold de calidad |
| `jsonValidPass1: 0.54` | `defaults.ts:179` | **DOMINIO** - Quality gate |
| `copyableRate: 0.54` | `defaults.ts:185` | **DOMINIO** - Quality gate |
| `latencyP95Max: 12000` | `defaults.ts:198` | **DOMINIO** - Quality gate |

### 6.2 Valores dependientes de configuración de usuario

| Valor | Fuente | Naturaleza |
|-------|--------|------------|
| `baseUrl: "http://localhost:11434"` | `defaults.ts:15` | **CONFIGURACIÓN** - Endpoint del usuario |
| `model: "qwen3-coder:30b"` | `defaults.ts:21` | **CONFIGURACIÓN** - Modelo seleccionado |
| `fallbackModel: "devstral:24b"` | `defaults.ts:27` | **CONFIGURACIÓN** - Modelo alternativo |
| `timeoutMs: 30000` | `defaults.ts:33` | **CONFIGURACIÓN** - Preferencia de timeout |
| `preset: "structured"` | `defaults.ts:142` | **CONFIGURACIÓN** - Modo de operación |

---

## 7. ESTRUCTURA PROPUESTA PARA MIGRACIÓN

### 7.1 Archivos a mover a `core/` (sin cambios)

```
core/
├── llm/
│   ├── ollamaRaw.ts           # 100% movible
│   ├── jsonExtractor.ts       # 100% movible
│   ├── ollamaStructured.ts    # 95% movible (solo quitar import de config)
│   └── improvePrompt.ts       # 98% movible (solo quitar dependencia de config)
├── domain/
│   ├── constants.ts           # NUEVO: bannedSnippets, metaLineStarters
│   ├── quality.ts             # NUEVO: qualityIssues(), presets
│   └── schemas.ts             # NUEVO: improvePromptSchemaZod
└── PromptEngine.ts            # NUEVO: Facade principal
```

### 7.2 Archivos a permanecer en `dashboard/`

```
dashboard/src/
├── core/
│   └── config/
│       ├── index.ts           # MODIFICAR: Implementar ConfigProvider
│       ├── schema.ts          # Mover a core/domain/schemas.ts
│       └── defaults.ts        # Dividir: constants.ts + config defaults
└── promptify-quick.tsx        # Adaptador Raycast (sin cambios lógica)
```

### 7.3 Nuevo directorio CLI

```
cli/
├── index.ts                   # NUEVO: Entry point CLI
├── CliConfigProvider.ts       # NUEVO: Config desde args/env
└── prompt.ts                  # NUEVO: Comando "prompt improve"
```

---

## 8. RESUMEN EJECUTIVO

### 8.1 Funciones Acopladas (requieren refactorización)

| Función | Razón del acoplamiento |
|---------|------------------------|
| `loadConfig()` | Llama `getPreferenceValues()` de Raycast |
| `isSafeMode()` | Llama `getPreferenceValues()` para override manual |

### 8.2 Funciones Puras (candidatas inmediatas a core/)

**Extracción JSON:**
- `extractJsonFromText()`, `extractFromFence()`, `extractFromTag()`, `extractFirstJsonObject()`, `validateExtractedJson()`

**Transporte Ollama:**
- `fetchTransport()`, `makeOllamaGenerateRaw()`

**Structured generation:**
- `ollamaGenerateStructured()`, `tryParseJson()`, `sanitizeStructuredOutput()`, `buildRepairPrompt()`

**Prompt improvement:**
- `improvePromptWithOllama()`, `buildImprovePromptUser()`, `presetToRules()`, `normalizeImproverOutput()`, `qualityIssues()`

### 8.3 Esfuerzo estimado de refactorización

| Componente | Complejidad | Descripción |
|------------|-------------|-------------|
| Extracción JSON | **NINGUNA** | Ya está desacoplada |
| Transporte Ollama | **NINGUNA** | Ya está desacoplada |
| Structured wrapper | **MÍNIMA** | Solo inyectar config |
| Improve prompt | **MÍNIMA** | Solo inyectar config |
| Config loader | **MEDIA** | Implementar interfaz ConfigProvider |
| UI Adapter | **NINGUNA** | Ya separada |

**Total:** ~4-6 horas de desarrollo + testing

---

**FIN DE LA AUDITORÍA**
