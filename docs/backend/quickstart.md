# 🚀 Quick Start - DSPy PromptImprover Backend

**Tiempo estimado para tener el backend corriendo: ~2 minutos**

---

## ⚡️ TL;DR (Fish)

```fish
cd /Users/felipe_gonzalez/Developer/raycast_ext
# Configure .env with Anthropic API key first
cp .env.example .env
# Edit .env and set: HEMDOV_ANTHROPIC_API_KEY=sk-ant-...
source .venv/bin/activate
python main.py
```

```fish
curl -s http://localhost:8000/api/v1/improve-prompt \
  -H 'Content-Type: application/json' \
  -d '{"idea":"Design ADR process"}'
```

**Default provider:** Anthropic Haiku 4.5 (7.2s avg latency, $0.0035/prompt)
**Other providers:** DeepSeek (slower, cheaper), Sonnet 4.5 (higher quality), Opus 4 (max quality)

---

## ⚡ 5 Minutos a Backend DSPy Funcional

### Paso 1: Instalar y Configurar (2 min)

```fish
# Ejecutar script automatizado
./scripts/setup_dspy_backend.sh

# Si el script falla, hacerlo manual:
uv sync --all-extras
cp .env.example .env
```

### Paso 2: Configurar API Keys (1 min)

```fish
# Editar .env
nano .env

# Configurar Anthropic API key (requerido para Haiku 4.5)
# Obtener API key de: https://console.anthropic.com/
HEMDOV_ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Opcional: Configurar DeepSeek API key (alternativa más económica)
DEEPSEEK_API_KEY=sk-deepseek-your-key-here
```

### Paso 3: Iniciar Backend (1 min)

```fish
# Activar venv e iniciar
source .venv/bin/activate
python main.py
```

**Output esperado:**
```
INFO:     ✓ Anthropic API Key configured: sk-ant-api03...5B2A
INFO:     ✓ Cloud provider configured - API validation passed
INFO:     DSPy configured with anthropic/claude-haiku-4-5-20251001
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Paso 5: Probar (30 segundos)

```fish
# Health check
curl http://localhost:8000/health

# Test con prompt real
curl -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Design ADR process"}'
```

---

## 🧪 Verificación de Instalación

### Opción 1: Health Check

```fish
# Verificar que backend está corriendo
curl http://localhost:8000/health

# Output esperado:
# {"status":"healthy","provider":"anthropic","model":"claude-haiku-4-5-20251001","dspy_configured":true}
```

### Opción 2: Test Manual

```fish
# Test con prompt simple
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "create a todo app"}'

# Output esperado: JSON con "improved_prompt", "role", "directive", etc.
```

### Opción 3: Verificar Imports

```fish
source .venv/bin/activate

python -c "from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature; print('✅ Signature OK')"
python -c "from main import app; print('✅ App OK')"
python -c "import dspy; print(f'✅ DSPy {dspy.__version__}')"
```

---

## 🔧 Troubleshooting Rápido

### Problema: "ModuleNotFoundError: No module named 'dspy'"

**Solución:**
```fish
# Activar venv e instalar dependencias
source .venv/bin/activate
pip install dspy-ai litellm fastapi uvicorn
```

### Problema: "ANTHROPIC_API_KEY is required"

**Solución:**
```fish
# Editar .env y agregar API key
nano .env

# Agregar línea:
HEMDOV_ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Obtener API key de: https://console.anthropic.com/
```

### Problema: "AnthropicException - token expired or incorrect"

**Solución:**
```fish
# Verificar que API key sea válida y tenga formato correcto
# Debe comenzar con: sk-ant-api03-

# Si usaste ANTHROPIC_API_KEY, intenta con HEMDOV_ANTHROPIC_API_KEY
# Ambas son soportadas
```

### Problema: "Port 8000 already in use"

**Solución:**
```fish
# Cambiar puerto en .env
echo "API_PORT=8001" >> .env

# O matar proceso usando puerto 8000
kill -9 (lsof -ti:8000)
```

### Problema: "DSPy backend not available" (en frontend Raycast)

**Solución:**
1. Verificar que backend está corriendo: `curl http://localhost:8000/health`
2. Verificar CORS (debería permitir `*`)
3. Verificar URL base en frontend (debería ser `http://localhost:8000`)

### Problema: "LiteLLM request failed - wrong API base"

**Solución:**
El adapter Anthropic fuerza `https://api.anthropic.com` automáticamente. Si usas un proxy, puede fallar. Verifica que no hay variables de entorno conflicting.

---

## 📊 Qué Tienes Ahora

### Backend DSPy Completado con:

1. **PromptImprover Module** - Transforma ideas crudas en prompts SOTA
2. **Multi-Provider Support** - Anthropic (Haiku/Sonnet/Opus), DeepSeek, Gemini, OpenAI
3. **FastAPI Backend** - Endpoint REST production-ready
4. **HemDov Compatible** - 100% reutilizable
5. **Default: Haiku 4.5** - 7.2s latency, $0.0035/prompt
6. **Documentación Completa** - README + Troubleshooting

