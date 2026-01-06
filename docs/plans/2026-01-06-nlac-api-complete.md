# Plan de Implementación: API NLaC (Natural Language as Code)

> **Architectura:** Transformar la API actual de "Prompt Engineering" a una arquitectura NLaC determinista con compilación, optimización y validación automáticas.

**Estado:** Ready for Implementation
**Fecha:** 2026-01-06
**Decisiones Arquitectónicas:** Ver sección "Decisiones Key"

---

## Decisiones Key (Arquitectura)

| Aspecto | Decisión | Justificación |
|---------|----------|---------------|
| **Prioridad** | Híbrido | Simple → Fast (<5s), Complejo → ÓPTIMO (15-30s) |
| **Alcance** | Ambos | Refactor Strategy Pattern + módulo NLaC |
| **Compatibilidad** | Feature flag | `?mode=nlac` para activar, backward compatible |
| **Budget LLM** | 5-10 llamadas | OPRO + SCoT + validación completos |
| **Intent Classifier** | Híbrido | Reglas estructurales → LLM si duda |
| **OPRO Stop** | 3 iteraciones | Max fijo + early stopping si score=100% |
| **Cache** | Hash completo | SHA256(idea + context + mode) |
| **RaR Output** | Invisible | Solo interno, no expuesto al usuario |
| **Validación** | Autocorrección | Reflexion loop (1 retry) + fallback |
| **Storage** | SQLite + tablas | Reusar SQLite actual |

---

## 1. Estructura de Base de Datos (SQLite)

Migración del schema actual para soportar el ciclo de vida completo de prompts NLaC.

### 1.1 Tabla Maestra: `prompts`

```sql
-- El "Binario Ejecutable" del prompt
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,              -- UUID v4
    version TEXT NOT NULL,             -- Semántica (1.0, 1.1, ...)
    intent_type TEXT NOT NULL,        -- 'generate', 'debug', 'refactor', 'explain'
    template TEXT NOT NULL,           -- String con placeholders {{variable}}
    strategy_meta JSON,                -- {"technique": "RaR", "role": "Expert"}
    constraints JSON,                  -- ["no_markdown", "json_only"]
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompts_intent ON prompts(intent_type);
CREATE INDEX idx_prompts_active ON prompts(is_active);
```

### 1.2 Tabla de Casos de Prueba: `test_cases`

```sql
-- Fundamental para Execution Accuracy (Spider methodology)
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    input_context TEXT,                 -- Contexto simulado o inputs
    expected_output TEXT,              -- Assertions o salida esperada
    test_type TEXT,                    -- 'unit', 'integration', 'regression'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
);

CREATE INDEX idx_test_cases_prompt ON test_cases(prompt_id);
```

### 1.3 Historial OPRO: `opro_trajectory`

```sql
-- Trayectoria de aprendizaje del optimizador
CREATE TABLE opro_trajectory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    iteration_number INTEGER NOT NULL,
    meta_prompt_used TEXT,             -- Instrucción al LLM optimizador
    generated_instruction TEXT,        -- Variación generada
    score REAL,                        -- Pass rate (0.0 - 1.0)
    feedback TEXT,                     -- Feedback del evaluador
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
);

CREATE INDEX idx_opro_prompt ON opro_trajectory(prompt_id, iteration_number);
```

### 1.4 Cache de Prompts: `prompt_cache`

```sql
-- Cache para Simple strategy (hash completo)
CREATE TABLE prompt_cache (
    cache_key TEXT PRIMARY KEY,        -- SHA256(idea + context + mode)
    prompt_id TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id)
);

CREATE INDEX idx_cache_accessed ON prompt_cache(last_accessed);
```

---

## 2. Esquema Pydantic (Data Contracts)

Validación estricta de entradas y salidas con soporte para feature flag.

### 2.1 Input Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

class NLaCInputs(BaseModel):
    """Inputs estructurados para NLaC (vs. string simple)"""
    instruction: str = Field(..., min_length=5, description="Instrucción principal")
    code_snippet: Optional[str] = None      # Para Debug/Refactor
    error_log: Optional[str] = None          # Para Debug (stacktrace)
    schema_context: Optional[Dict] = None    # Para Spider SQL pruning
    constraints: List[str] = []             # Restricciones adicionales

