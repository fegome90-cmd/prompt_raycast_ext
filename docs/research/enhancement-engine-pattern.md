# Enhancement Engine Pattern - Motor de Mejora Iterativa

**Prioridad:** 🔴 CRÍTICA - ROI MUY ALTO
**Fuente:** Architect v3.2.0 - `/services/enhancementService.ts`
**Complejidad:** Media
**Adaptabilidad:** Perfecta para Raycast

---

## 🎯 Concepto Core

Motor de mejora iterativa AI-powered que optimiza prompts automáticamente mediante múltiples ciclos de enhancement, detectando rendimientos decrecientes y aplicando mejoras dirigidas a áreas específicas (claridad, completitud, estructura, ejemplos, guardrails).

**El problema que resuelve:**
- ¿Cómo mejorar prompts automáticamente sin intervención manual?
- ¿Cuándo parar de optimizar (rendimientos decrecientes)?
- ¿Cómo preservar la intención original mientras se mejora?
- ¿Cómo medir progreso de forma objetiva?

**La solución:**
- Iteraciones controladas de mejora AI
- Métricas de calidad cuantitativas
- Detección de convergencia
- Mejoras dirigidas por objetivos
- Preservación de intención original

---

## 🏗️ Arquitectura del Sistema

### Flujo Principal de Enhancement

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENHANCEMENT ENGINE FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT: Prompt Original + Objetivos de Enhancement                     │
│         ↓                                                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ITERATION 0: Medición Baseline                                   │  │
│  │  ├─ Calcular métricas iniciales                                   │  │
│  │  ├─ Guardar estado original                                      │  │
│  │  └─ Establecer línea base                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│         ↓                                                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ITERATIVE ENHANCEMENT LOOP                                        │  │
│  │  For i = 1 to maxIterations:                                     │  │
│  │                                                                   │  │
│  │  1. CHECK TARGETS                                                 │  │
│  │     └─ ¿Se alcanzaron los objetivos? → STOP                       │  │
│  │                                                                   │  │
│  │  2. BUILD ENHANCEMENT PROMPT                                     │  │
│  │     ├─ Prompt actual + métricas                                  │  │
│  │     ├─ Objetivos de mejora                                       │  │
│  │     └─ Áreas focales identificadas                               │  │
│  │                                                                   │  │
│  │  3. EXECUTE AI ENHANCEMENT                                       │  │
│  │     ├─ LLM (gemini-2.5-pro)                                      │  │
│  │     ├─ Temperature: 0.6 (moderada)                              │  │
│  │     └─ Output en YAML estructurado                              │  │
│  │                                                                   │  │
│  │  4. PARSE ENHANCED RESULT                                        │  │
│  │     ├─ Extraer YAML                                              │  │
│  │     ├─ Validar componentes                                      │  │
│  │     └─ Reconstruir prompt                                       │  │
│  │                                                                   │  │
│  │  5. CALCULATE NEW METRICS                                        │  │
│  │     ├─ Calidad general                                           │  │
│  │     ├─ Claridad, completitud, etc.                              │  │
│  │     └─ Identificar cambios aplicados                            │  │
│  │                                                                   │  │
│  │  6. CHECK DIMINISHING RETURNS                                    │  │
│  │     └─ ¿Mejora < 0.1 en últimas 3 iteraciones? → STOP            │  │
│  │                                                                   │  │
│  │  7. UPDATE STATE                                                 │  │
│  │     └─ prompt = enhancedPrompt                                   │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│         ↓                                                               │
│  OUTPUT: Enhanced Prompt + Métricas + Historial de Iteraciones         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes Clave

### 1. **Quality Metrics - 5 Dimensiones**

**Estructura de métricas:**

```typescript
interface QualityMetrics {
  overallScore: number;   // 1-5: Puntuación general
  clarity: number;        // 1-5: Claridad del lenguaje
  completeness: number;   // 1-5: Presencia de componentes
  structure: number;      // 1-5: Organización lógica
  examples: number;       // 1-5: Presencia de ejemplos
  guardrails: number;     // 1-5: Cantidad de restricciones
}
```

