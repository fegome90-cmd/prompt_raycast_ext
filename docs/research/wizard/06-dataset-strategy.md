# 📚 Estrategia de Dataset - PromptImprover DSPy

**Fecha:** 2026-01-01
**Propósito:** Definir estrategia completa de adquisición, curación y crecimiento del dataset de entrenamiento para PromptImprover Module
**Status:** ESTRATEGIA - REQUIERE VALIDACIÓN

---

## 🔥 El Problema Crítico

**DSPy necesita ejemplos para aprender.** Sin un dataset de calidad, el PromptImprover Module no puede aprender el patrón de "idea cruda → prompt SOTA".

```
Dataset Pequeño (3-5 ejemplos)  →  Overfitting, outputs genéricos
Dataset Mediano (10-20 ejemplos) →  Buena base, patrones claros
Dataset Grande (50+ ejemplos)    →  Robustez, dominios diversos
```

---

## 📊 Inventario de Fuentes Disponibles

### Fuente 1: Templates Completos (simulation/db.ts)
**Ubicación:** `/Users/felipe_gonzalez/Developer/promtassss-main/simulation/db.ts`

| Template | ID | Dominio | Complejidad | Rating | ¿Usar? |
|----------|-----|---------|-------------|--------|--------|
| Plan for ADR Process | `template-adr` | Software Architecture | Alta | 4.8/5 | ✅ SÍ |
| SaaS Product Launch | `template-product-launch` | Marketing | Media | 4.6/5 | ✅ SÍ |
| Scientific Research Proposal | `template-research-proposal` | Research | Alta | 4.9/5 | ✅ SÍ |
| Microservice Architecture Design | `template-microservice-design` | Software Architecture | Alta | 4.5/5 | ✅ SÍ |

**Total:** 4 templates completos listos para convertir en ejemplos DSPy

### Fuente 2: Componentes Individuales
**Ubicación:** `/Users/felipe_gonzalez/Developer/promtassss-main/simulation/db.ts`

| Tipo | Cantidad | Ejemplos |
|------|----------|----------|
| **Roles** | 9 | Software Architect, Marketing Strategist, Scientist, Customer Service, Code Reviewer, Project Architect, Prompt Engineer, Workflow Automator, Research Analyst |
| **Directives** | 7 | ADR Process, Product Launch, Research Proposal, Customer Inquiry, Code Review, Configure Project, Optimize Prompt, Design Workflow, Conduct Research, Manage Incident |
| **Frameworks** | 2 | Chain-of-Thought, Tree-of-Thoughts |
| **Constraints** | 12 | Clarity, Pragmatism, Actionability, Integration, Budget, Data-Driven, Empathy, Security, Testing, Tool Integration, Research Integrity, Incident Protocol |

**Total:** 30 componentes que pueden combinarse en ejemplos sintéticos

### Fuente 3: Ejemplos Existente DSPy
**Ubicación:** `/Users/felipe_gonzalez/Developer/raycast_ext/docs/research/wizard/03-dspy-integration-guide.md` (líneas 488-577)

| Ejemplo | Dominio | Complejidad | Estado |
|---------|---------|-------------|--------|
| Design ADR Process | Software Architecture | Alta | ✅ Listo |
| Plan Product Launch | Marketing | Media | ✅ Listo |
| Research Proposal | Scientific Research | Alta | ✅ Listo |

**Total:** 3 ejemplos ya implementados en código

---

## 🎯 Estrategia de Construcción de Dataset

### Principio Fundamental: **Calidad > Cantidad**

Mejor 10 ejemplos perfectos que 50 ejemplos mediocres. DSPy aprende patrones, y patrones malos enseñan mal.

### Fase 1: Dataset Base (10 ejemplos) - OPCIÓN RÁPIDA
**Tiempo:** 2-3 horas
**Objetivo:** Validar que PromptImprover funciona
**Cobertura:** 3 dominios principales