class NLaCRequest(BaseModel):
    """Request con feature flag"""
    idea: str = Field(..., min_length=5)
    context: str = ""
    mode: Literal["legacy", "nlac"] = "legacy"
    show_reasoning: bool = False            # ¿Exponer SCoT?
    high_quality: bool = True               # ¿Usar OPRO? (Complex)
```

### 2.2 NLaC Object Model

```python
class PromptObject(BaseModel):
    """El 'Binario' compilado del prompt"""
    id: str                                # UUID
    version: str
    intent_type: str
    template: str                           # Con placeholders {{var}}
    inputs: NLaCInputs
    strategy_meta: Dict[str, str]          # {"technique": "RaR", "role": "Expert"}
    constraints: List[str]                 # ["no_markdown"]
    verification: Dict[str, List] = None    # {"tests": [...], "constraints": [...]}

class IntermediateStep(BaseModel):
    """Pasos intermedios (SCoT, RaR) - solo si show_reasoning=True"""
    step_type: Literal["rephrase", "reasoning", "verification"]
    content: str
    timestamp: float
```

### 2.3 Response Models

```python
class OptimizeResponse(BaseModel):
    """Response polimórfico (legacy + nlac)"""
    # Campos legacy (siempre presentes)
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: List[str]
    reasoning: Optional[str]
    confidence: Optional[float]
    backend: str                           # "simple", "moderate", "complex"
    model: str
    provider: str
    latency_ms: int

    # Campos NLaC (solo si mode="nlac")
    nlac_object: Optional[PromptObject] = None
    intermediate_steps: Optional[List[IntermediateStep]] = None
    warnings: Optional[List[str]] = None     # De autocorrección

    # Metadata de procesamiento
    processing_info: Dict[str, float] = Field(
        default_factory=lambda: {
            "oprop_iterations": 0,
            "oprop_score": 0.0,
            "validation_passed": True
        }
    )
```

---

## 3. Módulos Core

### 3.1 IntentClassifier (Router Híbrido)

**Responsabilidad:** Clasificar input en GENERATE, DEBUG, REFACTOR, EXPLAIN

```python
class IntentClassifier:
    """
    Router híbrido: Reglas estructurales → LLM si duda.
    Basado en MultiAIGCD (Escenarios I, II, III).
    """

    INTENT_DEBUG_RUNTIME = "debug_runtime"
    INTENT_DEBUG_VAGUE = "debug_vague"
    INTENT_REFACTOR_LOGIC = "refactor_logic"
    INTENT_GENERATE = "generate"
    INTENT_EXPLAIN = "explain"

    def classify(self, request: NLaCRequest) -> str:
        """Enrutamiento en cascada"""
        # 1. REGLAS ESTRUCTURALES (MultiAIGCD)
        # Escenario II: Fixing Runtime Errors
        if request.inputs.code_snippet and request.inputs.error_log:
            return self.INTENT_DEBUG_RUNTIME

        # Escenario III: Incorrect Outputs
        if "expected" in request.context.lower():
            return self.INTENT_REFACTOR_LOGIC

        # 2. CLASIFICACIÓN SEMÁNTICA (LLM ligero)
        # Detectar frustración → priorizar debug
        sentiment = self._analyze_sentiment(request.idea)
        if sentiment == "negative" and "error" in request.idea.lower():
            return self.INTENT_DEBUG_VAGUE

        # Detectar verbos de optimización
        if any(verb in request.idea for verb in ["optimizar", "mejorar", "refactorizar"]):
            return self.INTENT_REFACTOR_LOGIC

        # Default: Text-to-Code
        return self.INTENT_GENERATE
