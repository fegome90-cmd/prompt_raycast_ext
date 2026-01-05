# Diseño: Integración de Prompt Dataset a raycast_ext

**Fecha**: 2026-01-05
**Autor**: Claude Code + Usuario
**Estado**: Aprobado para implementación

---

## Resumen Ejecutivo

Integrar los 42 prompts validados de `~/Desktop/prompt_dataset/` en el repositorio `raycast_ext` para uso con DSPy KNNFewShot, generando dos formatos de salida:
1. **Formato merge** - Para combinar con el pool existente (877 → 919 ejemplos)
2. **Formato DSPy** - Dataset independiente para KNNFewShot

---

## Arquitectura

### Componentes

1. **Script de Transformación** (`transform_prompts.py`)
   - Ubicación: `/raycast_ext/scripts/data/fewshot/`
   - Lee: `~/Desktop/prompt_dataset/prompts.json`
   - Genera: 2 archivos de salida

2. **Merge con Pool Existente**
   - Combina 42 prompts con `merged-trainset.json` (877 ejemplos)
   - Resultado: `merged-trainset-updated.json` (919 ejemplos)
   - Ubicación: `/raycast_ext/datasets/exports/`

3. **Dataset DSPy Independiente**
   - Formato optimizado para DSPy KNNFewShot
   - Resultado: `dspy-knnfewshot-prompts.json` (42 ejemplos)
   - Ubicación: `/raycast_ext/datasets/exports/`

### Flujo de Datos

```
~/Desktop/prompt_dataset/prompts.json (42 prompts)
                ↓
    transform_prompts.py
                ↓
    ┌───────────┴───────────┐
    ↓                       ↓
merged-trainset-     dspy-knnfewshot-
updated.json          prompts.json
(919 ejemplos)        (42 ejemplos)
```

---

## Mapeo de Datos

### Formato Merge (inputs/outputs)

```python
{
  "inputs": {
    "original_idea": prompt["original_idea"],
    "context": prompt.get("context", "")
  },
  "outputs": {
    "improved_prompt": prompt["improved_prompt"]
  },
  "metadata": {
    "domain": prompt.get("domain", ""),
    "category": prompt.get("task_category", ""),  # task_category → category
    "source": "prompt_dataset_v1",
    "framework": prompt.get("framework", ""),
    "complexity": prompt.get("complexity", "medium"),
    "sub_category": prompt.get("sub_category", ""),
    "quality_score": prompt.get("quality_score", 0.85)
  }
}
```

### Formato DSPy KNNFewShot (input/output)

```python
{
  "input": f"{prompt['original_idea']}\n\nContext: {prompt.get('context', '')}",
  "output": prompt["improved_prompt"],
  "metadata": {
    "role": prompt.get("role", ""),
    "framework": prompt.get("framework", ""),
    "task_category": prompt.get("task_category", ""),
    "sub_category": prompt.get("sub_category", ""),
    "domain": prompt.get("domain", ""),
    "complexity": prompt.get("complexity", "medium"),
    "source": "prompt_dataset_v1",
    "validation_timestamp": "2026-01-05T12:00:00Z",
    "quality_score": prompt.get("quality_score", 0.85),
    "example_validator_score": 0.960
  }
}
```

---

## Flujo DSPy KNNFewShot

```python
import dspy

# Cargar dataset
with open('dspy-knnfewshot-prompts.json') as f:
    examples = json.load(f)

# Crear KNNFewShot
knn_fewshot = dspy.KNNFewShot(k=5)

# Entrenar
knn_fewshot.train(train_examples=examples)

# Usar en inferencia
lm = dspy.OpenAI(model='gpt-4')
with dspy.context(lm=lm):
    result = knn_fewshot("Implement JWT validation")
```

---

## Validaciones

### Checks Obligatorios
1. ✅ Verificar que `prompts.json` existe
2. ✅ Validar que contiene exactamente 42 prompts
3. ✅ Verificar campos requeridos (`improved_prompt`, `task_category`, `domain`)
4. ✅ Validar formato de salida antes de guardar

### Reglas de Validación
- `inputs.original_idea` debe ser no-vacía
- `outputs.improved_prompt` debe ser no-vacío
- `metadata.domain` debe existir
- `metadata.quality_score` debe estar entre 0 y 1

---

## Manejo de Errores

| Error | Acción | Exit Code |
|-------|--------|-----------|
| Archivo no encontrado | Mensaje claro + exit | 1 |
| Formato inválido | Skip prompt + continuar | - |
| Campo faltante | Usar default + advertencia | - |
| Error de escritura | Traceback + exit | 2 |

---

## Testing

### Test de Formato Merge
```python
def test_merge_format():
    merged = load_json("merged-trainset-updated.json")
    assert len(merged) == 919  # 877 + 42
    for ex in merged[-42:]:
        assert "inputs" in ex
        assert ex["metadata"]["source"] == "prompt_dataset_v1"
```

### Test de Formato DSPy
```python
def test_dspy_format():
    dspy = load_json("dspy-knnfewshot-prompts.json")
    assert len(dspy) == 42
    for ex in dspy:
        assert "input" in ex
        assert "output" in ex
        assert len(ex["input"]) > 0
```

---

## Archivos de Salida

| Archivo | Ubicación | Tamaño | Propósito |
|---------|-----------|--------|-----------|
| `merged-trainset-updated.json` | `/raycast_ext/datasets/exports/` | 919 ejemplos | Pool completo |
| `dspy-knnfewshot-prompts.json` | `/raycast_ext/datasets/exports/` | 42 ejemplos | DSPy training |

---

## Pasos Siguientes

1. ✅ Diseño aprobado
2. ⏳ Implementar `transform_prompts.py`
3. ⏳ Ejecutar script
4. ⏳ Verificar salida
5. ⏳ Testing manual/automatizado
6. ⏳ Documentar uso

---

**Aprobado por**: Usuario
**Fecha de aprobación**: 2026-01-05