### Arquitectura de Flujo Completo:

```
Usuario Raycast UI
    ↓ "Design ADR process"
  TypeScript Client
    ↓ POST /api/v1/improve-prompt
  FastAPI Backend
    ↓ PromptImprover.forward()
  DSPy Module
    ↓ ChainOfThought reasoning
  LiteLLM Adapter
    ↓ Anthropic API (Haiku 4.5)
  Claude Haiku 4.5
    ↓ Structured prompt (7.2s avg)
  FastAPI Response
    ↓ JSON: {improved_prompt, role, directive, framework, guardrails}
  TypeScript Client
    ↓ Parse response
  Raycast UI
    ↓ Display improved prompt
  Usuario final
```

### Provider Comparison:

| Provider | Latency | Cost/1K prompts | Best For |
|----------|---------|-----------------|----------|
| **Haiku 4.5** ⭐ | **7.2s** | $3.54 | **Default - Best UX** |
| Sonnet 4.5 | 8.7s | $10.62 | Higher quality |
| DeepSeek | 25.1s | $0.63 | High volume, cost-sensitive |
| Opus 4 | TBD | $53+ | Maximum quality |

---

## 🎯 Casos de Uso

### Caso 1: Mejorar Prompt para Código

**Input:**
```json
{
  "idea": "Create function to sort array",
  "context": "JavaScript development"
}
```

**Output esperado:**
```json
{
  "improved_prompt": "**[ROLE & PERSONA]**\nYou are a Senior JavaScript Developer...\n\n**[CORE DIRECTIVE]**\nCreate a function to sort an array...",
  "role": "Senior JavaScript Developer...",
  "directive": "Create a function to sort an array...",
  "framework": "chain-of-thought",
  "guardrails": ["Use ES6+", "Include error handling", "Add comments"],
  "confidence": 0.92
}
```

### Caso 2: Mejorar Prompt para Marketing

**Input:**
```json
{
  "idea": "Write email campaign for new product",
  "context": "B2B SaaS launch"
}
```

**Output esperado:**
```json
{
  "improved_prompt": "**[ROLE & PERSONA]**\nYou are a Marketing Strategist with 10+ years of B2B experience...\n\n**[CORE DIRECTIVE]**\nWrite an email campaign for B2B SaaS launch...",
  "role": "Marketing Strategist...",
  "directive": "Write an email campaign for B2B SaaS launch...",
  "framework": "decomposition",
  "guardrails": ["Focus on ROI", "Include call-to-action", "B2B tone"],
  "confidence": 0.88
}
```

### Caso 3: Backend No Disponible (DSPy obligatorio)

**Behavior:**
1. Frontend intenta DSPy backend
2. Health check falla (backend no corriendo)
3. Se muestra error en Raycast: DSPy no disponible
4. Para usar Ollama directo, desactiva DSPy en preferencias

---

## 📚 Documentación Adicional

| Necesitas | Archivo |
|------------|----------|
| Documentación completa | `docs/backend/README.md` |
| Resumen de implementación | `IMPLEMENTATION_SUMMARY.md` |
| Índice de archivos | `ARCHIVOS_CREADOS.md` |
| Guía DSPy (especificación) | `docs/research/wizard/03-dspy-integration-guide.md` |
| HemDov patterns | `docs/research/wizard/DSPy_Audit_Report.md` |

---

## ✅ Checklist Final

- [ ] Anthropic API key configurada en .env
- [ ] Backend corriendo en http://localhost:8000
- [ ] Health check exitoso: `curl http://localhost:8000/health`
- [ ] Test exitoso: Prompt improvement funciona
- [ ] Verificar que usa Haiku 4.5 (model field en health)

## 🎉 ¡Estás Listo!

**En 2 minutos deberías tener:**
1. Backend DSPy corriendo con Haiku 4.5
2. Endpoint `/api/v1/improve-prompt` funcionando
3. Latencia promedio de ~7 segundos
4. Listo para mejorar prompts automáticamente

**Siguientes pasos opcionales:**
1. **Cambiar a Sonnet 4.5** para mayor calidad: Editar `LLM_MODEL` en .env
2. **Cambiar a DeepSeek** para menor costo: Editar `LLM_PROVIDER=deepseek` en .env
3. **Ajustar temperatura**: Modificar `DEFAULT_TEMPERATURE` en main.py
4. **Ejecutar A/B test**: `python scripts/eval/ab_test_haiku_sonnet.py`

---

## 📚 Documentación Adicional

| Necesitas | Archivo |
|------------|----------|
| Plan de implementación | `docs/plans/2026-01-04-anthropic-haiku-optimization.md` |
| Comparativa de costos | Ver "Cost Analysis" section en el plan arriba |
| Guía DSPy (especificación) | `docs/research/wizard/03-dspy-integration-guide.md` |
| HemDov patterns | `docs/research/wizard/DSPy_Audit_Report.md` |
