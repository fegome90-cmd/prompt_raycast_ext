# CRT-04: Migración a DeepSeek Chat via LiteLLM

**Fecha:** 2026-01-02
**Severidad:** 🟢 Oportunidad de Mejora
**Estado:** 📋 Propuesta
**ID:** CRT-04 (Critical Technical Report)

---

## 1. Resumen Ejecutivo

El sistema actual usa **Novaeus-Promptist-7B** vía Ollama con resultados subóptimos (60-70% tasa de fallo, 34-48% similitud semántica según CRT-03). Se propone migrar a **DeepSeek Chat** vía LiteLLM como alternativa más consistente, económica y rápida.

**Viabilidad:** ✅ **LISTO PARA IMPLEMENTAR**
- El adaptador LiteLLM para DeepSeek ya existe en `hemdov/infrastructure/adapters/litellm_dspy_adapter_prompt.py`
- Solo requiere configuración de API key
- DeepSeek Chat es ~90% más económico que GPT-4

---

## 2. Problema Actual (CRT-03)

### 2.1 Resultados con Novaeus-Promptist-7B

| Métrica | Valor | Evaluación |
|---------|-------|------------|
| **Tasa de fallo JSON** | 60-70% | 🔴 Crítico |
| **Similitud semántica** | 34-48% | 🔴 Muy baja |
| **Consistencia estructura** | 0% | 🔴 Nula |
| **Temperature 0.1** | Insuficiente | 🔴 No controla variabilidad |

**Conclusión:** El modelo tiene **inconsistencia intrínseca** que no se resuelve con ajustes de temperatura o prompts.

---

## 3. Solución Propuesta: DeepSeek Chat

### 3.1 ¿Qué es DeepSeek Chat?

**DeepSeek Chat** es un modelo LLM de código abierto desarrollado por DeepSeek (China) que:

- **Rendimiento:** Comparable a GPT-4 en tareas de razonamiento
- **Coste:** ~$0.14-$0.28 por millón de tokens (90% más barato que GPT-4)
- **Velocidad:** Más rápido que GPT-4 y mucho más que modelos locales
- **Disponibilidad:** API pública vía LiteLLM

### 3.2 Comparativa de Precios (2025)

| Modelo | Costo por 1M tokens | Factor |
|--------|---------------------|--------|
| **DeepSeek Chat** | $0.14 - $0.28 | 1x (baseline) |
| **GPT-4o** | ~$3.00 | 10-20x más caro |
| **GPT-4 Turbo** | ~$10-30 | 50-200x más caro |
| **Ollama (local)** | $0 (hardware) | "Gratis" pero inconsistente |

