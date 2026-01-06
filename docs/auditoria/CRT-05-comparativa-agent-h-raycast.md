# CRT-05: Comparativa de Implementaciones - Raycast vs Agent_H

**Fecha:** 2026-01-02
**Severidad:** 📊 Análisis Comparativo
**Estado:** ✅ Completado
**ID:** CRT-05 (Critical Technical Report)

---

## 1. Resumen Ejecutivo

Se investigó el código en `agent_h/eval` y `agent_h/hemdov/src` para entender cómo implementan la integración con DeepSeek y LiteLLM. El objetivo es aprender de la implementación existente para mejorar el sistema de Raycast.

**Hallazgo principal:** `agent_h` tiene una arquitectura más madura con:
- ✅ Sistema de evaluación robusto
- ✅ LiteLLM router con fallback chain
- ✅ Configuración centralizada en YAML
- ✅ Tests DSPy completos

---

## 2. Arquitectura en Agent_H

### 2.1 Estructura de Directorios

```
agent_h/
├── eval/                          # Sistema de evaluación
│   ├── adapters/                   # Adaptadores de routers
│   │   ├── router_adapter.py       # StubRouter, safe_call wrapper
│   │   └── router_entrypoint.py    # Carga de entrypoints dinámicos
│   ├── benchmarks/                 # Benchmarks de tool routing
│   ├── config/
│   │   └── eval_config.yaml        # Configuración centralizada
│   ├── lib/
│   │   └── router_eval_core.py     # Core de evaluación
│   └── tests/
│       ├── test_dspy_lm_config.py  # Tests DSPy LM
│       └── test_dspy_integration.py # Tests integración
│
└── hemdov/src/                    # Sistema principal HemDov
    └── hemdov/
        ├── infrastructure/
        │   └── adapters/
        │       ├── litellm_dspy_adapter.py      # DSPy ← LiteLLM
        │       ├── litellm_router.py             # Router con fallback
        │       ├── litellm_executor_adapter.py   # Executor adapter
        │       ├── deepseek_llm.py               # DeepSeek directo
        │       └── litellm_llm_client.py         # Cliente LiteLLM
        └── application/
            └── ports/
                └── llm_client.py                 # Puerto LLMClient
```

### 2.2 Archivos Clave Analizados

#### 2.2.1 DeepSeek LLM Client

**`hemdov/src/hemdov/infrastructure/adapters/deepseek_llm.py`**

```python
class DeepseekLLMClient(LLMClient):
    """LLM implementation using Deepseek API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        timeout: float = 120.0,
        silent: bool = False,
        **kwargs,
    ) -> str:
        """Generate text response using Deepseek API."""
        # Llamada HTTP directa a API de DeepSeek
        # Temperature: 0.0 (máxima consistencia)
        # Max tokens: 512
```

**Características:**
- ✅ Implementación directa HTTP con httpx
- ✅ Temperature 0.0 por defecto
- ✅ Max tokens 512 (ajustable)
- ✅ Timeout configurable (120s default)
- ✅ Sistema/system prompt soportado
- ✅ Manejo de errores robusto

#### 2.2.2 LiteLLM DSPy Adapter

**`hemdov/src/hemdov/infrastructure/adapters/litellm_dspy_adapter.py`**

```python
class LiteLLMDSPyAdapter(dspy.LM):
    """Adapter that makes LiteLLM router work as DSPy language model."""

    def __init__(self, router: LiteLLMRouter, timeout: float | None = None, **kwargs):
        super().__init__(model="litellm-router", **kwargs)
        self._router = router
        self._timeout = timeout if timeout is not None else Settings().llm_timeout
        self._history = []

    def __call__(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs
    ) -> list[str]:
        """DSPy calls this method for text generation."""
        # Soporta ambos estilos DSPy:
        # - DSPy 2.x: prompt string
        # - DSPy 3.x: messages list

        # Ejecuta via router con fallback chain
        response = self._router.execute(
            messages=messages,
            task_type=task_type,
            timeout=self._timeout,
            max_retries=1,  # FallbackChain retries
            num_retries=0,  # LiteLLM retries
            **kwargs
        )

        return [response['content']] * n
```

