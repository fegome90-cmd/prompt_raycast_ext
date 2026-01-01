# INFORME DE FACTIBILIDAD TÉCNICA

**Integración: Llama-3.1-8B-Instruct-Prompt-Engineer + Fabric**

**Repositorio:** Prompt Renderer Local (raycast_ext)

**Fecha:** 2025-01-01

**Método:** Análisis estático de código fuente

---

## 1. STACK TECNOLÓGICO ACTUAL

| Categoría | Tecnología | Versión | Fuente |
|-----------|------------|---------|--------|
| **Framework UI** | Raycast Extension API | latest | package.json:80 |
| **Lenguaje** | TypeScript | 5.2.2 | package.json:93 |
| **Runtime** | Node.js | 18.18.4 (types) | package.json:87 |
| **Motor LLM** | Ollama (local) | Dato no disponible | package.json:3 |
| **Validación** | Zod | 3.24.1 | package.json:83 |
| **Testing** | Vitest | 1.6.0 | package.json:94 |
| **HTTP Client** | node-fetch | 3.2.10 | package.json:82 |
| **Build Tool** | Ray CLI | Dato no disponible | package.json:97 |

**Modelos configurados actualmente:**
- Primario: `qwen3-coder:30b` (defaults.ts:21)
- Fallback: `devstral:24b` (defaults.ts:27)

---

## 2. ARQUITECTURA DE INFERENCIA

### 2.1 Método de integración con LLM

**HECHO:** El proyecto utiliza **llamadas HTTP directas a Ollama**, sin frameworks de abstracción como LangChain.

**Evidencia:**
```typescript
// ollamaStructured.ts:310-315
const result = await transport({
  baseUrl,
  model,
  prompt,
  timeoutMs,
});
```

**Flujo de datos:**
```
UI (promptify-quick.tsx)
  → improvePrompt.ts (lógica de negocio)
    → ollamaStructured.ts (wrapper con extracción + repair)
      → ollamaRaw.ts (transport HTTP)
        → Ollama API (localhost:11434)
```

### 2.2 Características del wrapper actual

**HECHO:** El wrapper `ollamaStructured.ts` implementa:
- 2 intentos máximo (directo → repair)
- Extracción JSON multi-estrategia (fence, tag, scan)
- Validación con Zod schemas
- Sanitización de arrays null/undefined
- Telemetría completa (intentos, extracción, reparación)

**Líneas relevantes:**
- ollamaStructured.ts:62: `"ollamaGenerateStructured<T>"`
- ollamaStructured.ts:137-197: `tryParseJson` con 3 modos

---

## 3. PUNTOS DE INTEGRACIÓN PARA FABRIC

### 3.1 CLI (Command Line Interface)

**HECHO:** **No existe CLI nativo** en este proyecto.

**Evidencia:**
- Búsqueda de archivos `cli*.ts`: Sin resultados (Glob)
- Scripts en package.json:96-107 son comandos npm estándar

**Scripts disponibles:**

| Script | Comando | Propósito |
|--------|---------|-----------|
| build | `ray build -e dist` | Compilación |
| dev | `ray develop` | Desarrollo en vivo |
| lint | `ray lint` | Verificación ESLint |
| test | `vitest run` | Ejecutar tests |
| eval | `tsx scripts/evaluator.ts` | Evaluación de calidad |

**MCP Server (alternativa a CLI):**
- Ubicación: `mcp-server/src/index.ts`
- Implementa: Model Context Protocol para integración con Zed
- Tools disponibles:
  - `run_quality_gates`
  - `get_quality_metrics`
  - `validate_code_quality`
  - `analyze_failure_patterns`

### 3.2 Sistema de Gestión de Templates

**HECHO:** Existe un sistema de plantillas basado en **presets hardcoded**.

**Evidencia:**
```typescript
// defaults.ts:141-144
presets: {
  default: "structured",
  available: ["default", "specific", "structured", "coding"],
}
```

**Archivo de plantilla universal:**
- Ruta: `dashboard/templates/META-PROMPT-UNIVERSAL-v2.0.0.patched.md`
- Propósito: Meta-prompt con sistema de validación, antidrift, y handoff
- Tamaño: ~1600 líneas

**Sin evidencia de:**
- Sistema de carga dinámica de templates desde directorios
- API para agregar/remover patrones en runtime
- Estructura de "Patterns" como Fabric

### 3.3 Soporte para Unix Pipes

**HECHO:** **Sin evidencia en el repositorio** de soporte para pipes Unix.

**Análisis:**
- El proyecto está diseñado como extensión de Raycast (GUI)
- Flujo de datos: Input → Raycast UI → Ollama → Output
- No existe interfaz stdin/stdout para chaining de comandos

**MCP Server usa:** stdio solo como transporte, no para datos de usuario

---

## 4. COMPATIBILIDAD DEL MODELO

### 4.1 Soporte GGUF / Ollama

**HECHO:** El backend está **construido exclusivamente para Ollama**.

**Evidencia:**
```typescript
// schema.ts:16-19
model: z
  .string()
  .min(1, "model cannot be empty")
  .regex(/^[a-z0-9][a-z0-9\-._:]*$/i, "model must be a valid Ollama model name")
```

**Validación acepta:** Nombres de modelo Ollama estándar (ej: `qwen3-coder:30b`)

