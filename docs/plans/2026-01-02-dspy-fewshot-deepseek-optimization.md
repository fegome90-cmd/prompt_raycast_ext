# DSPy Few-Shot Optimization with DeepSeek

**Date:** 2026-01-02
**Status:** Design Complete, Pending Implementation
**Related:** CRT-04 (DeepSeek Migration - COMPLETED)

## Resumen Ejecutivo

Optimizar el `PromptImprover` de DSPy usando few-shot learning con DeepSeek Chat. El sistema actualmente opera en modo zero-shot (sin ejemplos) y ha logrado 0% JSON failure rate con DeepSeek, pero quality gates muestran oportunidad de mejora (3/4 PASSED).

**Objetivo:** Mejorar calidad y consistencia usando un enfoque híbrido que combina:
- **ComponentCatalog** (847 componentes): Patrones de estructura y formato
- **cases.jsonl** (30 casos): Ejemplos reales input→output

## Arquitectura Propuesta

### Enfoque Híbrido de Dos Fuentes

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID EXAMPLE SELECTOR                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌────────────────────┐       │
│  │ ComponentCatalog │         │    cases.jsonl     │       │
│  │     (847)        │         │       (30)         │       │
│  └────────┬─────────┘         └──────────┬─────────┘       │
│           │                              │                  │
│     Domain Match                    Cosine Similarity      │
│           │                              │                  │
│           └──────────┬───────────────────┘                  │
│                      │                                      │
│               Top-k Examples (k=3-5)                        │
│                      │                                      │
│                      ▼                                      │
│            ┌──────────────────┐                            │
│            │ PromptImprover   │                            │
│            │  (with FewShot)  │                            │
│            └──────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**Racional:**
- ComponentCatalog enseña **estructura** (role, directive, framework, guardrails)
- cases.jsonl enseña **transformación** (input crudo → output estructurado)
- Ambos se complementan para máxima cobertura de patrones

## Componentes

### 1. HybridExampleSelector

**Ubicación:** `eval/src/hybrid_example_selector.py`

**Responsabilidades:**
- Selección inteligente de ejemplos desde ambas fuentes
- Matching por dominio para ComponentCatalog
- Similitud semántica (cosine) para cases.jsonl
- Combinación y ranking de resultados

**Interfaz:**

```python
class HybridExampleSelector:
    """Select few-shot examples from hybrid sources."""

    def __init__(
        self,
        component_catalog_path: str,
        cases_path: str,
        embedding_model: Optional[str] = None,  # None = keyword fallback
        k_components: int = 2,
        k_cases: int = 3
    ):
        """Initialize selector with both data sources."""
        # Load ComponentCatalog (847 components)
        # Load cases.jsonl (30 cases)
        # Initialize embedding model if available
        pass

    def select(
        self,
        query: str,
        domain_hint: Optional[str] = None
    ) -> List[dspy.Example]:
        """Select top-k examples for query.

        Returns:
            Combined list from ComponentCatalog + cases.jsonl
        """
        # 1. Domain-based selection from ComponentCatalog
        # 2. Similarity-based selection from cases.jsonl
        # 3. Merge, deduplicate, rank by relevance
        pass
```

### 2. PromptImproverWithFewShot

**Ubicación:** `eval/src/dspy_prompt_improver_fewshot.py`

**Responsabilidades:**
- Wrapper sobre PromptImprover base
- Compilación con KNNFewShot usando ejemplos
- Persistencia del módulo compilado
- Fallback a zero-shot si falla compilación

**Interfaz:**

```python
class PromptImproverWithFewShot(dspy.Module):
    """DSPy PromptImprover with few-shot compilation."""

    def __init__(
        self,
        compiled_path: Optional[str] = None,
        fallback_to_zeroshot: bool = True
    ):
        """Initialize few-shot enabled improver.

        Args:
            compiled_path: Path to load/save compiled module
            fallback_to_zeroshot: Allow zero-shot if compilation fails
        """
        super().__init__()
        self.base_improver = PromptImprover()
        self.compiled_path = compiled_path
        self.fallback_to_zeroshot = fallback_to_zeroshot
        self._compiled = False

    def compile(
        self,
        trainset: List[dspy.Example],
        k: int = 3
    ) -> None:
        """Compile with KNNFewShot.

        Args:
            trainset: Training examples with inputs() and outputs()
            k: Number of neighbors for KNN
        """
        # Compile with KNNFewShot
        # Save to compiled_path if provided
        pass

    def forward(
        self,
        original_idea: str,
        context: str = ""
    ) -> dspy.Prediction:
        """Generate improved prompt with few-shot examples.

        If compiled, uses KNNFewShot to select relevant examples.
        Otherwise falls back to zero-shot.
        """
        pass
```

