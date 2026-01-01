# Prompt Renderer Local - Guía para Claude

> Extensión de Raycast para mejorar prompts usando modelos locales (Ollama)

---

## Visión General

**Prompt Renderer Local** es una extensión de Raycast que transforma textos crudos en prompts deterministas y de alta calidad usando modelos LLM locales (Ollama). La diferencia clave frente a herramientas similares es que **todo ocurre localmente** — sin cloud, sin costes de API, y con privacidad total.

**Qué hace:**
- Toma input del usuario (selección de texto o portapapeles)
- Lo mejora mediante plantillas y modelos LLM locales
- Devuelve un prompt listo para usar, formateado y optimizado

**Stack tecnológico principal:**
- Raycast Extension API (React + TypeScript)
- Ollama como motor LLM local
- Zod para validación de esquemas
- Vitest para testing

**Características únicas:**
- Sistema de quality gates automatizados
- Fallback robusto entre modelos
- Extracción JSON multi-estrategia
- Integración MCP con Zed

---

## Arquitectura y Estructura

**Patrón arquitectónico:** Modular en capas con separación de responsabilidades

```
┌─────────────────────────────────────────────────────┐
│                    PRESENTATION                      │
│  promptify-quick.tsx (Raycast React UI)              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                     BUSINESS LOGIC                   │
│  improvePrompt.ts → Pipeline de mejora              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                       INFRASTRUCTURE                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Config     │  │     LLM      │  │ Templates │ │
│  │  (Zod-safe)  │  │  (Ollama)    │  │ (Presets) │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

**Directorios clave:**

- `dashboard/src/` → Código fuente principal
- `dashboard/src/core/config/` → Configuración centralizada con Zod
- `dashboard/src/core/llm/` → Integración Ollama con wrapper robusto
- `dashboard/src/core/pipeline/` → Lógica de procesamiento
- `dashboard/templates/` → Plantillas de prompts (META-PROMPT-UNIVERSAL)
- `mcp-server/` → Servidor MCP para integración con Zed
- `dashboard/scripts/evaluator.ts` → Sistema de quality gates

**Flujo de datos:**
1. Usuario ingresa texto en Raycast UI
2. Config se carga con fallback a defaults si falla
3. Health check a Ollama (localhost:11434)
4. Prompt mejorado vía `ollamaGenerateStructured` (2 intentos max)
5. Resultado validado contra Zod schema
6. Output copiado al clipboard con metadatos

---

## Patrones y Convenciones

### Código

**Naming conventions:**
- `camelCase` para funciones y variables
- `PascalCase` para tipos, interfaces y clases
- Prefijo `_` para variables privadas internas

**Estructura de imports:**
```typescript
// 1. Dependencies externas
import { z } from "zod";
import { getPreferenceValues } from "@raycast/api";

// 2. Dependencias internas (relativas)
import { DEFAULTS } from "./defaults";
import { validateConfig } from "./schema";
```

**Manejo de errores:**
- Custom error classes con metadata para debugging
- Siempre incluir `failureReason` en resultados fallidos
- Usar `safeParse` de Zod para validación sin excepciones

### Configuración

**Schema-driven:**
- Toda configuración se valida con Zod antes de usar
- Ver `dashboard/src/core/config/schema.ts` para esquemas completos

**Safe mode:**
- Si la validación falla, el sistema activa safe mode automáticamente
- Usa defaults pre-validados como fallback
- Nunca falla por configuración inválida

**Modelos:**
- Modelo primario: `qwen3-coder:30b` (configurable)
- Modelo fallback: `devstral:24b` (se usa si el primario falla)
- Cambiar en: `package.json` o `defaults.ts`

### Testing

**Framework:** Vitest con coverage v8

**Comandos:**
```bash
npm test              # Ejecutar tests
npm run test:coverage # Con reporte de cobertura
npm run eval          # Ejecutar evaluador de calidad
```

**Quality gates:**
- `jsonValidPass1`: ≥54% (JSON válido en primer intento)
- `copyableRate`: ≥54% (prompts copiables directamente)
- `latencyP95`: ≤12s (latencia percentil 95)

---

## Componentes Clave

### Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `promptify-quick.tsx` | UI principal de Raycast |
| `improvePrompt.ts` | Lógica core de mejora de prompts |
| `ollamaStructured.ts` | Wrapper robusto para JSON generation |
| `evaluator.ts` | Sistema de quality gates |
| `config/index.ts` | Gestión centralizada de configuración |

### Ollama Wrapper (`ollamaStructured.ts`)

**Características:**
- 2 intentos máximo (directo → repair)
- Extracción JSON multi-estrategia:
  - `fence`: Busca ```json ... ```
  - `tag`: Busca <json>...</json>
  - `scan`: Busca cualquier JSON válido
- Sanitización automática de arrays null/undefined
- Telemetría completa en cada resultado

**Modos de operación:**
- `strict`: Solo parse directo, sin extracción
- `extract`: Intenta extraer JSON si falla parse
- `extract+repair`: Extrae + repara si falla validación

### Config System

**Loader (`config/index.ts`):**
```typescript
const state = loadConfig();
// state.config → Configuración validada
// state.safeMode → true si hubo error
// state.errors → Array de errores
```

**Defaults (`config/defaults.ts`):**
- Single source of truth para todos los valores
- Documentado con rationale para cada setting

---

## Desarrollo

### Scripts Disponibles

```bash
# Desarrollo
npm run dev          # Desarrollo en vivo con Raycast
npm run build        # Compilación para producción