```

### 3.2 NLaCBuilder (El Compilador)

**Responsabilidad:** Ensamblar PromptObject según estrategia

```python
class NLaCBuilder:
    """
    Compila prompts usando Role + RaR + Context Injection.
    Basado en DSPy (compilador) + MultiAIGCD (técnicas).
    """

    def build(self, request: NLaCRequest, intent: str) -> PromptObject:
        """Construir PromptObject estructurado"""

        # 1. Seleccionar estrategia según ComplexityAnalyzer + Intent
        complexity = self.complexity_analyzer.analyze(request.idea, request.context)
        strategy = self._select_strategy(complexity, intent)

        # 2. Role Injection (MultiAIGCD)
        role = self._inject_role(intent, complexity)

        # 3. Template con RaR si es complejo
        if strategy == "complex":
            template = self._build_rar_template(request, role)
        else:
            template = self._build_simple_template(request, role)

        # 4. Context Injection (Spider) si es SQL
        if self._is_sql_request(request):
            schema_context = self._prune_schema(request.inputs.schema_context)
            # Inyectar en inputs
            request.inputs.schema_context = schema_context

        return PromptObject(
            id=str(uuid.uuid4()),
            version="1.0",
            intent_type=intent,
            template=template,
            inputs=request.inputs,
            strategy_meta=strategy,
            constraints=request.inputs.constraints,
            verification=self._build_verification(intent)
        )

    def _inject_role(self, intent: str, complexity: str) -> str:
        """Inyectar rol experto (activa subespacios latentes)"""
        roles = {
            "debug_runtime": "Senior Debugging Expert",
            "refactor_logic": "Software Architect",
            "generate": "Full-Stack Developer"
        }
        return roles.get(intent, "Software Engineer")
```

### 3.3 OPOROptimizer (El Optimizador)

**Responsabilidad:** Mejorar template iterativamente con OPRO

```python
class OPOROptimizer:
    """
    Optimization by PROmpting (OPRO).
    Basado en papers de OPRO (Optimization by PROmpting).
    """

    MAX_ITERATIONS = 3  # Iteraciones fijas (control latencia)
    QUALITY_THRESHOLD = 1.0  # Early stopping si 100% pass

    def run_loop(self, prompt_obj: PromptObject) -> PromptObject:
        """Bucle OPRO con early stopping"""
        trajectory = []

        for i in range(self.MAX_ITERATIONS):
            # 1. Generar variación (meta-prompt + trajectory)
            candidate = self._generate_variation(prompt_obj, trajectory)

            # 2. Evaluar contra test_cases (Execution Accuracy)
            score, feedback = self._evaluate(candidate)

            # 3. Early stopping (quality threshold)
            if score >= self.QUALITY_THRESHOLD:
                return candidate  # Éxito total, salir

            # 4. Guardar trayectoria
            trajectory.append({
                "iteration": i,
                "prompt": candidate.template,
                "score": score,
                "feedback": feedback
            })

        # 5. Devolver mejor de la historia
        return self._get_best_from(trajectory)

    def _evaluate(self, prompt_obj: PromptObject) -> tuple[float, str]:
        """Evaluar prompt contra test_cases (Spider Execution Accuracy)"""
        # Ejecutar tests definidos en verification
        passed = 0
        total = len(prompt_obj.verification.get("tests", []))

        for test in prompt_obj.verification["tests"]:
            if self._run_test(prompt_obj, test):
                passed += 1

        score = passed / total if total > 0 else 0.0
        feedback = f"Passed {passed}/{total} tests"

        return score, feedback
```

### 3.4 PromptValidator (Linting + Autocorrección)

**Responsabilidad:** Validar restricciones y autocorregir (Reflexion)

```python
class PromptValidator:
    """
    Linter de prompts basado en IFEval + Reflexion loop.
    1 retry con autocorrección antes de fallback permisivo.
    """

    MAX_RETRIES = 1

    def validate(self, prompt_obj: PromptObject) -> tuple[bool, List[str]]:
        """Validar restricciones, retornar (passed, warnings)"""
        warnings = []

        # 1. Verificar restricciones de formato
        for constraint in prompt_obj.constraints:
            if constraint == "no_markdown" and "```" in prompt_obj.template:
                warnings.append("Contiene bloques markdown (prohibido)")

            if constraint == "json_only" and not self._is_json_ready(prompt_obj.template):
                warnings.append("No es JSON válido")

        # 2. Autocorrección si hay warnings
        if warnings and self._autocorrect(prompt_obj, warnings):
            # Re-validar después de corrección
            return self.validate(prompt_obj)

        # 3. Fallback permisivo
        passed = len(warnings) == 0
        return passed, warnings

    def _autocorrect(self, prompt_obj: PromptObject, warnings: List[str]) -> bool:
        """Intentar corrección automática (Reflexion loop)"""
        correction_prompt = f"""
Tu respuesta anterior falló por:
{chr(10).join(f'- {w}' for w in warnings)}

Corrige el prompt y responde solo con el JSON corregido.
"""
        # Llamada al LLM para corregir
        corrected = self._llm.correct(prompt_obj.template, correction_prompt)

        if corrected and self._is_valid_correction(corrected):
            prompt_obj.template = corrected
            return True

        return False