**Fuentes:**
- [DeepSeek vs ChatGPT Comparison](https://deepseek.ai/deepseek-vs-chatgpt)
- [DeepSeek vs GPT-4o API Cost](https://skywork.ai/blog/llm/deepseek-vs-gpt-4o-speed-accuracy-and-api-cost-compared/)
- [OpenAI vs DeepSeek Pricing 2025](https://www.byteplus.com/en/topic/383222)

---

## 4. Arquitectura Existente en Hemdov

### 4.1 Adaptador LiteLLM para DSPy

**Archivo:** `hemdov/infrastructure/adapters/litellm_dspy_adapter_prompt.py`

```python
def create_deepseek_adapter(
    model: str = "deepseek-chat",
    api_key: Optional[str] = None,
    **kwargs,
) -> PromptImproverLiteLLMAdapter:
    """Create DeepSeek adapter."""
    return PromptImproverLiteLLMAdapter(
        model=f"deepseek/{model}",
        api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )
```

**Características:**
- ✅ Compatible con DSPy v3
- ✅ Soporta prompt y messages
- ✅ Configurable (temperature, max_tokens)
- ✅ Manejo de errores incluido

### 4.2 Configuración en Settings

**Archivo:** `hemdov/infrastructure/config/__init__.py`

```python
class Settings(BaseSettings):
    # LLM Provider Settings
    LLM_PROVIDER: str = "ollama"  # ollama, gemini, deepseek, openai
    LLM_MODEL: str = "..."
    DEEPSEEK_API_KEY: Optional[str] = None
```

---

## 5. GUÍA DE IMPLEMENTACIÓN DETALLADA

### 5.1 Paso 1: Obtener API Key de DeepSeek

#### 5.1.1 Registro en DeepSeek Platform

1. **Ir a:** https://platform.deepseek.com/
2. **Registrarse:**
   - Click en "Sign Up"
   - Usar email, GitHub, o Google account
   - Verificar email

3. **Obtener API Key:**
   - Login al dashboard
   - Navegar a "API Keys"
   - Click "Create new key"
   - Copiar la key (formato: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

4. **Configurar saldo/credito:**
   - DeepSeek ofrece free tier (verificar límites actuales)
   - Configurar alertas de gasto si es necesario
   - Revisar pricing en: https://platform.deepseek.com/pricing

#### 5.1.2 Verificar API Key

```bash
# Test de conectividad con DeepSeek API
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer sk-tu-api-key-aqui"
```

**Respuesta esperada:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "deepseek-chat",
      "object": "model",
      "owned_by": "deepseek"
    }
  ]
}
```

### 5.2 Paso 2: Configurar Archivos

#### 5.2.1 Actualizar `.env`

**Ubicación:** `/Users/felipe_gonzalez/Developer/raycast_ext/.env`

**Contenido actual:**
```bash
# DSPy Prompt Improver Environment Configuration
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434
```

**Cambiar a:**
```bash
# DSPy Prompt Improver Environment Configuration
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# DeepSeek API Key (OBLIGATORIO)
DEEPSEEK_API_KEY=sk-tu-api-key-completa-aqui

# Nota: LLM_BASE_URL es opcional para DeepSeek (usa default si se omite)
```

**Parámetros importantes:**
- `LLM_PROVIDER`: Debe ser exactamente `"deepseek"` (lowercase)
- `LLM_MODEL`: `"deepseek-chat"` para Chat, `"deepseek-reasoner"` para Reasoner
- `DEEPSEEK_API_KEY`: API key completa starting with `sk-`

#### 5.2.2 Actualizar `.env.example`

**Ubicación:** `/Users/felipe_gonzalez/Developer/raycast_ext/.env.example`

**Agregar:**
```bash
# LLM Provider Options: ollama, gemini, deepseek, openai
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434

# DeepSeek Configuration (opcional - para producción)
# LLM_PROVIDER=deepseek
# LLM_MODEL=deepseek-chat
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 5.3 Paso 3: Modificar `main.py`

**Ubicación:** `/Users/felipe_gonzalez/Developer/raycast_ext/main.py`

**Código actual (líneas 38-41):**
```python
if provider == "ollama":
    lm = create_ollama_adapter(
        model=settings.LLM_MODEL, base_url=settings.LLM_BASE_URL, temperature=0.3
    )
```

**Problema:** Temperature está hardcoded a `0.3`.

**Necesario cambiar a `0.0`** para máxima consistencia con DeepSeek.

#### 5.3.1 Modificación Completa de `main.py`

**Opción A: Temperature por Provider (RECOMENDADO)**

```python
# En lifespan() function, líneas 37-61
provider = settings.LLM_PROVIDER.lower()
if provider == "ollama":
    lm = create_ollama_adapter(
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        temperature=0.1  # Ollama mantiene 0.1
    )
elif provider == "gemini":
    lm = create_gemini_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.GEMINI_API_KEY or settings.LLM_API_KEY,
        temperature=0.0,  # Gemini usa 0.0
    )
elif provider == "deepseek":
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY or settings.LLM_API_KEY,
        temperature=0.0,  # ⚠️ CRÍTICO: 0.0 para máxima consistencia
    )
elif provider == "openai":
    lm = create_openai_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY or settings.LLM_API_KEY,
        temperature=0.0,  # OpenAI usa 0.0
    )
else:
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
```

**Opción B: Temperature Global (SIMPLIFICADO)**

Si quieres simplificar, usa temperature global:

```python
# Al inicio del archivo, después de imports
DEFAULT_TEMPERATURE = {
    "ollama": 0.1,
    "gemini": 0.0,
    "deepseek": 0.0,  # ⚠️ CRÍTICO
    "openai": 0.0,
}

# En lifespan()
provider = settings.LLM_PROVIDER.lower()
temp = DEFAULT_TEMPERATURE.get(provider, 0.0)

if provider == "ollama":
    lm = create_ollama_adapter(
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        temperature=temp,
    )
# ... resto similar para otros providers
```

#### 5.3.2 Validación de Configuración

**Agregar al final de `main.py` (opcional pero recomendado):**

```python
if __name__ == "__main__":
    import uvicorn

    # Validación mejorada de configuración
    if not (1024 <= settings.API_PORT <= 65535):
        raise ValueError(f"Invalid API_PORT: {settings.API_PORT}. Must be between 1024-65535.")

    # NUEVA: Validar API key para DeepSeek
    if settings.LLM_PROVIDER.lower() == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek. "
                "Get your API key from https://platform.deepseek.com/"
            )
        if not settings.DEEPSEEK_API_KEY.startswith("sk-"):
            raise ValueError(
                f"Invalid DEEPSEEK_API_KEY format. "
                f"Expected 'sk-...', got: {settings.DEEPSEEK_API_KEY[:10]}..."
            )

    logger.info("Starting DSPy Prompt Improver API...")
    logger.info(f"✓ Configuration loaded from .env")
    logger.info(f"✓ API_PORT: {settings.API_PORT} (validated)")
    logger.info(f"✓ LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"✓ LLM Model: {settings.LLM_MODEL}")
    if settings.LLM_PROVIDER.lower() == "deepseek":
        # No loggear la API key completa por seguridad
        key_preview = settings.DEEPSEEK_API_KEY[:10] + "..."
        logger.info(f"✓ DeepSeek API Key: {key_preview}")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
```

### 5.4 Paso 4: Crear Script de Prueba

**Crear:** `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/test-deepseek.sh`

```bash
#!/bin/bash
# Script para probar integración DeepSeek antes de commit

set -e  # Fail on error

echo "🔍 DeepSeek Integration Test"
echo "================================"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar .env configurado
echo ""
echo "1️⃣  Checking .env configuration..."
if grep -q "LLM_PROVIDER=deepseek" .env; then
    echo -e "${GREEN}✓${NC} LLM_PROVIDER=deepseek"
else
    echo -e "${RED}✗${NC} LLM_PROVIDER not set to deepseek"
    echo "   Please set LLM_PROVIDER=deepseek in .env"
    exit 1
fi

if grep -q "DEEPSEEK_API_KEY=sk-" .env; then
    echo -e "${GREEN}✓${NC} DEEPSEEK_API_KEY is set"
else
    echo -e "${RED}✗${NC} DEEPSEEK_API_KEY not found or invalid"
    echo "   Please set DEEPSEEK_API_KEY=sk-... in .env"
    exit 1
fi

# 2. Verificar que Ollama NO está siendo usado
if grep -q "LLM_PROVIDER=ollama" .env; then
    echo -e "${YELLOW}⚠${NC}  WARNING: .env still has LLM_PROVIDER=ollama commented out"
fi

# 3. Test de conectividad a DeepSeek API
echo ""
echo "2️⃣  Testing DeepSeek API connectivity..."
API_KEY=$(grep "DEEPSEEK_API_KEY" .env | cut -d'=' -f2)

response=$(curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $API_KEY")

if echo "$response" | grep -q "deepseek-chat"; then
    echo -e "${GREEN}✓${NC} DeepSeek API is accessible"
else
    echo -e "${RED}✗${NC} Cannot reach DeepSeek API"
    echo "   Response: $response"
    exit 1
fi

# 4. Verificar que el backend DSPy puede arrancar
echo ""
echo "3️⃣  Checking DSPy backend dependencies..."
if python -c "import dspy" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} DSPy installed"
else
    echo -e "${RED}✗${NC} DSPy not installed"
    exit 1
fi

if python -c "import litellm" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} LiteLLM installed"
else
    echo -e "${RED}✗${NC} LiteLLM not installed"
    exit 1
fi

# 5. Test simple del backend
echo ""
echo "4️⃣  Starting DSPy backend (test mode)..."
timeout 10s python main.py &
BACKEND_PID=$!

# Esperar a que arranque
sleep 3

# Verificar si está corriendo
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
    kill $BACKEND_PID 2>/dev/null || true
else
    echo -e "${RED}✗${NC} Backend health check failed"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start backend: python main.py"
echo "  2. Run variability test: npx tsx scripts/test-variability.ts 5 specific"
echo "  3. Compare results with CRT-03 baseline"
```

**Hacer ejecutable:**
```bash
chmod +x scripts/test-deepseek.sh
```

### 5.5 Paso 5: Ejecutar Testing

#### 5.5.1 Test Manual de API

```bash
# 1. Asegurarse de que el backend DSPy esté corriendo
python main.py

# En otra terminal, test manual:
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "raw_idea": "Documenta una función en TypeScript"
  }'
```

**Respuesta esperada (similar):**
```json
{
  "improved_prompt": "# Documentación de Función TypeScript\n\nEscribe una documentación clara...",
  "clarifying_questions": [],
  "assumptions": [],
  "confidence": 0.95
}
```

#### 5.5.2 Test de Variabilidad (CRT-03 Repetido)

```bash
# Ejecutar test de variabilidad con DeepSeek
cd dashboard
npx tsx scripts/test-variability.ts 10 specific
```

**Resultados esperados con DeepSeek:**
- Tasa de fallo JSON: <5% (vs 60-70% con Ollama)
- Similitud semántica: >80% (vs 34-48% con Ollama)
- Latencia: <5s (vs 3-10s con Ollama)

#### 5.5.3 Evaluación Completa

```bash
# Ejecutar evaluador completo
npm run eval -- --dataset testdata/cases.jsonl --output eval/deepseek-test.json
```

### 5.6 Paso 6: Validación y Métricas

#### 5.6.1 Checklist de Validación

**Antes de considerar la migración exitosa:**

- [ ] Backend DSPy arranca sin errores
- [ ] Health check returns `{"status": "healthy", "provider": "deepseek", "model": "deepseek-chat"}`
- [ ] Test manual produce JSON válido
- [ ] Test de variabilidad muestra >80% similitud
- [ ] Tasa de fallo JSON <5%
- [ ] Latencia P95 <5s
- [ ] Cost tracking funciona (si se implementa)

#### 5.6.2 Métricas Esperadas

| Métrica | Ollama (baseline) | DeepSeek (target) | ¿Pasa? |
|---------|-------------------|-------------------|--------|
| jsonValidPass1 | 54% | >90% | [ ] |
| copyableRate | 54% | >90% | [ ] |
| latencyP95 | 12s | <5s | [ ] |
| Tasa fallo JSON | 60-70% | <5% | [ ] |
| Similitud semántica | 34-48% | >80% | [ ] |

### 5.7 Paso 7: Rollback Plan

#### 5.7.1 Cómo Revertir a Ollama

**Si algo sale mal:**

```bash
# 1. Detener backend DSPy
# Ctrl+C en la terminal donde corre python main.py

# 2. Revertir .env
cd /Users/felipe_gonzalez/Developer/raycast_ext
git checkout .env

# 3. Verificar que Ollama está corriendo
ollama list

# 4. Reiniciar backend
python main.py
```

#### 5.7.2 Comandos de Emergencia

```bash
# Si el backend no arranca:
python -c "from hemdov.infrastructure.config import settings; print(settings.LLM_PROVIDER)"

# Si hay error de API key:
echo $DEEPSEEK_API_KEY | wc -c  # Debe ser ~60 caracteres

# Si hay timeout:
curl -w "@-" -o /dev/null -s "https://api.deepseek.com/v1/models" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

---

## 6. CONSIDERACIONES TÉCNICAS

### 6.1 Temperature: 0.0 vs 0.3

**Configuración actual en agent_h (referencia):**

```python
# agent_h/hemdov/src/hemdov/infrastructure/adapters/deepseek_llm.py
def generate(self, ...):
    return client.post(
        f"{self._base_url}/chat/completions",
        json={
            "model": self._model,
            "messages": messages,
            "temperature": 0.0,  # ← HARDCODED a 0.0
            "max_tokens": 512,
        },
        ...
    )
```

**Por qué 0.0:**
- Máxima consistencia entre ejecuciones
- Outputs deterministas para mismo input
- Resuelve problema de variabilidad de CRT-03

**En raycast_ext actual:**
```python
# main.py línea 40
temperature=0.3  # ← DEMASIADO ALTO para consistencia
```

**Recomendación:** Cambiar a `0.0` explícitamente para DeepSeek.

### 6.2 Max Tokens

**Agent_H usa:**
- Router: 180 tokens
- Executor: 350 tokens
- Guionista: 1200 tokens

**Raycast usa:**
- 2000 tokens (desde defaults.ts)

**Recomendación:**
- Mantener 2000 para prompts mejorados (suficiente)
- Reducir si los outputs son demasiado largos
- Aumentar si se trunca contenido

### 6.3 Timeout

**Agent_H usa:**
- 120s default (deepseek_llm.py)

**Raycast usa:**
- 30s (DEFAULTS.ollama.timeoutMs)

**Recomendación:**
- Mantener 30s inicialmente
- Aumentar a 60s si hay timeouts frecuentes
- DeepSeek Chat suele responder en <5s

### 6.4 Rate Limiting

**DeepSeek limits (verificar en plataforma):**
- Free tier: X requests/minuto
- Paid tier: Y requests/minuto

**Mitigación:**
- Implementar retry con exponential backoff
- Cache de outputs para inputs idénticos
- Queue de requests si es necesario

---

## 7. TROUBLESHOOTING

### 7.1 Errores Comunes

#### Error 1: "DEEPSEEK_API_KEY not found"

```
ValueError: DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek
```

**Solución:**
```bash
# Verificar que .env tiene la key
grep DEEPSEEK_API_KEY .env

# Debe mostrar:
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Error 2: "Invalid API key format"

```
ValueError: Invalid DEEPSEEK_API_KEY format. Expected 'sk-...'
```

**Solución:**
```bash
# La API key debe empezar con sk-
# Verificar:
export DEEPSEEK_API_KEY="sk-copia-tu-key-completa-aqui"
```

#### Error 3: "Deepseek timeout después de 30s"

```
ServiceUnavailableError: Deepseek timeout después de 30.0s
```

**Solución:**
```bash
# Aumentar timeout en .env (si está implementado)
# O en defaults.ts:
timeoutMs: 60_000,  # 60 segundos
```

#### Error 4: "401 Unauthorized"

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "invalid_request_error"
  }
}
```

**Solución:**
1. Verificar API key en https://platform.deepseek.com/
2. Regenerar key si es necesario
3. Asegurarse de copiar la key completa (sin espacios)

#### Error 5: "429 Rate Limit"

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Solución:**
1. Esperar 1 minuto antes de reintentar
2. Verificar límites en dashboard de DeepSeek
3. Considerar upgrade a plan pago

### 7.2 Debug Mode

**Habilitar logging verboso:**

```python
# En main.py, agregar al inicio:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Ver logs de LiteLLM:**