**Cómo se calcula cada métrica:**

#### Claridad Score (1-5)

```
Base: 3 puntos
+0.5 si rol > 20 caracteres
+0.5 si rol incluye "expert" o "specialist"
+0.5 si directiva > 50 caracteres
+0.5 si directiva incluye verbos de acción
(analyze, create, evaluate, generate, optimize)

Máximo: 5 puntos
```

**Ejemplos:**
```
❌ Rol: "AI assistant" → Poco claro
✅ Rol: "Expert software architect specialized in API design" → Muy claro

❌ Directiva: "Help me" → Vago
✅ Directiva: "Analyze the codebase and generate comprehensive documentation" → Claro
```

#### Completitud Score (1-5)

```
Base: 1 punto
+1 si tiene rol
+1 si tiene directiva
+1 si tiene framework
+1 si tiene guardrails
+0.5 si directiva > 100 caracteres
+0.5 si tiene ≥3 guardrails

Máximo: 5 puntos
```

**Ejemplos:**
```
Prompt vacío: 1/5
Solo rol: 2/5
Rol + directiva: 3/5
Todos los componentes: 5/5
```

#### Estructura Score (1-5)

```
Base: 3 puntos
+0.5 si tiene rol Y directiva
+0.5 si tiene framework
+0.5 si tiene guardrails
+0.5 si directiva tiene estructura (\n o listas)

Máximo: 5 puntos
```

#### Ejemplos Score (1-5)

```
Base: 1 punto
+2 si contiene "example", "e.g.", "for instance"
+1 si tiene "input:" Y "output:" (ejemplos específicos)

Máximo: 5 puntos
```

**Ejemplos:**
```
❌ Sin ejemplos: 1/5
✅ "For example, when the user asks for..." → 3/5
✅ "Input: 'help' → Output: 'How can I assist?'" → 4/5
```

#### Guardrails Score (1-5)

```
0 guardrails: 1/5
1 guardrail: 2/5
2 guardrails: 3/5
3 guardrails: 4/5
4+ guardrails: 5/5
```

### 2. **Enhancement Targets - Objetivos Dirigidos**

**Estructura:**

```typescript
interface EnhancementTarget {
  type: "clarity" | "completeness" | "structure" |
        "examples" | "guardrails";
  priority: "high" | "medium" | "low";
  currentScore?: number;    // Score actual (1-5)
  targetScore?: number;     // Score objetivo (1-5)
}
```

**Ejemplos de configuración:**

```typescript
// Mejora general equilibrada
const targets: EnhancementTarget[] = [
  { type: "clarity", priority: "high", currentScore: 2.5, targetScore: 4.0 },
  { type: "completeness", priority: "medium", currentScore: 3.0, targetScore: 4.5 },
  { type: "structure", priority: "medium" },
  { type: "examples", priority: "low" },
  { type: "guardrails", priority: "high", currentScore: 1.0, targetScore: 4.0 }
]

// Enfoque específico en claridad
const focusedTargets: EnhancementTarget[] = [
  { type: "clarity", priority: "high", currentScore: 2.0, targetScore: 4.5 }
]
```

### 3. **Enhancement Prompt - Prompt que Mejora Prompts**

**Estructura del prompt de enhancement:**