```

---

## 4. Integración con Strategy Pattern

Extensión del Strategy Pattern actual para soportar NLaC.

```python
class NLaCStrategy(PromptImproverStrategy):
    """
    Estrategia NLaC: Compilación + Optimización + Validación.
    Compatible con Strategy Pattern actual.
    """

    @property
    def name(self) -> str:
        return "nlac"

    @property
    def max_length(self) -> int:
        return 8000  # Más largo por metadata

    def _improve_with_strategy(self, original_idea: str, context: str) -> str:
        """Pipeline NLaC completo"""
        request = NLaCRequest(
            idea=original_idea,
            context=context,
            mode="nlac",
            high_quality=True  # Usar OPRO
        )

        # 1. Clasificar intención
        intent = self.classifier.classify(request)

        # 2. Construir PromptObject
        prompt_obj = self.builder.build(request, intent)

        # 3. Optimizar (OPRO loop)
        if request.high_quality:
            prompt_obj = self.optimizer.run_loop(prompt_obj)

        # 4. Validar + Autocorregir
        passed, warnings = self.validator.validate(prompt_obj)

        # 5. Renderizar (compilar template final)
        final_prompt = self._render_template(prompt_obj)

        # 6. Guardar en DB
        self._save_to_db(prompt_obj, warnings)

        return final_prompt

    def _render_template(self, prompt_obj: PromptObject) -> str:
        """Compilar template con valores"""
        # Reemplazar {{variable}} con valores de inputs
        rendered = prompt_obj.template
        for key, value in prompt_obj.inputs.dict().items():
            if value:
                rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered
```

---

## 5. Plan de Pruebas (Coverage ≥80%)

### 5.1 Unit Tests (Python)

```python
# tests/test_intent_classifier.py
def test_classifier_detects_debug_scenario_ii():
    """MultiAIGCD Scenario II: {Code + Error} → DEBUG"""
    request = NLaCRequest(
        idea="fix this",
        context="",
        inputs=NLaCInputs(
            instruction="fix",
            code_snippet="def foo():\n    bar()",
            error_log="NameError: name 'bar' is not defined"
        )
    )
    classifier = IntentClassifier()
    assert classifier.classify(request) == IntentClassifier.INTENT_DEBUG_RUNTIME

def test_classifier_hybrid_fallback_to_llm():
    """Si no hay señal estructural, usa análisis semántico"""
    request = NLaCRequest(
        idea="esto es un desastre, nada funciona",
        context="",
        inputs=NLaCInputs(instruction="esto es un desastre")
    )
    classifier = IntentClassifier()
    # Debe detectar frustración → DEBUG_VAGUE
    assert classifier.classify(request) == IntentClassifier.INTENT_DEBUG_VAGUE
```

### 5.2 Integration Tests (OPRO)

```python
# tests/test_opro_optimizer.py
def test_opro_trajectory_improves():
    """Verificar que el score tiende a subir"""
    prompt_obj = PromptObject(
        id="test-123",
        template="Escribe una función para {{task}}",
        inputs=NLaCInputs(instruction="Escribe función"),
        verification={"tests": [{"input": "sumar", "expected": "def sum(a,b)"}]}
    )

    optimizer = OPOROptimizer()
    result = optimizer.run_loop(prompt_obj)

    # Recuperar trayectoria de DB
    trajectory = db.get_opro_trajectory(result.id)

    # Verificar que score mejora o se mantiene
    scores = [t["score"] for t in trajectory]
    assert scores[-1] >= scores[0]  # No empeora

