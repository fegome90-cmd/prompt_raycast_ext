# 🚀 Quick Start - DSPy PromptImprover Backend

**Tiempo estimado para tener el backend corriendo: ~2 minutos**

---

## ⚡️ TL;DR (Fish)

```fish
cd /Users/felipe_gonzalez/Developer/raycast_ext/.worktrees/dspy-ollama-hf-pipeline
./setup_dspy_backend.sh
ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
uv run python main.py
```

```fish
curl -s http://localhost:8000/api/v1/improve-prompt \
  -H 'Content-Type: application/json' \
  -d '{"idea":"Design ADR process"}'
```

**Nota:** En Raycast, DSPy es obligatorio cuando está habilitado; no hay fallback automático a Ollama. Para usar Ollama directo, desactiva DSPy en preferencias.

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

### Paso 2: Iniciar Ollama (1 min)

```fish
# Si ya tienes Ollama instalado, solo iniciar:
ollama serve

# Si no, instalar primero:
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
```

### Paso 3: Configurar Backend (1 min)

```fish
# Editar .env si necesitas cambiar algo
nano .env

# Valores por defecto (ya deberían funcionar):
LLM_PROVIDER=ollama
LLM_MODEL=hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
LLM_BASE_URL=http://localhost:11434
```

### Paso 4: Iniciar Backend (1 min)

```fish
uv run python main.py
```

**Output esperado:**
```
🚀 Starting DSPy Prompt Improver API...
📍 Server: http://0.0.0.0:8000
🧠 LLM: ollama/hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
✅ DSPy configured with ollama/hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
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

### Opción 1: Test Manual con Python

```fish
# Test 1: Import signature
uv run python -c "from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature; print('✅ Signature OK')"

# Test 2: Import module
uv run python -c "from eval.src.dspy_prompt_improver import PromptImprover; print('✅ Module OK')"

# Test 3: Import FastAPI app
uv run python -c "from main import app; print('✅ App OK')"
```

**Output esperado:**
```
✅ Signature OK
✅ Module OK
✅ App OK
```

### Opción 2: Verificar Tests

```fish
set -x PYTHONPATH /Users/felipe_gonzalez/Developer/raycast_ext
uv run pytest tests/test_dspy_prompt_improver.py::TestPromptImprover::test_load_prompt_improvement_examples -v
```

**Output esperado:**
```
tests/...::test_load_prompt_improvement_examples PASSED [100%]
================ 1 passed ====================
```

### Opción 3: API con Navegador

1. Abrir navegador: http://localhost:8000/docs
2. Ver que tienes 3 endpoints:
   - GET `/` - API information
   - GET `/health` - Health check
   - POST `/api/v1/improve-prompt` - Main endpoint
3. En Swagger UI, probar con:
   ```json
   {
     "idea": "Design ADR process",
     "context": "Software architecture team"
   }
   ```

---

## 🔧 Troubleshooting Rápido

### Problema: "ModuleNotFoundError: No module named 'dspy'"

**Solución:**
```fish
# Instalar dependencias
uv sync --all-extras

# Verificar instalación
uv run python -c "import dspy; print(f'DSPy version: {dspy.__version__}')"
```

### Problema: "Ollama request timed out"

**Solución:**
```fish
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags

# Si no responde, iniciar Ollama:
ollama serve

# En otra terminal, verificar modelo:
ollama list
ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
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
4. Recuerda: no hay fallback automático cuando DSPy está habilitado

---

## 📊 Qué Tienes Ahora

### Backend DSPy Completado con:

1. **PromptImprover Module** - Transforma ideas crudas en prompts SOTA
2. **Multi-Provider Support** - Ollama, Gemini, DeepSeek, OpenAI
3. **FastAPI Backend** - Endpoint REST production-ready
4. **HemDov Compatible** - 100% reutilizable
5. **Tests TDD** - RED-GREEN-REFACTOR pattern
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
    ↓ Ollama / Gemini API
  LLM Provider
    ↓ Structured prompt
  FastAPI Response
    ↓ JSON: {improved_prompt, role, directive, framework, guardrails}
  TypeScript Client
    ↓ Parse response
  Raycast UI
    ↓ Display improved prompt
  Usuario final
```

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
| Documentación completa | `DSPY_BACKEND_README.md` |
| Resumen de implementación | `IMPLEMENTATION_SUMMARY.md` |
| Índice de archivos | `ARCHIVOS_CREADOS.md` |
| Guía DSPy (especificación) | `docs/research/wizard/03-dspy-integration-guide.md` |
| HemDov patterns | `docs/research/wizard/DSPy_Audit_Report.md` |

---

## ✅ Checklist Final

- [ ] Ejecutado `setup_dspy_backend.sh`
- [ ] Ollama corriendo en http://localhost:11434
- [ ] Backend corriendo en http://localhost:8000
- [ ] Health check exitoso: `curl http://localhost:8000/health`
- [ ] Test exitoso con Swagger: http://localhost:8000/docs
- [ ] Verificado que imports funcionan
- [ ] Verificado que al menos 1 test pasa

---

## 🎉 ¡Estás Listo!

**En 5 minutos deberías tener:**
1. Backend DSPy corriendo
2. Ollama respondiendo
3. Endpoint `/api/v1/improve-prompt` funcionando
4. Listo para mejorar prompts automáticamente
5. Integración con Raycast posible via TypeScript client

**Siguientes pasos opcionales:**
1. Añadir más ejemplos al dataset (actualmente 5)
2. Compilar con BootstrapFewShot para mejor calidad
3. Configurar otro provider (Gemini, DeepSeek, etc.)
4. Desplegar en producción (no local)

---

**¡Comienza a usar el backend DSPy PromptImprover ahora mismo! 🚀**