```
You are an expert prompt engineer tasked with enhancing an AI prompt.

**CURRENT ITERATION**: {iteration}

**CURRENT PROMPT**:
**Role**: {role}
**Directive**: {directive}
**Framework**: {framework}
**Guardrails**: {guardrails}

**CURRENT QUALITY METRICS**:
- Overall Score: {overall}/5
- Clarity: {clarity}/5
- Completeness: {completeness}/5
- Structure: {structure}/5
- Examples: {examples}/5
- Guardrails: {guardrails}/5

**ENHANCEMENT TARGETS**:
- CLARITY: Priority high (Current: 2.5/5, Target: 4.0/5)
- COMPLETENESS: Priority medium (Current: 3.0/5, Target: 4.5/5)
...

**ENHANCEMENT GUIDELINES**:

1. **CLARITY**:
   - Use clear, unambiguous language
   - Remove jargon and complex terminology
   - Ensure instructions are easy to understand
   - Add specific action verbs

2. **COMPLETENESS**:
   - Include all necessary context
   - Specify expected outputs
   - Provide relevant constraints
   - Add missing components

3. **STRUCTURE**:
   - Organize content logically
   - Use consistent formatting
   - Ensure proper flow
   - Add clear sections

4. **EXAMPLES**:
   - Add relevant examples where helpful
   - Include input/output examples
   - Provide edge case examples
   - Make examples specific and actionable

5. **GUARDRAILS**:
   - Strengthen safety constraints
   - Add boundary conditions
   - Include ethical guidelines
   - Specify what NOT to do

**OUTPUT FORMAT**:
Please provide the enhanced prompt in this YAML structure:

```yaml
role: [Enhanced role description]
directive: [Enhanced directive with clear instructions]
framework: [Reasoning framework to use]
guardrails:
  - [Guardrail 1]
  - [Guardrail 2]
  - [Additional guardrails]
```

**FOCUS AREAS**:
Based on the current metrics, prioritize improvements in:
clarity: +1.5 needed, completeness: +1.5 needed

Please make targeted improvements that address the identified
weaknesses while preserving the original intent and strengths.
```

**Conceptos clave del prompt de enhancement:**

1. **Contexto completo:** Prompt actual + métricas
2. **Objetivos claros:** Targets específicos con scores
3. **Guías estructuradas:** 5 áreas de mejora
4. **Output formateado:** YAML para parsing confiable
5. **Preservación:** Mantiene intención original

### 4. **Iterative Enhancement - Ciclo de Mejora**

**Lógica de iteración:**

```typescript
for (let iteration = 1; iteration <= maxIterations; iteration++) {

  // 1. Check si se alcanzaron objetivos
  if (hasAchievedTargets(currentMetrics, targets)) {
    break; // Éxito - objetivos cumplidos
  }

  // 2. Generar prompt de enhancement
  const enhancementPrompt = buildEnhancementPrompt(
    currentContent,
    currentMetrics,
    targets,
    iteration
  );

  // 3. Ejecutar enhancement
  const enhancedContent = await executeEnhancement(enhancementPrompt);

  // 4. Calcular nuevas métricas
  const newMetrics = calculateQualityMetrics(enhancedContent);

  // 5. Identificar cambios
  const changes = identifyChanges(currentContent, enhancedContent);

  // 6. Guardar iteración
  iterationResults.push({
    iteration,
    content: enhancedContent,
    metrics: newMetrics,
    changes,
    processingTime
  });

  // 7. Check rendimientos decrecientes
  if (hasDiminishingReturns(iterationResults)) {
    break; // No hay mejora significativa
  }

  // 8. Actualizar estado
  currentContent = enhancedContent;
  currentMetrics = newMetrics;
}
```

### 5. **Diminishing Returns Detection - Cuándo Parar

**Algoritmo de detección:**

```typescript
function hasDiminishingReturns(iterationResults: IterationResult[]): boolean {
  if (iterationResults.length < 3) return false;

  const lastThree = iterationResults.slice(-3);
  const improvements = lastThree.map(r => r.metrics.overallScore);

  // Si la mejora es < 0.1 en las últimas 3 iteraciones
  for (let i = 1; i < improvements.length; i++) {
    if (improvements[i] - improvements[i - 1] < 0.1) {
      return true; // Rendimientos decrecientes detectados
    }
  }

  return false;
}
```

**Ejemplo de convergencia:**

```
Iteración 0: Score 2.5 (baseline)
Iteración 1: Score 3.2 (+0.7) ← Mejora significativa
Iteración 2: Score 3.6 (+0.4) ← Mejora moderada
Iteración 3: Score 3.7 (+0.1) ← Rendimientos decrecientes → STOP
```