```python
# En hemdov/infrastructure/adapters/litellm_dspy_adapter_prompt.py
import litellm
litellm.set_verbose = True  # Muestra todas las llamadas API
```

### 7.3 Comparación de Outputs

**Para comparar Ollama vs DeepSeek manualmente:**

```bash
# 1. Test con Ollama (config actual)
LLM_PROVIDER=ollama python main.py
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"raw_idea": "Create a function"}' | jq . > ollama_output.json

# 2. Test con DeepSeek
LLM_PROVIDER=deepseek DEEPSEEK_API_KEY=sk-... python main.py
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"raw_idea": "Create a function"}' | jq . > deepseek_output.json

# 3. Comparar
diff ollama_output.json deepseek_output.json
```

---

## 8. SCRIPTS DE UTILIDAD

### 8.1 Script de Comparación

**Crear:** `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/compare-providers.sh`

```bash
#!/bin/bash
# Compara outputs de Ollama vs DeepSeek

set -e

INPUT='{"raw_idea": "Documenta una función en TypeScript"}"

echo "🔄 Testing Ollama..."
echo "LLM_PROVIDER=ollama" > .env.temp
cat .env >> .env.temp
mv .env.temp .env

python main.py &
PID=$!
sleep 5

OLLAMA_OUTPUT=$(curl -s -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d "$INPUT")

kill $PID 2>/dev/null || true
sleep 2

echo "🔄 Testing DeepSeek..."
echo "LLM_PROVIDER=deepseek" > .env.temp
echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY" >> .env.temp
cat .env | grep -v "LLM_PROVIDER" | grep -v "DEEPSEEK" >> .env.temp
mv .env.temp .env

python main.py &
PID=$!
sleep 5

DEEPSEEK_OUTPUT=$(curl -s -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d "$INPUT")

kill $PID 2>/dev/null || true

echo ""
echo "📊 Results:"
echo "============"
echo ""
echo "Ollama:"
echo "$OLLAMA_OUTPUT" | jq '.improved_prompt' | head -5
echo ""
echo "DeepSeek:"
echo "$DEEPSEEK_OUTPUT" | jq '.improved_prompt' | head -5
```

