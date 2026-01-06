# Multi-Provider LLM Abstraction - Capa de Abstracción Unificada

**Prioridad:** 🔴 CRÍTICA - ROI MUY ALTO
**Fuente:** Architect v3.2.0 - `/services/llmService.ts`, `/backend/services/llm/LLMServiceManager.js`
**Complejidad:** Alta
**Adaptabilidad:** Requerida para Raycast (Ollama + otros)

---

## 🎯 Concepto Core

Capa de abstracción que unifica múltiples proveedores de LLM (OpenAI, Anthropic, Google Gemini, GLM, etc.) bajo una interfaz común, permitiendo cambio dinámico de proveedor, fallback automático, selección inteligente por capacidades, y optimización de costos.

**El problema que resuelve:**
- ¿Cómo cambiar entre proveedores sin modificar todo el código?
- ¿Qué hacer si un proveedor falla?
- ¿Cómo seleccionar el modelo óptimo para cada tarea?
- ¿Cómo optimizar costos comparando proveedores?

**La solución:**
- Interfaz unificada para todos los proveedores
- Sistema de registro dinámico de proveedores
- Selección inteligente por capacidades
- Fallback automático entre proveedores
- Reintentos con backoff exponencial
- Tracking de costos y performance

---

## 🏗️ Arquitectura del Sistema

### Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-PROVIDER LLM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  APPLICATION LAYER                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ "Generate text with best model"                                   ││
│  └──────────────────────────┬──────────────────────────────────────────┘│
│                             ↓                                          │
│  ABSTRACTION LAYER (LLMServiceManager)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ 1. Provider Selection                                               ││
│  │    ├─ Explicit (user specifies)                                   ││
│  │    ├─ Default (configured fallback)                               ││
│  │    └─ Intelligent (by capabilities)                               ││
│  │                                                                    ││
│  │ 2. Capability Matching                                             ││
│  │    ├─ Features required (streaming, vision, etc.)                 ││
│  │    ├─ Cost constraints                                            ││
│  │    └─ Performance requirements                                     ││
│  │                                                                    ││
│  │ 3. Retry & Fallback Logic                                          ││
│  │    ├─ Retry with exponential backoff                              ││
│  │    ├─ Fallback to alternative providers                           ││
│  │    └─ Error categorization (auth, rate-limit, etc.)              ││
│  └──────────────────────────┬──────────────────────────────────────────┘│
│                             ↓                                          │
│  PROVIDER LAYER (Specific Implementations)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Gemini   │  │  OpenAI  │  │Anthropic │  │   GLM    │              │
│  │ Provider │  │ Provider │  │ Provider │  │ Provider │              │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘              │
│        │             │             │             │                      │
│        └─────────────┴─────────────┴─────────────┘                     │
│                             ↓                                          │
│  API LAYER (External Services)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Google AI │ OpenAI API │ Anthropic API │ GLM API                  ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes Clave

### 1. **Model Capabilities Matrix**

**Estructura de capacidades:**

```typescript
interface ModelCapabilities {
  textGeneration: boolean;   // ¿Genera texto?
  streaming: boolean;        // ¿Soporta streaming?
  functionCalling: boolean;  // ¿Soporta function calling?
  imageAnalysis: boolean;    // ¿Analiza imágenes?
  longContext: boolean;      // ¿Soporta contexto largo?
  jsonMode: boolean;         // ¿Output en JSON?
}
```

**Matriz de modelos:**