| # | original_idea | Dominio | Source |
|---|---------------|---------|--------|
| 1 | "Design ADR process" | Software Architecture | ✅ Ya existe (03-dspy...) |
| 2 | "Plan product launch" | Marketing | ✅ Ya existe (03-dspy...) |
| 3 | "Research proposal" | Scientific Research | ✅ Ya existe (03-dspy...) |
| 4 | "Microservice design" | Software Architecture | ⚠️ Convertir desde template-adr |
| 5 | "Customer service workflow" | Customer Service | 🆕 Crear nuevo |
| 6 | "Code review process" | Development | 🆕 Crear nuevo |
| 7 | "Data analysis pipeline" | Data Science | 🆕 Crear nuevo |
| 8 | "Security audit checklist" | Security | 🆕 Crear nuevo |
| 9 | "Content marketing calendar" | Marketing | 🆕 Crear nuevo |
| 10 | "API documentation" | Technical Writing | 🆕 Crear nuevo |

**Acción Inmediata:**
- [ ] Validar 3 ejemplos existentes
- [ ] Convertir template-microservice-design a formato DSPy
- [ ] Crear 6 ejemplos nuevos cubriendo los dominios faltantes

### Fase 2: Dataset Expandido (25 ejemplos) - OPCIÓN RECOMENDADA
**Tiempo:** 6-8 horas adicionales
**Objetivo:** Cobertura sólida de dominios comunes
**Cobertura:** 8-10 dominios

**Nuevos Dominios a Añadir:**
- Business Operations (3 ejemplos)
- DevOps/SRE (2 ejemplos)
- Product Management (2 ejemplos)
- UX/UI Design (2 ejemplos)
- Legal/Compliance (2 ejemplos)
- Education/Training (2 ejemplos)
- Finance/Accounting (2 ejemplos)
- Sales/Customer Success (2 ejemplos)

**Distribución Final:**
```
Software Development: 6 ejemplos (24%)
Marketing/Sales:       4 ejemplos (16%)
Research/Science:      3 ejemplos (12%)
Operations:            3 ejemplos (12%)
Product:               2 ejemplos (8%)
Design:                2 ejemplos (8%)
Data/AI:               2 ejemplos (8%)
Legal/Finance:         2 ejemplos (8%)
Education:             1 ejemplo  (4%)
```

### Fase 3: Dataset Robusto (50+ ejemplos) - OPCIÓN PRODUCCIÓN
**Tiempo:** 16-20 horas adicionales
**Objetivo:** Robustez extrema, manejo de edge cases
**Cobertura:** 15+ dominios, múltiples niveles de complejidad

**Añadir:**
- Casos edge (ambiguos, multi-dominio)
- Niveles de complejidad (básico, intermedio, avanzado)
- Idiomas (inglés, español, bilingüe)
- Estilos de prompt (formal, casual, técnico)

---

## 🔄 Proceso de Conversión: Template → Ejemplo DSPy

### Paso 1: Extraer del Template (simulation/db.ts)

```typescript
// Template original en db.ts
{
  id: 'template-adr',
  name: 'Plan for ADR Process',
  description: 'A comprehensive template for architects...',
  componentIds: {
    role: 'role-sw-architect',
    directive: 'dir-adr',
    framework: 'fw-cot',
    constraints: ['con-clarity', 'con-pragmatism', 'con-actionable', 'con-integration']
  }
}
```

### Paso 2: Hidratar Componentes

```python
# Buscar cada componente por ID
role = components.find(c => c.id === 'role-sw-architect').content
directive = components.find(c => c.id === 'dir-adr').content
framework = components.find(c => c.id === 'fw-cot').content
constraints = [
    components.find(c => c.id === 'con-clarity').content,
    components.find(c => c.id === 'con-pragmatism').content,
    components.find(c => c.id === 'con-actionable').content,
    components.find(c => c.id === 'con-integration').content
]
```

### Paso 3: Ensamblar Prompt Final

```python
# Usar función de ensamblaje (04-prompt-assembly-patterns.md)
improved_prompt = assembleFinalPrompt({
    role: role,
    directive: directive,
    framework: framework,
    guardrails: constraints
})
```

### Paso 4: Crear Ejemplo DSPy