**Por qué 3 iteraciones:**
- Una sola mejora pequeña podría ser ruido
- Dos mejoras pequeñas podrían ser patrón
- Tres mejoras pequeñas = convergencia real

### 6. **Change Identification - Rastreo de Mejoras**

**Sistema de tracking de cambios:**

```typescript
function identifyChanges(previous, current): string[] {
  const changes = [];

  // Comparación de componentes
  if (previous.role !== current.role) {
    changes.push("Updated role description");
  }

  if (previous.directive !== current.directive) {
    changes.push("Enhanced directive clarity");
  }

  // Diferencia en cantidad de guardrails
  const prevCount = previous.guardrails.length;
  const currCount = current.guardrails.length;
  if (prevCount !== currCount) {
    changes.push(`${currCount > prevCount ? "Added" : "Removed"} guardrails`);
  }

  // Mejora en score
  const scoreDiff = current.qualityScore - previous.qualityScore;
  if (scoreDiff > 0) {
    changes.push(`Improved quality score (+${scoreDiff.toFixed(1)})`);
  }

  return changes;
}
```

**Ejemplo de tracking:**

```
Iteración 0 → 1:
- "Updated role description"
- "Enhanced directive clarity"
- "Improved quality score (+0.7)"

Iteración 1 → 2:
- "Added guardrails"
- "Improved quality score (+0.4)"

Iteración 2 → 3:
- "Improved quality score (+0.1)"
→ Siguiente iteración: diminishing returns
```

---

## 📊 Resultados del Enhancement

### Estructura de Output

```typescript
interface EnhancementResult {
  originalPromptId: string;
  enhancedContent: ParsedPrompt;          // Prompt mejorado
  appliedEnhancements: AppliedEnhancement[];  // Lista de mejoras
  qualityMetrics: {
    before: QualityMetrics;              // Métricas iniciales
    after: QualityMetrics;               // Métricas finales
    improvement: number;                 // Diferencia (after - before)
  };
  iterationResults: IterationResult[];   // Historial completo
  totalProcessingTime: number;           // Tiempo total (ms)
}
```

### Ejemplo de Resultado

```typescript
{
  originalPromptId: "prompt-123",
  enhancedContent: { /* prompt mejorado */ },
  appliedEnhancements: [
    {
      target: { type: "clarity", priority: "high" },
      appliedChanges: [
        "Updated role description",
        "Enhanced directive clarity"
      ],
      improvement: 1.5,  // de 2.5 → 4.0
      confidence: 0.75
    },
    {
      target: { type: "completeness", priority: "medium" },
      appliedChanges: ["Added guardrails"],
      improvement: 1.0,  // de 3.0 → 4.0
      confidence: 0.5
    }
  ],
  qualityMetrics: {
    before: { overall: 2.8, clarity: 2.5, completeness: 3.0, ... },
    after: { overall: 4.1, clarity: 4.0, completeness: 4.0, ... },
    improvement: 1.3
  },
  iterationResults: [
    { iteration: 0, content: /* original */, metrics: { overall: 2.8 } },
    { iteration: 1, content: /* enhanced */, metrics: { overall: 3.5 } },
    { iteration: 2, content: /* enhanced */, metrics: { overall: 4.0 } },
    { iteration: 3, content: /* enhanced */, metrics: { overall: 4.1 } }
  ],
  totalProcessingTime: 12500  // 12.5 segundos
}
```

---

## 💡 Aplicación a Raycast

### Adaptación del Concepto

**Para Mejora de Extension Commands:**

```typescript
// Adaptación para Raycast
interface RaycastEnhancementRequest {
  commandCode: string;              // Código del comando
  enhancementTargets: EnhancementTarget[];
  maxIterations: number;
}

interface RaycastEnhancementResult {
  enhancedCode: string;             // Código mejorado
  improvements: CodeImprovement[];
  qualityMetrics: {
    before: CodeQualityMetrics;
    after: CodeQualityMetrics;
  };
}
```

**Métricas específicas para código Raycast:**