| Modelo | Provider | Text | Stream | Func Call | Vision | Long Context | JSON | Cost/1M tokens | Speed |
|--------|----------|------|--------|-----------|--------|--------------|------|---------------|-------|
| Gemini 2.5 Pro | Google | ✅ | ✅ | ✅ | ✅ | ✅ (32K) | ✅ | $1.25 | Medium |
| Gemini 2.5 Flash | Google | ✅ | ✅ | ✅ | ✅ | ✅ (32K) | ❌ | $0.075 | Fast |
| Flash Lite | Google | ✅ | ❌ | ❌ | ❌ | ❌ (8K) | ❌ | $0.0375 | Fast |
| GPT-4 Turbo | OpenAI | ✅ | ✅ | ✅ | ✅ | ✅ (128K) | ✅ | $1.00 | Medium |
| GPT-3.5 Turbo | OpenAI | ✅ | ✅ | ✅ | ❌ | ❌ (16K) | ✅ | $0.50 | Fast |
| Claude 3.5 Sonnet | Anthropic | ✅ | ✅ | ✅ | ✅ | ✅ (200K) | ❌ | $0.003 | Medium |
| Claude 3 Opus | Anthropic | ✅ | ✅ | ✅ | ✅ | ✅ (200K) | ❌ | $0.015 | Slow |
| GLM-4.6 | Zhipu AI | ✅ | ✅ | ✅ | ❌ | ✅ (128K) | ✅ | ~$0.50 | Fast |

**Uso de la matriz:**

```typescript
// Selección por capacidades requeridas
function selectModel(requirements: {
  needsVision: boolean;
  needsStreaming: boolean;
  needsLongContext: boolean;
  maxCostPer1M: number;
}): LLMModel {
  // Filtrar modelos que cumplen requisitos
  const candidates = allModels.filter(model => {
    if (requirements.needsVision && !model.capabilities.imageAnalysis) return false;
    if (requirements.needsStreaming && !model.capabilities.streaming) return false;
    if (requirements.needsLongContext && !model.capabilities.longContext) return false;
    if (model.costPerToken > requirements.maxCostPer1M) return false;
    return true;
  });

  // Ordenar por costo (más barato primero)
  candidates.sort((a, b) => a.costPerToken - b.costPerToken);

  return candidates[0]; // Retorna el más barato que cumple
}
```

### 2. **Provider Registry**

**Sistema de registro dinámico:**

```typescript
class LLMServiceManager {
  providers: Map<string, LLMProvider> = new Map();
  defaultProvider: string = null;
  providerPriority: string[] = [];  // Orden de fallback

  // Registro de proveedor
  registerProvider(providerId: string, config: any): LLMProvider {
    let provider;

    switch (providerId) {
      case "gemini":
        provider = new GeminiProvider(config);
        break;
      case "openai":
        provider = new OpenAIProvider(config);
        break;
      case "anthropic":
        provider = new AnthropicProvider(config);
        break;
      case "glm":
        provider = new GLMProvider(config);
        break;
      default:
        throw new Error(`Unknown provider: ${providerId}`);
    }

    // Registrar en el mapa
    this.providers.set(providerId, provider);

    // Primer proveedor registrado → default
    if (!this.defaultProvider) {
      this.defaultProvider = providerId;
    }

    // Agregar a lista de prioridad si no existe
    if (!this.providerPriority.includes(providerId)) {
      this.providerPriority.push(providerId);
    }

    return provider;
  }

  // Configurar orden de fallback
  setProviderPriority(providerIds: string[]) {
    // Validar que todos estén registrados
    for (const id of providerIds) {
      if (!this.providers.has(id)) {
        throw new Error(`Provider ${id} not registered`);
      }
    }
    this.providerPriority = providerIds;
  }
}
```

**Uso práctico:**

```typescript
// Inicialización
const manager = new LLMServiceManager();

manager.registerProvider("gemini", {
  apiKey: process.env.GEMINI_API_KEY
});

manager.registerProvider("openai", {
  apiKey: process.env.OPENAI_API_KEY
});

manager.registerProvider("anthropic", {
  apiKey: process.env.ANTHROPIC_API_KEY
});

// Configurar prioridad de fallback
manager.setProviderPriority([
  "gemini",      // Primero (más barato)
  "openai",      // Segundo (backup)
  "anthropic"    // Tercero (último recurso)
]);
```

### 3. **Unified Request Interface**

**Interfaz única para todos los proveedores:**

```typescript
interface LLMRequest {
  // Modelo a usar (opcional - puede ser seleccionado automáticamente)
  model?: string;

  // Contenido del prompt
  prompt: PlanData | string;

  // Configuración opcional
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;

  // Contexto para selección inteligente
  context?: {
    useCase?: string;
    priority?: "speed" | "quality" | "cost";
    requiresStreaming?: boolean;
    requiresVision?: boolean;
    maxCost?: number;
  };
}
```