```python
dspy.Example(
    # INPUT: Idea cruda del usuario
    original_idea="Design ADR process for my team",
    context="We need a lightweight process, not bureaucracy",

    # OUTPUT: Prompt SOTA completo
    improved_prompt=improved_prompt,  # Del paso 3
    role=role,
    directive=directive,
    framework=framework,
    guardrails=constraints,

    # METADATA (opcional pero recomendado)
    reasoning="Added emphasis on lightweight, pragmatic approach",
    confidence=0.9
).with_inputs("original_idea", "context")
```

---

## 📝 Template para Crear Nuevos Ejemplos

### Formato Estándar

```python
dspy.Example(
    # ============================================================
    # INPUT: Qué diría un usuario real (crudo, incompleto)
    # ============================================================
    original_idea="[IDEA CRUDA AQUÍ - 5-15 palabras]",
    context="[CONTEXTO ADICIONAL - opcional]",

    # ============================================================
    # OUTPUT: Prompt SOTA completo (siguiendo estructura wizard)
    # ============================================================
    improved_prompt="""
**[ROLE & PERSONA]**
[Descripción detallada del rol - 3-5 líneas]

**[CORE DIRECTIVE]**
**Your ultimate mission is:** [Directiva clara y específica]

**[EXECUTION FRAMEWORK: Chain-of-Thought]**
[Instrucciones del framework - CoT o ToT]

**[CONSTRAINTS & GUARDRAILS]**
* [Constraint 1]
* [Constraint 2]
* [Constraint 3]

**[FINAL OUTPUT]**
Based on all the information above, provide:
1. [Output específico 1]
2. [Output específico 2]
3. [Output específico 3]
""",

    # ============================================================
    # COMPONENTS (para análisis DSPy)
    # ============================================================
    role="[Mismo rol que en improved_prompt]",
    directive="[Misma directiva que en improved_prompt]",
    framework="Chain-of-Thought",  # o "Tree-of-Thoughts"
    guardrails="[Misma lista que constraints]",

    # ============================================================
    # METADATA (para debugging y mejora)
    # ============================================================
    reasoning="[Por qué se hicieron estas elecciones]",
    confidence=0.85  # Qué tan confiado estás en este ejemplo (0-1)
).with_inputs("original_idea", "context")
```

### Ejemplo Completo: Data Analysis Pipeline

```python
dspy.Example(
    original_idea="Create data analysis pipeline for sales data",
    context="We have monthly sales CSV files, need automated insights",

    improved_prompt="""
**[ROLE & PERSONA]**
You are a **Senior Data Scientist** with 8+ years of experience building production data pipelines. You are expert in Python, SQL, and statistical analysis. Your communication is clear, visualizing complex data in understandable ways, and your decisions are always data-driven.

**[CORE DIRECTIVE]**
**Your ultimate mission is:** To design a robust, automated data analysis pipeline that processes monthly sales CSV files, extracts actionable insights, and presents them in a clear executive dashboard format.

**[EXECUTION FRAMEWORK: Chain-of-Thought]**
You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.

1.  **Synthesize the "Why":** Begin with a high-level understanding of what business insights we need from sales data.
2.  **Deconstruct the Problem:** Break down the pipeline into: data ingestion, cleaning, analysis, visualization, and reporting.
3.  **Design the Solution - Step-by-Step:** Address each component with specific technologies and approaches.
4.  **Synthesize and Plan:** Consolidate into a cohesive implementation plan with priorities.

**[CONSTRAINTS & GUARDRAILS]**
*   **Clarity and Conciseness**: Avoid jargon where possible. Explain complex technical concepts in business terms.
*   **Pragmatism over Dogmatism**: Prioritize what works in practice over theoretical perfection. Use proven libraries (pandas, plotly).
*   **Actionability**: Every recommendation must be a concrete, actionable step with specific tools or commands.
*   **Data-Driven**: All analysis choices must be justified by statistical principles and data characteristics.

**[FINAL OUTPUT]**
Based on all the information above, provide:
1. **Architecture Diagram**: A visual representation of the pipeline components
2. **Technology Stack**: Specific Python libraries and tools for each component
3. **Implementation Steps**: Numbered steps to build the pipeline from scratch
4. **Sample Analysis**: Example of insights the pipeline would extract
5. **Monitoring Strategy**: How to ensure pipeline health and data quality
""",

    role="You are a **Senior Data Scientist** with 8+ years of experience building production data pipelines. You are expert in Python, SQL, and statistical analysis.",
    directive="To design a robust, automated data analysis pipeline that processes monthly sales CSV files, extracts actionable insights, and presents them in a clear executive dashboard format.",
    framework="Chain-of-Thought",
    guardrails=[
        "Clarity and Conciseness: Avoid jargon where possible",
        "Pragmatism over Dogmatism: Prioritize what works in practice",
        "Actionability: Every recommendation must be concrete",
        "Data-Driven: All choices justified by statistical principles"
    ],
    reasoning="Emphasized practical tools (pandas, plotly) over theoretical solutions. Added monitoring because production pipelines require observability.",
    confidence=0.90
).with_inputs("original_idea", "context")
```