**Características:**
- ✅ Compatible con DSPy 2.x y 3.x
- ✅ Historial de llamadas para debugging
- ✅ Task type differentiation
- ✅ Configuración de timeouts robusta
- ✅ Retries configurables

#### 2.2.3 DSPy LM Configuration Tests

**`eval/tests/test_dspy_lm_config.py`**

```python
def test_deepseek_lm_config(self):
    """Test Deepseek (OpenAI-compatible) LM configuration."""
    import dspy

    lm = dspy.LM(
        model="openai/deepseek-chat",
        api_key="test-key-12345",
        api_base="https://api.deepseek.com/v1",
        temperature=0.0,
        max_tokens=1024
    )

    assert lm is not None

def test_configure_sets_default_lm(self):
    """Test dspy.configure() sets default LM."""
    import dspy

    lm = dspy.LM(model="openai/gpt-3.5-turbo", api_key="dummy")
    dspy.configure(lm=lm)

    assert dspy.settings.lm is not None
```

**Características:**
- ✅ Tests unitarios de configuración DSPy
- ✅ Tests de múltiples configuraciones
- ✅ Tests de integración con BaselineExecutor
- ✅ Runtime <5 segundos (rápido feedback)

#### 2.2.4 Evaluación Config

**`eval/config/eval_config.yaml`**

```yaml
providers:
  qwen_local:
    kind: "ollama"
    model: "qwen3-coder:30b"
    base_url: "http://localhost:11434"
    cost_per_million_in: 0.0
    cost_per_million_out: 0.0

  gemini_flash:
    kind: "gemini"
    model: "gemini-2.0-flash"
    api_key_env: "GEMINI_API_KEY"
    cost_per_million_in: 0.10
    cost_per_million_out: 0.40

run:
  temperature: 0.0
  max_tokens:
    guionista: 1200
    executor: 350
    router: 180

thresholds:
  executor:
    schema_strict_pass: 0.98
    no_preamble_pass: 1.00
    action_gate_passed: 0.95
```

**Características:**
- ✅ Configuración declarativa en YAML
- ✅ Múltiples providers con costos
- ✅ Umbrales de calidad configurables
- ✅ Temperature global 0.0
- ✅ Max tokens por componente

---

## 3. Comparativa: Raycast vs Agent_H

### 3.1 Implementación DeepSeek

| Aspecto | Raycast (raycast_ext) | Agent_H |
|---------|----------------------|----------|
| **Integración DeepSeek** | Via LiteLLM en hemdov | Via LiteLLM + HTTP directo |
| **Adaptador DSPy** | ✅ `litellm_dspy_adapter_prompt.py` | ✅ `litellm_dspy_adapter.py` |
| **Cliente HTTP propio** | ❌ No | ✅ `deepseek_llm.py` |
| **Tests DSPy** | ❌ No | ✅ `test_dspy_lm_config.py` |
| **Configuración YAML** | ❌ No (solo .env) | ✅ `eval_config.yaml` |
| **Temperature default** | 0.3 | 0.0 |
| **Max tokens** | 2000 | 512-1200 (por componente) |

### 3.2 Sistema de Evaluación

| Aspecto | Raycast | Agent_H |
|---------|---------|----------|
| **Evaluador propio** | ✅ `scripts/evaluator.ts` | ✅ Sistema completo en `eval/` |
| **Tests variabilidad** | ✅ `test-variability.ts` | ✅ Tests DSPy integration |
| **Configuración thresholds** | En código (`defaults.ts`) | En YAML (`eval_config.yaml`) |
| **Quality gates** | ✅ jsonValidPass1, copyableRate | ✅ schema_strict_pass, action_gate |
| **Reporting** | JSON output | JSON + análisis completo |

### 3.3 Configuración de Providers