**Response unificada:**

```typescript
interface LLMResponse {
  content: string;              // Contenido generado
  model: string;                // Modelo usado
  provider: string;             // Proveedor usado
  tokensUsed: {
    input: number;
    output: number;
    total: number;
  };
  cost: number;                 // Costo en USD
  executionTime: number;        // Tiempo en ms
  metrics: {
    averageGenerationSpeed: number;  // tokens/segundo
    firstTokenTime: number;          // tiempo al primer token
  };
  metadata?: {
    reasoning?: string;
    confidence?: number;
    sources?: any[];
  };
}
```

### 4. **Retry Logic with Exponential Backoff**

**Algoritmo de reintento:**

```typescript
async _generateWithRetry(providerId: string, request: LLMRequest): Promise<LLMResponse> {
  const provider = this.getProvider(providerId);
  const maxRetries = 3;
  const baseDelay = 2000;  // 2 segundos
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // Intentar generación
      return await provider.generateText(request);

    } catch (error) {
      lastError = error;

      // No reintentar en errores irrecuperables
      if (error instanceof AuthenticationError ||
          error instanceof InvalidRequestError ||
          error instanceof ModelNotFoundError) {
        throw error;  // Fallar inmediatamente
      }

      // Para rate limits, respetar retry-after
      if (error instanceof RateLimitError && error.retryAfter) {
        const delay = parseInt(error.retryAfter) * 1000;
        await sleep(delay);
        continue;
      }

      // Exponential backoff para otros errores
      if (attempt < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, attempt);
        // Intento 1: 2000ms
        // Intento 2: 4000ms
        // Intento 3: 8000ms
        await sleep(delay);
      }
    }
  }

  throw lastError;
}
```

**Matriz de decisiones de reintento:**

| Error Type | ¿Reintentar? | Razón |
|------------|--------------|---------|
| `AuthenticationError` | ❌ No | Credenciales inválidas no se corrigen solas |
| `InvalidRequestError` | ❌ No | Request mal formado no mejora al reintentar |
| `ModelNotFoundError` | ❌ No | Modelo inexistente no aparece mágicamente |
| `RateLimitError` | ✅ Sí | Con retry-after delay |
| `NetworkError` | ✅ Sí | Con backoff exponencial |
| `TimeoutError` | ✅ Sí | Con backoff exponencial |

### 5. **Fallback System**

**Cascada de proveedores:**

```typescript
async _generateWithFallback(request: LLMRequest, failedProviderId: string): Promise<LLMResponse> {
  // Probar cada proveedor en orden de prioridad
  for (const providerId of this.providerPriority) {
    // Saltar el que ya falló
    if (providerId === failedProviderId) continue;

    // Verificar que esté registrado
    if (!this.providers.has(providerId)) continue;

    try {
      // Intentar con este proveedor
      const result = await this._generateWithRetry(providerId, {
        ...request,
        provider: providerId  // Sobrescribir proveedor
      });

      // Éxito - loggear y retornar
      logger.info(`Fallback successful with provider: ${providerId}`);
      return result;

    } catch (error) {
      // Falló - probar siguiente
      logger.warn(`Fallback provider ${providerId} also failed`);
      continue;
    }
  }

  // Todos fallaron
  throw new Error("All providers failed");
}
```

**Ejemplo de cascada:**

```
Request → Gemini (primary)
         ↓ fails (RateLimit)
         ↓
         OpenAI (fallback 1)
         ↓ fails (Network Error)
         ↓
         Anthropic (fallback 2)
         ↓ success
         ↓
         Response (from Anthropic)
```

---

## 🎯 Intelligent Provider Selection

### Selección por Prioridad

