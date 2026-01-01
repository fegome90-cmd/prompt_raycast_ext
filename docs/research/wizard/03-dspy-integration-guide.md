# DSPy Integration - Reduciendo el Wizard de 6 Pasos a 1

**Prioridad:** 🔴 CRÍTICA - Objetivo principal del proyecto
**Fuente:** Architect v3.2.0 + DSPy best practices + HemDov Audit Report
**Aplicabilidad:** Directamente aplicable a Raycast extension

---

## 🔴 CRITICAL: GAP IDENTIFICADO (Auditoría HemDov)

**Fecha del Hallazgo:** 2026-01-01
**Fuente:** `/Users/felipe_gonzalez/Developer/raycast_ext/docs/research/wizard/DSPy_Audit_Report.md`

### El Problema Crítico

```
DSPy HemDov Actual          Requerimiento Raycast
┌──────────────────┐         ┌──────────────────┐
│ Tool Selection   │   ≠      │ Prompt Improvement│
│ Tool Execution   │         │ (NO EXISTE)       │
│ Code Generation  │         │ Idea → Better     │
└──────────────────┘         └──────────────────┘
      ↓                              ↓
  Tool Routing              Prompt Enhancement
```

### Hechos del Informe

| Capability | Estado HemDov | Requerimiento Raycast |
|------------|---------------|----------------------|
| Tool Selection | ✅ Implementado | ❌ No necesario |
| Tool Execution | ✅ Implementado | ❌ No necesario |
| Code Generation | ✅ Implementado | ❌ No necesario |
| **Prompt Improvement** | ❌ **NO EXISTE** | ✅ **REQUERIDO** |

### Solución: Crear PromptImprover Module

**Estimación esfuerzo:** 8-16 horas
**ROI:** 🔥🔥🔥 MÁXIMO - Es el único componente faltante

**Componentes Reutilizables (del informe):**
- ✅ `LiteLLMDSPyAdapter` - 100% reutilizable
- ✅ `DSPyOptimizer` (BootstrapFewShot) - 90% reutilizable
- ✅ Test suites pattern - 100% reutilizable
- ✅ Settings infrastructure - 100% reutilizable

