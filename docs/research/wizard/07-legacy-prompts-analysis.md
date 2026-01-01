# 🏆 Análisis: Mina de Oro de Prompts Legacy

**Fecha:** 2026-01-01
**Fecha Corrección:** 2026-01-01 (CRÍTICO: Estrategia corregida)
**Ubicación:** `/Users/felipe_gonzalez/Developer/promtassss-main/docs/legacy/inventario-documental-collection`
**Descubrimiento:** 1,188 archivos únicos, 362 con "PROMPT" en el nombre

---

## ⚠️ CRÍTICO: Corrección Estratégica

**PROBLEMA IDENTIFICADO:** Los prompts legacy NO son training data directo para DSPy.

**Por qué:**
- DSPy necesita pares: `(idea_cruda → prompt_mejorado)`
- Los agentes legacy son SOLO `prompt_mejorado` (ya estructurados)
- Nos falta el `idea_cruda` (input del usuario)
- **Inventar inputs = training data sintético, NO real**

**Uso CORRECTO de legacy:**
- ❌ **NO:** Convertir agentes directamente a ejemplos DSPy
- ✅ **SÍ:** Extraer COMPONENTES production-proven (roles, directives, frameworks)
- ✅ **SÍ:** Usar componentes como building blocks para ejemplos sintéticos MEJORES

---

## 🚀 Impacto Inmediato (CORREGIDO)

### Antes del Descubrimiento
- Dataset base planeado: 10 ejemplos (7 horas de trabajo manual)
- Fuentes conocidas: 4 templates en `simulation/db.ts` + 30 componentes

### Después del Descubrimiento (Con Corrección)
- **Potencial real: Componentes para 50-100 ejemplos sintéticos de ALTA calidad**
- **Diversidad masiva:** sprints, agentes, workflows, arquitectura, testing, seguridad
- **Calidad verificada:** Componentes usados en producción con validación

**ROI:** 5-10x mejora en CALIDAD de ejemplos sintéticos (no en cantidad)

### Mitos Aclarados
| Mito | Realidad |
|------|----------|
| "200-500 ejemplos listos" | NO - Solo componentes, no ejemplos completos |
| "Conversión directa" | NO - Requiere construcción de ejemplos sintéticos |
| "Training data real" | NO - Inputs siempre inventados (aunque realistas) |

---

## 🔴 El GAP Fundamental

### Qué necesita DSPy vs Qué tiene legacy

```
┌─────────────────────────────────────────────────────────────┐
│ DSPy NECESITA (Training Data)                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: "Design system architecture"  ← Idea CRUDA del usuario│
│                                                              │
│  OUTPUT: "You are a World-Class Architect...               │
│          Your mission is to design..."  ← Prompt MEJORADO   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓ aprende transformación

┌─────────────────────────────────────────────────────────────┐
│ LEGACY AGENTS (Solo OUTPUT)                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  "You are an expert AI System Architect.                    │
│   Your task is to analyze requirements..."                  │
│                                                              │
│  ❌ NO HAY INPUT (idea cruda del usuario)                   │
│  ❌ Solo existe el prompt final                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓ NO sirve como training data directo
```

**Conclusión:** Los agentes legacy son PROMPTS COMPLETOS, no ejemplos de transformación.

---

## 📊 Inventario Completo (CORREGIDO)

### Resumen Numérico REALISTA

| Categoría | Cantidad | Componentes Extraíbles | Esfuerzo |
|-----------|----------|----------------------|----------|
| **Total Archivos** | 1,188 | - | - |
| **Archivos "PROMPT"** | 362 | ~150 útiles con componentes | 30-50h |
| **CodeMachine Agents** | 22 | 22 agentes = 22 roles + 22 directives | 8-10h |
| **Agentes Especializados** | 15 | 15 agentes = 15 roles completos | 3-5h |
| **Sprint Prompts** | 45 | 30 con metadata rica | 10-15h |
| **Workflows** | 18 | 15 frameworks implícitos | 5-8h |
| **Templates Varios** | 50+ | 40 con estructuras útiles | 15-20h |

**Total Estimado:** 50-100 ejemplos sintéticos de ALTA calidad con 50-80 horas de trabajo

---

## 🗂️ Tipos de Prompts Identificados

### Tipo 1: CodeMachine Agents (22 archivos)
**Ubicación:** `codemachine-cli/prompts/templates/codemachine/agents/`

**Características:**
- Estructura semi-SOTA: "You are an expert X"
- Input/Output claramente definidos
- Output structure detallado
- Ejemplos concretos