### 3. Preprocessing: ComponentNormalizer

**Ubicación:** `scripts/phase3_fewshot/component_normalizer.py`

**Responsabilidades:**
- Normalizar ComponentCatalog al formato DSPy
- Generar inputs sintéticos para componentes
- Guardar dataset procesado

**Interfaz:**

```python
def normalize_component_catalog(
    input_path: str,
    output_path: str,
    input_generator: Callable[[dict], str]
) -> None:
    """Normalize ComponentCatalog to DSPy format.

    For each component:
    1. Extract role, directive, framework, guardrails
    2. Generate synthetic input using input_generator
    3. Save as DSPy Example with inputs() + outputs()

    Args:
        input_path: Path to ComponentCatalog.json
        output_path: Path to save normalized dataset
        input_generator: Function to generate synthetic inputs
    """
    pass
```

**Ejemplo de input_generator:**

```python
def generate_component_input(component: dict) -> str:
    """Generate synthetic input for component.

    Uses domain, category, and framework to create
    realistic input that would produce this component.
    """
    domain = component.get("domain", "")
    category = component.get("category", "")
    framework = component.get("framework", "")

    # Template-based generation
    templates = {
        "softdev": "Crea un prompt para {category} usando {framework}",
        "default": "Genera prompt de {category}"
    }

    template = templates.get(domain, templates["default"])
    return template.format(category=category, framework=framework)
```

## Data Flow

### Fase 1: Preparación Offline (One-time)

```
┌─────────────────────┐
│   ComponentCatalog  │ (847 components)
│   .json             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ComponentNormalizer│
│  (input_generator)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  normalized_        │
│  components.json    │ (DSPy format)
└──────────┬──────────┘
           │
           │    ┌─────────────┐
           └────┤  Merge      │
                │  with       │
    ┌───────────┤  cases.jsonl│
    │           └──────┬───────┘
    │                   │
    ▼                   ▼
┌─────────────────────────────────┐
│  DSPy Trainset                  │
│  (847 normalized + 30 cases)    │
└─────────────────────────────────┘
```

### Fase 2: Runtime Selection

```
User Input: "Documenta una función en TypeScript"
           │
           ▼
┌─────────────────────────────────────┐
│  HybridExampleSelector.select()     │
├─────────────────────────────────────┤
│                                     │
│  1. Classify domain: "function"     │
│     → Match ComponentCatalog entries│
│     → Top-2 domain-specific         │
│                                     │
│  2. Cosine similarity: cases.jsonl  │
│     → Vectorize input               │
│     → Compare with 30 cases         │
│     → Top-3 most similar            │
│                                     │
│  3. Combine → 5 examples            │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  PromptImproverWithFewShot.forward()│
│  (uses compiled KNNFewShot)         │
└─────────────────────────────────────┘
           │
           ▼
    Improved Prompt
```

### Fase 3: Compilación DSPy

```python
# One-time compilation
from dspy.teleprompt import KNNFewShot

trainset = load_trainset("normalized_components.json", "testdata/cases.jsonl")
improver = PromptImproverWithFewShot()

# Compile with KNNFewShot
compiled = KNNFewShot(k=3).compile(
    improver,
    trainset=trainset
)

# Save for reuse
save_compiled(compiled, "models/prompt_improver_fewshot.json")
```

## Testing Strategy

### Fase 1: Generación de Dataset

**Objetivo:** Crear dataset completo de training

**Tests:**
```bash
# 1. Normalización de ComponentCatalog
pytest scripts/phase3_fewshot/test_component_normalizer.py

# 2. Validación de formato
pytest scripts/phase3_fewshot/test_dataset_format.py

# 3. Calidad de inputs sintéticos
pytest scripts/phase3_fewshot/test_input_quality.py
```

**Assertions:**
- Todos los componentes tienen inputs/outputs válidos
- Formato DSPy compatible (inputs(), outputs())
- No duplicados
- Cobertura de dominios completa

### Fase 2: Integración DSPy

**Objetivo:** Verificar que módulo compila y ejecuta

**Tests:**
```bash
# 1. Compilación exitosa
pytest eval/src/test_dspy_compilation.py

# 2. Inferencia (con módulo compilado)
pytest eval/src/test_dspy_inference.py

# 3. Performance (latency, throughput)
pytest eval/src/test_dspy_performance.py
```

**Assertions:**
- Compilación completa sin errores
- Inferencia produce outputs válidos
- Latencia < 10s p95 (baseline actual: 4.9s)

### Fase 3: Comparación Quality Gates