---

## ✅ Criterios de Calidad del Dataset

### Regla de Oro: **Un ejemplo es válido si un humano lo considera SOTA**

| Criterio | Peso | Cómo Validar |
|----------|------|--------------|
| **Idea Cruda Creíble** | 20% | ¿Suena como algo que un usuario real diría? |
| **Prompt Mejor Visible** | 30% | ¿La diferencia entre input/output es obvia? |
| **Estructura Completa** | 20% | ¿Tiene TODOS los componentes (role, directive, framework, guardrails)? |
| **Sin Alucinaciones** | 15% | ¿Todo el contenido está justificado? |
| **Diversidad** | 15% | ¿Aporta un patrón nuevo vs ejemplos existentes? |

### Quality Gate: **Solo ejemplos con score ≥ 0.7 pasan al dataset**

```python
def validate_example(example: dspy.Example) -> tuple[bool, str]:
    """Valida que un ejemplo cumpla criterios de calidad"""
    score = 0
    reasons = []

    # 1. Idea cruda creíble (20%)
    if 5 <= len(example.original_idea.split()) <= 15:
        score += 0.2
    else:
        reasons.append("Idea cruda no creíble (muy corta o muy larga)")

    # 2. Mejora visible (30%)
    improvement_ratio = len(example.improved_prompt) / len(example.original_idea)
    if improvement_ratio >= 5:  # Al menos 5x más largo
        score += 0.3
    else:
        reasons.append(f"Mejora no visible (ratio: {improvement_ratio:.1f}x)")

    # 3. Estructura completa (20%)
    required_fields = ['role', 'directive', 'framework', 'guardrails']
    if all(hasattr(example, field) for field in required_fields):
        score += 0.2
    else:
        reasons.append("Faltan componentes obligatorios")

    # 4. Confidence (15%)
    if example.confidence >= 0.8:
        score += 0.15
    else:
        reasons.append(f"Confidence bajo ({example.confidence})")

    # 5. Sin duplicados (15%)
    if not is_duplicate(example):
        score += 0.15
    else:
        reasons.append("Ejemplo duplicado de otro existente")

    passed = score >= 0.7
    return passed, f"Score: {score:.2f} - " + "; ".join(reasons)
```

---

## 🚀 Plan de Acción Inmediato

### Semana 1: Dataset Base (10 ejemplos)

**Día 1 (2h): Validación y Conversión**
- [ ] Validar 3 ejemplos existentes (ADR, Product Launch, Research)
- [ ] Convertir template-microservice-design a formato DSPy
- [ ] Crear script de conversión automatizada

**Día 2 (3h): Creación de 4 Ejemplos Nuevos**
- [ ] Customer service workflow
- [ ] Code review process
- [ ] Data analysis pipeline
- [ ] Security audit checklist

**Día 3 (2h): Creación de 3 Ejemplos y Validación**
- [ ] Content marketing calendar
- [ ] API documentation
- [ ] Budget planning process
- [ ] Validar todos los 10 ejemplos con quality gate
- [ ] Integrar dataset en código DSPy

### Semana 2-3: Dataset Expandido (+15 ejemplos)

**Día 4-6: Dominios Business Operations**
- [ ] 3 ejemplos de operaciones
- [ ] 2 ejemplos de DevOps/SRE
- [ ] Validación y testing

**Día 7-9: Dominios Product y Design**
- [ ] 2 ejemplos de Product Management
- [ ] 2 ejemplos de UX/UI Design
- [ ] Validación y testing