**Ver implementación completa en la sección [PromptImprover Module](#promptimprover-module) abajo.**

---

## 📋 Índice

1. [CRITICAL: GAP Identificado](#critical-gap-identificado) ← NUEVO
2. [Visión General](#visión-general)
3. [Análisis de Automatización](#análisis-de-automatización)
4. [Arquitectura DSPy](#arquitectura-dspy)
5. [PromptImprover Module](#promptimprover-module) ← NUEVO (MÁXIMO ROI)
6. [Signatures DSPy](#signatures-dspy)
7. [Implementación Paso a Paso](#implementación-paso-a-paso)
8. [One-Step Wizard](#one-step-wizard)
9. [Template Retrieval Augmented Generation](#template-retrieval-augmented-generation)
10. [Optimización y Teleprompting](#optimización-y-teleprompting)
11. [Integración con Ollama](#integración-con-ollama)
12. [Ejemplos Completo](#ejemplos-completo)

---

## Visión General

### El Problema

```
Wizard Actual: 6 Pasos = ~5-10 minutos del usuario

┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Step 1  │ → │ Step 2  │ → │ Step 3  │ → │ Step 4  │ → │ Step 5  │ → │ Step 6  │
│Objective│   │  Role   │   │Directive│   │Framework│   │Guardrail│   │ Save   │
│   60s   │   │   90s   │   │   60s   │   │   30s   │   │   40s   │   │   20s  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     ↓            ↓            ↓            ↓            ↓            ↓
   Usuario     Usuario      Usuario      Usuario      Usuario     Usuario
   escribe     espera       escribe     selecciona   escribe     confirma
```

### La Solución DSPy

```
Wizard DSPy: 1 Paso = ~10-30 segundos del usuario

┌─────────────────────────────────────────────────┐
│           Step 1: Describe tu objetivo          │
│                 Usuario escribe                 │
│                   ~10 segundos                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
        ┌─────────────────┐
        │   DSPy Engine   │
        │   (automático)  │
        └────────┬────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  Prompt completo generado: Role + Directive + Framework │
│                     + Guardrails                        │
│                  (~5-10 segundos LLM)                   │
└─────────────────────────────────────────────────────────┘
```

### Ahorro de Tiempo

| Métrica | Wizard 6 Pasos | Wizard DSPy | Ahorro |
|---------|---------------|-------------|--------|
| **Tiempo Usuario** | 5-10 min | 10-30s | **90-95%** |
| **Interacciones** | 12 clicks | 1 input | **92%** |
| **Decisión Parálisis** | Alta | Nula | **100%** |
| **Consistencia** | Variable | Alta | **+80%** |

---

## Análisis de Automatización

### Qué Puede Automatizar DSPy

| Step Original | Acción Usuario | Acción DSPy | % Automatizable |
|---------------|----------------|-------------|-----------------|
| **Step 0: Discovery** | Escribir objetivo | Automático | 95% |
| **Step 1: Objective** | Escribir objetivo | Requerido | 0% (input usuario) |
| **Step 2: Role** | Escribir/Seleccionar | Generar | 80% |
| **Step 3: Directive** | Escribir | Generar | 85% |
| **Step 4: Framework** | Seleccionar | Recomendar | 75% |
| **Step 5: Guardrails** | Escribir/Seleccionar | Generar | 80% |
| **Step 6: Assembly** | Revisar | Automático | 100% |

### Análisis Detallado

```python
# Análisis de automatización por componente

automation_analysis = {
    "Step 1 - Objective": {
        "user_action": "Escribir objetivo",
        "dspy_action": None,  # Requerido input del usuario
        "automation_potential": 0.0,
        "reason": "El objetivo es la intención del usuario, no se puede inventar"
    },

    "Step 2 - Role": {
        "user_action": "Escribir rol manualmente o seleccionar sugerencia",
        "dspy_action": "Generar rol basado en objetivo + few-shot examples",
        "automation_potential": 0.8,
        "reason": "DSPy puede inferir rol del dominio del objetivo con alta precisión"
    },

    "Step 3 - Directive": {
        "user_action": "Escribir directiva detallada",
        "dspy_action": "Generar directiva basada en objetivo + rol",
        "automation_potential": 0.85,
        "reason": "La directiva es una expansión estructurada del objetivo"
    },

    "Step 4 - Framework": {
        "user_action": "Seleccionar entre 4 opciones",
        "dspy_action": "Recomendar framework basado en complejidad",
        "automation_potential": 0.75,
        "reason": "Patrones claros: problemas secuenciales→CoT, exploratorios→ToT"
    },

    "Step 5 - Guardrails": {
        "user_action": "Escribir 3-5 restricciones",
        "dspy_action": "Generar guardrails contextuales",
        "automation_potential": 0.8,
        "reason": "Los guardrails siguen patrones predecibles por dominio"
    },

    "Step 6 - Assembly": {
        "user_action": "Revisar prompt final",
        "dspy_action": "Ensamblar componentes automáticamente",
        "automation_potential": 1.0,
        "reason": "Proceso puramente mecánico, sin decisión del usuario"
    }
}

# Automatización total: (0 + 0.8 + 0.85 + 0.75 + 0.8 + 1.0) / 6 = 70%
# Con RAG de templates: +15% = 85%
# Con optimización: +5% = 90%
```

### Lo Que NO Se Puede Automatizar

```typescript
// Requiere input del usuario
const non_automatable = {
  domain_expertise: "Conocimiento específico del dominio del usuario",
  preferences: "Preferencias personales de estilo",
  context: "Contexto específico del proyecto",
  constraints: "Restricciones únicas del entorno"
};

// Requiere validación del usuario
const requires_validation = {
  role_selection: "El usuario debe aprobar el rol generado",
  framework_choice: "Algunos usuarios prefieren frameworks específicos",
  guardrails: "Algunas restricciones son business-specific"
};
```

---

## Arquitectura DSPy

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DSPY WIZARD ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   USER       │    │  DSPY CORE   │    │  TEMPLATE    │             │
│  │   INPUT      │───→│   ENGINE     │←───│   LIBRARY    │             │
│  │  Objective   │    │              │    │  (174+ items)│             │
│  └──────────────┘    └──────┬───────┘    └──────────────┘             │
│                             │                                           │
│                             ↓                                           │
│                    ┌─────────────────┐                                 │
│                    │  DSPY Signatures│                                 │
│                    │  - Role         │                                 │
│                    │  - Directive    │                                 │
│                    │  - Framework    │                                 │
│                    │  - Guardrails   │                                 │
│                    └────────┬────────┘                                 │
│                             │                                           │
│                             ↓                                           │
│                    ┌─────────────────┐                                 │
│                    │  DSPY Programs  │                                 │
│                    │  - Chained      │                                 │
│                    │  - One-Step     │                                 │
│                    │  - Optimized    │                                 │
│                    └────────┬────────┘                                 │
│                             │                                           │
│                             ↓                                           │
│                    ┌─────────────────┐                                 │
│                    │   FINAL OUTPUT  │                                 │
│                    │  Complete Prompt│                                 │
│                    └─────────────────┘                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Componentes DSPy

```python
# 1. LLM Backend (Ollama)
class OllamaBackend(dspy.backends.LM):
    """DSPy backend para Ollama"""
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        super().__init__(model, base_url)
        self.model = model
        self.base_url = base_url

    def basic_request(self, prompt: str, **kwargs) -> str:
        """Usar /api/chat endpoint de Ollama"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert prompt engineer."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
        )
        return response.json()["message"]["content"]

# 2. Template Index (RAG)
class TemplateIndex:
    """Vector index para retrieval de templates"""
    def __init__(self, templates: List[SotaTemplate], embedder):
        self.templates = templates
        self.embedder = embedder
        self.embeddings = self._build_index()

    def search(self, query: str, k: int = 3) -> List[SotaTemplate]:
        """Buscar templates similares usando cosine similarity"""
        query_embedding = self.embedder.embed(query)
        similarities = cosine_similarity(self.embeddings, query_embedding)
        top_k = np.argsort(similarities)[-k:][::-1]
        return [self.templates[i] for i in top_k]

# 3. Quality Validator
class QualityValidator:
    """Validar calidad de prompts generados"""
    def validate(self, prompt: str) -> Dict[str, float]:
        return {
            "clarity": self._calculate_clarity(prompt),
            "completeness": self._check_completeness(prompt),
            "conciseness": self._check_conciseness(prompt),
            "overall": self._calculate_overall(prompt)
        }
```

---

## 🔥 PromptImprover Module - MÁXIMO ROI

**Basado en:** Auditoría HemDov DSPy (2026-01-01)
**Prioridad:** 🔴 CRÍTICA - Componente faltante identificado
**Esfuerzo estimado:** 8-16 horas
**ROI:** 🔥🔥🔥 MÁXIMO - Soluciona el GAP crítico

### El Problema

DSPy HemDov tiene:
- ✅ Tool Selection (Semantic Router)
- ✅ Tool Execution (Baseline + MultiStep)
- ✅ Code Generation
- ❌ **Prompt Improvement** ← **ESTE ES EL GAP**

### La Solución: PromptImprover DSPy Module

Crear un nuevo módulo DSPy específico para mejorar prompts desde ideas crudas.

#### Arquitectura del PromptImprover

```
┌─────────────────────────────────────────────────────────────┐
│                    Raycast Extension                         │
│  (Swift/TypeScript - Cliente)                               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI / Flask Server                     │
│  POST /api/v1/improve-prompt                                │
│  Body: {"idea": "...", "context": "..."}                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           PromptImprover DSPy Module (NUEVO)                │
│  Location: eval/src/dspy_prompt_improver.py                 │
│  - Signature: PromptImproverSignature                       │
│  - Module: PromptImprover (ChainOfThought)                  │
│  - Optimized: BootstrapFewShot con dataset de prompts       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LiteLLMDSPyAdapter (EXISTENTE - Reutilizar)     │
│  Location: hemdov/infrastructure/adapters/litellm_dspy...   │
│  - Soporta: Ollama, Gemini, DeepSeek, etc.                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LiteLLM or Ollama Direct                   │
└─────────────────────────────────────────────────────────────┘
```

### Paso 1: Crear Signature

**Archivo:** `hemdov/domain/dspy_modules/prompt_improver.py` (NUEVO)

```python
"""
Prompt Improver DSPy Signature

Based on HemDov DSPy patterns for prompt optimization.
"""
import dspy

class PromptImproverSignature(dspy.Signature):
    """
    Improve a user's raw idea into a high-quality, structured prompt.

    This signature transforms vague or incomplete ideas into State-of-the-Art (SOTA)
    prompts following the Architect pattern: Role + Directive + Framework + Guardrails.
    """

    # Input fields
    original_idea = dspy.InputField(
        desc="User's raw idea or objective that needs improvement"
    )

    context = dspy.InputField(
        desc="Additional context about the use case, audience, or constraints (optional)",
        default=""
    )

    # Optional: Few-shot examples for better quality
    examples = dspy.InputField(
        desc="Similar prompt examples for few-shot learning (optional)",
        default=None
    )

    # Output fields
    improved_prompt = dspy.OutputField(
        desc="Complete, structured SOTA prompt with role, directive, framework, and guardrails"
    )

    role = dspy.OutputField(
        desc="AI role description extracted from the improved prompt"
    )

    directive = dspy.OutputField(
        desc="Core directive/mission extracted from the improved prompt"
    )

    framework = dspy.OutputField(
        desc="Recommended reasoning framework (chain-of-thought, tree-of-thoughts, decomposition, role-playing)"
    )

    guardrails = dspy.OutputField(
        desc="List of 3-5 key constraints or guardrails"
    )

    reasoning = dspy.OutputField(
        desc="Explanation of why these improvements were made",
        default=None
    )

    confidence = dspy.OutputField(
        desc="Confidence score (0-1) in the quality of the improved prompt",
        default=None
    )
```

### Paso 2: Crear Module

**Archivo:** `eval/src/dspy_prompt_improver.py` (NUEVO)

```python
"""
Prompt Improver DSPy Module

Based on HemDov DSPy module patterns (BaselineExecutor, MultiStepExecutor).
"""
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature

class PromptImprover(dspy.Module):
    """
    DSPy Module for improving user ideas into high-quality prompts.

    Uses Chain of Thought to reason through the improvement process step by step.
    """

    def __init__(self, *, pass_back_context: list[str] = []):
        super().__init__()
        # Use ChainOfThought for better reasoning quality
        self.improver = dspy.ChainOfThought(PromptImproverSignature)

    def forward(self, original_idea: str, context: str = "") -> dspy.Prediction:
        """
        Improve a raw idea into a structured SOTA prompt.

        Args:
            original_idea: User's raw idea or objective
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails, reasoning
        """
        return self.improver(
            original_idea=original_idea,
            context=context
        )

# Alternative: Zero-shot version (faster)
class PromptImproverZeroShot(dspy.Module):
    """
    Zero-shot version of PromptImprover (faster, lower quality).
    """

    def __init__(self):
        super().__init__()
        self.improver = dspy.Predict(PromptImproverSignature)

    def forward(self, original_idea: str, context: str = "") -> dspy.Prediction:
        return self.improver(
            original_idea=original_idea,
            context=context
        )
```

### Paso 3: Crear Dataset de Entrenamiento

**Archivo:** `eval/src/dspy_prompt_dataset.py` (NUEVO)

```python
"""
Dataset for Prompt Improver training.

Following HemDov pattern from dspy_dataset.py
"""
import dspy

def load_prompt_improvement_examples() -> list[dspy.Example]:
    """
    Load examples of raw ideas → improved prompts.

    This dataset will be used for BootstrapFewShot optimization.
    """
    examples = [
        # Example 1: ADR Process
        dspy.Example(
            original_idea="Design ADR process",
            context="Software architecture team",
            improved_prompt="""**[ROLE & PERSONA]**
You are a World-Class Software Architect with over 20 years of experience leading complex digital transformations. You balance technical excellence with business acumen. Your communication is precise, your reasoning is transparent, and your decisions are traceable to first principles.

**[CORE DIRECTIVE]**
**Your ultimate mission is:** To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs). This is not about creating bureaucracy; it's about building a system of "durable, asynchronous communication" that safeguards the architectural integrity of our software as it evolves.

**[EXECUTION FRAMEWORK: Chain-of-Thought]**
You must use the Chain-of-Thought framework to structure your entire response...

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
*   Avoid jargon where possible. Explain complex ideas simply.
*   Prioritize what works in practice over theoretical perfection.
*   Every recommendation must be a concrete, actionable step.
*   The plan must consider integration with common developer tools like Git and Pull Requests.

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan.""",
            role="World-Class Software Architect...",
            directive="To design and detail a robust...",
            framework="chain-of-thought",
            guardrails=["Avoid jargon", "Prioritize pragmatism", "Actionable steps", "Git integration"]
        ).with_inputs("original_idea", "context"),

        # Example 2: Marketing Campaign
        dspy.Example(
            original_idea="Create marketing campaign",
            context="SaaS product launch",
            improved_prompt="""**[ROLE & PERSONA]**
You are a Senior Marketing Strategist with a decade of experience in launching global brands. You are data-driven, customer-obsessed, and an expert in digital channels. Your thinking is focused on ROI, brand positioning, and creating measurable impact. You must communicate with clarity and persuasive, executive-level language.

**[CORE DIRECTIVE]**
**Your ultimate mission is:** To create a comprehensive, multi-channel marketing plan for a new SaaS product launch. The goal is to maximize market penetration, generate 1,000 marketing-qualified leads (MQLs) in the first quarter, and establish a strong brand presence in a competitive landscape.

... [rest of structured prompt]
""",
            role="Senior Marketing Strategist...",
            directive="To create a comprehensive...",
            framework="chain-of-thought",
            guardrails=["Data-driven", "Budget-conscious", "Actionable steps"]
        ).with_inputs("original_idea", "context"),

        # Example 3: Research Proposal
        dspy.Example(
            original_idea="Write research proposal",
            context="Academic grant application",
            improved_prompt="""**[ROLE & PERSONA]**
You are a Lead Scientific Researcher with a Ph.D. in your field and a portfolio of peer-reviewed publications. You are meticulous, analytical, and deeply skeptical. Your reasoning must be based on evidence, logical deduction, and established scientific principles.

... [rest of structured prompt]
""",
            role="Lead Scientific Researcher...",
            directive="To develop a comprehensive research proposal...",
            framework="decomposition",
            guardrails=["Evidence-based", "Rigor", "Cite sources"]
        ).with_inputs("original_idea", "context"),

        # TODO: Add 10-20 more examples covering different domains:
        # - Code review
        # - API documentation
        # - User story creation
        # - Test strategy
        # - etc.
    ]

    return examples
```

### Paso 4: Optimización con BootstrapFewShot

**Archivo:** `eval/src/dspy_prompt_optimizer.py` (NUEVO)

```python
"""
Prompt Improver Optimizer

Following HemDov pattern from dspy_optimizer.py
"""
import dspy
from dspy.teleprompt import BootstrapFewShot
from eval.src.dspy_prompt_improver import PromptImprover
from eval.src.dspy_prompt_dataset import load_prompt_improvement_examples

def prompt_improver_metric(example, prediction, trace=None) -> float:
    """
    Metric to evaluate prompt improvement quality.

    Following HemDov's executor_production_metric pattern.
    """
    # 1. Must have all required components
    if not prediction.improved_prompt:
        return 0.0

    # 2. Must include role
    if not prediction.role or len(prediction.role) < 20:
        return 0.3

    # 3. Must include directive
    if not prediction.directive or len(prediction.directive) < 30:
        return 0.3

    # 4. Must include framework
    valid_frameworks = ["chain-of-thought", "tree-of-thoughts", "decomposition", "role-playing"]
    if not prediction.framework or prediction.framework.lower() not in valid_frameworks:
        return 0.3

    # 5. Must include guardrails
    if not prediction.guardrails or len(prediction.guardrails) < 2:
        return 0.5

    # 6. Check for structured format
    required_sections = ["ROLE", "DIRECTIVE", "FRAMEWORK", "GUARDRAILS"]
    has_sections = sum(1 for section in required_sections if section in prediction.improved_prompt.upper())

    if has_sections < 3:
        return 0.7

    # Perfect
    return 1.0

def compile_prompt_improver(
    baseline: PromptImprover,
    max_bootstrapped_demos: int = 5,
    max_labeled_demos: int = 3
) -> PromptImprover:
    """
    Compile PromptImprover using BootstrapFewShot optimization.

    This is the key step that makes DSPy powerful - it learns from examples.

    Args:
        baseline: Unoptimized PromptImprover module
        max_bootstrapped_demos: Maximum few-shot examples to generate
        max_labeled_demos: Maximum labeled examples to use

    Returns:
        Compiled (optimized) PromptImprover module
    """
    # Load training data
    trainset = load_prompt_improvement_examples()

    # Create optimizer
    optimizer = BootstrapFewShot(
        metric=prompt_improver_metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=min(max_labeled_demos, len(trainset))
    )

    # Compile (this may take a few minutes)
    print("Compiling PromptImprover with BootstrapFewShot...")
    compiled = optimizer.compile(baseline, trainset=trainset)
    print("Compilation complete!")

    return compiled
```

### Paso 5: API Endpoint (FastAPI)

**Archivo:** `api/endpoints/prompt_improver.py` (NUEVO)

```python
"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import dspy

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings

router = APIRouter(prefix="/api/v1", tags=["prompts"])

class ImprovePromptRequest(BaseModel):
    idea: str
    context: str = ""

class ImprovePromptResponse(BaseModel):
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: str | None = None
    confidence: float | None = None

# Initialize module (lazy loading)
_prompt_improver: PromptImprover | None = None

def get_prompt_improver(settings: Settings) -> PromptImprover:
    """Get or initialize PromptImprover module."""
    global _prompt_improver

    if _prompt_improver is None:
        # Initialize module
        improver = PromptImprover()

        # Load compiled version if available
        if settings.dspy_compiled_path:
            improver.load(settings.dspy_compiled_path)
        else:
            # Use uncompiled version
            pass

        _prompt_improver = improver

    return _prompt_improver

@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    POST /api/v1/improve-prompt
    {
        "idea": "Design ADR process",
        "context": "Software architecture team"
    }

    Response:
    {
        "improved_prompt": "**[ROLE & PERSONA]**\\nYou are...",
        "role": "World-Class Software Architect...",
        "directive": "To design and detail...",
        "framework": "chain-of-thought",
        "guardrails": ["Avoid jargon", "Prioritize pragmatism", ...],
        "reasoning": "Selected role for expertise...",
        "confidence": 0.87
    }
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(status_code=400, detail="Idea must be at least 5 characters")

    # Get module
    from hemdov.interfaces import container
    settings = container.get(Settings)
    improver = get_prompt_improver(settings)

    # Improve prompt
    try:
        result = improver(
            original_idea=request.idea,
            context=request.context
        )

        return ImprovePromptResponse(
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=result.guardrails.split("\n") if isinstance(result.guardrails, str) else result.guardrails,
            reasoning=getattr(result, 'reasoning', None),
            confidence=getattr(result, 'confidence', None)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt improvement failed: {str(e)}")
```

### Paso 6: Tests (TDD Pattern)

**Archivo:** `tests/test_dspy_prompt_improver.py` (NUEVO)

```python
"""
Tests for PromptImprover module.

Following HemDov TDD pattern (RED-GREEN-REFACTOR).
"""
import pytest
from unittest.mock import patch
from eval.src.dspy_prompt_improver import PromptImprover
from eval.src.dspy_prompt_dataset import load_prompt_improvement_examples

class TestPromptImprover:
    """Test suite for PromptImprover module."""

    def test_load_prompt_improvement_examples(self):
        """GREEN: Dataset should load at least 3 examples."""
        examples = load_prompt_improvement_examples()
        assert len(examples) >= 3
        assert all(hasattr(ex, 'original_idea') for ex in examples)
        assert all(hasattr(ex, 'improved_prompt') for ex in examples)

    @patch('dspy.settings')
    def test_prompt_improver_basic_call(self, mock_dspy_settings):
        """GREEN: Should improve a raw idea into structured prompt."""
        # Setup
        mock_dspy_settings.configure = lambda lm=None: None
        improver = PromptImprover()

        # Execute (with mock LM to avoid real calls in tests)
        # TODO: Add mock LM response

        # Assert
        # TODO: Verify output structure

    def test_prompt_improver_requires_idea(self):
        """RED: Empty idea should raise error."""
        improver = PromptImprover()

        with pytest.raises(ValueError, match="at least 5 characters"):
            improver(original_idea="   ", context="")

    def test_prompt_improver_output_format(self):
        """GREEN: Output should contain all required sections."""
        # TODO: Test that improved_prompt contains:
        # - ROLE section
        # - DIRECTIVE section
        # - FRAMEWORK section
        # - GUARDRAILS section
        pass

    @patch('dspy.settings')
    def test_compile_prompt_improver(self, mock_dspy_settings):
        """GREEN: Should compile with BootstrapFewShot."""
        # Setup
        mock_dspy_settings.configure = lambda lm=None: None
        from eval.src.dspy_prompt_improver import PromptImprover
        from eval.src.dspy_prompt_optimizer import compile_prompt_improver

        improver = PromptImprover()
        trainset = load_prompt_improvement_examples()

        # Execute
        # TODO: Mock the optimization process

        # Assert
        # TODO: Verify compiled module loads successfully

# Integration test
class TestPromptImproverIntegration:
    """Integration tests for PromptImprover."""

    @pytest.mark.integration
    def test_end_to_end_improvement(self):
        """GREEN: Full flow from idea to improved prompt."""
        # TODO: Test with real DSPy LM (Ollama)
        pass
```

### Paso 7: Integración con Raycast

Desde la extensión Raycast (TypeScript/Swift):

```typescript
// Raycast Extension - API Client
interface ImprovePromptRequest {
  idea: string;
  context?: string;
}

interface ImprovePromptResponse {
  improved_prompt: string;
  role: string;
  directive: string;
  framework: string;
  guardrails: string[];
  reasoning?: string;
  confidence?: number;
}

async function improvePrompt(idea: string, context?: string): Promise<ImprovePromptResponse> {
  const response = await fetch('http://localhost:8000/api/v1/improve-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea, context: context || '' })
  });

  if (!response.ok) {
    throw new Error(`Failed to improve prompt: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const result = await improvePrompt(
  "Design ADR process",
  "Software architecture team"
);

console.log(result.improved_prompt);
// → Complete structured prompt ready to use
```

### Resumen de Implementación

| Paso | Archivo | Esfuerzo | ROI |
|------|---------|----------|-----|
| 1. Signature | `hemdov/domain/dspy_modules/prompt_improver.py` | 1h | 🔥🔥🔥 |
| 2. Module | `eval/src/dspy_prompt_improver.py` | 1h | 🔥🔥🔥 |
| 3. Dataset | `eval/src/dspy_prompt_dataset.py` | 2h | 🔥🔥 |
| 4. Optimizer | `eval/src/dspy_prompt_optimizer.py` | 1h | 🔥🔥 |
| 5. API Endpoint | `api/endpoints/prompt_improver.py` | 2h | 🔥🔥 |
| 6. Tests | `tests/test_dspy_prompt_improver.py` | 2h | 🔥 |
| 7. Integration | Raycast extension | 2h | 🔥🔥 |
| **TOTAL** | | **8-16h** | **MÁXIMO** |

---

## Signatures DSPy

### 1. Role Signature

```python
import dspy

class RoleSignature(dspy.Signature):
    """
    Generar un rol de AI basado en el objetivo del usuario.

    El rol debe incluir:
    - Nivel de experiencia (ej: "senior", "expert")
    - Área de expertise (ej: "software architecture", "marketing")
    - Años de experiencia (si aplicable)
    - Estilo de comunicación (ej: "precise", "empathetic")
    """

    # Input
    objective = dspy.InputField(
        desc="User's high-level goal or objective"
    )

    # Contexto opcional (few-shot examples)
    context = dspy.InputField(
        desc="Similar roles from template library for context",
        default=None
    )

    # Output
    role = dspy.OutputField(
        desc="AI role description with expertise, experience, and communication style"
    )

    reasoning = dspy.OutputField(
        desc="Brief explanation of why this role fits the objective",
        default=None
    )

# Ejemplo de uso:
role_predictor = dspy.Predict(RoleSignature)
result = role_predictor(
    objective="Design a scalable ADR process for my team"
)

# Resultado esperado:
# result.role = "You are a World-Class Software Architect with over 20 years of experience..."
# result.reasoning = "This role requires technical expertise, leadership experience, and architectural thinking..."
```

### 2. Directive Signature

```python
class DirectiveSignature(dspy.Signature):
    """
    Generar una directiva basada en el objetivo y el rol.

    La directiva debe:
    - Comenzar con verbo de acción (ej: "design", "create", "develop")
    - Expandir el objetivo con detalles específicos
    - Incluir outcomes medibles cuando sea posible
    - Ser clara y concisa
    """

    # Inputs
    objective = dspy.InputField(
        desc="User's high-level goal"
    )

    role = dspy.InputField(
        desc="Selected AI role"
    )

    context = dspy.InputField(
        desc="Similar directives from templates",
        default=None
    )

    # Output
    directive = dspy.OutputField(
        desc="Core directive with specific actions and outcomes"
    )

    metrics = dspy.OutputField(
        desc="Measurable success criteria (if applicable)",
        default=None
    )

# Ejemplo de uso:
directive_predictor = dspy.Predict(DirectiveSignature)
result = directive_predictor(
    objective="Design a scalable ADR process",
    role="World-Class Software Architect with 20+ years experience"
)

# result.directive = "To design and detail a robust, scalable, and developer-friendly process..."
# result.metrics = ["Completion time < 2 weeks", "Team adoption rate > 80%"]
```

### 3. Framework Signature

```python
class FrameworkSignature(dspy.Signature):
    """
    Recomendar el framework de razonamiento apropiado.

    Frameworks disponibles:
    - Chain-of-Thought (CoT): Problemas secuenciales, lógica paso a paso
    - Tree of Thoughts (ToT): Exploración de opciones, trade-offs
    - Decomposition: Tareas complejas, sub-problemas
    - Role-Playing: Diálogos, simulaciones
    """

    # Inputs
    objective = dspy.InputField(
        desc="User's high-level goal"
    )

    directive = dspy.InputField(
        desc="Core directive (helps determine complexity)"
    )

    # Output
    framework = dspy.OutputField(
        desc="Best reasoning framework: CoT, ToT, Decomposition, or Role-Playing"
    )

    reasoning = dspy.OutputField(
        desc="Explanation of why this framework fits best"
    )

# Ejemplo de uso:
framework_predictor = dspy.Predict(FrameworkSignature)
result = framework_predictor(
    objective="Design a scalable ADR process",
    directive="To design and detail a robust process..."
)

# result.framework = "Chain-of-Thought"
# result.reasoning = "ADR design requires sequential, logical steps from analysis to implementation"
```

### 4. Guardrails Signature

```python
class GuardrailsSignature(dspy.Signature):
    """
    Generar guardrails contextuales basados en objetivo y framework.

    Los guardrails deben ser:
    - Relevantes para el dominio
    - Específicos y accionables
    - 3-5 en cantidad
    """

    # Inputs
    objective = dspy.InputField(
        desc="User's high-level goal"
    )

    framework = dspy.InputField(
        desc="Selected reasoning framework"
    )

    domain = dspy.InputField(
        desc="Domain hints (e.g., 'software', 'marketing', 'research')",
        default=None
    )

    # Output
    guardrails = dspy.OutputField(
        desc="List of 3-5 relevant, actionable constraints"
    )

    categories = dspy.OutputField(
        desc="Categories: quality, format, scope, safety",
        default=None
    )

# Ejemplo de uso:
guardrails_predictor = dspy.Predict(GuardrailsSignature)
result = guardrails_predictor(
    objective="Design a scalable ADR process",
    framework="Chain-of-Thought",
    domain="software architecture"
)

# result.guardrails = [
#   "Avoid jargon where possible. Explain complex ideas simply.",
#   "Prioritize what works in practice over theoretical perfection.",
#   "Every recommendation must be a concrete, actionable step.",
#   "Consider integration with existing tools like Git and PRs."
# ]
```

### 5. Unified One-Step Signature

```python
class UnifiedPromptGeneration(dspy.Signature):
    """
    Generar prompt completo en un solo paso.

    Esta es la signature definitiva que reemplaza los 6 pasos del wizard.
    """

    # Input único
    objective = dspy.InputField(
        desc="User's goal or task - the only required input"
    )

    # Contexto opcional (mejora calidad)
    examples = dspy.InputField(
        desc="Few-shot examples from similar templates",
        default=None
    )

    # Output completo
    role = dspy.OutputField(desc="AI role description")
    directive = dspy.OutputField(desc="Core directive")
    framework = dspy.OutputField(desc="Reasoning framework")
    guardrails = dspy.OutputField(desc="List of constraints")

    # Ensamblado final
    complete_prompt = dspy.OutputField(
        desc="Fully assembled SOTA prompt ready to use"
    )

    # Metadatos
    confidence = dspy.OutputField(
        desc="Confidence score (0-1) in the generated prompt",
        default=None
    )

# Ejemplo de uso:
one_step_predictor = dspy.Predict(UnifiedPromptGeneration)
result = one_step_predictor(
    objective="Design a scalable ADR process for my software team"
)

# result.contiene todos los componentes del prompt
```

---

## Implementación Paso a Paso

### Fase 1: Setup Inicial

```python
# 1. Instalar dependencias
# pip install dspy-ai
# pip install sentence-transformers  # Para embeddings locales

# 2. Configurar DSPy con Ollama
import dspy

# Configurar backend de Ollama
ollama_lm = dspy.OllamaLocal(
    model="llama3.1",
    base_url="http://localhost:11434",
    temperature=0.3  # Baja temperatura para más consistencia
)

dspy.settings.configure(lm=ollama_lm)

# 3. Cargar biblioteca de templates
from template_library import load_templates

templates = load_templates()  # 174+ templates
print(f"Loaded {len(templates)} templates")
```

### Fase 2: Template Index

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class TemplateIndex:
    """Vector index para búsqueda semántica de templates"""

    def __init__(self, templates: List[SotaTemplate]):
        self.templates = templates
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Embeddings locales
        self.embeddings = self._build_index()

    def _build_index(self) -> np.ndarray:
        """Pre-computar embeddings para todos los templates"""
        descriptions = [t.description for t in self.templates]
        embeddings = self.embedder.encode(descriptions)
        return embeddings

    def search(self, query: str, k: int = 3) -> List[SotaTemplate]:
        """Buscar k templates más similares"""
        # Embed query
        query_embedding = self.embedder.encode([query])[0]

        # Calcular cosine similarity
        similarities = np.dot(
            self.embeddings,
            query_embedding
        ) / (
            np.linalg.norm(self.embeddings, axis=1) *
            np.linalg.norm(query_embedding)
        )

        # Top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        # Retornar templates
        return [self.templates[i] for i in top_k_indices]

    def get_examples(self, query: str, k: int = 3) -> List[dspy.Example]:
        """Retornar templates como ejemplos DSPy"""
        templates = self.search(query, k)
        examples = []

        for t in templates:
            example = dspy.Example(
                objective=t.description,
                role=t.components.role.content,
                directive=t.components.directive.content,
                framework=t.components.framework.content,
                guardrails=[c.content for c in t.components.constraints]
            ).with_inputs("objective")  # Marcar objective como input
            examples.append(example)

        return examples

# Usar el índice
template_index = TemplateIndex(templates)

# Buscar templates similares
similar_templates = template_index.search("Design ADR process")
print(f"Found {len(similar_templates)} similar templates")
```

### Fase 3: Chained DSPy Program

```python
class ChainedPromptWizard(dspy.Module):
    """
    Programa DSPy que genera prompts paso a paso,
    usando templates como few-shot examples.
    """

    def __init__(self, template_index: TemplateIndex):
        super().__init__()
        self.template_index = template_index

        # Predictores para cada componente
        self.role_predictor = dspy.Predict(RoleSignature)
        self.directive_predictor = dspy.Predict(DirectiveSignature)
        self.framework_predictor = dspy.Predict(FrameworkSignature)
        self.guardrails_predictor = dspy.Predict(GuardrailsSignature)

    def forward(self, objective: str) -> dspy.Prediction:
        """Generar prompt completo desde objetivo"""

        # 1. Recuperar templates similares (RAG)
        similar_templates = self.template_index.search(objective, k=3)
        examples = self.template_index.get_examples(objective, k=3)

        # 2. Generar Role (con few-shot)
        role_result = self.role_predictor(
            objective=objective,
            context=[t.components.role.content for t in similar_templates]
        )

        # 3. Generar Directive (usando role)
        directive_result = self.directive_predictor(
            objective=objective,
            role=role_result.role,
            context=[t.components.directive.content for t in similar_templates]
        )

        # 4. Recomendar Framework
        framework_result = self.framework_predictor(
            objective=objective,
            directive=directive_result.directive
        )

        # 5. Generar Guardrails
        guardrails_result = self.guardrails_predictor(
            objective=objective,
            framework=framework_result.framework,
            domain=self._infer_domain(objective)
        )

        # 6. Ensamblar prompt final
        complete_prompt = self._assemble_prompt(
            role=role_result.role,
            directive=directive_result.directive,
            framework=framework_result.framework,
            guardrails=guardrails_result.guardrails
        )

        # Retornar predicción completa
        return dspy.Prediction(
            role=role_result.role,
            directive=directive_result.directive,
            framework=framework_result.framework,
            guardrails=guardrails_result.guardrails,
            complete_prompt=complete_prompt,
            confidence=self._calculate_confidence(
                role_result,
                directive_result,
                framework_result,
                guardrails_result
            )
        )

    def _infer_domain(self, objective: str) -> str:
        """Inferir dominio del objetivo"""
        keywords = {
            "software": ["code", "api", "architecture", "development", "programming"],
            "marketing": ["campaign", "brand", "audience", "leads", "conversion"],
            "research": ["study", "analysis", "data", "hypothesis", "experiment"],
            "writing": ["content", "article", "blog", "narrative", "story"]
        }

        objective_lower = objective.lower()
        for domain, kw in keywords.items():
            if any(k in objective_lower for k in kw):
                return domain
        return "general"

    def _assemble_prompt(self, role, directive, framework, guardrails) -> str:
        """Ensamblar prompt final con formato SOTA"""
        return f"""**[ROLE & PERSONA]**
{role}

**[CORE DIRECTIVE]**
**Your ultimate mission is:** {directive}

**[EXECUTION FRAMEWORK: {framework}]**
{self._get_framework_description(framework)}

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
{chr(10).join(f'*   {g}' for g in guardrails)}

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan. Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section. Use Markdown for formatting. Begin your response with a title for the plan."""

    def _get_framework_description(self, framework: str) -> str:
        """Descripción del framework seleccionado"""
        descriptions = {
            "Chain-of-Thought": "You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.",
            "Tree of Thoughts": "You must use the Tree of Thoughts framework to structure your entire response. Your output should explore multiple solution paths before converging on an optimal one.",
            "Decomposition": "You must use the Decomposition framework to break down the problem into smaller, manageable sub-problems and address each systematically.",
            "Role-Playing": "You must use the Role-Playing framework to simulate dialogues, user interactions, or scenarios relevant to the objective."
        }
        return descriptions.get(framework, "Use a systematic approach to problem-solving.")

    def _calculate_confidence(self, *results) -> float:
        """Calcular score de confianza"""
        # Simplificado: basado en longitud y completitud
        scores = []
        for r in results:
            if hasattr(r, 'confidence'):
                scores.append(r.confidence)
            else:
                scores.append(0.7)  # Default
        return sum(scores) / len(scores)
```

### Fase 4: Usar el Programa

```python
# Crear instancia del wizard
wizard = ChainedPromptWizard(template_index)

# Generar prompt desde objetivo
result = wizard(
    objective="Design a scalable ADR process for my software engineering team"
)

# Ver resultados
print("=== Generated Role ===")
print(result.role)

print("\n=== Generated Directive ===")
print(result.directive)

print("\n=== Selected Framework ===")
print(result.framework)

print("\n=== Generated Guardrails ===")
for g in result.guardrails:
    print(f"  - {g}")

print("\n=== Complete Prompt ===")
print(result.complete_prompt)

print(f"\nConfidence: {result.confidence:.2f}")
```

---

## One-Step Wizard

### Implementación Optimizada

```python
class OneStepWizard(dspy.Module):
    """
    Generar prompt completo en UN solo paso.

    Esta es la implementación definitiva que reduce el wizard de 6 pasos a 1.
    """

    def __init__(self, template_index: TemplateIndex):
        super().__init__()
        self.template_index = template_index

        # Un solo predictor que hace todo
        self.generator = dspy.Predict(UnifiedPromptGeneration)

    def forward(self, objective: str) -> dspy.Prediction:
        """Generar prompt completo en una sola llamada al LLM"""

        # 1. Recuperar ejemplos similares (RAG)
        examples = self.template_index.get_examples(objective, k=3)

        # 2. Generar TODO en una sola llamada
        result = self.generator(
            objective=objective,
            examples=examples  # Few-shot examples mejoran calidad
        )

        # 3. Ensamblar prompt si no viene ensamblado
        if not hasattr(result, 'complete_prompt') or not result.complete_prompt:
            result.complete_prompt = self._assemble_prompt(
                result.role,
                result.directive,
                result.framework,
                result.guardrails
            )

        return result

    def _assemble_prompt(self, role, directive, framework, guardrails) -> str:
        """Ensamblar prompt final (misma lógica que ChainedPromptWizard)"""
        # ... (código idéntico a ChainedPromptWizard._assemble_prompt)
        pass
```

### Comparación: Chained vs One-Step

| Aspecto | Chained | One-Step |
|---------|---------|----------|
| **LLM Calls** | 4 (role, directive, framework, guardrails) | 1 (unified) |
| **Tiempo** | ~8-12s | ~3-5s |
| **Calidad** | Alta (cada componente optimizado) | Media-Alta (depende de LLM) |
| **Costo** | 4x tokens | 1x tokens |
| **Debugging** | Fácil (cada componente aislado) | Difícil (todo junto) |
| **Uso Recomendado** | Alta calidad requerida | Velocidad prioritaria |

---

## Template Retrieval Augmented Generation

### RAG con DSPy

```python
class RAGPromptWizard(dspy.Module):
    """
    Wizard con Template Retrieval Augmented Generation.

    Combina:
    1. Recuperación de templates similares (RAG)
    2. Few-shot learning con templates recuperados
    3. Generación de componentes
    """

    def __init__(self, template_index: TemplateIndex, k: int = 3):
        super().__init__()
        self.template_index = template_index
        self.k = k  # Número de templates a recuperar

        # Usar Chain of Thought para mejor razonamiento
        self.generator = dspy.ChainOfThought(UnifiedPromptGeneration)

    def forward(self, objective: str) -> dspy.Prediction:
        """Generar prompt con RAG"""

        # 1. Recuperar templates similares
        similar_templates = self.template_index.search(objective, k=self.k)

        # 2. Construir contexto con examples
        context = self._build_context(similar_templates)

        # 3. Generar con CoT (razonamiento visible)
        result = self.generator(
            objective=objective,
            context=context
        )

        # 4. Ensamblar prompt
        result.complete_prompt = self._assemble_prompt(
            result.role,
            result.directive,
            result.framework,
            result.guardrails
        )

        return result

    def _build_context(self, templates: List[SotaTemplate]) -> str:
        """Construir contexto con few-shot examples"""
        context_parts = []

        for i, t in enumerate(templates, 1):
            context_parts.append(f"""
Example {i}:
Objective: {t.description}
Role: {t.components.role.content}
Directive: {t.components.directive.content}
Framework: {t.components.framework.content}
Guardrails: {[c.content for c in t.components.constraints]}
""")

        return "\n".join(context_parts)
```

---

## Optimización y Teleprompting

### DSPy Teleprompters

```python
# 1. BootstrapFewShot - Aprende de ejemplos
from dspy.teleprompt import BootstrapFewShot

# Crear dataset de entrenamiento desde templates
trainset = []
for template in templates:
    trainset.append(
        dspy.Example(
            objective=template.description,
            role=template.components.role.content,
            directive=template.components.directive.content,
            framework=template.components.framework.content,
            guardrails=[c.content for c in template.components.constraints]
        ).with_inputs("objective")
    )

# Configurar teleprompter
teleprompter = BootstrapFewShot(
    max_bootstrapped_demos=5,  # Máximo 5 few-shot examples
    max_labeled_demos=3,        # Máximo 3 ejemplos etiquetados
    teacher_settings=dict(lm=dspy.OllamaLocal(model="llama3.1"))
)

# Optimizar programa
base_wizard = OneStepWizard(template_index)
optimized_wizard = teleprompter.compile(
    base_wizard,
    trainset=trainset[:50]  # Usar primeros 50 templates
)

# 2. K-NN FewShot - Retrieval dinámico
from dspy.teleprompt import KNNFewShot

knn_teleprompter = KNNFewShot(k=3)  # Usar 3 nearest neighbors
knn_wizard = knn_teleprompter.compile(
    base_wizard,
    trainset=trainset
)

# Usar wizard optimizado
result = optimized_wizard(objective="Design ADR process")
```

---

## Integración con Ollama

### Configuración Completa

```python
import dspy
from dspy import OllamaLocal

# Configurar Ollama
ollama = OllamaLocal(
    model="llama3.1",  # o "mistral", "codellama", etc.
    base_url="http://localhost:11434",
    temperature=0.3,
    max_tokens=2000
)

dspy.settings.configure(lm=ollama)

# Crear wizard
template_index = TemplateIndex(templates)
wizard = OneStepWizard(template_index)

# Generar prompt
result = wizard(
    objective="Design a scalable ADR process for my team"
)

print(result.complete_prompt)
```

### Modelos Ollama Recomendados

| Modelo | Parámetros | Use Case | Ventajas |
|--------|-----------|----------|----------|
| **llama3.1** | 8B | General | Balance calidad/velocidad |
| **mistral** | 7B | General | Más rápido que llama |
| **codellama** | 13B/34B | Código | Especializado en technical prompts |
| **yam-34b** | 34B | Alta calidad | Mejor razonamiento |

---

## Ejemplos Completo

### Ejemplo 1: ADR Process

```python
# Input
objective = "Design a scalable ADR process for my software engineering team"

# Generar
result = wizard(objective=objective)

# Output
print(result.complete_prompt)
```

**Resultado esperado:**

```
**[ROLE & PERSONA]**
You are a World-Class Software Architect with over 20 years of experience leading complex digital transformations. You balance technical excellence with business acumen. Your communication is precise, your reasoning is transparent, and your decisions are traceable to first principles.

**[CORE DIRECTIVE]**
**Your ultimate mission is:** To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs). This is not about creating bureaucracy; it's about building a system of "durable, asynchronous communication" that safeguards the architectural integrity of our software as it evolves.

**[EXECUTION FRAMEWORK: Chain-of-Thought]**
You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.

1. **Synthesize the "Why":** Begin with a high-level strategic analysis.
2. **Deconstruct the Problem:** Break down the core directive into its essential components.
3. **Design the Solution - Step-by-Step:** Address each component with a detailed solution.
4. **Synthesize and Plan:** Consolidate the solutions into a cohesive, actionable implementation plan.

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
*   Avoid jargon where possible. Explain complex ideas simply.
*   Prioritize what works in practice over theoretical perfection.
*   Every recommendation must be a concrete, actionable step.
*   The plan must consider integration with common developer tools like Git and Pull Requests.

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan. Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section. Use Markdown for formatting. Begin your response with a title for the plan.
```

### Ejemplo 2: Marketing Campaign

```python
# Input
objective = "Create a marketing campaign to launch a new SaaS product to SMBs"

# Generar
result = wizard(objective=objective)

# Output
# ... (prompt completo con role de marketing strategist, framework CoT, etc.)
```

---

## Resumen de Implementación

### Roadmap de Implementación

```
Phase 1: Setup (1 día)
├─ Instalar DSPy y dependencias
├─ Configurar Ollama backend
└─ Cargar biblioteca de templates

Phase 2: Template Index (1 día)
├─ Crear TemplateIndex con embeddings
├─ Implementar búsqueda semántica
└─ Testear recuperación de templates

Phase 3: Signatures DSPy (2 días)
├─ Implementar RoleSignature
├─ Implementar DirectiveSignature
├─ Implementar FrameworkSignature
├─ Implementar GuardrailsSignature
└─ Implementar UnifiedPromptGeneration

Phase 4: Programs (2 días)
├─ ChainedPromptWizard (4 pasos)
├─ OneStepWizard (1 paso)
└─ RAGPromptWizard (con retrieval)

Phase 5: Optimización (2 días)
├─ BootstrapFewShot teleprompter
├─ KNNFewShot teleprompter
└─ Evaluar y comparar resultados

Phase 6: Integración Raycast (2 días)
├─ Crear UI de 1 solo input
├─ Conectar con backend DSPy
└─ Testing end-to-end

Total: ~10 días
```

---

**Próximos documentos:**
- `04-prompt-assembly-patterns.md` - Patrones de ensamblaje
- `05-quality-validation-system.md` - Validación de calidad