**Objetivo:** Medir mejora vs baseline

**Dataset:** `testdata/variance-hybrid.jsonl` (73 casos)

**Comando:**
```bash
# Baseline (zero-shot)
npm run eval -- \
  --dataset testdata/variance-hybrid.jsonl \
  --backend dspy \
  --output eval/baseline-zeroshot.json \
  --repeat 10

# Few-shot
npm run eval -- \
  --dataset testdata/variance-hybrid.jsonl \
  --backend dspy-fewshot \
  --output eval/fewshot-optimized.json \
  --repeat 10

# Comparación
scripts/compare_quality_gates.py \
  --baseline eval/baseline-zeroshot.json \
  --treatment eval/fewshot-optimized.json \
  --output eval/comparison.md
```

**Métricas:**

| Métrica | Baseline | Target | Delta |
|---------|----------|--------|-------|
| Quality Gates (4/4) | 3/4 (75%) | 4/4 (100%) | +25% |
| Confidence Promedio | 0.82 | 0.90+ | +10% |
| JSON Validity | 100% | 100% | = |
| Latency p95 | 4.9s | <7s | +40% |
| Variability (10x) | 100% | 100% | = |

## Error Handling

### 1. Dataset Failures

```python
try:
    components = load_component_catalog(path)
except FileNotFoundError:
    logger.warning(f"ComponentCatalog not found: {path}")
    logger.info("Falling back to cases.jsonl only")
    components = []
except json.JSONDecodeError as e:
    logger.error(f"Invalid ComponentCatalog: {e}")
    raise DatasetError("ComponentCatalog is required")
```

### 2. Compilation Errors

```python
try:
    compiled = KNNFewShot(k=3).compile(improver, trainset=trainset)
    save_compiled(compiled, compiled_path)
except Exception as e:
    logger.error(f"Compilation failed: {e}")
    if fallback_to_zeroshot:
        logger.info("Using zero-shot mode")
        return PromptImprover()  # Original zero-shot
    else:
        raise CompilationError("Few-shot compilation failed")
```

### 3. Embedding Unavailability

```python
# HybridExampleSelector
if embedding_model is None:
    logger.info("Embedding model not available, using keyword matching")
    similarity_fn = keyword_similarity
else:
    similarity_fn = cosine_similarity
```

### 4. Inference Failures

```python
# PromptImproverWithFewShot.forward()
try:
    if self._compiled:
        return self.compiled_improver.forward(original_idea, context)
    else:
        return self.base_improver.forward(original_idea, context)
except Exception as e:
    logger.error(f"Inference failed: {e}")
    if self.fallback_to_zeroshot:
        logger.info("Falling back to zero-shot")
        return self.base_improver.forward(original_idea, context)
    else:
        raise
```

## Plan de Implementación

### Phase 1: Dataset Preparation (1-2 días)
1. Implement `ComponentNormalizer`
2. Generar inputs sintéticos para ComponentCatalog
3. Validar formato DSPy
4. Merge con cases.jsonl

### Phase 2: Core Components (2-3 días)
1. Implement `HybridExampleSelector`
2. Implement `PromptImproverWithFewShot`
3. Integración con backend FastAPI
4. Tests de integración

### Phase 3: Compilation & Validation (1-2 días)
1. Compilar módulo con dataset completo
2. Tests de inferencia
3. Comparación quality gates
4. Documentar resultados

## Archivos a Crear/Modificar

**Nuevos:**
```
eval/src/
├── hybrid_example_selector.py
├── dspy_prompt_improver_fewshot.py
└── __tests__/
    ├── test_hybrid_selector.py
    └── test_fewshot_improver.py

scripts/phase3_fewshot/
├── component_normalizer.py
├── generate_synthetic_inputs.py
└── test_dataset_quality.py

models/  # Nuevo directorio
└── prompt_improver_fewshot.json  # Compiled module
```

**Modificar:**
```
main.py  # Agregar endpoint /fewshot
api/prompt_improver_api.py  # Nuevo endpoint opcional
eval/src/dspy_prompt_improver.py  # Mantener zero-shot como fallback
```

## Referencias

- DSPy KNNFewShot: https://dspy-docs.vercel.app/docs/deep-dive/teleprompt/knn
- ComponentCatalog: `/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/ComponentCatalog.json`
- cases.jsonl: `/Users/felipe_gonzalez/Developer/raycast_ext/dashboard/testdata/cases.jsonl`
- HANDOFF.md: Contexto completo de CRT-04

---

**Próximo paso:** Ejecutar Phase 1 (Dataset Preparation) y validar que ComponentCatalog se normaliza correctamente al formato DSPy.