```typescript
enum Priority {
  SPEED = "speed",        // Más rápido primero
  QUALITY = "quality",    // Mejor calidad primero
  COST = "cost"          // Más barato primero
}

function selectModelByPriority(priority: Priority, requirements: Capabilities): LLMModel {
  const candidates = allModels.filter(m => meetsCapabilities(m, requirements));

  switch (priority) {
    case Priority.SPEED:
      // Ordenar por velocidad (fast → medium → slow)
      const speedOrder = { fast: 1, medium: 2, slow: 3 };
      return candidates.sort((a, b) => speedOrder[a.speed] - speedOrder[b.speed])[0];

    case Priority.QUALITY:
      // Ordenar por calidad (heurística: contexto largo + reputación)
      return candidates.sort((a, b) => {
        const aScore = (a.capabilities.longContext ? 1 : 0) +
                       (a.provider === "anthropic" ? 0.5 : 0);
        const bScore = (b.capabilities.longContext ? 1 : 0) +
                       (b.provider === "anthropic" ? 0.5 : 0);
        return bScore - aScore;
      })[0];

    case Priority.COST:
      // Ordenar por costo (más barato primero)
      return candidates.sort((a, b) => a.costPerToken - b.costPerToken)[0];
  }
}
```

### Ejemplos de Selección

```
Caso 1: Respuesta rápida para chat
├── Priority: SPEED
├── Requirements: streaming=true
└── Selected: Gemini 2.5 Flash (fast, streaming)

Caso 2: Análisis complejo
├── Priority: QUALITY
├── Requirements: longContext=true
└── Selected: Claude 3.5 Sonnet (quality, 200K context)

Caso 3: Procesamiento masivo barato
├── Priority: COST
├── Requirements: textGeneration=true
└── Selected: Gemini Flash Lite ($0.0375/1M)

Caso 4: Con imágenes
├── Priority: QUALITY
├── Requirements: imageAnalysis=true
└── Selected: Gemini 2.5 Pro (vision, quality)
```

---

## 💡 Aplicación a Raycast

### Patrón para Ollama + Otros Proveedores

**Arquitectura híbrida:**

```typescript
// Interfaz unificada para Raycast
interface RaycastLLMProvider {
  name: string;
  generate(request: LLMRequest): Promise<LLMResponse>;
  generateStreaming(request: LLMRequest): AsyncGenerator<LLMStreamChunk>;
}

// Implementación Ollama
class OllamaProvider implements RaycastLLMProvider {
  name = "Ollama (Local)";

  async generate(request: LLMRequest): Promise<LLMResponse> {
    const response = await fetch("http://localhost:11434/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: request.model || "llama3.1",
        messages: [
          { role: "system", content: request.systemPrompt || "" },
          { role: "user", content: request.prompt }
        ],
        stream: false,
        temperature: request.temperature || 0.7
      })
    });

    const data = await response.json();

    return {
      content: data.message.content,
      model: request.model || "llama3.1",
      provider: "ollama",
      tokensUsed: {
        input: data.prompt_eval_count || 0,
        output: data.eval_count || 0,
        total: (data.prompt_eval_count || 0) + (data.eval_count || 0)
      },
      cost: 0,  // Gratis (local)
      executionTime: data.total_duration || 0,
      metrics: {
        averageGenerationSpeed: 0,  // Calcular si está disponible
        firstTokenTime: 0
      }
    };
  }

  async *generateStreaming(request: LLMRequest): AsyncGenerator<LLMStreamChunk> {
    const response = await fetch("http://localhost:11434/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: request.model || "llama3.1",
        messages: [
          { role: "system", content: request.systemPrompt || "" },
          { role: "user", content: request.prompt }
        ],
        stream: true
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n").filter(line => line.trim());

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.slice(6));
          if (data.done) {
            yield { content: "", isComplete: true, tokensGenerated: data.eval_count || 0 };
          } else {
            yield { content: data.message.content, isComplete: false, tokensGenerated: 0 };
          }
        }
      }
    }
  }
}

// Servicio unificado para Raycast
class RaycastLLMService {
  private providers = new Map<string, RaycastLLMProvider>();

  constructor() {
    // Registrar Ollama (local, gratis)
    this.providers.set("ollama", new OllamaProvider());

    // Registrar proveedores cloud (opcionales, requieren API key)
    if (process.env.OPENAI_API_KEY) {
      this.providers.set("openai", new OpenAIProvider());
    }
    if (process.env.ANTHROPIC_API_KEY) {
      this.providers.set("anthropic", new AnthropicProvider());
    }
  }

  async generate(request: LLMRequest): Promise<LLMResponse> {
    const providerId = request.provider || this.selectBestProvider(request);

    try {
      return await this.providers.get(providerId).generate(request);

    } catch (error) {
      // Si Ollama falla, intentar con cloud
      if (providerId === "ollama") {
        logger.warn("Ollama failed, trying cloud provider");

        for (const [id, provider] of this.providers) {
          if (id !== "ollama") {
            try {
              return await provider.generate({ ...request, provider: id });
            } catch (e) {
              continue;
            }
          }
        }
      }

      throw error;
    }
  }

  private selectBestProvider(request: LLMRequest): string {
    // Preferir Ollama si está disponible (gratis, local)
    if (this.providers.has("ollama")) {
      return "ollama";
    }

    // Si no, usar el más barato disponible
    // TODO: Implementar lógica de costo
    return this.providers.keys().next().value;
  }
}
```