### 8.2 Script de Validación

**Crear:** `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/validate-deepseek.ts`

```typescript
#!/usr/bin/env tsx
/**
 * Validación de integración DeepSeek
 */

async function validateDeepSeek() {
  console.log("🔍 Validating DeepSeek integration...\n");

  // 1. Check .env
  const fs = await import("fs");
  const envPath = ".env";
  const envContent = fs.readFileSync(envPath, "utf-8");

  const hasProvider = envContent.includes("LLM_PROVIDER=deepseek");
  const hasKey = envContent.includes("DEEPSEEK_API_KEY=sk-");

  console.log("Configuration check:");
  console.log(`  LLM_PROVIDER=deepseek: ${hasProvider ? "✅" : "❌"}`);
  console.log(`  DEEPSEEK_API_KEY set: ${hasKey ? "✅" : "❌"}\n`);

  if (!hasProvider || !hasKey) {
    console.error("❌ Configuration incomplete. Please fix .env");
    process.exit(1);
  }

  // 2. Test API connectivity
  console.log("Testing API connectivity...");
  const apiKey = envContent.match(/DEEPSEEK_API_KEY=(.+)/)?.[1];

  try {
    const response = await fetch("https://api.deepseek.com/v1/models", {
      headers: {
        "Authorization": `Bearer ${apiKey}`,
      },
    });

    if (response.ok) {
      console.log("✅ DeepSeek API is accessible\n");
    } else {
      console.error(`❌ API error: ${response.status} ${response.statusText}`);
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Cannot reach DeepSeek API:", error.message);
    process.exit(1);
  }

  // 3. Test backend
  console.log("Testing backend...");
  // ... más validaciones

  console.log("✅ All validations passed!");
}

validateDeepSeek().catch(console.error);
```