# Calidad
npm run lint         # Verificar ESLint
npm run fix-lint     # Auto-fix de problemas
npm test             # Ejecutar tests
npm run test:coverage # Con reporte de cobertura

# Evaluación
npm run eval         # Ejecutar quality gates

# Publicación
npm run publish      # Publicar a Raycast Marketplace
```

### Agregar un Nuevo Preset

1. Agregar nombre a `defaults.ts`:
```typescript
presets: {
  available: ["default", "specific", "structured", "coding", "nuevo_preset"],
}
```

2. Actualizar `schema.ts`:
```typescript
available: z
  .array(z.enum(["default", "specific", "structured", "coding", "nuevo_preset"]))
```

3. Agregar lógica en `improvePrompt.ts` para el nuevo preset

### Configurar un Modelo Diferente

**Opción 1: Via Raycast UI**
- Abrir preferences de la extensión
- Cambiar "Model" y "Fallback Model"

**Opción 2: Via código**
1. Editar `package.json:32` (default)
2. Editar `dashboard/src/core/config/defaults.ts:21`
3. Asegurar que el modelo esté disponible en Ollama: `ollama pull <modelo>`

---

## MCP Server (Integración con Zed)

**Ubicación:** `mcp-server/src/index.ts`

**Tools disponibles:**
- `run_quality_gates` - Ejecuta evaluador de calidad
- `get_quality_metrics` - Obtiene métricas históricas
- `validate_code_quality` - Ejecuta ESLint y TypeScript checking
- `analyze_failure_patterns` - Analiza patrones de fallo

**Uso en Zed:**
Configurar en `.zed/settings.json` bajo `mcp_servers`

---

## Troubleshooting

### Ollama no responde

```bash
# Verificar que Ollama esté corriendo
ollama list

# Si no está corriendo, iniciarlo
ollama serve
```

### Timeout errors

**Síntoma:** `Error: timed out` después de 30s

**Solución:** Aumentar timeout en preferences:
- Abrir configuración de la extensión
- Cambiar "Timeout (ms)" a 60000 (60s)

### Modelo no encontrado

**Síntoma:** `model not found` en output

**Solución:**
```bash
# Descargar el modelo
ollama pull qwen3-coder:30b
```

### Safe mode activado

**Síntoma:** Toast "Invalid Configuration - Using safe mode"

**Solución:**
1. Revisar logs en consola
2. Verificar que `package.json` tenga valores válidos
3. Reiniciar Raycast

---

## Notas Importantes

### Dependencias de Raycast

Este proyecto **está acoplado a Raycast API**. La UI (`@raycast/api`) no funciona standalone.

### Para crear una CLI independiente

Se requiere refactorizar:
1. Extraer business logic de `promptify-quick.tsx`
2. Crear entry point CLI que use `improvePrompt.ts`
3. Reemplazar `getPreferenceValues()` con argumentos de CLI
4. Reemplazar clipboard/toast con stdout/console.log

### Modelos GGUF

Ollama soporta modelos en formato GGUF nativamente. Para usar un modelo personalizado:

```bash
# Crear Modelfile
FROM /path/to/model.gguf
PARAMETER temperature 0.7

# Construir
ollama create nombre-modelo -f Modelfile
```

---

## Referencias

- **Documentación de Raycast:** https://developers.raycast.com
- **Documentación de Ollama:** https://ollama.com/docs
- **Quality Gates:** Ver `dashboard/scripts/evaluator.ts`
- **Meta-prompt universal:** `dashboard/templates/META-PROMPT-UNIVERSAL-v2.0.0.patched.md`