### Estrategia de Fallback para Raycast

```
Usuario ejecuta comando de Raycast
        ↓
Intentar Ollama (local, gratis)
        ↓
¿Ollama disponible? ──No→ Usar OpenAI (cloud, paga)
        │Sí
        ↓
¿Ollama falla? ──Sí→ Fallback a Anthropic
        │No
        ↓
Respuesta exitosa
```

**Beneficios:**
- **Gratis por defecto:** Ollama es local y gratuito
- **Resiliencia:** Si Ollama falla, hay fallback
- **Flexibilidad:** Usuario puede agregar API keys para más opciones
- **Transparencia:** Sistema indica qué proveedor usó

---

## 🚀 Decisiones de Diseño

### Por qué Map en lugar de Array

```typescript
// MAL: Array para proveedores
const providers = [geminiProvider, openaiProvider, anthropicProvider];
const provider = providers.find(p => p.id === "gemini");

// BIEN: Map para lookup O(1)
const providers = new Map([
  ["gemini", geminiProvider],
  ["openai", openaiProvider],
  ["anthropic", anthropicProvider]
]);
const provider = providers.get("gemini");
```

**Ventajas del Map:**
- ✅ Lookup O(1) vs O(n)
- ✅ IDs como claves (más legible)
- ✅ Eliminación/adicción eficiente
- ✅ No requiere reindexar

### Por why Exponential Backoff

**Alternativa:** Retraso fijo entre reintentos

```typescript
// MAL: Siempre 2 segundos
for (let i = 0; i < 3; i++) {
  try { return await generate(); }
  catch { await sleep(2000); }
}

// BIEN: Backoff exponencial
// Intento 1: inmediato
// Intento 2: 2s después
// Intento 3: 4s después (2^1 * 2000)
// Intento 4: 8s después (2^2 * 2000)
```

**Por qué exponencial:**
- ✅ Da tiempo al servicio para recuperarse
- ✅ No sobrecarga con reintentos agresivos
- ✅ Pat estándar en sistemas distribuidos
- ✅ Balance entre velocidad y persistencia

### Por qué Categorización de Errores

```typescript
// Error types determinan comportamiento
class AuthenticationError extends Error { }
class RateLimitError extends Error { retryAfter?: string; }
class InvalidRequestError extends Error { }
class ModelNotFoundError extends Error { }

// Retry decision basado en tipo
if (error instanceof AuthenticationError) {
  throw error;  // No reintentar - credenciales inválidas
}
if (error instanceof RateLimitError) {
  await sleep(error.retryAfter * 1000);  // Respetar retry-after
  retry();
}
```

---

## 📈 Patrones a Adoptar (Conceptualmente)

### 1. **Interfaz Única**

```typescript
// Todos los proveedores implementan la misma interfaz
interface LLMProvider {
  generateText(request: LLMRequest): Promise<LLMResponse>;
  generateStreaming(request: LLMRequest): AsyncGenerator<LLMStreamChunk>;
  getModels(): Promise<LLMModel[]>;
  validateApiKey(): Promise<boolean>;
}

// Código cliente no necesita saber qué proveedor usa
const response = await llmService.generateText({
  prompt: "Hello, world!",
  provider: "cualquiera"  // O dejar que el sistema elija
});
```