**Agentes disponibles:**
1. `01-architecture-agent.md` - System Architecture Blueprint
2. `02-planning-agent.md` - Implementation Planning
3. `03-task-breakdown-agent.md` - Task Decomposition
4. `04-context-manager-agent.md` - Context Management
5. `05-code-generation-agent.md` - Code Generation (2-phase)
6. `06-task-validation-agent.md` - Task Validation
7. `07-runtime-preparation-agent.md` - Runtime Preparation

**Valor para Dataset:** ⭐⭐⭐⭐ ALTO (como FUENTE DE COMPONENTES)
- Roles production-proven
- Directivas validadas en producción
- Frameworks implícitos extraíbles
- Guardrails claros

**❌ NO es training data directo:** Solo output, sin input del usuario

**✅ Uso CORRECTO:** Extraer componentes para construir ejemplos sintéticos
```
Agente Legacy → Extraer role + directive + framework + guardrails
                           ↓
            Combinar con INPUT realista (inventado)
                           ↓
                  Ejemplo DSPy VÁLIDO
```

### Tipo 2: Agentes Especializados (15 archivos)
**Ubicación:** `agents/memtech/`, `agents/guardian/`, `agents/prompting/`

**Características:**
- Estructura operativa clara: Rol, Propósito, Instrucciones
- Contrato de salida JSON obligatorio
- Estándares de operación explícitos

**Agentes disponibles:**
1. `memtech/prompt.md` - Memory Management Technician
2. `guardian/templates/audit-report-template.md` - Security Audit
3. `prompting/agent.js` - Prompting Agent
4. `mac-maintenance-agent-prompt.md` - Mac Maintenance

**Valor para Dataset:** ⭐⭐⭐⭐ ALTO (como FUENTE DE COMPONENTES)
- Dominios especializados (memoria, seguridad, infra)
- Roles muy específicos y probados
- Guardrails operativos reales

**❌ NO es training data directo:** Solo output, sin input del usuario

**✅ Uso CORRECTO:** Extraer componentes especializados para dominios nicho

### Tipo 3: Sprint/Project Prompts (45 archivos)
**Ubicación:** `core/surprise-metrics/`, `sprints/`, raíz `files/`

**Características:**
- Frontmatter YAML extenso con metadata
- Estructura libre después del YAML
- Validación score (95+ en muchos)
- Success criteria explícitos

**Ejemplos:**
- `PROMPT-SPRINT-13-MEMTECH-AGENT-v1.0.0.md` - MemTech Agent Sprint
- `PROMPT-SPRINT-15-REFINAMIENTO-MEMTECH-v1.0.0.md` - Memory Refinement
- `PROMPT-sprint-14-mejorado-v1.0.0.md` - Improved Sprint 14
- `PROMPT-SPRINT-12-OPTIMIZACION-MEMORIA-INTEGRADA-v1.0.0.md` - Memory Optimization

**Valor para Dataset:** ⭐⭐⭐ ALTO
- Metadata rica (complexity, innovation_level, business_value)
- Validados en producción (sprints reales)
- Diversos dominios (infraestructura, memoria, testing)

**Conversión:** REQUIERE TRANSFORMACIÓN - Extraer del YAML + generar estructura SOTA

### Tipo 4: Workflow Prompts (18 archivos)
**Ubicación:** `codemachine-cli/prompts/templates/codemachine/workflows/`

**Características:**
- Pasos secuenciales claramente definidos
- Input/Output por paso
- Fallback strategies

**Workflows disponibles:**
1. `task-verification-workflow.md` - Task Verification
2. `cleanup-code-fallback-workflow.md` - Code Cleanup
3. `git-commit-workflow.md` - Git Commits

**Valor para Dataset:** ⭐⭐⭐⭐ MUY ALTO
- Framework implícito (pasos secuenciales = CoT)
- Fallbacks (guardrails)
- Reales y probados

**Conversión:** DIRECTA - Pasos → `framework: Chain-of-Thought`

### Tipo 5: Output Format Templates (10 archivos)
**Ubicación:** `codemachine-cli/prompts/templates/codemachine/output-formats/`

**Características:**
- Solo definen estructura de output
- Sin rol ni directiva
- Útiles como componentes

**Valor para Dataset:** ⭐⭐ MEDIO
- Complementan otros prompts
- No suficientes por sí solos

**Conversión:** COMPONENTES - Usar como `directive` parcial

---

## 🔄 Estrategia CORREGIDA: Extracción de Componentes

### Principio General (CORREGIDO)

**Los agentes legacy NO son training data. Son FUENTE DE COMPONENTES.**

