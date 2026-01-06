# Template Library - Análisis Completo

**Prioridad:** 🔴 CRÍTICA - Base de conocimiento para DSPy
**Fuente:** Architect v3.2.0 - `simulation/db.ts` + `services/templateRecommendationService.ts`
**Adaptabilidad:** Estructura可直接 aplicable a Raycast

---

## 📋 Índice

1. [Overview de la Biblioteca](#overview-de-la-biblioteca)
2. [Estructura de Datos](#estructura-de-datos)
3. [Categorías de Templates](#categorías-de-templates)
4. [Componentes de Templates](#componentes-de-templates)
5. [Templates Completos - Ejemplos](#templates-completos---ejemplos)
6. [Sistema de Recomendación](#sistema-de-recomendación)
7. [Similitud y Matching](#similitud-y-matching)
8. [Aplicación a DSPy](#aplicación-a-dspy)

---

## Overview de la Biblioteca

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TEMPLATE LIBRARY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐                                                    │
│  │  10 CATEGORIES │                                                    │
│  │  (Domain-based)│                                                    │
│  └────────┬───────┘                                                    │
│           │                                                            │
│           ↓                                                            │
│  ┌────────────────┐                                                    │
│  │   4 COMPONENTS │──────────────┐                                     │
│  │   per Template │              │                                     │
│  └────────┬───────┘              │                                     │
│           │                      │                                     │
│           ↓                      │                                     │
│  ┌────────────────┐              │                                     │
│  │   COMPONENTS   │              │                                     │
│  │   (30+ items)  │◄─────────────┘                                     │
│  └────────────────┘                                                    │
│           ↑                                                            │
│           │                                                            │
│  ┌────────┴───────┐    ┌─────────────────┐    ┌─────────────────┐    │
│  │   ROLE         │    │   DIRECTIVE     │    │   FRAMEWORK     │    │
│  │   (9 items)    │    │   (7 items)     │    │   (2 items)     │    │
│  └────────────────┘    └─────────────────┘    └─────────────────┘    │
│                                                                         │
│  ┌─────────────────┐                                                   │
│  │   CONSTRAINTS   │                                                   │
│  │   (12 items)    │                                                   │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estadísticas Actuales

| Métrica | Cantidad | Notas |
|---------|----------|-------|
| **Categorías** | 10 | 3 originales + 7 especializadas |
| **Roles** | 9 | Expertise variado |
| **Directives** | 7 | Por dominio |
| **Frameworks** | 2 | CoT y ToT principales |
| **Constraints** | 12 | Específicos por contexto |
| **Templates Completos** | 4+ | En base de datos simulada |
| **Promedio Rating** | 4.5-4.9 | Alta calidad general |

---

## Estructura de Datos

### SotaTemplateDB Interface

```typescript
// simulation/db.ts - Database Schema
export interface SotaTemplateDB {
  id: string;                    // Identificador único
  name: string;                  // Nombre del template
  description: string;           // Descripción del caso de uso
  categoryId: string;            // Categoría a la que pertenece
  componentIds: {
    role: string;                // ID del componente de rol
    directive: string;           // ID del componente de directiva
    framework: string;           // ID del componente de framework
    constraints: string[];       // IDs de componentes de restricciones
  };
  usageCount: number;            // Veces utilizado
  averageRating: number;         // Rating promedio (0-5)
  ratingCount: number;           // Cantidad de ratings
  createdAt: string;             // Fecha de creación (ISO)
}
```

### PromptComponent Interface

```typescript
// Componentes individuales que pueden reutilizarse
export interface PromptComponent {
  id: string;
  componentType: 'role' | 'directive' | 'framework' | 'constraint';
  name: string;                  // Nombre descriptivo
  content: string;               // Contenido del componente
}
```

### Category Interface

```typescript
export interface Category {
  id: string;
  name: string;
  description: string;
}
```

### EnhancedSotaTemplate (Frontend)

```typescript
// types.ts - Frontend interface con componentes hidratados
export interface EnhancedSotaTemplate extends SotaTemplate {
  components: {
    role: ComponentContent;
    directive: ComponentContent;
    framework: ComponentContent;
    constraints: ComponentContent[];
  };
  externalMetadata?: {
    importDate?: string;
    lastModified?: string;
    extractedTags?: string[];
  };
}

export interface ComponentContent {
  name: string;
  content: string;
}
```

---

## Categorías de Templates

### Las 10 Categorías

```typescript
const categories: Category[] = [
  // === ORIGINALES (3) ===
  {
    id: 'cat-sw-arch',
    name: 'Software Architecture',
    description: 'Templates for designing robust and scalable software systems.'
  },
  {
    id: 'cat-marketing',
    name: 'Marketing & Strategy',
    description: 'Templates for planning and executing marketing campaigns.'
  },
  {
    id: 'cat-research',
    name: 'Scientific Research',
    description: 'Templates for structuring research proposals and experiments.'
  },

  // === ESPECIALIZADAS (7) ===
  {
    id: 'cat-ai-agents',
    name: 'AI Agents',
    description: 'Specialized AI agent templates and configurations for different roles and personalities.'
  },
  {
    id: 'cat-commands',
    name: 'Commands',
    description: 'Slash command templates and automation scripts for streamlined workflows.'
  },
  {
    id: 'cat-claude-projects',
    name: 'Claude Projects',
    description: 'Claude-specific project templates and configurations for domain-specific tasks.'
  },
  {
    id: 'cat-meta-prompts',
    name: 'Meta Prompts',
    description: 'Templates for generating, optimizing, and improving other prompts.'
  },
  {
    id: 'cat-workflows',
    name: 'Workflows',
    description: 'Multi-step workflow templates and process automation frameworks.'
  },
  {
    id: 'cat-research-templates',
    name: 'Research Templates',
    description: 'Research analysis, investigation, and synthesis templates.'
  },
  {
    id: 'cat-operations',
    name: 'Operations',
    description: 'Operational procedures, incident response, and audit templates.'
  }
];
```

### Uso de Categorías

```typescript
// Filtrar templates por categoría
const templatesByCategory = templates.filter(
  t => t.categoryId === 'cat-sw-arch'
);

// Obtener templates de múltiples categorías
const multiCategoryTemplates = templates.filter(
  t => ['cat-sw-arch', 'cat-ai-agents'].includes(t.categoryId)
);
```

---

## Componentes de Templates

### 1. Roles (9 componentes)

Los roles definen la persona, expertise y estilo de comunicación del AI.

#### Software Architecture Roles

```typescript
{
  id: 'role-sw-architect',
  componentType: 'role',
  name: 'World-Class Software Architect',
  content: `You are an expert-level AI planning agent embodying the persona of a **World-Class Software Architect** with over 20 years of experience leading complex digital transformations. You are not just a drafter; you are a strategic thinker who balances technical excellence with business acumen. Your communication is precise, your reasoning is transparent, and your decisions are always traceable to first principles.`
}
```

**Análisis del patrón:**
- ✅ **Expertise específico**: "World-Class Software Architect"
- ✅ **Experiencia cuantificada**: "over 20 years"
- ✅ **Contexto de aplicación**: "digital transformations"
- ✅ **Balance habilidades**: "technical excellence with business acumen"
- ✅ **Estilo de comunicación**: "precise", "transparent"
- ✅ **Metodología**: "traceable to first principles"

#### Marketing Role

```typescript
{
  id: 'role-mktg-strat',
  componentType: 'role',
  name: 'Senior Marketing Strategist',
  content: `You are a **Senior Marketing Strategist** with a decade of experience in launching global brands. You are data-driven, customer-obsessed, and an expert in digital channels. Your thinking is focused on ROI, brand positioning, and creating measurable impact. You must communicate with clarity and persuasive, executive-level language.`
}
```

**Análisis del patrón:**
- ✅ **Experiencia**: "a decade", "launching global brands"
- ✅ **Enfoque**: "data-driven", "customer-obsessed"
- ✅ **Expertise**: "digital channels", "ROI", "brand positioning"
- ✅ **Estilo**: "clarity", "persuasive", "executive-level"

#### Research Role

```typescript
{
  id: 'role-sci-researcher',
  componentType: 'role',
  name: 'Lead Scientific Researcher',
  content: `You are a **Lead Scientific Researcher** with a Ph.D. in your field and a portfolio of peer-reviewed publications. You are meticulous, analytical, and deeply skeptical. Your reasoning must be based on evidence, logical deduction, and established scientific principles. You must formulate hypotheses, design experiments, and interpret data with rigorous intellectual honesty.`
}
```

**Análisis del patrón:**
- ✅ **Credenciales**: "Ph.D.", "peer-reviewed publications"
- ✅ **Cualidades**: "meticulous", "analytical", "skeptical"
- ✅ **Metodología**: "evidence", "logical deduction", "scientific principles"
- ✅ **Tareas**: "formulate hypotheses", "design experiments", "interpret data"
- ✅ **Estándar**: "rigorous intellectual honesty"

#### Specialized Roles (Collection Categories)

```typescript
// Customer Service
{
  id: 'role-customer-service-agent',
  componentType: 'role',
  name: 'Customer Service Agent',
  content: `You are a professional customer service agent with excellent communication skills and deep product knowledge. You are empathetic, patient, and focused on providing exceptional customer experiences while efficiently resolving issues.`
}

// Code Reviewer
{
  id: 'role-code-reviewer',
  componentType: 'role',
  name: 'Senior Code Reviewer',
  content: `You are an experienced senior developer specializing in code review and quality assurance. You have a keen eye for potential issues, security vulnerabilities, and performance bottlenecks. Your feedback is constructive, educational, and focused on maintaining high code quality standards.`
}

// Claude Project Architect
{
  id: 'role-project-architect',
  componentType: 'role',
  name: 'Claude Project Architect',
  content: `You are an expert in configuring Claude projects for specific domains and workflows. You understand how to structure prompts, set up tools, and optimize Claude's capabilities for particular use cases and industries.`
}

// Prompt Engineer
{
  id: 'role-prompt-engineer',
  componentType: 'role',
  name: 'Prompt Engineer',
  content: `You are a specialized prompt engineer with expertise in crafting, optimizing, and troubleshooting prompts. You understand the nuances of AI model behavior and can create prompts that elicit precise, reliable responses.`
}

// Workflow Automator
{
  id: 'role-workflow-automator',
  componentType: 'role',
  name: 'Workflow Automation Specialist',
  content: `You are an expert in designing and implementing automated workflows. You can break down complex processes into manageable steps and create efficient automation that reduces manual effort and improves consistency.`
}

// Research Analyst
{
  id: 'role-research-analyst',
  componentType: 'role',
  name: 'Research Analyst',
  content: `You are a skilled research analyst with expertise in gathering, synthesizing, and presenting information from multiple sources. You are methodical, thorough, and able to identify key insights and patterns in complex data.`
}

// Incident Responder
{
  id: 'role-incident-responder',
  componentType: 'role',
  name: 'Incident Response Specialist',
  content: `You are an experienced incident response specialist with expertise in managing and resolving technical issues under pressure. You are systematic, calm, and focused on minimizing impact while restoring normal operations.`
}
```

### Patrones de Roles Identificados

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| **Opening** | "You are a [ROLE]..." | "You are a Senior Marketing Strategist" |
| **Experience** | Quantified timeframe | "with over 20 years of experience" |
| **Expertise** | Specific domain | "leading complex digital transformations" |
| **Style** | Communication approach | "precise, transparent reasoning" |
| **Focus** | Key priorities | "ROI, brand positioning, measurable impact" |
| **Standard** | Quality bar | "rigorous intellectual honesty" |

### 2. Directives (7 componentes)

Las directivas definen la misión última y las instrucciones específicas.

#### ADR Directive

```typescript
{
  id: 'dir-adr',
  componentType: 'directive',
  name: 'Design ADR Process',
  content: `To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs). This is not about creating bureaucracy; it's about building a system of "durable, asynchronous communication" that safeguards the architectural integrity of our software as it evolves.`
}
```

**Análisis del patrón:**
- ✅ **Verbo de acción**: "design and detail"
- ✅ **Cualidades**: "robust, scalable, developer-friendly"
- ✅ **Objetivo claro**: "Architecture Decision Records (ADRs)"
- ✅ **Clarificación negativa**: "not about creating bureaucracy"
- ✅ **Propósito superior**: "durable, asynchronous communication"
- ✅ **Outcome**: "safeguards architectural integrity"

#### Product Launch Directive

```typescript
{
  id: 'dir-product-launch',
  componentType: 'directive',
  name: 'Plan a Product Launch',
  content: `To create a comprehensive, multi-channel marketing plan for a new SaaS product launch. The goal is to maximize market penetration, generate 1,000 marketing-qualified leads (MQLs) in the first quarter, and establish a strong brand presence in a competitive landscape.`
}
```

**Análisis del patrón:**
- ✅ **Verbo**: "create"
- ✅ **Alcance**: "comprehensive, multi-channel"
- ✅ **Objetivo**: "SaaS product launch"
- ✅ **Métricas específicas**: "1,000 MQLs in first quarter"
- ✅ **Outcomes múltiples**: "market penetration", "brand presence"

#### Research Proposal Directive

```typescript
{
  id: 'dir-research-proposal',
  componentType: 'directive',
  name: 'Develop Research Proposal',
  content: `To develop a comprehensive research proposal to investigate the efficacy of a new drug candidate. The proposal must be detailed enough to submit for grant funding and ethical review. It must clearly state the hypothesis, methodology, expected outcomes, and potential impact.`
}
```

**Análisis del patrón:**
- ✅ **Verbo**: "develop"
- ✅ **Estándar**: "detailed enough to submit for grant funding"
- ✅ **Componentes requeridos**: "hypothesis, methodology, expected outcomes, potential impact"
- ✅ **Stakeholders**: "grant funding and ethical review"

#### Specialized Directives

```typescript
// Customer Inquiry
{
  id: 'dir-handle-inquiry',
  componentType: 'directive',
  name: 'Handle Customer Inquiry',
  content: `To professionally handle customer inquiries with empathy and efficiency, providing accurate information and ensuring customer satisfaction while following company policies and procedures.`
}

// Code Review
{
  id: 'dir-perform-review',
  componentType: 'directive',
  name: 'Perform Code Review',
  content: `To conduct a thorough code review focusing on functionality, security, performance, and maintainability. Provide constructive feedback that helps improve code quality and team knowledge.`
}

// Configure Claude Project
{
  id: 'dir-configure-project',
  componentType: 'directive',
  name: 'Configure Claude Project',
  content: `To set up and optimize a Claude project configuration for specific use cases, including prompt structure, tool selection, and capability optimization.`
}

// Optimize Prompt
{
  id: 'dir-optimize-prompt',
  componentType: 'directive',
  name: 'Optimize Prompt Performance',
  content: `To analyze and improve existing prompts for better clarity, effectiveness, and reliability. Identify weaknesses and implement enhancements that elicit more consistent and accurate responses.`
}

// Design Workflow
{
  id: 'dir-design-workflow',
  componentType: 'directive',
  name: 'Design Automated Workflow',
  content: `To create a comprehensive automated workflow that reduces manual effort, improves consistency, and streamlines complex processes through intelligent automation and integration.`
}

// Conduct Research
{
  id: 'dir-conduct-research',
  componentType: 'directive',
  name: 'Conduct Research Analysis',
  content: `To systematically gather, analyze, and synthesize information from multiple sources to identify patterns, insights, and evidence-based conclusions that support decision-making.`
}

// Manage Incident
{
  id: 'dir-manage-incident',
  componentType: 'directive',
  name: 'Manage Incident Response',
  content: `To effectively manage technical incidents from detection through resolution, minimizing impact, communicating clearly with stakeholders, and implementing preventive measures for the future.`
}
```

### Patrones de Directives Identificados

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| **Infinitivo** | "To [verb]..." | "To design and detail..." |
| **Cualificadores** | Adjetivos de calidad | "robust, scalable, developer-friendly" |
| **Objetivo** | Entidad específica | "Architecture Decision Records" |
| **Clarificación** | "This is not X; it's Y" | "not bureaucracy; it's communication" |
| **Outcome** | Resultado final | "safeguards architectural integrity" |
| **Métricas** | Números cuantificables | "1,000 MQLs in Q1" |

### 3. Frameworks (2 componentes)

Los frameworks definen el modelo de razonamiento.

#### Chain-of-Thought (CoT)

```typescript
{
  id: 'fw-cot',
  componentType: 'framework',
  name: 'Chain-of-Thought',
  content: `You must use the Chain-of-Thought framework to structure your entire response. Your output should be a direct reflection of this sequential reasoning process. Follow these steps precisely and use them as section headers in your final output.

1. **Synthesize the "Why":** Begin with a high-level strategic analysis.
2. **Deconstruct the Problem:** Break down the core directive into its essential components.
3. **Design the Solution - Step-by-Step:** Address each component with a detailed solution.
4. **Synthesize and Plan:** Consolidate the solutions into a cohesive, actionable implementation plan.`
}
```

**Análisis del patrón:**
- ✅ **Obligación**: "must use"
- ✅ **Estructura**: "section headers in your final output"
- ✅ **Pasos secuenciales**: 1, 2, 3, 4
- ✅ **Nombres descriptivos**: "Synthesize the Why", "Deconstruct", etc.
- ✅ **Acción por paso**: Verbo imperativo + descripción

#### Tree of Thoughts (ToT)

```typescript
{
  id: 'fw-tot',
  componentType: 'framework',
  name: 'Tree of Thoughts',
  content: `You must use the Tree of Thoughts framework to structure your entire response. Your output should explore multiple solution paths before converging on an optimal one. Follow these steps precisely...

1. **Identify Key Decision Forks.**
2. **Explore Branches (Thoughts).**
3. **Evaluate and Prune.**
4. **Synthesize the Final Path.`
}
```

### 4. Constraints (12 componentes)

Las restricciones definen reglas y límites.

#### Original Constraints

```typescript
// Clarity and Conciseness
{
  id: 'con-clarity',
  componentType: 'constraint',
  name: 'Clarity and Conciseness',
  content: 'Avoid jargon where possible. Explain complex ideas simply.'
}

// Pragmatism
{
  id: 'con-pragmatism',
  componentType: 'constraint',
  name: 'Pragmatism over Dogmatism',
  content: 'Prioritize what works in practice over theoretical perfection.'
}

// Actionability
{
  id: 'con-actionable',
  componentType: 'constraint',
  name: 'Actionability',
  content: 'Every recommendation must be a concrete, actionable step.'
}

// Integration
{
  id: 'con-integration',
  componentType: 'constraint',
  name: 'Integration with Dev Tools',
  content: 'The plan must consider integration with common developer tools like Git and Pull Requests.'
}

// Budget
{
  id: 'con-budget',
  componentType: 'constraint',
  name: 'Budget-Conscious',
  content: 'All proposed activities must fall within a strict budget of $50,000.'
}

// Data-Driven
{
  id: 'con-data-driven',
  componentType: 'constraint',
  name: 'Data-Driven',
  content: 'Every strategic choice must be backed by data, market research, or a clear hypothesis to be tested.'
}
```

#### Specialized Constraints

```typescript
// Empathy
{
  id: 'con-empathy',
  componentType: 'constraint',
  name: 'Empathy and Professionalism',
  content: 'Always maintain an empathetic tone while upholding professional standards and company values.'
}

// Security
{
  id: 'con-security',
  componentType: 'constraint',
  name: 'Security-First Approach',
  content: 'Prioritize security considerations in all recommendations and implementations.'
}

// Claude Optimization
{
  id: 'con-claude-optimization',
  componentType: 'constraint',
  name: 'Claude Capabilities',
  content: 'Optimize for Claude\'s specific strengths and limitations in project configuration.'
}

// Prompt Testing
{
  id: 'con-prompt-testing',
  componentType: 'constraint',
  name: 'Test and Validate',
  content: 'Always test prompt improvements and validate results before finalizing changes.'
}

// Workflow Integration
{
  id: 'con-workflow-integration',
  componentType: 'constraint',
  name: 'Tool Integration',
  content: 'Ensure workflows integrate seamlessly with existing tools and systems.'
}

// Research Integrity
{
  id: 'con-research-integrity',
  componentType: 'constraint',
  name: 'Research Integrity',
  content: 'Maintain high standards of research integrity, cite sources properly, and avoid bias.'
}

// Incident Protocol
{
  id: 'con-incident-protocol',
  componentType: 'constraint',
  name: 'Follow Incident Protocol',
  content: 'Adhere strictly to established incident response protocols and communication procedures.'
}
```

---

## Templates Completos - Ejemplos

### Template 1: Plan for ADR Process

```typescript
{
  id: 'template-adr',
  name: 'Plan for ADR Process',
  description: 'A comprehensive template for architects to design a lightweight and effective Architecture Decision Record (ADR) process for their team.',
  categoryId: 'cat-sw-arch',
  componentIds: {
    role: 'role-sw-architect',
    directive: 'dir-adr',
    framework: 'fw-cot',
    constraints: ['con-clarity', 'con-pragmatism', 'con-actionable', 'con-integration']
  },
  usageCount: 142,
  averageRating: 4.8,
  ratingCount: 25,
  createdAt: '2023-10-26T10:00:00Z'
}
```

**Prompt Final Ensamblado:**

```
**[ROLE & PERSONA]**
You are an expert-level AI planning agent embodying the persona of a **World-Class Software Architect** with over 20 years of experience leading complex digital transformations. You are not just a drafter; you are a strategic thinker who balances technical excellence with business acumen. Your communication is precise, your reasoning is transparent, and your decisions are always traceable to first principles.

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

### Template 2: SaaS Product Launch Marketing Plan

```typescript
{
  id: 'template-product-launch',
  name: 'SaaS Product Launch Marketing Plan',
  description: 'A strategic template for marketing leaders to plan the launch of a new SaaS product, focusing on lead generation and brand presence.',
  categoryId: 'cat-marketing',
  componentIds: {
    role: 'role-mktg-strat',
    directive: 'dir-product-launch',
    framework: 'fw-cot',
    constraints: ['con-data-driven', 'con-budget', 'con-actionable']
  },
  usageCount: 215,
  averageRating: 4.6,
  ratingCount: 42,
  createdAt: '2023-10-20T11:00:00Z'
}
```

### Template 3: Scientific Research Proposal

```typescript
{
  id: 'template-research-proposal',
  name: 'Scientific Research Proposal',
  description: 'A rigorous template for scientists to structure a detailed research proposal suitable for grant applications and ethical review boards.',
  categoryId: 'cat-research',
  componentIds: {
    role: 'role-sci-researcher',
    directive: 'dir-research-proposal',
    framework: 'fw-cot',
    constraints: ['con-clarity', 'con-data-driven']
  },
  usageCount: 78,
  averageRating: 4.9,
  ratingCount: 18,
  createdAt: '2023-11-01T12:00:00Z'
}
```

### Template 4: Microservice Architecture Design

```typescript
{
  id: 'template-microservice-design',
  name: 'Microservice Architecture Design',
  description: 'Use the Tree of Thoughts framework to explore different architectural choices for a new e-commerce microservice (e.g., shopping cart).',
  categoryId: 'cat-sw-arch',
  componentIds: {
    role: 'role-sw-architect',
    directive: 'Design a scalable and resilient microservice architecture for a new e-commerce shopping cart feature. The design must handle high traffic, be independently deployable, and easy to maintain.',
    framework: 'fw-tot',
    constraints: ['con-pragmatism', 'con-actionable']
  },
  usageCount: 95,
  averageRating: 4.5,
  ratingCount: 31,
  createdAt: '2023-11-05T14:00:00Z'
}
```

---

## Sistema de Recomendación

### TemplateRecommendationService

El servicio de recomendación proporciona sugerencias inteligentes basadas en:

1. **Similitud semántica** del objetivo
2. **Calidad del template** (rating, usage)
3. **Contexto del usuario** (preferencias, historial)
4. **Eficiencia de tokens**

### Interfaces del Servicio

```typescript
// Solicitud de recomendación
export interface RecommendationRequest {
  objective: string;                        // Objetivo del usuario
  currentStep?: "objective" | "role" | "directive" | "framework" | "guardrails";
  currentContent?: Partial<PlanData>;       // Contenido de pasos previos
  userPreferences?: {
    preferredFramework?: ReasoningFramework;
    complexityLevel?: "basic" | "intermediate" | "advanced";
    tokenLimit?: number;
    qualityThreshold?: number;              // Rating mínimo (0-5)
  };
  context?: {
    industry?: string;
    useCase?: string;
    audience?: string;
  };
}

// Resultado de recomendación
export interface RecommendationResult {
  recommendations: TemplateRecommendation[];      // Templates completos
  componentSuggestions: ComponentSuggestion[];     // Componentes individuales
  insights: RecommendationInsights;                // Estadísticas
  processingTime: number;                          // ms
}

// Recomendación individual
export interface TemplateRecommendation {
  template: EnhancedSotaTemplate;
  relevanceScore: number;                    // 0-1
  matchReason: string;                       // "💡 Basado en X..."
  estimatedQuality: number;                  // 0-5
  tokenEfficiency: number;                   // 0-1
  suggestedModifications?: TemplateModification[];
  useCase: "exact_match" | "close_match" | "component_source" | "inspiration";
}
```

### Algoritmo de Recomendación

```typescript
// services/templateRecommendationService.ts
class TemplateRecommendationService {
  async getRecommendations(
    request: RecommendationRequest,
    availableTemplates: EnhancedSotaTemplate[]
  ): Promise<RecommendationResult> {
    // 1. Buscar templates similares por objetivo
    const similarTemplates =
      await duplicateDetectionService.findSimilarTemplatesByObjective(
        request.objective,
        availableTemplates,
        this.MAX_RECOMMENDATIONS * 2
      );

    // 2. Procesar y filtrar recomendaciones
    const recommendations = await this.processRecommendations(
      similarTemplates,
      request,
      availableTemplates
    );

    // 3. Obtener sugerencias de componentes específicos
    const componentSuggestions = await this.getComponentSuggestions(
      request,
      availableTemplates
    );

    // 4. Generar insights estadísticos
    const insights = this.generateInsights(
      recommendations,
      availableTemplates
    );

    return {
      recommendations: recommendations.slice(0, 5), // Top 5
      componentSuggestions,
      insights,
      processingTime: Date.now() - startTime
    };
  }
}
```

### Filtros de Usuario

```typescript
private passesUserFilters(
  template: EnhancedSotaTemplate,
  preferences?: RecommendationRequest["userPreferences"]
): boolean {
  if (!preferences) return true;

  // Verificar umbral de calidad
  if (
    preferences.qualityThreshold &&
    template.averageRating < preferences.qualityThreshold
  ) {
    return false;
  }

  // Verificar preferencia de framework
  if (preferences.preferredFramework) {
    const templateFramework = template.components.framework.content;
    if (templateFramework !== preferences.preferredFramework) {
      return false;
    }
  }

  // Verificar límite de tokens
  if (preferences.tokenLimit) {
    const estimatedTokens = this.estimateTokens(template);
    if (estimatedTokens > preferences.tokenLimit) {
      return false;
    }
  }

  return true;
}
```

---

## Similitud y Matching

### Algoritmos de Similitud

```typescript
// services/duplicateDetectionService.ts

// 1. Jaccard Similarity (para keywords)
function jaccardSimilarity(set1: string[], set2: string[]): number {
  const intersection = set1.filter(x => set2.includes(x));
  const union = [...new Set([...set1, ...set2])];
  return intersection.length / union.length;
}

// 2. Levenshtein Distance (para texto)
function levenshteinSimilarity(str1: string, str2: string): number {
  const distance = levenshtein(str1, str2);
  const maxLength = Math.max(str1.length, str2.length);
  return 1 - (distance / maxLength);
}

// 3. Cosine Similarity (para embeddings)
function cosineSimilarity(embed1: number[], embed2: number[]): number {
  const dotProduct = embed1.reduce((sum, a, i) => sum + a * embed2[i], 0);
  const magnitude1 = Math.sqrt(embed1.reduce((sum, a) => sum + a * a, 0));
  const magnitude2 = Math.sqrt(embed2.reduce((sum, a) => sum + a * a, 0));
  return dotProduct / (magnitude1 * magnitude2);
}

// 4. Combined Score
function calculateSimilarity(
  template: EnhancedSotaTemplate,
  objective: string
): number {
  const keywords = extractKeywords(objective);
  const templateKeywords = extractKeywords(template.description);

  const jaccardScore = jaccardSimilarity(keywords, templateKeywords);
  const levenshteinScore = levenshteinSimilarity(objective, template.description);
  const cosineScore = cosineSimilarity(
    embed(objective),
    embed(template.description)
  );

  // Weighted combination
  return (
    jaccardScore * 0.3 +
    levenshteinScore * 0.3 +
    cosineScore * 0.4
  );
}
```

### Umbrales de Matching

```typescript
const MATCH_THRESHOLDS = {
  EXACT_MATCH: 0.85,      // 85%+ similitud
  CLOSE_MATCH: 0.6,       // 60-85% similitud
  COMPONENT_SOURCE: 0.4,  // 40-60% similitud
  INSPIRATION: 0.0        // <40% similitud
};

function determineUseCase(relevanceScore: number): TemplateRecommendation["useCase"] {
  if (relevanceScore > 0.85) return "exact_match";
  if (relevanceScore > 0.6) return "close_match";
  if (relevanceScore > 0.4) return "component_source";
  return "inspiration";
}
```

---

## Aplicación a DSPy

### Mapeo a DSPy Signatures

```python
import dspy

# Role Signature
class RoleSignature(dspy.Signature):
    """Define AI persona and expertise"""
    objective = dspy.InputField(desc="User's high-level goal")
    role = dspy.OutputField(desc="AI persona description with expertise and experience")

# Directive Signature
class DirectiveSignature(dspy.Signature):
    """Define core instruction and mission"""
    objective = dspy.InputField(desc="User's high-level goal")
    role = dspy.InputField(desc="AI persona")
    directive = dspy.OutputField(desc="Core instruction with specific outcomes")

# Framework Signature
class FrameworkSignature(dspy.Signature):
    """Select reasoning framework"""
    objective = dspy.InputField(desc="User's high-level goal")
    framework = dspy.OutputField(desc="Best reasoning framework: CoT, ToT, Decomposition, or Role-Playing")

# Guardrails Signature
class GuardrailsSignature(dspy.Signature):
    """Generate relevant constraints"""
    objective = dspy.InputField(desc="User's high-level goal")
    framework = dspy.InputField(desc="Selected reasoning framework")
    guardrails = dspy.OutputField(desc="List of 3-5 relevant constraints")

# Unified Prompt Signature
class UnifiedPromptGeneration(dspy.Signature):
    """Generate complete prompt from objective only"""
    objective = dspy.InputField(desc="User's goal or task")
    complete_prompt = dspy.OutputField(desc="State-of-the-art prompt with role, directive, framework, guardrails")
```

### DSPy Program con Template Retrieval

```python
class TemplateBasedPromptWizard(dspy.Module):
    """DSPy program that uses template library for few-shot examples"""

    def __init__(self, template_index):
        super().__init__()
        self.template_index = template_index  # Vector index of templates
        self.role_generator = dspy.Predict(RoleSignature)
        self.directive_generator = dspy.Predict(DirectiveSignature)
        self.framework_recommender = dspy.Predict(FrameworkSignature)
        self.guardrail_generator = dspy.Predict(GuardrailsSignature)

    def forward(self, objective: str) -> dspy.Prediction:
        # 1. Retrieve similar templates (RAG)
        similar_templates = self.template_index.search(objective, k=3)

        # 2. Use retrieved templates as few-shot examples
        few_shot_examples = [
            {
                "objective": t.description,
                "role": t.components.role.content,
                "directive": t.components.directive.content,
                "framework": t.components.framework.content,
                "guardrails": [c.content for c in t.components.constraints]
            }
            for t in similar_templates
        ]

        # 3. Generate each component using few-shot prompting
        role = self.role_generator(
            objective=objective,
            few_shot_examples=few_shot_examples
        )

        directive = self.directive_generator(
            objective=objective,
            role=role.role,
            few_shot_examples=few_shot_examples
        )

        framework = self.framework_recommender(
            objective=objective,
            few_shot_examples=few_shot_examples
        )

        guardrails = self.guardrail_generator(
            objective=objective,
            framework=framework.framework,
            few_shot_examples=few_shot_examples
        )

        # 4. Assemble final prompt
        return dspy.Prediction(
            role=role.role,
            directive=directive.directive,
            framework=framework.framework,
            guardrails=guardrails.guardrails,
            complete_prompt=self.assemble_prompt(
                role.role,
                directive.directive,
                framework.framework,
                guardrails.guardrails
            )
        )

    def assemble_prompt(self, role, directive, framework, guardrails):
        return f"""**[ROLE & PERSONA]**
{role}

**[CORE DIRECTIVE]**
**Your ultimate mission is:** {directive}

**[EXECUTION FRAMEWORK: {framework}]**
{self.get_framework_description(framework)}

**[CONSTRAINTS & GUARDRAILS]**
You must adhere to the following rules:
{chr(10).join(f'*   {g}' for g in guardrails)}

**[FINAL OUTPUT]**
Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan."""
```

### Template Index para DSPy

```python
from typing import List
import numpy as np

class TemplateIndex:
    """Vector index for template retrieval"""

    def __init__(self, templates: List[EnhancedSotaTemplate], embedder):
        self.templates = templates
        self.embedder = embedder

        # Pre-compute embeddings
        self.embeddings = np.array([
            embedder.embed(t.description)
            for t in templates
        ])

    def search(self, query: str, k: int = 3) -> List[EnhancedSotaTemplate]:
        """Search for similar templates using cosine similarity"""
        query_embedding = self.embedder.embed(query)

        # Compute cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) *
            np.linalg.norm(query_embedding)
        )

        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        return [
            self.templates[i]
            for i in top_k_indices
        ]
```

### One-Step DSPy Program

```python
class OneStepWizard(dspy.Module):
    """Generate complete prompt in single step using DSPy optimization"""

    def __init__(self, template_index):
        super().__init__()
        self.template_index = template_index
        self.generator = dspy.Predict(UnifiedPromptGeneration)
        self.optimizer = dspy.BootstrapFewShot(max_bootstrapped_demos=3)

    def forward(self, objective: str) -> dspy.Prediction:
        # Retrieve similar templates for context
        similar_templates = self.template_index.search(objective, k=3)

        # Generate complete prompt in one call
        result = self.generator(
            objective=objective,
            context=[t.description for t in similar_templates]
        )

        return result

# Optimize with examples
def train_one_step_wizard():
    """Train the one-step wizard with template library as examples"""

    # Load template library
    templates = load_template_library()

    # Create template index
    embedder = LocalEmbedder()  # or OpenAIEmbedder()
    template_index = TemplateIndex(templates, embedder)

    # Create program
    program = OneStepWizard(template_index)

    # Create training data from templates
    trainset = [
        dspy.Example(
            objective=t.description,
            complete_prompt=assemble_prompt_from_template(t)
        )
        for t in templates
    ]

    # Optimize
    optimized_program = program.optimizer.compile(
        program=program,
        trainset=trainset
    )

    return optimized_program
```

---

**Próximos documentos:**
- `03-dspy-integration-guide.md` - Guía completa de integración DSPy
- `04-prompt-assembly-patterns.md` - Patrones de ensamblaje de prompts