**HECHO:** Ollama soporta nativamente modelos GGUF.

**Conclusión:** El modelo `Llama-3.1-8B-Instruct-Prompt-Engineer` **será compatible** si:
1. Está disponible en formato GGUF
2. Se agrega a Ollama vía `ollama pull`
3. Se configura en `package.json` o defaults.ts

### 4.2 Límites de Hardware / Configuración

**HECHO:** **Sin evidencia de límites de hardware explícitos** en el código.

**Búsqueda de términos:** `gguf`, `GGUF`, `quantization`, `memory`, `ram`, `vram`
- Resultado: Solo referencias en documentación y meta-prompts, no en código de configuración

**Configuración de timeouts:**
```typescript
// defaults.ts:33
timeoutMs: 30_000,  // 30 segundos

// schema.ts:28-32
.timeoutMs: z
  .number()
  .max(120_000, "timeoutMs must not exceed 2 minutes")
```

**Interpretación:**
- El timeout máximo es 2 minutos
- Para un modelo 8B (vs 30B actual), el timeout es **suficiente**
- No hay límites de memoria explícitos en la configuración

---

## 5. ANÁLISIS DE BLOQUEOS

### 5.1 Dependencias que impiden integración CLI

**HECHO:** **Arquitectura acoplada a Raycast API**.

**Evidencia:**
```typescript
// promptify-quick.tsx:1
import { Action, ActionPanel, Clipboard, Detail, Form, Toast, getPreferenceValues, showToast } from "@raycast/api";
```

**Bloqueos identificados:**

| Componente | Tipo de Bloqueo | Descripción |
|------------|-----------------|-------------|
| UI Layer | **HARD** | Componentes React específicos de Raycast |
| Preferences | **MEDIUM** | `getPreferenceValues()` requiere contexto Raycast |
| Clipboard | **SOFT** | Se puede reemplazar por stdout en CLI |
| Toast notifications | **SOFT** | Se puede reemplazar por console.log |

### 5.2 Arquitecturas rígidas

**HECHO:** El diseño sigue el patrón **Raycast Extension** con:

1. **Single entry point:** `promptify-quick.tsx` (Command export)
2. **UI-first:** La lógica está atada a ciclo de vida de componentes React
3. **Preferences-driven:** Configuración via GUI de Raycast

**Conclusión:** Para usar herramientas CLI externas (como Fabric), se requeriría:
- **Opción A:** Refactorizar para separar core business logic de UI
- **Opción B:** Crear un binario CLI separado que use el core
- **Opción C:** Integrar vía MCP Server (ya existe)

---

## 6. TABLA DE DECISIÓN

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| **Stack compatible con Ollama** | ✅ COMPATIBLE | HTTP directo a localhost:11434 |
| **Modelos 8B soportados** | ✅ SOPORTADO | Sin límites de parámetros en config |
| **CLI nativo** | ❌ NO EXISTE | Solo scripts npm |
| **Sistema de patterns** | ⚠️ HARDCODED | Presets fijos en defaults.ts |
| **Unix pipes** | ❌ SIN EVIDENCIA | Diseño GUI-only |
| **MCP Server** | ✅ EXISTE | mcp-server/src/index.ts |
| **Formato GGUF** | ✅ COMPATIBLE | Ollama lo soporta nativamente |
| **Límites de hardware** | ❌ SIN LÍMITES | No hay restricciones en código |

---

## 7. CONCLUSIONES (SOLO HECHOS)

### 7.1 Para integrar Llama-3.1-8B-Instruct-Prompt-Engineer

**Requisitos técnicos mínimos:**
1. Disponer del modelo en formato GGUF
2. Ejecutar `ollama pull <modelo>`
3. Cambiar configuración en:
   - `package.json:32` (default: "qwen3-coder:30b")
   - `dashboard/src/core/config/defaults.ts:21` (model: "qwen3-coder:30b")

**Sin evidencia de bloqueos técnicos** para esta integración.

### 7.2 Para integrar Fabric

**Bloqueos arquitectónicos:**
- Fabric requiere CLI con stdin/stdout
- Proyecto actual es GUI-only (Raycast)

**Opciones factibles según código existente:**
1. **Usar MCP Server existente** como punto de integración
2. **Crear script CLI separado** que importe core business logic
3. **Refactorizar** para desacoplar UI de lógica de negocio

**Sin evidencia en el repositorio** de que Fabric pueda integrarse directamente sin modificaciones arquitectónicas.

---

## 8. REFERENCIAS DE CÓDIGO

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `dashboard/package.json` | 1-109 | Configuración del proyecto |
| `dashboard/src/core/config/schema.ts` | 1-296 | Validación Zod de config |
| `dashboard/src/core/config/defaults.ts` | 1-221 | Valores por defecto |
| `dashboard/src/core/config/index.ts` | 1-283 | Loader de configuración |
| `dashboard/src/core/llm/ollamaStructured.ts` | 1-514 | Wrapper principal LLM |
| `dashboard/src/promptify-quick.tsx` | 1-233 | UI principal Raycast |
| `mcp-server/src/index.ts` | 1-340 | Servidor MCP |
| `dashboard/templates/META-PROMPT-UNIVERSAL-v2.0.0.patched.md` | 1-1600+ | Plantilla maestra |

---

**FIN DEL INFORME**