```
Agente Legacy (Prompt completo production-proven)
         ↓
    Extraer Componentes
    - role (producción probada)
    - directive (validada)
    - framework (inferido del contexto)
    - guardrails (reales)
         ↓
    Construir Ejemplo Sintético
    - INPUT: Inventado (realista basado en propósito del agente)
    - OUTPUT: Ensamblado desde componentes extraídos
         ↓
    Ejemplo DSPy VÁLIDO
    - Input/Output pair completo
    - Components production-proven
```

### Proceso CORREGIDO Paso a Paso

#### Paso 1: Extraer Componentes del Agente Legacy

```python
def extract_components_from_agent(agent_path: str) -> Components:
    """
    Extrae role, directive, framework, guardrails de un agente legacy.
    NOTA: Esto NO crea un ejemplo DSPy, solo extrae building blocks.
    """
    content = read_file(agent_path)

    return {
        "role": extract_role(content),           # "You are a World-Class..."
        "directive": extract_directive(content),  # "Your ultimate mission..."
        "framework": infer_framework(content),    # "Chain-of-Thought", "Tree-of-Thoughts"
        "guardrails": extract_constraints(content) # Lista de restricciones
    }
```

#### Paso 2: Generar Input Realista

**TRUCO:** Basar el input en el PROPÓSITO del agente (no en el nombre del archivo)

```python
def generate_realistic_input(agent_path: str, components: Components) -> str:
    """
    Genera un input realista basado en el propósito del agente.
    Este input representa lo que un usuario REAL diría.
    """
    filename = basename(agent_path)
    content = read_file(agent_path)

    # Extraer propósito del agente
    purpose = extract_purpose(content)

    # Generar input basado en propósito (NO inventar aleatoriamente)
    realistic_inputs = {
        "01-architecture-agent": "Design system architecture for my startup",
        "05-code-generation-agent": "Create authentication module in Python",
        "memtech/prompt": "Monitor memory health of production systems",
        # ... mapeo propósito → input realista
    }

    return realistic_inputs.get(filename, generate_from_purpose(purpose))
```

#### Paso 3: Construir Ejemplo DSPy VÁLIDO

```python
def build_synthetic_example(agent_path: str) -> dspy.Example:
    """
    Construye un ejemplo DSPy VÁLIDO usando componentes del agente legacy.
    """
    # 1. Extraer componentes production-proven
    components = extract_components_from_agent(agent_path)

    # 2. Generar input realista (basado en propósito del agente)
    original_idea = generate_realistic_input(agent_path, components)

    # 3. Ensamblar prompt mejorado usando componentes extraídos
    improved_prompt = assemble_final_prompt(components)

    # 4. Crear ejemplo DSPy VÁLIDO (con input y output)
    return dspy.Example(
        original_idea=original_idea,      # Input: Realista (inventado)
        context="",
        improved_prompt=improved_prompt,  # Output: Production-proven
        role=components["role"],
        directive=components["directive"],
        framework=components["framework"],
        guardrails=components["guardrails"],
        reasoning=f"Built from production-proven components of {basename(agent_path)}",
        confidence=0.85  # Alta confianza: components son production-proven
    ).with_inputs("original_idea", "context")
```

### Comparación: Estrategia INCORRECTA vs CORRECTA

```
❌ ESTRATEGIA INCORRECTA (Análisis original):
Agente Legacy → Copiar directamente → Ejemplo DSPy
PROBLEMA: Falta input (idea cruda)

✅ ESTRATEGIA CORRECTA (Análisis corregido):
Agente Legacy → Extraer componentes + Generar input → Ejemplo DSPy
BENEFICIO: Components production-proven + Input realista
```

---

## 📋 Plan de Acción CORREGIDO

### Opción Recomendada: Dataset Híbrido con Componentes Legacy

**NO reemplazar estrategia base - COMPLEMENTARLA con componentes de MEJOR CALIDAD.**

```
DATASET BASE (10 ejemplos)
├─ 3 de promptass (simulation/db.ts)  ← YA PLANEADO
├─ 7 sintéticos nuevos                ← YA PLANEADO
└─ Calidad: Media (components nuevos)

DATASET EXPANDIDO (25 ejemplos)
├─ 10 de Dataset Base                 ← COMPLETAR
├─ 15 sintéticos desde componentes legacy  ← NUEVO: componentes production-proven
│  ├─ 5 desde CodeMachine agents (arquitectura, código)
│  ├─ 5 desde agentes especializados (memtech, seguridad)
│  └─ 5 desde workflows (frameworks CoT)
└─ Calidad: ALTA (mejor que base)

DATASET ROBUSTO (50+ ejemplos) - OPCIONAL
├─ 25 de Dataset Expandido            ← COMPLETAR
├─ 25+ sintéticos desde más legacy     ← SOLO si tiempo disponible
└─ Calidad: MUY ALTA (diversidad máxima)
```