def test_opro_early_stopping():
    """Si score=100% en iteración 1, no continúa"""
    # Mock test para devolver score=1.0
    with mock.patch.object(optimizer, '_evaluate', return_value=(1.0, "Perfect")):
        result = optimizer.run_loop(prompt_obj)
        assert len(db.get_opro_trajectory(result.id)) == 1  # Solo 1 iteración
```

### 5.3 Prompt Regression Tests (HumanEval)

```python
# tests/test_prompt_regression.py
def test_humaneval_benchmarks():
    """
    Validar que prompts NLaC no rompen tareas básicas.
    Usa casos de HumanEval como 'sanity check'.
    """
    test_cases = [
        {
            "task": "Write a function to check if palindrome",
            "expected_behavior": "Must handle empty string, single char"
        },
        {
            "task": "Implement binary search",
            "expected_behavior": "Must handle unsorted input gracefully"
        }
    ]

    for case in test_cases:
        response = api.improve_prompt(NLaCRequest(idea=case["task"], mode="nlac"))

        # Validar comportamiento esperado
        validator = BehaviorValidator()
        assert validator.complies_with(response.improved_prompt, case["expected_behavior"])
```

---

## 6. Tareas de Implementación (Ordenadas)

### Fase 1: Schema + Storage (Base)
- [ ] Task 1.1: Crear migración SQLite con tablas prompts, test_cases, opro_trajectory, prompt_cache
- [ ] Task 1.2: Implementar modelos Pydantic (NLaCRequest, PromptObject, OptimizeResponse)
- [ ] Task 1.3: Tests de validación Pydantic (≥90% coverage)

### Fase 2: Core Modules
- [ ] Task 2.1: Implementar IntentClassifier (híbrido: reglas → LLM)
- [ ] Task 2.2: Implementar NLaCBuilder (Role + RaR + Context Injection)
- [ ] Task 2.3: Implementar OPOROptimizer (3 iteraciones + early stopping)
- [ ] Task 2.4: Implementar PromptValidator (IFEval + Reflexion loop)

### Fase 3: Integration
- [ ] Task 3.1: Extender Strategy Pattern con NLaCStrategy
- [ ] Task 3.2: Actualizar endpoint API con feature flag (?mode=nlac)
- [ ] Task 3.3: Implementar cache (SHA256 hash completo)

### Fase 4: Testing + Verification
- [ ] Task 4.1: Unit tests de todos los módulos (≥80% coverage)
- [ ] Task 4.2: Integration tests de OPRO trajectory
- [ ] Task 4.3: Prompt regression tests con HumanEval

---

## 7. Métricas de Éxito

| Métrica | Target | Validación |
|---------|--------|-------------|
| Test Coverage | ≥80% | `pytest --cov` |
| Prompt Accuracy (OPRO) | score ≥0.7 | Test cases pass rate |
| Latency Simple | <5s | 95th percentile |
| Latency Complex | <30s | 95th percentile |
| Cache Hit Rate | ≥40% | Para Simple strategy |
| Backward Compatibility | 100% | Legacy clients sin cambio |

---

## 8. Risks y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|-------------|
| Latencia OPRO | Alto | Max 3 iteraciones, early stopping |
| Costo LLM | Alto | Cache agresivo para Simple |
| Complejidad | Medio | Implementación incremental por fases |
| Storage overhead | Bajo | Reusar SQLite actual |

---

## Referencias

- **NLaC Foundation**: Prompting JSON, treating prompts as executable objects
- **MultiAIGCD**: Scenarios I, II, III (Lazy Prompting, Runtime Errors, Logic Errors)
- **OPRO Papers**: Optimization by PROmpting, meta-prompts with trajectory history
- **Spider Dataset**: Schema pruning, Execution Accuracy metrics
- **DSPy**: Few-shot compilation, KNN for example selection
- **IFEval**: Instruction following evaluation, constraints validation
- **HumanEval**: Benchmark regression testing para sanity checks