```typescript
interface CodeQualityMetrics {
  readability: number;      // 1-5: Claridad del código
  efficiency: number;       // 1-5: Performance
  errorHandling: number;    // 1-5: Manejo de errores
  typeSafety: number;       // 1-5: Uso de tipos
  documentation: number;    // 1-5: Comentarios/docs
}
```

### Ejemplo Práctico

**Comando original:**

```typescript
// Original: poco claro, sin error handling
export default async function searchGitHub() {
  const query = await argue({ placeholder: "Search" });
  const results = await fetch(`https://api.github.com/search?q=${query}`);
  const data = await results.json();
  showToast({ title: data.items[0].name });
}
```

**Enhancement targets:**

```typescript
const targets = [
  { type: "readability", priority: "high", currentScore: 2.0, targetScore: 4.0 },
  { type: "errorHandling", priority: "high", currentScore: 1.0, targetScore: 4.0 },
  { type: "documentation", priority: "medium", currentScore: 1.0, targetScore: 3.5 }
];
```

**Resultado mejorado:**

```typescript
// Enhanced: claro, robusto, documentado
/**
 * Searches GitHub repositories and displays the top result.
 * Shows loading toast during fetch and error toast on failure.
 *
 * @param query - Search query for GitHub repositories
 * @returns Promise<void> - Displays result in toast
 */
export default async function searchGitHub() {
  try {
    // Get search query from user
    const query = await argue({
      placeholder: "Enter GitHub search query...",
      title: "GitHub Search"
    });

    if (!query?.trim()) {
      showToast({
        title: "Search query required",
        style: Toast.Style.Failure
      });
      return;
    }

    // Show loading state
    const toast = await showToast({
      title: "Searching GitHub...",
      style: Toast.Style.Animated
    });

    // Fetch results with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(
      `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}`,
      { signal: controller.signal }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const data = await response.json();

    if (!data.items?.length) {
      toast.title = "No results found";
      toast.style = Toast.Style.Failure;
      return;
    }

    // Display top result
    const topResult = data.items[0];
    toast.title = topResult.full_name;
    toast.message = `⭐ ${topResult.stargazers_count} stars`;
    toast.style = Toast.Style.Success;

  } catch (error) {
    showToast({
      title: "Search failed",
      message: error instanceof Error ? error.message : "Unknown error",
      style: Toast.Style.Failure
    });
  }
}
```

**Mejoras aplicadas:**
- ✅ Readability: 2.0 → 4.5 (+2.5)
- ✅ ErrorHandling: 1.0 → 4.5 (+3.5)
- ✅ Documentation: 1.0 → 4.0 (+3.0)

---

## 🚀 Decisiones de Diseño

### Por qué Temperatura Moderada (0.6)

**Alternativa considerada:** Temperatura alta (0.8-1.0)

**Por qué no:**
- Demasiado creativa para enhancement
- Puede cambiar la intención original
- Resultados menos predecibles

**Por qué 0.6:**
- Balance entre creatividad y consistencia
- Mejoras significativas sin cambios drásticos
- Preserva mejor la intención original

### Por qué Detección de Diminishing Returns

**Alternativa considerada:** Número fijo de iteraciones

**Por qué no:**
- Algunos prompts mejoran rápido (2-3 iteraciones)
- Otros necesitan más (5+ iteraciones)
- Iteraciones fijas = desperdicio o insuficiencia

**Por qué detección dinámica:**
- Para cuando converge (ahorra tiempo/costo)
- Continúa mientras mejora significativamente
- Umbral de 0.1 = balance justo

### Por qué 5 Métricas Específicas

**Alternativa considerada:** Solo score general

**Por qué no:**
- Score general no indica qué mejorar
- Diferentes prompts tienen diferentes debilidades
- No permite targeting específico

**Por qué 5 métricas:**
- Cada una mide un aspecto distinto
- Permiten enhancement dirigido
- Más fácil de comunicar al usuario

---

## 📈 Patrones a Adoptar (Conceptualmente)

### 1. **Enhancement como Pipeline**

```typescript
// NO: Mejora ad-hoc
const improved = await improve(prompt)