| Aspecto | Raycast | Agent_H |
|---------|---------|----------|
| **Providers soportados** | ollama, gemini, deepseek, openai | ollama, gemini, deepseek, openai |
| **Configuración** | `.env` + `defaults.ts` | YAML + Settings class |
| **Fallback mechanism** | Simple (primary → fallback) | Complejo (FallbackChain) |
| **Cost tracking** | ❌ No | ✅ Sí (cost_per_million_in/out) |

---

## 4. Patrones y Mejores Prácticas Identificados

### 4.1 Patrones en Agent_H

#### 4.1.1 Adapter Pattern con Protocolos

```python
class RouterCallable(Protocol):
    def __call__(self, query: str) -> RouterPrediction: ...

class StubRouter:
    def __call__(self, query: str) -> RouterPrediction:
        # Implementación determinista para testing
```

**Ventajas:**
- ✅ Intercambiable (stub → production)
- ✅ Type safe con Protocol
- ✅ Fácil de mockear en tests

#### 4.1.2 Safe Call Wrapper

```python
def safe_call(router: RouterCallable, query: str) -> RouterPrediction:
    """Wrap router call to prevent eval crash on exceptions."""
    try:
        pred = router(query)
        tools = normalize_tools(pred.tools)
        errs = consistency_checks(tools)
        # ... procesamiento con tolerancia a fallos
    except Exception as e:
        return RouterPrediction(tools=[], conf=0.0, raw={"error": str(e)})
```

**Ventajas:**
- ✅ Eval nunca crash
- ✅Errores reportados en metadata
- ✅ Latency tracking inclusivo

#### 4.1.3 Configuración Declarativa YAML

```yaml
providers:
  deepseek_chat:
    kind: "deepseek"
    model: "deepseek-chat"
    api_key_env: "DEEPSEEK_API_KEY"
    cost_per_million_in: 0.14
    cost_per_million_out: 0.28
```

**Ventajas:**
- ✅ Fácil de modificar sin código
- ✅ Versionable en git
- ✅ Documentación inline
- ✅ Múltiples environments

### 4.2 Patrones en Raycast

#### 4.2.1 Type-Safe Config con Zod

```typescript
const DEFAULTS = {
  ollama: {
    model: "hf.co/...",
    temperature: 0.1,
    timeoutMs: 30_000,
  }
} as const;

type Defaults = typeof DEFAULTS;
```

**Ventajas:**
- ✅ Type safety completo
- ✅ Autocompletado en IDE
- ✅ Single source of truth

#### 4.2.2 Test de Variabilidad Empírico

```typescript
// Ejecuta mismo input 10 veces
const results = await Promise.all(
  Array(RUNS).fill(null).map(() =>
    improvePromptWithOllama({ rawInput: input })
  )
);

// Calcula similitud Jaccard
const similarity = jaccardSimilarity(results[0], results[1]);
```

**Ventajas:**
- ✅ Datos empíricos reales
- ✅ Cuantifica variabilidad
- ✅ Reproducible

---

## 5. Recomendaciones para Raycast

### 5.1 Prioridad Alta: Migrar a DeepSeek

**Acción inmediata:**
1. Usar adaptador existente en hemdov
2. Configurar temperature 0.0
3. Ejecutar test de variabilidad para validar

**Código de referencia:**
```python
# En raycast_ext/hemdov/infrastructure/config/__init__.py
class Settings(BaseSettings):
    LLM_PROVIDER: str = "deepseek"  # Cambiar de "ollama"
    LLM_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_KEY: Optional[str] = None
```

### 5.2 Prioridad Media: Agregar Tests DSPy

**Crear:** `dashboard/tests/dspystuff/deepseek_integration.test.ts`

```typescript
describe('DeepSeek Integration', () => {
  it('should configure DSPy with DeepSeek', async () => {
    const lm = create_deepseek_adapter(
      model="deepseek-chat",
      api_key=process.env.DEEPSEEK_API_KEY,
      temperature=0.0
    );

    const response = await lm("Test prompt");
    expect(response).toBeDefined();
    expect(response.length).toBeGreaterThan(0);
  });
});
```

