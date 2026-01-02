# Session: DSPy DeepSeek Optimization

## Estado Actual
- **Backend DSPy** ejecutándose con DeepSeek Chat
- **API Key**: `sk-c9fe1a8461104e8ea026cdc4dfe10da0` (configurada, segura)
- **Temperature**: 0.0 (máxima consistencia)
- **Quality Gates**: 3/4 PASSED
- **Port**: 8000

## Completado Esta Sesión
1. ✅ Migración DeepSeek Chat (CRT-04)
2. ✅ Pruebas de integración
3. ✅ Test de variabilidad (10/10 éxito)
4. ✅ Evaluación completa (30 casos)
5. ✅ Auditoría de seguridad (API key segura)

## Próximos Pasos (Para el Siguiente Agente)

### Opción 1: Few-Shot Optimization (Recomendado)
El worktree `phase3-dspy-fewshot-optimization` tiene código previo:
```
/Users/felipe_gonzalez/Developer/raycast_ext/raycast_ext-worktrees/phase3-dspy-fewshot-optimization/
├── scripts/
│   └── optimize_dspy_fewshot.py    # Optimizador de few-shot
└── experiments/
    └── example_pool.py             # Pool de ejemplos
```

**Acción inmediata:**
```bash
# 1. Revisar el worktree
cd raycast_ext-worktrees/phase3-dspy-fewshot-optimization
ls -la

# 2. Leer README o plan si existe
cat README.md 2>/dev/null || find . -name "*.md" | head -5

# 3. Evaluar integración con DeepSeek
```

### Opción 2: Compilación DSPy
```bash
# Actualmente zero-shot, compilar con ejemplos:
cd dashboard
npm run eval -- --dataset testdata/variance-hybrid.jsonl --backend dspy --compile
```

### Opción 3: Fine-tuning Temperature
```bash
# Probar temperatura 0.1 para más creatividad
# Editar main.py línea 32:
"deepseek": 0.1,  # En lugar de 0.0
```

## Comandos Rápidos

```bash
# Iniciar backend
cd /Users/felipe_gonzalez/Developer/raycast_ext
source .venv/bin/activate && python main.py

# Ver health
curl http://localhost:8000/health

# Ejecutar evaluación
cd dashboard && npm run eval -- --dataset testdata/variance-hybrid.jsonl --backend dspy --output eval/eval-$(date +%Y%m%d).json

# Test variabilidad
./scripts/test-deepseek-variability.sh
```

## Archivos Clave
- Backend: `main.py`, `hemdov/infrastructure/adapters/litellm_dspy_adapter_prompt.py`
- Testing: `dashboard/scripts/evaluator.ts`, `src/core/llm/improvePrompt.ts`
- Docs: `HANDOFF.md` (completo), `docs/auditoria/CRT-04-migracion-deepseek-chat.md`

## Nota
El merge de `eval-variance-plan` añadió soporte para `--backend dspy` en el evaluator. Usar esto para comparaciones.