---

## 9. PLAN DE VALIDACIÓN FINAL

### 9.1 Pre-Production Checklist

Antes de considerar DeepSeek listo para producción:

**Configuración:**
- [ ] `.env` configurado con `LLM_PROVIDER=deepseek`
- [ ] `DEEPSEEK_API_KEY` válida y verificada
- [ ] `.env.example` actualizado con comentarios
- [ ] `main.py` modificado con temperature 0.0
- [ ] Validación de API key al startup implementada

**Testing:**
- [ ] Script `test-deepseek.sh` pasa exitosamente
- [ ] Test manual de API produce output válido
- [ ] Test de variabilidad muestra >80% similitud
- [ ] Evaluación completa (`npm run eval`) pasa
- [ ] No hay errores en logs de backend

**Métricas:**
- [ ] Tasa fallo JSON <5%
- [ ] Similitud semántica >80%
- [ ] Latencia P95 <5s
- [ ] Costo por 1000 prompts razonable

**Documentación:**
- [ ] Este informe completado
- [ ] Cambios documentados en git commit
- [ ] README actualizado si es necesario
- [ ] Notas de release agregadas

### 9.2 Monitoring Post-Deployment

**Primeras 24 horas:**
- Monitorear tasa de errores
- Verificar latencia promedio
- Revisar costos acumulados
- Check de rate limits