### Cronograma Actualizado

**Semana 1: Dataset Base (10) - Sin Legacy**
- Día 1-2: Completar 10 ejemplos base (3 sintéticos + 4 promptass + 3 existentes)
- Día 3: Validación y testing inicial

**Semana 2: Componentes Legacy (15 adicionales)**
- Día 4-5: Extraer componentes de 10 CodeMachine agents
- Día 6-7: Extraer componentes de 5 agentes especializados
- Construir 15 ejemplos sintéticos con components production-proven

**Semana 3: Integración y Testing**
- Día 8-10: Testing con dataset expandido (25 ejemplos)
- Día 11-12: Ajuste de hiperparámetros DSPy
- Día 13-14: Validación final de calidad

**Total:** 25 ejemplos de ALTA calidad en ~14 días

---

## 🎯 Ejemplo CORREGIDO: Construcción desde Componentes

### Paso 1: Agente Legacy Original

```markdown
# CODE GENERATION WORKFLOW

**CRITICAL: You MUST complete BOTH phases in sequence:**
1. First, complete PHASE 1 (Strategic Planning)
2. Then, immediately proceed to PHASE 2 (Implementation)

Do not stop after Phase 1. Both phases are required for task completion.

---

# PHASE 1: STRATEGIC PLANNING

You are an expert Problem-Solving Strategist. Your sole task is to analyze the problem provided below and generate a comprehensive, step-by-step guide on the **optimal methodology** for solving it.
...
```

### Paso 2: Extraer Componentes

```python
components = {
    "role": "You are an expert Problem-Solving Strategist with deep expertise in algorithm design, data structures, and development best practices.",
    "directive": "Analyze the problem and generate a comprehensive, step-by-step guide on the optimal methodology for solving it, covering problem understanding, approach selection, data structures, implementation plan, and best practices.",
    "framework": "Two-Phase Planning (Strategic Planning → Implementation)",
    "guardrails": [
        "Work on ONLY the single task specified",
        "Plan before executing",
        "Follow design instructions",
        "Aim for acceptance criteria"
    ]
}
```

### Paso 3: Generar Input Realista

```python
# Basado en el propósito del agente (code generation)
original_idea = "Create a user authentication system with login and registration"
```

### Paso 4: Construir Ejemplo DSPy VÁLIDO

```python
dspy.Example(
    # INPUT: Idea cruda del usuario (realista)
    original_idea="Create a user authentication system with login and registration",
    context="Need to support email/password and OAuth",

    # OUTPUT: Prompt ensamblado desde components production-proven
    improved_prompt="""
**[ROLE & PERSONA]**
You are an **Expert Problem-Solving Strategist** with deep expertise in algorithm design, data structures, and software development best practices. Your communication is methodical, thorough, and always focused on optimal solutions.

**[CORE DIRECTIVE]**
**Your ultimate mission is:** To analyze the provided requirements and generate a comprehensive, step-by-step guide on the optimal methodology for implementing the solution, covering problem understanding, approach selection, data structures, implementation plan, key considerations, and testing strategy.

**[EXECUTION FRAMEWORK: Two-Phase Planning]**
You must structure your work in two distinct phases:
1. **PHASE 1: Strategic Planning** - Analyze the problem and generate methodology
2. **PHASE 2: Implementation** - Execute the methodology to produce the actual solution

**[CONSTRAINTS & GUARDRAILS]**
*   **Single-Task Focus:** Work on ONLY the single task specified
*   **Plan Before Execute:** Always plan your approach before coding
*   **Follow Design:** Adhere to design instructions and requirements
*   **Acceptance Criteria:** Ensure your solution meets all specified criteria
*   **Best Practices:** Apply industry-standard patterns and practices

**[FINAL OUTPUT]**
Generate the complete solution following the two-phase framework above.
""",

    # COMPONENTS (para DSPy)
    role="You are an **Expert Problem-Solving Strategist** with deep expertise...",
    directive="To analyze requirements and generate comprehensive methodology...",
    framework="Two-Phase Planning",
    guardrails=[
        "Single-Task Focus: Work on ONLY the specified task",
        "Plan Before Execute: Always plan before coding",
        "Follow Design: Adhere to requirements",
        "Acceptance Criteria: Meet all specified criteria",
        "Best Practices: Apply industry-standard patterns"
    ],

    # METADATA
    reasoning="Built from production-proven components of CodeMachine 05-code-generation-agent.md",
    confidence=0.88  # Alta: components usados en producción real
).with_inputs("original_idea", "context")
```

