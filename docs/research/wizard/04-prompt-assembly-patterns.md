# Prompt Assembly Patterns - Patrones de Ensamblaje

**Prioridad:** 🟡 IMPORTANTE - Necesario para generación final
**Fuente:** Architect v3.2.0 - `components/PlanView.tsx`, `types.ts`
**Aplicabilidad:** Directamente aplicable a Raycast

---

## 📋 Índice

1. [Overview](#overview)
2. [PlanData Structure](://plandata-structure)
3. [Ensamblaje Estándar](#ensamblaje-estándar)
4. [Patrones de Framework](#patrones-de-framework)
5. [Formatos de Salida](#formatos-de-salida)
6. [Optimizaciones](#optimizaciones)
7. [DSPy Integration](#dspy-integration)

---

## Overview

### El Proceso de Ensamblaje

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROMPT ASSEMBLY PROCESS                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT: PlanData                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                │   │
│  │   objective: "Design ADR process",                              │   │
│  │   role: "World-Class Architect...",                            │   │
│  │   directive: "To design and detail...",                        │   │
│  │   framework: "chain-of-thought",                               │   │
│  │   guardrails: ["Be concise", "Prioritize pragmatism"]          │   │
│  │ }                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│                         ASSEMBLER                                       │
│                              ↓                                          │
│  OUTPUT: Formatted SOTA Prompt                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                 │   │
│  │   **[ROLE & PERSONA]**                                          │   │
│  │   You are a World-Class Architect...                           │   │
│  │                                                                 │   │
│  │   **[CORE DIRECTIVE]**                                          │   │
│  │   Your ultimate mission is: To design and detail...            │   │
│  │                                                                 │   │
│  │   **[EXECUTION FRAMEWORK: Chain-of-Thought]**                  │   │
│  │   You must use the Chain-of-Thought framework...               │   │
│  │                                                                 │   │
│  │   **[CONSTRAINTS & GUARDRAILS]**                                │   │
│  │   You must adhere to the following rules:                      │   │
│  │   *   Be concise and to the point                               │   │
│  │   *   Prioritize pragmatism                                     │   │
│  │                                                                 │   │
│  │   **[FINAL OUTPUT]**                                           │   │
│  │   Based on all the information above...                        │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PlanData Structure

### Interfaz TypeScript

```typescript
// types.ts - Estructura central de datos
export interface PlanData {
  objective: string;             // STEP 1
  role: string;                  // STEP 2
  directive: string;             // STEP 3
  framework: ReasoningFramework; // STEP 4
  guardrails: string[];          // STEP 5
}

export type ReasoningFramework =
  | "chain-of-thought"
  | "tree-of-thoughts"
  | "decomposition"
  | "role-playing";
```

### Ejemplo Completo de PlanData

```typescript
const examplePlanData: PlanData = {
  objective: "Design a scalable and developer-friendly process for establishing Architecture Decision Records (ADRs)",

  role: `You are an expert-level AI planning agent embodying the persona of a **World-Class Software Architect** with over 20 years of experience leading complex digital transformations. You are not just a drafter; you are a strategic thinker who balances technical excellence with business acumen. Your communication is precise, your reasoning is transparent, and your decisions are always traceable to first principles.`,

  directive: `To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs). This is not about creating bureaucracy; it's about building a system of "durable, asynchronous communication" that safeguards the architectural integrity of our software as it evolves.`,

  framework: "chain-of-thought",

  guardrails: [
    "Avoid jargon where possible. Explain complex ideas simply.",
    "Prioritize what works in practice over theoretical perfection.",
    "Every recommendation must be a concrete, actionable step.",
    "The plan must consider integration with common developer tools like Git and Pull Requests."
  ]
};
```

---

## Ensamblaje Estándar

### Función de Ensamblaje Base

```typescript
// components/PlanView.tsx
function assembleFinalPrompt(data: PlanData): string {
  // 1. Obtener detalles del framework
  const frameworkDetails = FRAMEWORKS.find(f => f.id === data.framework);

  // 2. Formatear guardrails como lista
  const guardrailList = data.guardrails.length > 0
    ? data.guardrails.map(g => `*   ${g}`).join('\n')
    : '*   No specific constraints';

  // 3. Ensamblar prompt
  return `
**[ROLE & PERSONA]**
${data.role}

**[CORE DIRECTIVE]**
**Your ultimate mission is:** ${data.directive}

**[EXECUTION FRAMEWORK: ${frameworkDetails?.name || 'Custom'}]**
${frameworkDetails?.description || 'Follow a systematic approach to problem-solving.'}

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
${guardrailList}

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan.
Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section.
Use Markdown for formatting. Begin your response with a title for the plan.
  `.trim();
}
```

### Frameworks Definitions

```typescript
const FRAMEWORKS: Array<{
  id: ReasoningFramework;
  name: string;
  description: string;
}> = [
  {
    id: "chain-of-thought",
    name: "Chain-of-Thought",
    description: `You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.

1. **Synthesize the "Why":** Begin with a high-level strategic analysis.
2. **Deconstruct the Problem:** Break down the core directive into its essential components.
3. **Design the Solution - Step-by-Step:** Address each component with a detailed solution.
4. **Synthesize and Plan:** Consolidate the solutions into a cohesive, actionable implementation plan.`
  },
  {
    id: "tree-of-thoughts",
    name: "Tree of Thoughts",
    description: `You must use the Tree of Thoughts framework to structure your entire response. Your output should explore multiple solution paths before converging on an optimal one. Follow these steps precisely...

1. **Identify Key Decision Forks.**
2. **Explore Branches (Thoughts).**
3. **Evaluate and Prune.**
4. **Synthesize the Final Path.**`
  },
  {
    id: "decomposition",
    name: "Decomposition",
    description: `You must use the Decomposition framework to break down the problem into smaller, manageable sub-problems and address each systematically.

1. **Identify Main Components:** Break down the directive into 3-5 key components.
2. **Address Each Component:** Provide detailed solutions for each.
3. **Integrate Solutions:** Show how components work together.
4. **Validate Decomposition:** Ensure no overlaps or gaps.`
  },
  {
    id: "role-playing",
    name: "Role-Playing",
    description: `You must use the Role-Playing framework to simulate dialogues, user interactions, or scenarios relevant to the objective.

1. **Set the Scene:** Describe the context and participants.
2. **Simulate Interactions:** Show realistic dialogue or exchanges.
3. **Explore Outcomes:** Highlight key insights from the simulation.
4. **Synthesize Learnings:** Extract actionable conclusions.`
  }
];
```

---

## Patrones de Framework

### Chain-of-Thought Pattern

```
INPUT: Problem → OUTPUT: Sequential solution

Structure:
┌─────────────────────────────────────────────────────────┐
│ 1. Synthesize the "Why"                                  │
│    • High-level strategic analysis                      │
│    • Why this problem matters                           │
│    • Key stakeholders and context                       │
├─────────────────────────────────────────────────────────┤
│ 2. Deconstruct the Problem                              │
│    • Break into 3-5 essential components                │
│    • Identify dependencies                              │
│    • Clarify scope                                      │
├─────────────────────────────────────────────────────────┤
│ 3. Design the Solution - Step-by-Step                   │
│    • Component 1: Detailed solution                     │
│    • Component 2: Detailed solution                     │
│    • Component 3: Detailed solution                     │
│    • Integration: How components work together          │
├─────────────────────────────────────────────────────────┤
│ 4. Synthesize and Plan                                  │
│    • Consolidate into cohesive plan                     │
│    • Timeline and milestones                            │
│    • Success metrics                                    │
└─────────────────────────────────────────────────────────┘
```

### Tree of Thoughts Pattern

```
INPUT: Complex problem → OUTPUT: Evaluated solution paths

Structure:
┌─────────────────────────────────────────────────────────┐
│ 1. Identify Key Decision Forks                          │
│    • Fork 1: Major decision point A                     │
│    • Fork 2: Major decision point B                     │
│    • Fork 3: Major decision point C                     │
├─────────────────────────────────────────────────────────┤
│ 2. Explore Branches (Thoughts)                          │
│    ├─ Branch 1A: Option 1 at Fork A                     │
│    │  ├─ Branch 2A: Option 1 at Fork B                  │
│    │  └─ Branch 2B: Option 2 at Fork B                  │
│    └─ Branch 1B: Option 2 at Fork A                     │
│       ├─ Branch 2C: Option 1 at Fork B                  │
│       └─ Branch 2D: Option 2 at Fork B                  │
├─────────────────────────────────────────────────────────┤
│ 3. Evaluate and Prune                                   │
│    • Criteria: Cost, Time, Quality, Risk               │
│    • Branch 1A → 2A: Score 8.5/10 ✓ Recommended        │
│    • Branch 1A → 2B: Score 6.0/10 ✗ Pruned             │
│    • Branch 1B → 2C: Score 7.5/10 Backup               │
│    • Branch 1B → 2D: Score 5.0/10 ✗ Pruned             │
├─────────────────────────────────────────────────────────┤
│ 4. Synthesize the Final Path                            │
│    • Selected: Branch 1A → 2A                          │
│    • Rationale: Highest score on all criteria          │
│    • Implementation plan                                │
└─────────────────────────────────────────────────────────┘
```

### Decomposition Pattern

```
INPUT: Large problem → OUTPUT: Component-based solution

Structure:
┌─────────────────────────────────────────────────────────┐
│ 1. Identify Main Components                             │
│    ├─ Component A: [Sub-problem 1]                      │
│    ├─ Component B: [Sub-problem 2]                      │
│    ├─ Component C: [Sub-problem 3]                      │
│    └─ Component D: [Sub-problem 4]                      │
├─────────────────────────────────────────────────────────┤
│ 2. Address Each Component                               │
│    │                                                     │
│    Component A: [Sub-problem 1]                         │
│    ├─ Analysis: [Understanding of the component]       │
│    ├─ Solution: [Detailed approach]                     │
│    ├─ Dependencies: [What it needs from others]        │
│    └─ Output: [Deliverable]                            │
│    │                                                     │
│    Component B: [Sub-problem 2]                         │
│    ├─ Analysis: [Understanding of the component]       │
│    ├─ Solution: [Detailed approach]                     │
│    ├─ Dependencies: [What it needs from others]        │
│    └─ Output: [Deliverable]                            │
│    │                                                     │
│    [Repeat for C and D]                                 │
│    │                                                     │
├─────────────────────────────────────────────────────────┤
│ 3. Integrate Solutions                                  │
│    • How A and B interact                               │
│    • How C enhances A and B                             │
│    • How D supports the overall system                 │
│    • Unified workflow                                   │
├─────────────────────────────────────────────────────────┤
│ 4. Validate Decomposition                               │
│    ✓ No overlaps (each component unique)               │
│    ✓ No gaps (all aspects covered)                     │
│    ✓ Clear boundaries (well-defined interfaces)        │
│    ✓ Testable (each component measurable)              │
└─────────────────────────────────────────────────────────┘
```

### Role-Playing Pattern

```
INPUT: Scenario → OUTPUT: Simulated dialogue with insights

Structure:
┌─────────────────────────────────────────────────────────┐
│ 1. Set the Scene                                         │
│    • Context: [Background information]                  │
│    • Participants: [Roles and personas]                 │
│    • Goal: [What the simulation aims to achieve]        │
├─────────────────────────────────────────────────────────┤
│ 2. Simulate Interactions                                │
│    │                                                     │
│    [User]: [Question or statement]                      │
│    [AI Persona]: [Response in character]               │
│    [User]: [Follow-up]                                  │
│    [AI Persona]: [Response with expertise]              │
│    │                                                     │
│    [Continue dialogue to explore the scenario]          │
│    │                                                     │
├─────────────────────────────────────────────────────────┤
│ 3. Explore Outcomes                                     │
│    • Key insight 1: [Learning from dialogue]            │
│    • Key insight 2: [Understanding gained]             │
│    • Key insight 3: [Pattern identified]                │
├─────────────────────────────────────────────────────────┤
│ 4. Synthesize Learnings                                 │
│    • Actionable conclusion 1                            │
│    • Actionable conclusion 2                            │
│    • Actionable conclusion 3                            │
└─────────────────────────────────────────────────────────┘
```

---

## Formatos de Salida

### Markdown Output

```typescript
// Generar salida en Markdown
function generateMarkdownOutput(data: PlanData): string {
  const prompt = assembleFinalPrompt(data);

  return `# ${extractTitle(data.objective)}

${prompt}

---

## Expected Output Structure

The response should follow this structure:

\`\`\`markdown
# [Plan Title]

## 1. [Framework Step 1 Title]
[Detailed content]

## 2. [Framework Step 2 Title]
[Detailed content]

## 3. [Framework Step 3 Title]
[Detailed content]

## 4. [Framework Step 4 Title]
[Detailed content]

## Summary
[Consolidated plan with next steps]
\`\`\`
`;
}
```

### JSON Output (para API)

```typescript
// Generar salida estructurada en JSON
function generateJSONOutput(data: PlanData): object {
  return {
    version: "1.0",
    prompt: {
      objective: data.objective,
      components: {
        role: {
          name: "Role & Persona",
          content: data.role
        },
        directive: {
          name: "Core Directive",
          content: `Your ultimate mission is: ${data.directive}`
        },
        framework: {
          name: "Execution Framework",
          type: data.framework,
          content: getFrameworkDescription(data.framework)
        },
        guardrails: {
          name: "Constraints & Guardrails",
          items: data.guardrails.map((g, i) => ({
            id: `constraint-${i + 1}`,
            content: g
          }))
        }
      },
      assembled_prompt: assembleFinalPrompt(data),
      metadata: {
        word_count: assembleFinalPrompt(data).split(/\s+/).length,
        estimated_tokens: Math.ceil(assembleFinalPrompt(data).split(/\s+/).length * 1.3),
        framework_complexity: getFrameworkComplexity(data.framework)
      }
    }
  };
}
```

---

## Optimizaciones

### Token Efficiency

```typescript
// Optimización: Eliminar redundancias
function optimizeForTokens(data: PlanData): PlanData {
  const optimized = { ...data };

  // 1. Eliminar palabras repetidas en role
  optimized.role = removeRepetitions(data.role);

  // 2. Simplificar directive si objective ya contiene contexto
  if (optimized.directive.includes(optimized.objective)) {
    optimized.directive = optimized.directive.replace(
      optimized.objective,
      "[the above objective]"
    );
  }

  // 3. Consolidar guardrails similares
  optimized.guardrails = consolidateSimilarItems(data.guardrails);

  return optimized;
}

// Ejemplo de consolidación
function consolidateSimilarItems(items: string[]): string[] {
  const groups: Record<string, string[]> = {};

  // Agrupar items similares
  for (const item of items) {
    const key = extractKeyword(item);
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  }

  // Consolidar cada grupo
  return Object.values(groups).map(group =>
    group.length > 1 ? combineItems(group) : group[0]
  );
}

// Ejemplo:
// Input: ["Avoid jargon", "Don't use technical terms", "Keep it simple"]
// Output: ["Avoid jargon and technical terms. Keep explanations simple."]
```

### Quality-Based Assembly

```typescript
// Ensamblaje adaptativo basado en calidad de componentes
function adaptiveAssembly(data: PlanData): string {
  const quality = assessComponentQuality(data);
  let prompt = "";

  // Role: Si es corto, añadir expansión automática
  if (quality.role.length < 100) {
    prompt += `**[ROLE & PERSONA]**\n${expandRole(data.role)}\n\n`;
  } else {
    prompt += `**[ROLE & PERSONA]**\n${data.role}\n\n`;
  }

  // Directive: Si no tiene verbos de acción, añadir prefijo
  if (!quality.directive.hasActionVerbs) {
    prompt += `**[CORE DIRECTIVE]**\n**Your ultimate mission is:** ${addActionVerbs(data.directive)}\n\n`;
  } else {
    prompt += `**[CORE DIRECTIVE]**\n**Your ultimate mission is:** ${data.directive}\n\n`;
  }

  // Guardrails: Si son menos de 3, sugerir automáticamente
  if (data.guardrails.length < 3) {
    const suggested = suggestGuardrails(data.objective, data.framework);
    prompt += `**[CONSTRAINTS & GUARDRAILS]**\nYou must adhere to the following rules:\n`;
    prompt += data.guardrails.map(g => `*   ${g}`).join('\n');
    prompt += suggested.map(g => `*   ${g} (suggested)`).join('\n');
  } else {
    prompt += `**[CONSTRAINTS & GUARDRAILS]**\nYou must adhere to the following rules:\n`;
    prompt += data.guardrails.map(g => `*   ${g}`).join('\n');
  }

  // Final output
  prompt += `\n**[FINAL OUTPUT]**\nBased on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan. Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section. Use Markdown for formatting. Begin your response with a title for the plan.`;

  return prompt;
}
```

---

## DSPy Integration

### DSPy Assembly Module

```python
import dspy

class PromptAssembler(dspy.Module):
    """Módulo DSPy para ensamblar prompts"""

    def __init__(self):
        super().__init__()
        self.frameworks = self._load_frameworks()

    def forward(self, objective: str, role: str, directive: str,
                framework: str, guardrails: list) -> dspy.Prediction:
        """Ensamblar prompt completo"""

        # Obtener descripción del framework
        framework_desc = self.frameworks.get(framework, "")

        # Formatear guardrails
        guardrail_text = "\n".join([f"*   {g}" for g in guardrails])

        # Ensamblar prompt
        assembled_prompt = f"""**[ROLE & PERSONA]**
{role}

**[CORE DIRECTIVE]**
**Your ultimate mission is:** {directive}

**[EXECUTION FRAMEWORK: {framework.upper()}]**
{framework_desc}

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
{guardrail_text}

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan. Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section. Use Markdown for formatting. Begin your response with a title for the plan."""

        return dspy.Prediction(
            assembled_prompt=assembled_prompt,
            word_count=len(assembled_prompt.split()),
            estimated_tokens=len(assembled_prompt.split()) * 13 // 10
        )

    def _load_frameworks(self) -> dict:
        """Cargar definiciones de frameworks"""
        return {
            "chain-of-thought": """You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.

1. **Synthesize the "Why":** Begin with a high-level strategic analysis.
2. **Deconstruct the Problem:** Break down the core directive into its essential components.
3. **Design the Solution - Step-by-Step:** Address each component with a detailed solution.
4. **Synthesize and Plan:** Consolidate the solutions into a cohesive, actionable implementation plan.""",

            "tree-of-thoughts": """You must use the Tree of Thoughts framework to structure your entire response. Your output should explore multiple solution paths before converging on an optimal one. Follow these steps precisely...

1. **Identify Key Decision Forks.**
2. **Explore Branches (Thoughts).**
3. **Evaluate and Prune.**
4. **Synthesize the Final Path.**""",

            "decomposition": """You must use the Decomposition framework to break down the problem into smaller, manageable sub-problems and address each systematically.

1. **Identify Main Components:** Break down the directive into 3-5 key components.
2. **Address Each Component:** Provide detailed solutions for each.
3. **Integrate Solutions:** Show how components work together.
4. **Validate Decomposition:** Ensure no overlaps or gaps.""",

            "role-playing": """You must use the Role-Playing framework to simulate dialogues, user interactions, or scenarios relevant to the objective.

1. **Set the Scene:** Describe the context and participants.
2. **Simulate Interactions:** Show realistic dialogue or exchanges.
3. **Explore Outcomes:** Highlight key insights from the simulation.
4. **Synthesize Learnings:** Extract actionable conclusions."""
        }

# Uso del assembler
assembler = PromptAssembler()
result = assembler(
    objective="Design ADR process",
    role="You are a World-Class Software Architect...",
    directive="To design and detail a robust...",
    framework="chain-of-thought",
    guardrails=["Avoid jargon", "Prioritize pragmatism"]
)

print(result.assembled_prompt)
```

---

**Próximo documento:**
- `05-quality-validation-system.md` - Sistema de validación de calidad