// SÍ: Pipeline con etapas
const enhanced = await enhancementPipeline({
  input: prompt,
  stages: [
    validate,
    enhance,
    validate,
    improve(while: !converged),
    finalize
  ]
})
```

### 2. **Objetivos como Contrato**

```typescript
// Contrato claro de qué se quiere lograr
const targets: EnhancementTarget[] = [
  {
    type: "clarity",
    priority: "high",
    currentScore: 2.5,
    targetScore: 4.0
  }
]

// El engine cumple el contrato
const result = await enhance(prompt, targets)
// result.qualityMetrics.clarity >= 4.0
```

### 3. **Historial de Iteraciones**

```typescript
// Mantener todo el historial
interface EnhancementResult {
  iterationResults: IterationResult[]  // Todas las iteraciones
}

// Permite:
// - Ver progreso
// - Revertir si necesario
// - Entender qué funcionó
```

### 4. **Early Exit Patterns**

```typescript
// Múltiples condiciones de parada
if (hasAchievedTargets(metrics, targets)) break;
if (hasDiminishingReturns(iterations)) break;
if (iteration >= maxIterations) break;

// Prioridad de condiciones:
// 1. Objetivos cumplidos (éxito)
// 2. Rendimientos decrecientes (optimización)
// 3. Máximo iteraciones (seguridad)
```

---

## ⚠️ Patrones a Evitar

### 1. **No Ignorar Métricas de Input**

```typescript
// MAL: Usar siempre defaults
const targets = defaultTargets

// BIEN: Adaptar a estado actual
const targets = calculateTargets(currentMetrics)
// Si clarity ya es 4.5, no targetear clarity
```

### 2. **No Sobre-Mejorar (Over-Engineering)**

```typescript
// MAL: Seguir mejorando sin necesidad
while (true) { enhance() }

// BIEN: Parar cuando es suficiente
while (!hasConverged() && iteration < MAX) { enhance() }
```

### 3. **No Perder Intención Original**

```typescript
// MAL: Enhancement drástico
const enhanced = await completelyRewrite(prompt)

// BIEN: Enhancement incremental
const enhanced = await iterativeImprovement(prompt)
// Cada iteración preserva el core de la anterior
```

---

## 📈 Métricas de Éxito

### Para Medir Calidad del Enhancement

- **Mejora promedio:** >0.5 puntos en escala 1-5
- **Tiempo de convergencia:** <3 iteraciones
- **Preservación de intención:** >90% según validación humana
- **Satisfacción del usuario:** >4/5

### Benchmarks Sugeridos

| Métrica | Bueno | Excelente |
|---------|-------|-----------|
| Mejora en score general | +0.5 | +1.0+ |
| Iteraciones hasta convergencia | 3-4 | 2-3 |
| Tiempo total | <15s | <10s |
| Tasa de aceptación | 60% | 80%+ |
| Preservación de intención | 80% | 95%+ |

---

## 🔍 Referencias del Código Fuente

### Archivos Principales

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `/services/enhancementService.ts` | Motor de enhancement iterativo | 29-841 |

### Secciones Clave

- **Enhancement loop:** 51-107 (main iteration logic)
- **Enhancement prompt builder:** 173-267
- **YAML parsing:** 272-353
- **Quality metrics calculation:** 441-490
- **Diminishing returns detection:** 645-659
- **Change identification:** 664-708

---

**Próximos documentos:**
- `quality-metrics-system.md` - Detalle de métricas cuantitativas
- `multi-provider-llm-abstraction.md` - Abstracción de LLMs
- `validation-pipeline-pattern.md` - Pipeline de validación

---

**Documentos completados:**
✅ `prompt-wizard-pattern.md` - Sistema wizard de 5 pasos
✅ `ab-testing-architecture.md` - Testing A/B completo
✅ `enhancement-engine-pattern.md` - Motor de mejora iterativa