**Día 10-12: Dominios Especializados**
- [ ] 2 ejemplos de Legal/Compliance
- [ ] 2 ejemplos de Education/Training
- [ ] 2 ejemplos de Finance/Accounting

**Día 13-15: Integración y Testing**
- [ ] Testing de PromptImprover con dataset expandido
- [ ] Ajuste de hiperparámetros DSPy
- [ ] Validación de quality score promedio

---

## 📈 Métricas de Éxito del Dataset

### Métricas Cuantitativas

| Métrica | Target Base | Target Expandido | Target Robusto |
|---------|-------------|------------------|----------------|
| **Total Ejemplos** | 10 | 25 | 50+ |
| **Dominios Cubiertos** | 5 | 10 | 15+ |
| **Quality Score Prom** | ≥ 0.75 | ≥ 0.80 | ≥ 0.85 |
| **Diversidad (Entropía)** | ≥ 1.5 | ≥ 2.0 | ≥ 2.5 |
| **Tokens por Ejemplo** | 500-1500 | 500-1500 | 500-1500 |

### Métricas Cualitativas

**Validación Humana:**
- [ ] 10 personas revisan 5 ejemplos random
- [ ] ≥ 80% acuerdan "este es un prompt SOTA"
- [ ] ≤ 5% encuentran errores u omisiones

**Validación Automatizada:**
- [ ] Sin warnings de calidad
- [ ] Sin duplicados (similarity < 0.85)
- [ ] Balance de dominios (ninguno > 40%)

**Validación DSPy:**
- [ ] BootstrapFewShot converge en < 5 minutos
- [ ] Métrica de calidad ≥ 0.7 en test set
- [ ] Outputs generados pasan quality gate

---

## 🔄 Estrategia de Crecimiento Continuo

### Loop de Mejora del Dataset

```
┌─────────────────────────────────────────────────────────────┐
│  1. PRODUCCIÓN: Generar nuevos ejemplos                     │
│     → Basados en feedback real de usuarios                  │
│     → Casos edge encontrados en producción                  │
│     → Nuevos dominios según demanda                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. VALIDACIÓN: Quality Gate automático                     │
│     → Score ≥ 0.7 para pasar                               │
│     → Revisión humana de 10% random                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. TESTING: Test A/B vs dataset anterior                    │
│     → Si nuevo es mejor → Reemplazar                       │
│     → Si similar → Añadir (diversidad)                      │
│     → Si peor → Descartar                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. REENTRENAMIENTO: Compilar PromptImprover                │
│     → Cada 10 ejemplos nuevos                               │
│     → Comparar métricas antes/después                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                        (volver a 1)
```

---

## 🎯 Conclusión y Recomendación

### Recomendación: **Opción Híbrida Inteligente**

1. **INMEDIATO (Día 1-3):** Dataset Base de 10 ejemplos
   - Validar que DSPy funciona con tu setup
   - Probar que la calidad es aceptable
   - **Costo:** 7 horas de trabajo

2. **CORTO PLAZO (Semana 2-3):** Dataset Expandido a 25 ejemplos
   - Si los resultados del base son prometedores
   - Añadir dominios business y product
   - **Costo:** 12 horas adicionales

3. **MEDIANO PLAZO (Mes 1):** Dataset Robusto a 50+ ejemplos
   - Basado en feedback real de usuarios
   - Añadir edge cases y multi-dominio
   - **Costo:** 20 horas adicionales

### NO Hacer:

- ❌ NO generar 50 ejemplos de golpe sin validar los primeros 10
- ❌ NO usar ejemplos de baja calidad solo para aumentar cantidad
- ❌ NO confiar solo en templates de promptass (falta diversidad)
- ❌ NO skipear validación humana (automático no es suficiente)

### SÍ Hacer:

- ✅ SÍ validar calidad de cada ejemplo manualmente
- ✅ Sí crear ejemplos sintéticos de alta calidad
- ✅ Sí basarse en templates de promptass como guía
- ✅ Sí iterar basado en feedback real

---

**Próximo paso:** Validar esta estrategia y comenzar con Dataset Base (10 ejemplos).