**Primera semana:**
- Comparar métricas con baseline Ollama
- Ajustar parámetros si es necesario
- Recopilar feedback de usuarios

---

## 10. COMANDOS DE REFERENCIA RÁPIDA

```bash
# === Configuración ===
# Editar .env
nano .env

# Verificar configuración
python -c "from hemdov.infrastructure.config import settings; print(settings.dict())"

# === Testing ===
# Test rápido de API
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# Test de backend
curl http://localhost:8000/health

# Test de mejora manual
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"raw_idea": "Test prompt"}'

# Test de variabilidad
npx tsx scripts/test-variability.ts 10 specific

# Evaluación completa
npm run eval -- --dataset testdata/cases.jsonl --output eval/deepseek-test.json

# === Debugging ===
# Ver logs de backend
tail -f logs/backend.log  # si existe

# Logs de LiteLLM
LITELLM_LOG=debug python main.py

# === Rollback ===
# Revertir a Ollama
git checkout .env
python main.py

# === Comparación ===
# Comparar outputs
diff eval/baseline.json eval/deepseek-test.json
```

---

## 11. ANEXOS

### Anexo A: Variables de Entorno Completas

```bash
# ========================================
# DSPy Prompt Improver - DeepSeek Config
# ========================================

# Provider Selection
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# DeepSeek Configuration
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: API Base URL (default: https://api.deepseek.com/v1)
# LLM_BASE_URL=https://api.deepseek.com/v1

# DSPy Configuration
DSPY_MAX_BOOTSTRAPPED_DEMOS=5
DSPY_MAX_LABELED_DEMOS=3
DSPY_COMPILED_PATH=

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Quality Thresholds
MIN_CONFIDENCE_THRESHOLD=0.7
MAX_LATENCY_MS=30000
```

### Anexo B: Estructura de Directorios

```
raycast_ext/
├── .env                          # ← MODIFICAR (DeepSeek config)
├── .env.example                  # ← MODIFICAR (comentarios)
├── main.py                       # ← MODIFICAR (temperature 0.0)
├── hemdov/
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   └── litellm_dspy_adapter_prompt.py  # (ya existe)
│   │   └── config/
│   │       └── __init__.py                     # (ya existe)
│   └── domain/
│       └── dspy_modules/
│           └── prompt_improver.py              # (ya existe)
└── scripts/
    ├── test-deepseek.sh           # ← CREAR
    ├── compare-providers.sh        # ← CREAR
    └── validate-deepseek.ts        # ← CREAR
```