**Resultado:** Ejemplo VÁLIDO con input realista + output production-proven

---

## 🚨 Antipatrices Corregidas

### ❌ Antipatrón 1: Conversión Directa (Mi error original)

```python
# ❌ MAL: Copiar agente directamente como ejemplo
def convert_legacy_to_dspy_wrong(agent_path: str):
    agent_content = read_file(agent_path)

    return dspy.Example(
        original_idea="",  # ¿De dónde sale? INVENTADO
        improved_prompt=agent_content,  # Solo output, sin transformación
        # ...
    )

# PROBLEMA: DSPy no aprende el patrón de transformación
```

### ✅ Patrón 1: Extracción de Componentes

```python
# ✅ BIEN: Extraer components y construir ejemplo válido
def build_example_from_components(agent_path: str):
    components = extract_components_from_agent(agent_path)
    original_idea = generate_realistic_input(agent_path, components)
    improved_prompt = assemble_final_prompt(components)

    return dspy.Example(
        original_idea=original_idea,      # Realista (basado en propósito)
        improved_prompt=improved_prompt,  # Ensamblado desde components
        role=components["role"],
        directive=components["directive"],
        # ...
    )

# BENEFICIO: DSPy aprende transformación + components production-proven
```

---

## 📈 Impacto en Métricas (CORREGIDO)

### Sin Componentes Legacy (Estrategia Original)

| Métrica | Target Base | Target Expandido | Target Robusto |
|---------|-------------|------------------|----------------|
| Ejemplos | 10 | 25 | 50 |
| Tiempo | 7 días | 20 días | 40 días |
| Calidad Components | Nueva (teórica) | Nueva (teórica) | Nueva (teórica) |
| Diversidad | 5 dominios | 8 dominios | 12 dominios |

### Con Componentes Legacy (Estrategia Corregida)

| Métrica | Target Base | Target Expandido | Target Robusto |
|---------|-------------|------------------|----------------|
| Ejemplos | 10 | 25 | 50 |
| Tiempo | 7 días | 14 días | 25 días |
| Calidad Components | Nueva (teórica) | **Production-proven** ⭐ | **Production-proven** ⭐ |
| Diversidad | 5 dominios | 12 dominios | 20 dominios |

**Mejora:** 1.4x más rápido, calidad SUPERIOR (production-proven vs teórica)

---

## ✅ Decision Checklist (CORREGIDO)

Antes de usar prompts legacy:

- [ ] **Entendido:** Los agentes legacy NO son training data directo
- [ ] **Entendido:** Solo son FUENTE DE COMPONENTES production-proven
- [ ] **Identificado:** Qué agentes tienen los mejores componentes
- [ ] **Planificado:** Cómo extraer components de cada tipo de agente
- [ ] **Validado:** Que los ejemplos construidos pasen quality gate
- [ ] **Recordado:** Inputs SIEMPRE serán inventados (aunque realistas)

---

## 🚀 Próximos Pasos Inmediatos (CORREGIDO)

### Hoy (2 horas)

1. **Exploración manual** de 5 agentes legacy
2. **Extracción de components** de cada uno
3. **Construcción de 1 ejemplo sintético** para validar proceso

### Esta Semana (12 horas)

1. **Script de extracción** (3h)
   - `extract_components_from_agent()`
   - `generate_realistic_input()`
   - `build_synthetic_example()`

2. **Extracción lote inicial** (5h)
   - 10 CodeMachine agents
   - 5 agentes especializados

3. **Construcción de ejemplos** (3h)
   - 15 ejemplos sintéticos con components production-proven
   - Validación de quality score

---

## 🎯 Conclusión (CORREGIDA)

**Los prompts legacy son VALIOSOS pero NO como training data directo.**

**Key Takeaways CORREGIDOS:**
1. ✅ **Componentes production-proven** - Roles, directives, frameworks validados
2. ✅ **Mejor calidad sintética** - Ejemplos construidos con components reales vs teóricos
3. ✅ **Diversidad real** - 12-20 dominios vs 5-8 originales
4. ✅ **Tiempo similar** - 12-14 días vs 20 días (mejor ROI)
5. ✅ **Inputs inventados** - Aceptable si son realistas y basados en propósito

**Recomendación Final:**
- **Usar componentes legacy** como building blocks para ejemplos sintéticos
- **NO convertir agentes directamente** a ejemplos DSPy
- **Validar calidad** de cada ejemplo construido
- **Priorizar CodeMachine agents** (mejores estructuras)

**Próximo paso:** Script de extracción de componentes + probar con 5 ejemplos iniciales

---

**Fin de Análisis (Versión Corregida)**