### 2. **Registro Dinámico**

```typescript
// Proveedores se registran en runtime
llmService.registerProvider("gemini", geminiConfig);
llmService.registerProvider("ollama", ollamaConfig);

// No está hardcodeado
// Fácil agregar nuevos proveedores
```

### 3. **Selección Basada en Features**

```typescript
const model = llmService.selectModel({
  requiredCapabilities: ["streaming", "longContext"],
  maxCost: 0.002,
  priority: "speed"
});

// Sistema automáticamente selecciona el mejor modelo
```

### 4. **Fallback Transparente**

```typescript
// Cliente no maneja fallback
try {
  const response = await llmService.generate(request);
} catch (error) {
  // El servicio ya intentó todos los proveedores
  // Si llega aquí, todos fallaron
  showError("All AI providers are unavailable");
}

// Fallback es interno al servicio
```

---

## ⚠️ Patrones a Evitar

### 1. No Asumir Disponibilidad

```typescript
// MAL: Asumir que el proveedor siempre funciona
const result = await geminiProvider.generate(request);

// BIEN: Manejar falla con fallback
try {
  const result = await geminiProvider.generate(request);
} catch (error) {
  const result = await fallbackProvider.generate(request);
}
```

### 2. No Hardcodear Proveedores

```typescript
// MAL: Provider específico en código de negocio
if (provider === "gemini") {
  return await callGeminiAPI(request);
} else if (provider === "openai") {
  return await callOpenAIAPI(request);
}

// BIEN: Llamada polimórfica
const provider = providers.get(providerId);
return await provider.generate(request);
```

### 3. No Ignorar Costos

```typescript
// MAL: Usar el modelo más potente siempre
const model = "claude-3-opus";  // $0.015/1M tokens

// BIEN: Seleccionar por caso de uso
const model = selectBestModel({
  priority: userWantsSpeed ? "speed" : "quality",
  maxCost: userBudget
});
```

---

## 📈 Métricas de Éxito

### Para Medir Calidad del Servicio

- **Disponibilidad:** >99.5% uptime
- **Tiempo de respuesta:** P50 <500ms, P95 <2s
- **Tasa de éxito:** >95% (incluyendo fallbacks)
- **Costo optimizado:** Reducción >50% vs single provider

### Benchmarks Sugeridos

| Métrica | Bueno | Excelente |
|---------|-------|-----------|
| Proveedores soportados | 2+ | 4+ |
| Tiempo de fallback | <2s | <500ms |
| Tasa de éxito con fallback | 95% | 99%+ |
| Ahorro de costos | 30% | 50%+ |

---

## 🔍 Referencias del Código Fuente

### Archivos Principales

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `/services/llmService.ts` | Servicio unificado frontend | 97-300+ |
| `/backend/services/llm/LLMServiceManager.js` | Manager backend | 19-427 |
| `/backend/services/llm/providers/*` | Implementaciones específicas | - |

### Funciones Clave

- **Provider Registration:** `registerProvider()` - LLMServiceManager.js:34-75
- **Retry Logic:** `_generateWithRetry()` - LLMServiceManager.js:297-336
- **Fallback:** `_generateWithFallback()` - LLMServiceManager.js:342-380
- **Capability Matching:** `selectBestModel()` - llmService.ts (inferido)

---

**Próximos documentos:**
- `validation-pipeline-pattern.md` - Pipeline de validación multi-etapa
- `template-recommendation-strategy.md` - Recomendación por similitud

---

**Documentos completados:**
✅ `prompt-wizard-pattern.md` - Sistema wizard de 6 pasos
✅ `ab-testing-architecture.md` - Testing A/B completo
✅ `enhancement-engine-pattern.md` - Motor de mejora iterativa
✅ `quality-metrics-system.md` - Sistema cuantitativo de evaluación
✅ `multi-provider-llm-abstraction.md` - Capa de abstracción unificada