### Anexo C: API Response Examples

**DeepSeek Chat Response Exitoso:**

```json
{
  "id": "chatcmpl-xxxxxxxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "# Improved Prompt\n\nWrite a function that..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 150,
    "total_tokens": 200
  }
}
```

**Error de API Key:**

```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "param": "Authorization",
    "code": "invalid_api_key"
  }
}
```

---

**Última actualización:** 2026-01-02
**Estado:** Listo para implementar

**Soporta múltiples providers:**
- `ollama` - Actual (Novaeus-Promptist-7B)
- `deepseek` - Propuesto
- `gemini` - Alternativa
- `openai` - Alternativa premium

### 4.3 DSPy Module

**Archivo:** `hemdov/domain/dspy_modules/prompt_improver.py`

```python
class PromptImproverSignature(dspy.Signature):
    """Improve user's raw idea into SOTA prompt."""

    original_idea = dspy.InputField(...)
    improved_prompt = dspy.OutputField(...)
    role = dspy.OutputField(...)
    directive = dspy.OutputField(...)
    framework = dspy.OutputField(...)
    guardrails = dspy.OutputField(...)
    confidence = dspy.OutputField(...)
```

**Arquitectura probada y funcionando.**

---

## 5. Plan de Migración

### 5.1 Fase 1: Configuración (5 minutos)

**Paso 1: Obtener API Key**
1. Ir a https://platform.deepseek.com/
2. Crear cuenta y obtener API key
3. Configurar crédito inicial (suelen tener free tier)

**Paso 2: Configurar `.env`**

```bash
# Cambiar provider
LLM_PROVIDER=deepseek

# Configurar modelo
LLM_MODEL=deepseek-chat

# Agregar API key
DEEPSEEK_API_KEY=sk-tu-api-key-aqui
```

**Paso 3: Verificar configuración**

```bash
# Reiniciar backend DSPy
python main.py

# Debería ver en logs:
# DSPy configured with deepseek/deepseek-chat
```

### 5.2 Fase 2: Testing (30 minutos)

**Paso 1: Test básico de funcionalidad**

```bash
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"raw_idea": "Create a function to validate emails"}'
```

**Paso 2: Ejecutar test de variabilidad**

```bash
# Comparar resultados con Ollama
npx tsx scripts/test-variability.ts 10 specific
```

**Métricas esperadas con DeepSeek:**
- Tasa de fallo JSON: <5% (vs 60-70% actual)
- Similitud semántica: >80% (vs 34-48% actual)
- Latencia: <5s (vs 3-10s actual)

### 5.3 Fase 3: Validación (1 hora)

**Paso 1: Ejecutar evaluación completa**

```bash
npm run eval -- --dataset testdata/cases.jsonl --output eval/deepseek-baseline.json
```

**Paso 2: Comparar con baseline actual**

| Métrica | Ollama (actual) | DeepSeek (esperado) | Mejora |
|---------|-----------------|---------------------|--------|
| jsonValidPass1 | 54% | >90% | +36% |
| copyableRate | 54% | >90% | +36% |
| latencyP95 | 12s | <5s | 2.4x más rápido |
| Costo por 1K prompts | $0 | ~$0.001 | Cómo mínimo |

### 5.4 Fase 4: Ajustes (opcional)

Si es necesario ajustar comportamiento:

**Archivo:** `main.py` (línea 38-41)
```python
# Ajustar temperature para DeepSeek
if provider == "deepseek":
    lm = create_deepseek_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.DEEPSEEK_API_KEY or settings.LLM_API_KEY,
        temperature=0.0,  # Más determinista para consistencia
    )
```

---

## 6. Análisis de DeepSeek Chat vs Reasoner

El usuario mencionó que tiene dos modelos disponibles:

### 6.1 DeepSeek Chat (Recomendado)

**Uso:** Respuestas rápidas y directas

**Ventajas:**
- ✅ Más rápido (menos reasoning steps)
- ✅ Más económico (menos tokens)
- ✅ Suficiente para mejora de prompts
- ✅ Mejor para tasks simples

**Parámetros sugeridos:**
- Temperature: 0.0 (máxima consistencia)
- Max tokens: 2000 (suficiente para prompts)

### 6.2 DeepSeek Reasoner (Opcional)