### 5.3 Prioridad Media: Configuración YAML

**Crear:** `dashboard/config/eval_config.yaml`

```yaml
providers:
  deepseek_chat:
    kind: "deepseek"
    model: "deepseek-chat"
    api_key_env: "DEEPSEEK_API_KEY"
    temperature: 0.0
    max_tokens: 2000

quality_gates:
  json_valid_pass1: 0.90
  copyable_rate: 0.90
  latency_p95_max: 5000
```

### 5.4 Prioridad Baja: Safe Call Wrapper

**Agregar a:** `dashboard/src/core/llm/improvePrompt.ts`

```typescript
export async function safeImprovePrompt(
  input: string,
  options: ImproveOptions
): Promise<ImproveResult | { error: string }> {
  try {
    return await improvePromptWithOllama(input, options);
  } catch (e) {
    return {
      error: `${e.name}: ${e.message}`,
      improvedPrompt: "",
      metadata: { latencyMs: 0, attempt: 1 }
    };
  }
}
```

---

## 6. Lecciones Aprendidas

### 6.1 Arquitectura

1. **Separación de concerns:** Agent_H separa evaluación (`eval/`) del sistema principal (`hemdov/`)
2. **Adapters over hardcoding:** Todo es intercambiable vía adapters
3. **Configuración externa:** YAML > hardcoded constants

### 6.2 Testing

1. **Tests rápidos:** Agent_H tests corren en <5 segundos
2. **Stubs para testing:** `StubRouter` permite testing sin API calls
3. **Tests de integración:** Validan DSPy + LLM juntos

### 6.3 DeepSeek Specifics

1. **Temperature 0.0:** Agent_H usa 0.0 para máxima consistencia
2. **Max tokens bajo:** 512-1200 vs 2000 en Raycast (más rápido)
3. **HTTP directo:** `deepseek_llm.py` como alternativa a LiteLLM

### 6.4 Evaluación

1. **Umbrales explícitos:** Todo está cuantificado en YAML
2. **Cost tracking:** Seguimiento de costos por provider
3. **Quality gates:** Específicos por componente (router, executor, etc.)

---

## 7. Plan de Acción

### 7.1 Inmediato (Hoy)

1. ✅ Revisar código agent_h (completado)
2. ⏳ Configurar DeepSeek en raycast_ext
3. ⏳ Ejecutar test de variabilidad con DeepSeek

### 7.2 Corto Plazo (Esta semana)

4. ⏳ Migrar tests DSPy de agent_h a raycast
5. ⏳ Implementar safe_call wrapper
6. ⏳ Crear config YAML para thresholds

### 7.3 Medio Plazo (Este mes)

7. ⏳ Unificar sistemas de evaluación
8. ⏳ Implementar cost tracking
9. ⏳ Agregar más providers (Claude, etc.)

---

## 8. Conclusión

**Agent_H tiene una implementación más madura y robusta** que puede servir de referencia para mejorar Raycast:

**Fortalezas de Agent_H:**
- ✅ Arquitectura limpia con separación de concerns
- ✅ Testing completo y rápido
- ✅ Configuración flexible en YAML
- ✅ Integración DeepSeek probada
- ✅ Safe wrappers para tolerancia a fallos

**Fortalezas de Raycast:**
- ✅ Test de variabilidad empírico (único)
- ✅ Type safety con Zod/TypeScript
- ✅ Single source of truth (defaults.ts)

**Recomendación:** Combinar lo mejor de ambos mundos:
- Mantener type safety de Raycast
- Adoptar testing de Agent_H
- Implementar safe wrappers
- Migrar a DeepSeek con temperature 0.0

---

**Analizado por:** Comparación de código agent_h vs raycast_ext
**Fecha:** 2026-01-02
**Próximo paso:** Implementar migración a DeepSeek en raycast_ext
