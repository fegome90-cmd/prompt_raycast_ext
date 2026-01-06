# Prompt Wizard - Flujo Completo y Detallado

**Prioridad:** 🔴 CRÍTICA - Base para integración DSPy
**Fuente:** Architect v3.2.0 - Análisis completo de componentes
**Adaptabilidad:** Perfecta para entender el sistema actual antes de optimizar

---

## 📋 Índice

1. [Overview del Sistema](#overview-del-sistema)
2. [Flujo de 6 Pasos](#flujo-de-6-pasos)
3. [Step 0: Discovery (Opcional)](#step-0-discovery-opcional)
4. [Step 1: Objective](#step-1-objective)
5. [Step 2: Role & Persona](#step-2-role--persona)
6. [Step 3: Core Directive](#step-3-core-directive)
7. [Step 4: Execution Framework](#step-4-execution-framework)
8. [Step 5: Guardrails & Constraints](#step-5-guardrails--constraints)
9. [Step 6: Plan View & Assembly](#step-6-plan-view--assembly)
10. [Validaciones y Reglas](#validaciones-y-reglas)
11. [Manejo de Errores](#manejo-de-errores)

---

## Overview del Sistema

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROMPT WIZARD - 6 STEPS + DISCOVERY                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ STEP 0:      │ →  │ STEP 1:      │ →  │ STEP 2:      │             │
│  │ Discovery    │    │ Objective    │    │ Role         │             │
│  │ (Optional)   │    │ (Required)   │    │ (Required)   │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         ↓                   ↓                   ↓                       │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ STEP 3:      │ →  │ STEP 4:      │ →  │ STEP 5:      │             │
│  │ Directive    │    │ Framework    │    │ Guardrails   │             │
│  │ (Required)   │    │ (Required)   │    │ (Optional)   │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         ↓                   ↓                   ↓                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────┐                 │
│  │ STEP 6: Plan View & Assembly                      │                 │
│  │ Visualización completa + Guardado                │                 │
│  └──────────────────────────────────────────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estado Compartido (State)

```typescript
// Estado central del wizard
interface WizardState {
  // Progreso
  currentStep: number;           // 0-6

  // Datos del prompt (se construyen paso a paso)
  objective: string;             // STEP 1: El objetivo principal
  role: string;                  // STEP 2: El rol/persona del AI
  directive: string;             // STEP 3: Instrucciones específicas
  framework: ReasoningFramework; // STEP 4: Cómo debe pensar
  guardrails: string[];          // STEP 5: Restricciones y límites

  // Metadata
  promptName: string;            // STEP 6: Nombre para guardar
  isEditing: boolean;            // Si es edición o creación

  // Discovery (opcional)
  discoveredTemplates?: SotaTemplate[]; // Templates recomendados
  selectedTemplate?: SotaTemplate;      // Template aplicado
}
```

---

## Flujo de 6 Pasos

### Resumen Visual

```
STEP 0 (Optional): Discovery
├─ Input: Objetivo del usuario (min 5 chars)
├─ Proceso: Búsqueda de templates similares
├─ Output: Lista de recomendaciones
└─ Acción: Aplicar o "Crear desde cero"

STEP 1: Objective
├─ Input: "¿Qué quieres lograr?"
├─ Validación: Min 5 caracteres
└─ Output: objective string

STEP 2: Role & Persona
├─ Input: "¿Quién debe ser la IA?"
├─ Sugerencias: AI-powered basadas en objective
├─ Validación: Min 1 carácter
└─ Output: role string

STEP 3: Core Directive
├─ Input: "¿Cuál es la misión última?"
├─ Validación: No vacío
└─ Output: directive string

STEP 4: Execution Framework
├─ Opciones: CoT, ToT, Decomposition, Role-Playing
├─ Default: Chain-of-Thought
└─ Output: framework enum

STEP 5: Guardrails & Constraints
├─ Input: Lista de restricciones
├─ Sugerencias: Predefinidas
├─ Validación: Opcional
└─ Output: guardrails string[]

STEP 6: Plan View & Assembly
├─ Visualización: Prompt completo estructurado
├─ Input: Nombre del prompt
├─ Acciones: Copiar / Guardar
└─ Output: Prompt final guardado
```

---

## Step 0: Discovery (Opcional)

### Propósito
Encontrar templates existentes que coincidan con el objetivo del usuario para acelerar la creación y optimizar tokens.

### UI Components

**Título:** "Descubre Templates Inteligentes"
**Subtítulo:** "Describe tu objetivo y te recomendaremos templates probados de alta calidad para acelerar tu creación y optimizar el uso de tokens."

#### Input Field
```tsx
<Input>
  Label: "¿Qué quieres lograr con tu prompt?"
  Placeholder: "Ej: Analizar sentimiento de reseñas de productos, generar código Python para data science..."
  MinLength: 5 caracteres
  Trigger: Auto-search on type (debounce 500ms)
</Input>
```

### Comportamiento de Búsqueda

#### 1. Trigger Conditions
```typescript
// Usuario escribe objetivo
if (objective.length >= 5) {
  // Debounce 500ms después del último input
  setTimeout(() => {
    searchTemplates(objective);
  }, 500);
}
```

#### 2. Loading State
```typescript
{
  loading: true,
  message: "Analizando nuestro inventario de templates..."
}
```

#### 3. Success State
```typescript
interface RecommendationCard {
  template: SotaTemplate;
  matchLevel: "Exact match" | "Muy similar" | "Fuente de componentes" | "Inspiración";
  matchReason: string;        // "💡 Basado en tu objetivo de X..."
  qualityScore: number;        // 0-5 scale
  relevancePercentage: number; // 0-100
  tokenEfficiency: "Alta" | "Media" | "Baja";
  usageCount: number;
  badges: Badge[];
  suggestedModifications?: string[];
}
```

#### 4. Error State
```typescript
{
  error: true,
  message: "Error al buscar recomendaciones. Intenta de nuevo.",
  action: "Reintentar"
}
```

#### 5. No Results State
```typescript
{
  results: [],
  message: "No encontramos coincidencias exactas",
  action: "Crear desde cero"
}
```

### Algoritmo de Recomendación

```typescript
// services/templateRecommendationService.ts
async function getRecommendations(objective: string): Promise<RecommendationCard[]> {
  // 1. Extraer keywords del objective
  const keywords = extractKeywords(objective);

  // 2. Buscar templates similares
  const candidates = await templateRepository.search({
    keywords: keywords,
    threshold: 0.6 // Similarity threshold
  });

  // 3. Calcular scores de similitud
  const scored = candidates.map(template => ({
    template,
    jaccardScore: jaccardSimilarity(keywords, template.keywords),
    levenshteinScore: levenshteinSimilarity(objective, template.description),
    cosineScore: cosineSimilarity(embed(objective), embed(template.description))
  }));

  // 4. Combinar scores
  const ranked = scored.map(item => ({
    ...item,
    combinedScore: (
      item.jaccardScore * 0.3 +
      item.levenshteinScore * 0.3 +
      item.cosineScore * 0.4
    )
  })).sort((a, b) => b.combinedScore - a.combinedScore);

  // 5. Generar match reasons
  return ranked.slice(0, 5).map((item, index) => ({
    template: item.template,
    matchLevel: getMatchLevel(item.combinedScore),
    matchReason: generateMatchReason(objective, item.template),
    qualityScore: item.template.averageRating,
    relevancePercentage: Math.round(item.combinedScore * 100),
    tokenEfficiency: calculateTokenEfficiency(item.template),
    usageCount: item.template.usageCount,
    badges: generateBadges(item, index),
    suggestedModifications: generateModifications(objective, item.template)
  }));
}
```

### UI Cards Display

```tsx
// Cada tarjeta de recomendación
<Card>
  <Header>
    <Title>{template.name}</Title>
    <Badge>{matchLevel}</Badge>
  </Header>

  <Description>{template.description}</Description>

  <MatchReason>
    💡 {matchReason}
  </MatchReason>

  <Metrics>
    <Metric>
      <Icon>⭐</Icon>
      <Value>{qualityScore}/5</Value>
    </Metric>
    <Metric>
      <Icon>🎯</Icon>
      <Value>{relevancePercentage}%</Value>
    </Metric>
    <Metric>
      <Icon>🔥</Icon>
      <Value>{usageCount} usos</Value>
    </Metric>
    <Metric>
      <Icon>⚡</Icon>
      <Value>{tokenEfficiency} eficiencia</Value>
    </Metric>
  </Metrics>

  <Badges>
    {badges.map(badge => <Badge>{badge}</Badge>)}
  </Badges>

  {suggestedModifications && (
    <Modifications>
      <Title>Sugerencias:</Title>
      <ul>
        {suggestedModifications.map(m => <li>{m}</li>)}
      </ul>
    </Modifications>
  )}

  <ActionButton onClick={() => applyTemplate(template)}>
    Aplicar Template
  </ActionButton>
</Card>
```

### Badges System

```typescript
function generateBadges(item: ScoredItem, index: number): Badge[] {
  const badges: Badge[] = [];

  if (index === 0) badges.push("Perfecto para ti");
  if (item.template.averageRating >= 4.5) badges.push("Premium");
  if (item.template.usageCount > 100) badges.push("Popular");
  if (item.combinedScore < 0.8) badges.push("Requiere ajustes");

  return badges;
}
```

### Acciones Disponibles

```typescript
// Botones de navegación
const actions = {
  primary: {
    label: "Buscar Recomendaciones",
    disabled: objective.length < 5,
    onClick: () => searchTemplates(objective)
  },
  secondary: {
    label: "Crear desde cero",
    onClick: () => goToStep(1) // Skip to Step 1
  },
  tertiary: {
    label: "Reintentar",
    show: error,
    onClick: () => searchTemplates(objective)
  }
};
```

### Flujo de Aplicación de Template

```typescript
async function applyTemplate(template: SotaTemplate) {
  // 1. Extraer componentes del template
  const { role, directive, framework, constraints } = template.components;

  // 2. Mantener el objective del usuario (no sobrescribir)
  // 3. Prellenar todos los demás campos
  setWizardState({
    ...state,
    role: role.content,
    directive: directive.content,
    framework: framework.content as ReasoningFramework,
    guardrails: constraints.map(c => c.content)
  });

  // 4. Saltar al paso de Role (paso 2)
  // Usuario puede revisar y modificar antes de continuar
  setCurrentStep(2);
}
```

---

## Step 1: Objective

### Propósito
Establecer el objetivo claro y medible que el usuario quiere lograr.

### UI Components

**Título:** "What is your high-level objective?"
**Descripción:** "Describe the final goal you want the AI to achieve. Start with a verb."

#### Input Field
```tsx
<Textarea
  placeholder="e.g., Design a scalable and developer-friendly process for establishing Architecture Decision Records (ADRs)."
  minHeight="h-40" // 10rem
  value={objective}
  onChange={(e) => setObjective(e.target.value)}
/>
```

### Validaciones

```typescript
// Reglas de validación
const validations = {
  minLength: 5,           // Mínimo 5 caracteres
  required: true,         // Campo obligatorio
  trimWhitespace: true,   // Eliminar espacios al inicio/final

  // Indicadores visuales
  errorState: objective.length > 0 && objective.length < 5,
  successState: objective.length >= 5,

  // Mensajes
  errorMessage: objective.length > 0 && objective.length < 5
    ? "Mínimo 5 caracteres requeridos"
    : "Este campo es requerido"
};
```

### Ejemplos de Buenos Objetivos

```typescript
const goodExamples = [
  "Design a scalable process for Architecture Decision Records",
  "Generate comprehensive documentation for REST APIs",
  "Create a sentiment analysis system for product reviews",
  "Implement a caching strategy for API responses",
  "Design a database schema for multi-tenant SaaS"
];
```

### Ejemplos de Malos Objetivos

```typescript
const badExamples = [
  "help with code",           // Demasiado vago
  "something with AI",        // Sin contexto
  "",                         // Vacío
  "fix stuff",                // Sin especificar
  "make it better"            // Subjetivo
];
```

### Estado del Botón Next

```typescript
const nextButtonState = {
  disabled: objective.length < 5,
  text: "Next",
  tooltip: objective.length < 5
    ? "Escribe al menos 5 caracteres para continuar"
    : undefined
};
```

### Botón Back

```typescript
const backButtonState = {
  visible: currentStep > 1, // No visible en Step 1
  text: "Back",
  onClick: () => goToStep(currentStep - 1)
};
```

---

## Step 2: Role & Persona

### Propósito
Definir quién será la IA para cumplir el objetivo, estableciendo expertise, experiencia y estilo de comunicación.

### UI Components

**Título:** "Define el Rol & Persona de la IA"
**Descripción:** "¿Quién debe ser la IA? Sé específico sobre experiencia, conocimiento y estilo de comunicación."

#### AI-Powered Suggestions Section

```tsx
<SuggestionsPanel visible={objective.length > 5}>
  <Header>
    <Title>✨ Sugerencias de Roles Inteligentes</Title>
  </Header>

  <ContextMessage>
    Basado en tu objetivo "{objective}", estos roles han sido efectivos en casos similares:
  </ContextMessage>

  <SuggestionsList>
    {suggestions.map(suggestion => (
      <SuggestionCard key={suggestion.id}>
        <RoleContent>
          {truncate(suggestion.content, 2)} {/* 2 líneas max */}
        </RoleContent>

        <Metrics>
          <Metric type="quality">
            <Icon>⭐</Icon>
            <Value>{suggestion.qualityScore}/5</Value>
          </Metric>

          <Metric type="relevance">
            <Icon>🎯</Icon>
            <Value>{suggestion.relevanceScore}%</Value>
          </Metric>

          <Metric type="usage">
            <Icon>📊</Icon>
            <Value>{suggestion.usageCount} usos</Value>
          </Metric>
        </Metrics>

        <FitReason>
          {suggestion.fitReason}
        </FitReason>

        <ActionButton onClick={() => applySuggestion(suggestion)}>
          Usar
        </ActionButton>
      </SuggestionCard>
    ))}
  </SuggestionsList>
</SuggestionsPanel>
```

#### Main Input Field

```tsx
<Textarea
  placeholder="Ej: Eres un agente de planificación de IA de nivel experto que encarna la persona de un Arquitecto de Software de clase mundial con más de 20 años de experiencia en diseño de sistemas escalables, patrones arquitectónicos y mejores prácticas de desarrollo..."
  minHeight="h-48" // 12rem
  value={role}
  onChange={(e) => setRole(e.target.value)}
/>

<ValidationIndicators>
  <CharacterCount>
    <Value>{role.length}</Value>
    <Label>caracteres</Label>
    <Status color={role.length < 10 ? 'warning' : role.length < 20 ? 'good' : 'success'} />
  </CharacterCount>

  <SentenceCount>
    <Value>{countSentences(role)}</Value>
    <Label>oraciones</Label>
  </SentenceCount>

  {role.length > 10 && (
    <SuccessMessage>
      ✅ Buen nivel de detalle
    </SuccessMessage>
  )}
</ValidationIndicators>
```

#### Tips Section

```tsx
<TipsSection>
  <Title>Tips para un buen rol:</Title>
  <ul>
    <li>
      <Icon>💡</Icon>
      Especifica el nivel de experiencia
      <Example>(ej: "experto", "senior", "especialista")</Example>
    </li>
    <li>
      <Icon>🎯</Icon>
      Menciona el área de conocimiento relevante
      <Example>(ej: "data science", "marketing digital")</Example>
    </li>
    <li>
      <Icon>💬</Icon>
      Define el estilo de comunicación
      <Example>(ej: "amigable", "formal", "técnico")</Example>
    </li>
    <li>
      <Icon>📊</Icon>
      Incluye años de experiencia si es relevante
      <Example>(ej: "con más de 10 años en la industria")</Example>
    </li>
  </ul>
</TipsSection>
```

### Algoritmo de Sugerencias

```typescript
// services/duplicateDetectionService.ts
async function generateRoleSuggestions(objective: string): Promise<RoleSuggestion[]> {
  // 1. Buscar templates con objetivos similares
  const similarTemplates = await templateRepository.findByObjective(objective);

  // 2. Extraer roles de esos templates
  const roles = similarTemplates.map(t => t.components.role);

  // 3. Eliminar duplicados
  const uniqueRoles = deduplicateByContent(roles);

  // 4. Calcular scores
  const scored = uniqueRoles.map(role => ({
    ...role,
    qualityScore: calculateQualityScore(role.content),
    relevanceScore: calculateRelevanceScore(objective, role.content),
    usageCount: getUsageCount(role.id)
  }));

  // 5. Generar "fit reasons"
  return scored.map(role => ({
    ...role,
    fitReason: generateFitReason(role.qualityScore, role.relevanceScore)
  })).sort((a, b) =>
    (b.qualityScore * 0.5 + b.relevanceScore * 0.5) -
    (a.qualityScore * 0.5 + a.relevanceScore * 0.5)
  ).slice(0, 3);
}

function generateFitReason(qualityScore: number, relevanceScore: number): string {
  const reasons: string[] = [];

  if (qualityScore > 4.5) reasons.push("Role de alta calidad");
  if (relevanceScore > 0.8) reasons.push("Perfecto para tu objetivo");
  if (qualityScore > 4.0 && qualityScore <= 4.5) reasons.push("Bien estructurado");
  if (relevanceScore > 0.6 && relevanceScore <= 0.8) reasons.push("Relevante para tu caso");

  return reasons.length > 0
    ? reasons.join(" • ")
    : "Potencialmente útil";
}
```

### Validaciones

```typescript
const validations = {
  minLength: 1,            // Mínimo 1 carácter (pero se recomienda 10+)
  recommendedLength: 10,   // Mínimo recomendado
  optimalLength: 20,       // Longitud óptima
  required: true,

  // Indicadores visuales
  errorState: role.length === 0,
  warningState: role.length > 0 && role.length < 10,
  successState: role.length >= 20
};
```

### Toggle Sugerencias

```typescript
const toggleButton = {
  text: showSuggestions ? "Ocultar sugerencias" : "Ver Sugerencias de Roles",
  onClick: () => setShowSuggestions(!showSuggestions),
  disabled: objective.length <= 5
};
```

---

## Step 3: Core Directive

### Propósito
Definir la misión última y las instrucciones específicas que debe seguir la IA.

### UI Components

**Título:** "What is the Core Directive?"
**Descripción:** "This is the ultimate mission. It should be a clear, concise instruction that references the objective."

#### Input Field

```tsx
<Textarea
  placeholder="e.g., Your ultimate mission is: To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs)."
  minHeight="h-40" // 10rem
  value={directive}
  onChange={(e) => setDirective(e.target.value)}
/>
```

### Estructura Recomendada

```typescript
// Patrón recomendado para directive
const directivePattern = `Your ultimate mission is: ${objective}`;

// Ejemplo:
// objective: "Design a scalable ADR process"
// directive: "Your ultimate mission is: To design and detail a robust, scalable,
//             and developer-friendly process for establishing Architecture
//             Decision Records (ADRs)."
```

### Validaciones

```typescript
const validations = {
  required: true,
  minLength: 1,
  shouldReferenceObjective: true, // Debe hacer referencia al objetivo

  // Checks adicionales
  hasActionVerbs: (directive: string) => {
    const actionVerbs = ["design", "create", "develop", "implement", "build"];
    return actionVerbs.some(verb =>
      directive.toLowerCase().includes(verb)
    );
  },

  isSpecific: (directive: string) => {
    // No debe ser demasiado genérico
    const genericPhrases = ["do something", "help me", "make something"];
    return !genericPhrases.some(phrase =>
      directive.toLowerCase().includes(phrase)
    );
  }
};
```

### Ejemplos de Buenas Directives

```typescript
const goodDirectives = [
  {
    objective: "Design a scalable ADR process",
    directive: "Your ultimate mission is: To design and detail a robust, scalable, and developer-friendly process for establishing Architecture Decision Records (ADRs)."
  },
  {
    objective: "Generate API documentation",
    directive: "Your ultimate mission is: To create comprehensive, accurate, and developer-friendly documentation for REST API endpoints including request/response schemas, authentication details, and usage examples."
  },
  {
    objective: "Create a testing strategy",
    directive: "Your ultimate mission is: To develop a comprehensive testing strategy that covers unit tests, integration tests, and end-to-end tests with specific coverage targets and testing frameworks."
  }
];
```

### Estado del Botón Next

```typescript
const nextButtonState = {
  disabled: !directive || directive.trim().length === 0,
  text: "Next"
};
```

---

## Step 4: Execution Framework

### Propósito
Seleccionar el modelo de razonamiento que mejor se adapte a la complejidad del objetivo.

### UI Components

**Título:** "Choose an Execution Framework"
**Descripción:** "Select a reasoning model that best fits the complexity of your objective."

#### Framework Options Grid

```tsx
<FrameworkOptionsGrid>
  {frameworks.map(framework => (
    <FrameworkCard
      key={framework.id}
      selected={selectedFramework === framework.id}
      onClick={() => setSelectedFramework(framework.id)}
    >
      <Icon>{framework.icon}</Icon>
      <Name>{framework.name}</Name>
      <Description>{framework.description}</Description>
    </FrameworkCard>
  ))}
</FrameworkOptionsGrid>
```

### Frameworks Disponibles

```typescript
const frameworks: ReasoningFramework[] = [
  {
    id: "chain-of-thought",
    name: "Chain-of-Thought (CoT)",
    description: "For problems that require step-by-step resolution and logical deduction.",
    icon: "arrow-path-diagram",
    useCases: [
      "Problemas secuenciales",
      "Razonamiento lógico",
      "Deducción paso a paso",
      "Matemáticas y lógica"
    ],
    default: true
  },
  {
    id: "tree-of-thoughts",
    name: "Tree of Thoughts (ToT)",
    description: "For exploring multiple solution paths and evaluating complex trade-offs.",
    icon: "branching-tree-diagram",
    useCases: [
      "Exploración de opciones",
      "Evaluación de trade-offs",
      "Problemas con múltiples soluciones",
      "Toma de decisiones compleja"
    ]
  },
  {
    id: "decomposition",
    name: "Decomposition",
    description: "For breaking down large, complex tasks into smaller, manageable sub-problems.",
    icon: "grid-of-squares",
    useCases: [
      "Tareas complejas y grandes",
      "Descomposición en subproblemas",
      "Proyectos multipaso",
      "Análisis sistemático"
    ]
  },
  {
    id: "role-playing",
    name: "Role-Playing",
    description: "For simulating dialogues, user interactions, or adversarial scenarios.",
    icon: "user-group-icons",
    useCases: [
      "Simulaciones de diálogo",
      "Interacciones usuario-sistema",
      "Escenarios adversariales",
      "Role-playing y simulaciones"
    ]
  }
];
```

### Layout Responsivo

```tsx
// Medium screens: 2 columnas
<Grid cols={2} className="md:grid-cols-2">
  {/* Framework cards */}
</Grid>

// Small screens: 1 columna
<Grid cols={1} className="grid-cols-1">
  {/* Framework cards */}
</Grid>
```

### Estados Visuales

```typescript
const cardStates = {
  selected: {
    borderColor: "brand-primary",
    backgroundColor: "brand-primary-light",
    borderWidth: 2
  },
  unselected: {
    borderColor: "gray-300",
    backgroundColor: "white",
    borderWidth: 1
  },
  hover: {
    borderColor: "brand-primary",
    backgroundColor: "brand-primary-lighter"
  }
};
```

### Lógica de Selección

```typescript
function handleFrameworkSelection(frameworkId: string) {
  setSelectedFramework(frameworkId);

  // Auto-sugerir guardrailas basadas en el framework
  const suggestedGuardrails = getSuggestedGuardrails(frameworkId);
  setGuardrailSuggestions(suggestedGuardrails);
}

function getSuggestedGuardrails(frameworkId: string): string[] {
  const suggestions: Record<string, string[]> = {
    "chain-of-thought": [
      "Think step-by-step before answering",
      "Show your work and reasoning process"
    ],
    "tree-of-thoughts": [
      "Consider multiple solution paths",
      "Evaluate trade-offs explicitly"
    ],
    "decomposition": [
      "Break down the problem into sub-problems",
      "Address each component systematically"
    ],
    "role-playing": [
      "Stay in character throughout",
      "Maintain consistent persona"
    ]
  };

  return suggestions[frameworkId] || [];
}
```

### Botón Next

```typescript
const nextButtonState = {
  disabled: false, // Siempre habilitado (hay default)
  text: "Next"
};
```

---

## Step 5: Guardrails & Constraints

### Propósito
Establecer reglas y límites para la respuesta de la IA.

### UI Components

**Título:** "Set Guardrails & Constraints"
**Descripción:** "Define the rules and boundaries for the AI's response."

#### Add New Guardrail Input

```tsx
<AddGuardrailContainer>
  <Input
    type="text"
    placeholder="Add a custom guardrail..."
    value={newGuardrail}
    onChange={(e) => setNewGuardrail(e.target.value)}
    onKeyDown={(e) => {
      if (e.key === 'Enter') {
        addGuardrail(newGuardrail);
      }
    }}
  />
  <Button
    onClick={() => addGuardrail(newGuardrail)}
    disabled={!newGuardrail.trim()}
  >
    Add
  </Button>
</AddGuardrailContainer>
```

#### Suggested Guardrails

```tsx
<SuggestionsSection>
  <Title>Suggestions:</Title>
  <SuggestionsList>
    {[
      "Be concise and to the point.",
      "Prioritize simplicity and clarity.",
      "Do not use technical jargon unless necessary.",
      "Provide actionable steps.",
      "Structure the output in Markdown.",
      "Think step-by-step before answering."
    ].map(suggestion => (
      <SuggestionItem
        key={suggestion}
        onClick={() => addGuardrail(suggestion)}
      >
        {suggestion}
      </SuggestionItem>
    ))}
  </SuggestionsList>
</SuggestionsSection>
```

#### Active Guardrails Display

```tsx
<ActiveGuardrailsSection>
  <Title>Active Guardrails:</Title>

  {guardrails.length === 0 ? (
    <EmptyState>
      No guardrails added yet.
    </EmptyState>
  ) : (
    <GuardrailsList>
      {guardrails.map((guardrail, index) => (
        <GuardrailTag key={index}>
          <Text>{guardrail}</Text>
          <RemoveButton
            onClick={() => removeGuardrail(index)}
          >
            ×
          </RemoveButton>
        </GuardrailTag>
      ))}
    </GuardrailsList>
  )}
</ActiveGuardrailsSection>
```

### Estilos de Tags

```typescript
const guardrailTagStyles = {
  backgroundColor: "brand-primary",
  color: "primary-text",
  padding: "0.5rem 1rem",
  borderRadius: "full",
  display: "inline-flex",
  alignItems: "center",
  gap: "0.5rem"
};
```

### Lógica de Guardrails

```typescript
function addGuardrail(guardrail: string) {
  const trimmed = guardrail.trim();

  if (!trimmed) return;

  // Verificar duplicados
  if (guardrails.includes(trimmed)) {
    showError("This guardrail already exists");
    return;
  }

  // Agregar a la lista
  setGuardrails([...guardrails, trimmed]);
  setNewGuardrail(""); // Clear input
}

function removeGuardrail(index: number) {
  setGuardrails(guardrails.filter((_, i) => i !== index));
}
```

### Validaciones

```typescript
const validations = {
  // Las guardrailas son opcionales
  required: false,
  minCount: 0,
  maxCount: 10, // Límite recomendado

  // No duplicados
  unique: true,

  // Longitud máxima por guardraila
  maxLength: 200
};
```

### Botón Next

```typescript
const nextButtonState = {
  disabled: false, // Siempre habilitado (es opcional)
  text: "Next"
};
```

---

## Step 6: Plan View & Assembly

### Propósito
Visualizar el prompt completo y guardarlo en la biblioteca personal.

### UI Components

**Título:** "Your SOTA Prompt is Ready!"
**Descripción:** "Save this prompt to your personal library or copy it to use elsewhere."

#### Prompt Name Input

```tsx
<NameInputSection>
  <Input
    type="text"
    placeholder="Enter a name for your prompt..."
    value={promptName}
    onChange={(e) => setPromptName(e.target.value)}
    error={promptName.trim().length === 0}
    errorMessage="Please enter a name for your prompt"
  />
</NameInputSection>
```

#### Generated Prompt Display

```tsx
<PromptDisplay>
  <PromptContent>
    <PromptHeader>**[ROLE & PERSONA]**</PromptHeader>
    <PromptText>{role}</PromptText>

    <PromptHeader>**[CORE DIRECTIVE]**</PromptHeader>
    <PromptText>**Your ultimate mission is:** {directive}</PromptText>

    <PromptHeader>**[EXECUTION FRAMEWORK: {frameworkName}]**</PromptHeader>
    <PromptText>{frameworkDescription}</PromptText>

    <PromptHeader>**[CONSTRAINTS & GUARDRAILS]**</PromptHeader>
    <PromptText>You must adhere to the following rules:</PromptText>
    <GuardrailsList>
      {guardrails.map(g => `*   ${g}`).join('\n')}
    </GuardrailsList>

    <PromptHeader>**[FINAL OUTPUT]**</PromptHeader>
    <PromptText>
      Based on all the information above, generate a comprehensive, State-of-the-Art (SOTA) plan.
      Your response must strictly follow the multi-step structure defined in the EXECUTION FRAMEWORK section.
      Use Markdown for formatting. Begin your response with a title for the plan.
    </PromptText>
  </PromptContent>
</PromptDisplay>
```

### Función de Ensamblaje

```typescript
function assembleFinalPrompt(data: PlanData): string {
  const frameworkDetails = FRAMEWORKS.find(f => f.id === data.framework);
  const guardrailList = data.guardrails.length > 0
    ? data.guardrails.map(g => `*   ${g}`).join('\n')
    : '*   No specific constraints';

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

### Action Buttons

```tsx
<ActionButtons>
  <Button
    variant="secondary"
    onClick={handleCopy}
  >
    {copied ? "Copied!" : "Copy"}
  </Button>

  <Button
    variant="primary"
    onClick={handleSave}
    disabled={!promptName.trim()}
  >
    {isEditing ? "Save Changes" : "Save to My Prompts"}
  </Button>

  {saved && (
    <Button
      variant="secondary"
      onClick={handleClose}
    >
      Close
    </Button>
  )}
</ActionButtons>
```

### Lógica de Copiado

```typescript
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(assembledPrompt);
    setCopied(true);

    // Reset after 2 seconds
    setTimeout(() => setCopied(false), 2000);
  } catch (error) {
    console.error("Failed to copy:", error);
    showError("Failed to copy to clipboard");
  }
}
```

### Lógica de Guardado

```typescript
async function handleSave() {
  if (!promptName.trim()) {
    showError("Please enter a name for your prompt");
    return;
  }

  const promptToSave: Prompt = {
    id: isEditing ? editingId : generateId(),
    name: promptName.trim(),
    components: {
      objective: { name: "Objective", content: objective },
      role: { name: "Role", content: role },
      directive: { name: "Directive", content: directive },
      framework: { name: "Framework", content: framework },
      constraints: guardrails.map((g, i) => ({
        name: `Constraint ${i + 1}`,
        content: g
      }))
    },
    createdAt: new Date().toISOString(),
    usageCount: 0
  };

  try {
    await promptService.save(promptToSave);
    setSaved(true);
    showSuccess("Prompt saved successfully!");
  } catch (error) {
    console.error("Failed to save prompt:", error);
    showError("Failed to save prompt");
  }
}
```

---

## Validaciones y Reglas

### Tabla de Validaciones

| Step | Campo | Min Length | Required | Error Conditions | Success Indicator |
|------|-------|------------|----------|------------------|-------------------|
| 0 (Discovery) | Objective | 5 chars | ✓ | < 5 chars | >= 5 chars |
| 1 | Objective | 5 chars | ✓ | Empty or < 5 | >= 5 chars |
| 2 | Role | 1 char | ✓ | Empty | >= 10 chars (good) |
| 3 | Directive | 1 char | ✓ | Empty | Has action verbs |
| 4 | Framework | - | ✓ | - | Always selected |
| 5 | Guardrails | - | ✗ | - | - |
| 6 | Prompt Name | 1 char | ✓ | Empty | >= 3 chars |

### Reglas de Navegación

```typescript
const navigationRules = {
  // Progresivo: solo avanzar si validación pasa
  canGoNext: (step: number, data: WizardState) => {
    switch (step) {
      case 0: return data.objective.length >= 5;
      case 1: return data.objective.length >= 5;
      case 2: return data.role.length > 0;
      case 3: return data.directive.length > 0;
      case 4: return true; // Framework siempre tiene default
      case 5: return true; // Guardrails es opcional
      case 6: return data.promptName.length > 0;
      default: return false;
    }
  },

  // Siempre puede volver atrás
  canGoBack: (step: number) => step > 0,

  // Skip discovery
  skipDiscovery: () => goToStep(1)
};
```

### Indicadores de Progreso

```typescript
const progressBar = {
  currentStep: currentStep,
  totalSteps: 6,
  percentage: Math.round((currentStep / 6) * 100),

  // Texto del step
  stepText: (step: number) => {
    const titles = [
      "Discovery",
      "Objective",
      "Role & Persona",
      "Core Directive",
      "Execution Framework",
      "Guardrails & Constraints",
      "Review & Save"
    ];
    return titles[step];
  }
};
```

---

## Manejo de Errores

### Tipos de Errores

```typescript
const errorTypes = {
  // Discovery errors
  TEMPLATE_SEARCH_FAILED: {
    message: "Error al buscar recomendaciones. Intenta de nuevo.",
    action: "Reintentar",
    recovery: () => searchTemplates(objective)
  },

  // Validation errors
  VALIDATION_FAILED: {
    message: "Por favor, completa todos los campos requeridos.",
    action: "Revisar campos",
    recovery: () => highlightInvalidFields()
  },

  // Save errors
  SAVE_FAILED: {
    message: "Error al guardar el prompt. Por favor, intenta de nuevo.",
    action: "Reintentar",
    recovery: () => savePrompt()
  },

  // Copy errors
  COPY_FAILED: {
    message: "Error al copiar al portapapeles.",
    action: "Reintentar",
    recovery: () => copyToClipboard()
  },

  // Network errors
  NETWORK_ERROR: {
    message: "Error de conexión. Verifica tu internet.",
    action: "Reintentar",
    recovery: () => retryLastAction()
  }
};
```

### Estado de Error UI

```tsx
<ErrorState visible={hasError}>
  <ErrorMessage>{error.message}</ErrorMessage>
  <ErrorAction onClick={error.recovery}>
    {error.action}
  </ErrorAction>
</ErrorState>
```

### Loading States

```typescript
const loadingStates = {
  searchingTemplates: {
    message: "Analizando nuestro inventario de templates...",
    spinner: true
  },
  savingPrompt: {
    message: "Guardando tu prompt...",
    spinner: true
  },
  generatingSuggestions: {
    message: "Generando sugerencias inteligentes...",
    spinner: true
  }
};
```

---

**Próximos documentos:**
- `02-template-library-analysis.md` - Análisis completo de la biblioteca de templates
- `03-dspy-integration-guide.md` - Guía de integración con DSPy