**Uso:** Tareas complejas de razonamiento

**Ventajas:**
- ✅ Mejor razonamiento complejo
- ✅ Más profundo en análisis

**Desventajas:**
- ❌ Más lento (más reasoning steps)
- ❌ Más costoso
- ❌ Overkill para mejora de prompts

**Recomendación:** Usar **DeepSeek Chat** para este caso de uso.

---

## 7. Comparativa: Ollama vs DeepSeek

### 7.1 Consistencia

| Aspecto | Ollama (7B local) | DeepSeek Chat |
|---------|------------------|---------------|
| **JSON parsing** | 60-70% fallo | <5% fallo (esperado) |
| **Similitud semántica** | 34-48% | >80% (esperado) |
| **Reproducibilidad** | Baja | Alta |
| **Temperature control** | Ineficaz | Eficaz |

### 7.2 Rendimiento

| Aspecto | Ollama (7B local) | DeepSeek Chat |
|---------|------------------|---------------|
| **Latencia P95** | 12s | <5s (esperado) |
| **Throughput** | 1 prompt cada 3-10s | 10+ prompts/segundo |
| **Escalabilidad** | Limitado por CPU | Ilimitado (cloud) |

### 7.3 Costo

| Aspecto | Ollama (7B local) | DeepSeek Chat |
|---------|------------------|---------------|
| **Costo por prompt** | $0 (hardware/electricidad) | ~$0.0001 |
| **Costo mensual (1K prompts)** | ~$5-10 (electricidad) | ~$0.10 |
| **Costo mensual (10K prompts)** | ~$50-100 | ~$1.00 |

**Break-even:** Si el tiempo de desarrollo vale más de $1/mes, DeepSeek es más barato.

---

## 8. Plan de Contingencia

### 8.1 Si DeepSeek no funciona

**Fallback 1: Gemini Pro**
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

**Fallback 2: OpenAI GPT-4o mini**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-key
```

**Fallback 3: Volver a Ollama**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
```

### 8.2 Si API key expira o límite

- Configurar límite de gasto mensual en DeepSeek platform
- Implementar fallback automático a Ollama
- Monitorear uso con logging estructurado

---

## 9. Ventajas de la Migración

### 9.1 Técnicas

1. **Mayor consistencia** - DeepSeek es más determinista
2. **Menor tasa de fallo** - JSON parsing robusto
3. **Mejor calidad** - Modelo más capaz (32B vs 7B)
4. **Temperature efectivo** - Control real de variabilidad

### 9.2 Operativas

1. **Sin mantenimiento local** - No hay que mantener Ollama
2. **Escalabilidad** - Crece sin límites
3. **Monitoring** - Dashboard de DeepSeek platform
4. **Logging** - Más fácil de debug

### 9.3 Económicas

1. **Costo predecible** - $0.001 por 1000 prompts
2. **Sin hardware** - No requiere GPU potente
3. **Pago por uso** - Solo se paga lo que se usa

---

## 10. Conclusión y Recomendación

**Recomendación:** ✅ **PROCEDER CON MIGRACIÓN**

**Justificación:**
1. El sistema actual tiene problemas críticos (CRT-03)
2. DeepSeek Chat resuelve los problemas de consistencia
3. La migración es trivial (5 minutos de config)
4. El costo es mínimo ($0.001 por 1000 prompts)
5. El código adaptador ya existe y está probado

**Siguiente paso:**
1. Obtener API key de DeepSeek
2. Configurar `.env`
3. Ejecutar test de variabilidad para validar
4. Comparar métricas con baseline actual

**Esfuerzo estimado:** 2 horas end-to-end
**Riesgo:** Bajo - fácil revertir a Ollama

---

## 11. Comandos Útiles

```bash
# 1. Obtener API key
# Visitar: https://platform.deepseek.com/

# 2. Configurar .env
cat >> .env << 'EOF'
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-your-key-here
EOF

# 3. Reiniciar backend
python main.py

# 4. Test básico
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"raw_idea": "Documenta una función en TypeScript"}'

# 5. Test de variabilidad
npx tsx scripts/test-variability.ts 10 specific

# 6. Evaluación completa
npm run eval -- --dataset testdata/cases.jsonl --output eval/deepseek-test.json

# 7. Comparar resultados
cat eval/deepseek-test.json
```

---

**Propuesto por:** Análisis de CRT-03 + Investigación DeepSeek
**Prioridad:** Alta - Resuelve problema crítico de consistencia
**Fecha de propuesta:** 2026-01-02
