# Quality Metrics System - Evaluación Cuantitativa de Calidad

**Prioridad:** 🔴 CRÍTICA - ROI MUY ALTO
**Fuente:** Architect v3.2.0 - `/services/enhancementService.ts`, `/services/promptOptimizationService.ts`
**Complejidad:** Baja
**Adaptabilidad:** Perfecta para Raycast

---

## 🎯 Concepto Core

Sistema cuantitativo de evaluación de calidad que mide prompts en múltiples dimensiones (claridad, completitud, estructura, ejemplos, guardrails) mediante algoritmos deterministas y scoring normalizado (escala 1-5).

**El problema que resuelve:**
- ¿Cómo medir objetivamente la calidad de un prompt?
- ¿Cómo comparar prompts numéricamente?
- ¿Cómo detectar áreas específicas de mejora?
- ¿Cómo trackear progreso de optimización?

**La solución:**
- 5 métricas independientes pero complementarias
- Fórmulas matemáticas reproducibles
- Scores normalizados (1-5) para comparabilidad
- Detección automática de debilidades

---

## 📐 Las 5 Métricas Fundamentales

### Resumen Visual

```
                    QUALITY SCORE
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    CLARITY      COMPLETENESS      STRUCTURE
    (1-5)         (1-5)            (1-5)
        │               │               │
        └───────────────┼───────────────┘
                        │
                    EXAMPLES      GUARDRAILS
                    (1-5)          (1-5)

OVERALL SCORE = Promedio ponderado de las 5 métricas
```

---

## 🔢 Métrica 1: Claridad (Clarity Score)

**Definición:** Qué tan claro y comprensible es el lenguaje del prompt.

### Fórmula

```typescript
function calculateClarityScore(components): number {
  let score = 3.0;  // Base score

  // Factor 1: Longitud del rol (0-0.5 puntos)
  if (components.role && components.role.length > 20) {
    score += 0.5;
  }

  // Factor 2: Palabras clave de expertise (0-0.5 puntos)
  const expertiseKeywords = ["expert", "specialist", "professional",
                              "senior", "lead", "architect"];
  const hasExpertiseKeyword = expertiseKeywords.some(keyword =>
    components.role?.toLowerCase().includes(keyword)
  );
  if (hasExpertiseKeyword) {
    score += 0.5;
  }

  // Factor 3: Longitud de la directiva (0-0.5 puntos)
  if (components.directive && components.directive.length > 50) {
    score += 0.5;
  }

  // Factor 4: Verbos de acción (0-0.5 puntos)
  const actionVerbs = ["analyze", "create", "evaluate", "generate",
                       "optimize", "design", "implement", "review"];
  const hasActionVerb = actionVerbs.some(verb =>
    components.directive?.toLowerCase().includes(verb)
  );
  if (hasActionVerb) {
    score += 0.5;
  }

  return Math.min(5.0, Math.max(1.0, score));
}
```

### Umbrales

| Score | Nivel | Características |
|-------|-------|----------------|
| 1.0 - 2.0 | Pobre | Rol vago, sin verbos de acción, directiva corta |
| 2.1 - 3.0 | Aceptable | Rol básico, algún verbo de acción |
| 3.1 - 4.0 | Bueno | Rol claro, directiva específica |
| 4.1 - 5.0 | Excelente | Rol muy específico, directiva detallada con múltiples verbos |

### Ejemplos

```
❌ Score: 1.5/5
Role: "AI assistant"
Directive: "Help me with code"

✅ Score: 4.5/5
Role: "Senior software architect specialized in API design and microservices"
Directive: "Analyze the existing codebase, identify performance bottlenecks,
           and generate comprehensive optimization recommendations for the API layer"
```

---

## 🔢 Métrica 2: Completitud (Completeness Score)

**Definición:** Presencia de todos los componentes necesarios en el prompt.

### Fórmula

```typescript
function calculateCompletenessScore(components): number {
  let score = 1.0;  // Base score (prompt mínimo)

  // Factor 1: Rol presente (+1 punto)
  if (components.role && components.role.trim().length > 0) {
    score += 1.0;
  }

  // Factor 2: Directiva presente (+1 punto)
  if (components.directive && components.directive.trim().length > 0) {
    score += 1.0;
  }

  // Factor 3: Framework presente (+1 punto)
  if (components.framework) {
    score += 1.0;
  }

  // Factor 4: Guardrails presentes (+1 punto)
  if (components.guardrails && components.guardrails.length > 0) {
    score += 1.0;
  }

  // BONUS: Directiva comprehensiva (+0.5 puntos)
  if (components.directive && components.directive.length > 100) {
    score += 0.5;
  }

  // BONUS: Múltiples guardrails (+0.5 puntos)
  if (components.guardrails && components.guardrails.length >= 3) {
    score += 0.5;
  }

  return Math.min(5.0, score);
}
```

### Matriz de Completitud

| Componentes Presentes | Score Base | Con Bonuses | Score Máximo |
|----------------------|------------|-------------|--------------|
| Solo directiva | 2.0 | +0.5 | 2.5 |
| Rol + Directiva | 3.0 | +1.0 | 4.0 |
| Rol + Directiva + Framework | 4.0 | +1.0 | 5.0 |
| Todos los componentes | 5.0 | +1.0 | 5.0 |

### Ejemplos

```
❌ Score: 2.0/5
Role: -
Directive: "Create a REST API"
Framework: -
Guardrails: []

✅ Score: 5.0/5
Role: "API architect"
Directive: "Design a scalable REST API for an e-commerce platform with
           comprehensive error handling and rate limiting" (>100 chars)
Framework: "Chain-of-Thought"
Guardrails: ["Follow REST principles", "Document all endpoints",
             "Handle edge cases", "Validate inputs"]
```

---

## 🔢 Métrica 3: Estructura (Structure Score)

**Definición:** Qué tan bien organizado y lógico es el prompt.

### Fórmula

```typescript
function calculateStructureScore(components): number {
  let score = 3.0;  // Base score

  // Factor 1: Coherencia rol-directiva (+0.5 puntos)
  if (components.role && components.directive) {
    score += 0.5;
  }

  // Factor 2: Framework definido (+0.5 puntos)
  if (components.framework) {
    score += 0.5;
  }

  // Factor 3: Guardrails presentes (+0.5 puntos)
  if (components.guardrails && components.guardrails.length > 0) {
    score += 0.5;
  }

  // Factor 4: Estructura explícita (+0.5 puntos)
  const directive = components.directive || "";
  const hasNewlines = directive.includes("\n");
  const hasNumberedList = directive.match(/[1-9]\./);
  const hasBullets = directive.match(/[-*]\s/);

  if (hasNewlines || hasNumberedList || hasBullets) {
    score += 0.5;
  }

  return Math.min(5.0, Math.max(1.0, score));
}
```

### Indicadores de Estructura

```
Patrones que aumentan el score:
├── Listas numeradas: "1. Item, 2. Item, 3. Item"
├── Viñetas: "- Item, - Item, - Item"
├── Saltos de línea: "\n\n"
├── Secciones claras: "## Section"
├── Jerarquía visual: Sangría, espaciado

Patrones que no afectan:
├── Texto continuo (sin estructura)
├── Párrafos largos sin separación
```

### Ejemplos

```
❌ Score: 2.5/5
Directive: "create an api that does things and handles errors and
shows data and is fast and secure"

✅ Score: 4.5/5
Directive: "Create a REST API with the following structure:
           1. Define the data models
           2. Implement CRUD endpoints
           3. Add authentication middleware
           4. Implement error handling
           5. Add unit tests"
```

---

## 🔢 Métrica 4: Ejemplos (Examples Score)

**Definición:** Presencia y calidad de ejemplos en el prompt.

### Fórmula

```typescript
function calculateExamplesScore(components): number {
  let score = 1.0;  // Base score (sin ejemplos)

  const content = (components.role || "") + " " + (components.directive || "");

  // Factor 1: Indicadores de ejemplos (+2 puntos)
  const exampleIndicators = [
    "example", "for instance", "such as", "e.g.",
    "for example", "illustrate", "demonstrate"
  ];

  const hasExamples = exampleIndicators.some(indicator =>
    content.toLowerCase().includes(indicator)
  );

  if (hasExamples) {
    score += 2.0;
  }

  // Factor 2: Ejemplos input/output (+1 punto)
  const hasInput = content.toLowerCase().includes("input:");
  const hasOutput = content.toLowerCase().includes("output:");

  if (hasInput && hasOutput) {
    score += 1.0;
  }

  // Factor 3: Múltiples ejemplos (+1 punto)
  const exampleCount = (content.match(/example/gi) || []).length;
  if (exampleCount >= 2) {
    score += 1.0;
  }

  return Math.min(5.0, score);
}
```

### Niveles de Ejemplos

| Score | Tipo de Ejemplos | Calidad |
|-------|-----------------|---------|
| 1.0 | Sin ejemplos | Pobre |
| 3.0 | Genéricos ("for example") | Aceptable |
| 4.0 | Input/Output específicos | Bueno |
| 5.0 | Múltiples ejemplos específicos | Excelente |

### Ejemplos

```
❌ Score: 1.0/5
Role: "Developer"
Directive: "Write a function to parse dates"

✅ Score: 4.0/5
Role: "Developer"
Directive: "Write a function to parse dates.
           For example:
           Input: "2024-01-15" → Output: Date object
           Input: "15/01/2024" → Output: Date object"

⭐ Score: 5.0/5
Directive: "Parse dates in multiple formats.
           Example 1: ISO format
           Input: '2024-01-15T10:30:00Z' → Output: Date object
           Example 2: European format
           Input: '15/01/2024 10:30' → Output: Date object
           Example 3: US format
           Input: '01/15/2024 10:30 AM' → Output: Date object"
```

---

## 🔢 Métrica 5: Guardrails (Guardrails Score)

**Definición:** Cantidad y calidad de restricciones y límites.

### Fórmula

```typescript
function calculateGuardrailsScore(components): number {
  const guardrails = components.guardrails || [];
  const count = guardrails.length;

  // Escala simple basada en cantidad
  if (count === 0) return 1.0;
  if (count === 1) return 2.0;
  if (count === 2) return 3.0;
  if (count === 3) return 4.0;
  if (count >= 4) return 5.0;

  return 1.0;
}
```

### Categorías de Guardrails

```
Tipos de guardrails que se pueden detectar:

1. Seguridad (Safety)
   - "No generate malicious code"
   - "Avoid security vulnerabilities"
   - "Sanitize user input"

2. Calidad (Quality)
   - "Follow best practices"
   - "Include error handling"
   - "Add unit tests"

3. Formato (Format)
   - "Output as JSON"
   - "Use Markdown"
   - "Max 500 words"

4. Alcance (Scope)
   - "Only Python code"
   - "Frontend only"
   - "No external dependencies"

5. Ética (Ethics)
   - "Respect privacy"
   - "Avoid bias"
   - "Be inclusive"
```

### Ejemplos

```
❌ Score: 1.0/5
Guardrails: []

✅ Score: 4.0/5
Guardrails: [
  "Handle all error cases gracefully",
  "Follow TypeScript best practices",
  "Include JSDoc comments"
]

⭐ Score: 5.0/5
Guardrails: [
  "Handle all error cases gracefully",
  "Follow TypeScript best practices",
  "Include JSDoc comments for all functions",
  "Max 200 lines of code",
  "No external dependencies besides standard library"
]
```

---

## 📊 Score General (Overall Score)

### Fórmula

```typescript
function calculateOverallScore(metrics: QualityMetrics): number {
  // Promedio simple de las 5 métricas
  const overall = (
    metrics.clarity +
    metrics.completeness +
    metrics.structure +
    metrics.examples +
    metrics.guardrails
  ) / 5;

  // Redondear a 1 decimal
  return Math.round(overall * 10) / 10;
}
```

### Interpretación

| Overall Score | Calidad | Acción Recomendada |
|--------------|--------|-------------------|
| 1.0 - 2.0 | Muy Pobre | Requiere mejora completa |
| 2.1 - 3.0 | Pobre | Necesita enhancements significativos |
| 3.1 - 4.0 | Aceptable | Bueno, con optimizaciones opcionales |
| 4.1 - 4.5 | Bueno | Excelente, mejoras menores |
| 4.6 - 5.0 | Excelente | Óptimo, listo para producción |

---

## 🧮 Métricas Adicionales

### Token Estimation

**Propósito:** Estimar consumo de tokens para costos y límites.

```typescript
function estimateTokens(text: string): number {
  // Heurística: ~1.3 tokens por palabra
  const words = text.split(/\s+/).length;
  return Math.ceil(words * 1.3);
}

// Estimación más precisa
function estimateTokensPrecise(text: string): number {
  // ~4 caracteres por token (regla general)
  return Math.ceil(text.length / 4);
}
```

**Tabla de referencia:**

| Texto | Palabras | Tokens (1.3x) | Tokens (/4) |
|-------|---------|---------------|-------------|
| 100 chars | ~17 | 22 | 25 |
| 500 chars | ~83 | 108 | 125 |
| 1000 chars | ~167 | 217 | 250 |
| 5000 chars | ~833 | 1083 | 1250 |

### Compression Ratio

**Propósito:** Medir eficiencia de optimización.

```typescript
function calculateCompressionRatio(original: number, optimized: number): number {
  return original / optimized;
}

// Porcentaje de reducción
function calculateTokenReduction(original: number, optimized: number): number {
  return ((original - optimized) / original) * 100;
}
```

**Ejemplos:**

| Original | Optimizado | Ratio | Reducción |
|----------|-----------|-------|-----------|
| 1000 | 800 | 1.25x | 20% |
| 1000 | 500 | 2.00x | 50% |
| 1000 | 200 | 5.00x | 80% |

---

## 🎯 Aplicación a Raycast

### Métricas para Código de Extensiones

```typescript
interface RaycastCodeMetrics {
  readability: number;      // Basado en claridad
  efficiency: number;       // Basado en estructura
  errorHandling: number;    // Basado en guardrails
  typeSafety: number;       // TypeScript específico
  documentation: number;    // Basado en ejemplos
}
```

### Fórmulas Adaptadas

```typescript
function calculateRaycastReadability(code: string): number {
  let score = 3.0;

  // Factor 1: Nombres descriptivos
  const hasDescriptiveNames = /\b[a-z][a-zA-Z0-9]{8,}\b/.test(code);
  if (hasDescriptiveNames) score += 0.5;

  // Factor 2: Comentarios
  const commentRatio = (code.match(/\/\/.*$/gm) || []).length / code.split("\n").length;
  if (commentRatio > 0.1 && commentRatio < 0.3) score += 0.5;
  if (commentRatio >= 0.3) score -= 0.5; // Demasiados comentarios

  // Factor 3: Complejidad ciclomática
  const complexity = (code.match(/\bif\b/g) || []).length +
                    (code.match(/\bfor\b/g) || []).length +
                    (code.match(/\bwhile\b/g) || []).length;
  if (complexity <= 3) score += 0.5;
  if (complexity > 10) score -= 0.5;

  return Math.min(5.0, Math.max(1.0, score));
}

function calculateRaycastErrorHandling(code: string): number {
  const tryCount = (code.match(/\btry\s*{/g) || []).length;
  const catchCount = (code.match(/\bcatch\b/g) || []).length;

  if (tryCount === 0) return 1.0;
  if (catchCount === tryCount) {
    // Todo try tiene catch
    return tryCount >= 3 ? 5.0 : 3.5;
  }
  return 2.0; // try sin catch
}
```

---

## 📈 Patrones de Uso

### Para Comparación de Prompts

```typescript
// Comparar dos versiones
const v1Metrics = calculateQualityMetrics(promptV1);
const v2Metrics = calculateQualityMetrics(promptV2);

// Delta
const improvement = {
  clarity: v2Metrics.clarity - v1Metrics.clarity,
  completeness: v2Metrics.completeness - v1Metrics.completeness,
  overall: v2Metrics.overallScore - v1Metrics.overallScore
};

// Decisión
if (improvement.overall > 0.5) {
  // Adoptar V2
}
```

### Para Detección de Problemas

```typescript
function detectWeaknesses(metrics: QualityMetrics): string[] {
  const weaknesses = [];

  if (metrics.clarity < 3.0) {
    weaknesses.push("clarity: ambiguous language or vague instructions");
  }
  if (metrics.completeness < 3.0) {
    weaknesses.push("completeness: missing key components");
  }
  if (metrics.structure < 3.0) {
    weaknesses.push("structure: poor organization");
  }
  if (metrics.examples < 2.0) {
    weaknesses.push("examples: add concrete examples");
  }
  if (metrics.guardrails < 3.0) {
    weaknesses.push("guardrails: add safety constraints");
  }

  return weaknesses;
}
```

### Para Tracking de Optimización

```typescript
interface OptimizationHistory {
  timestamp: number;
  metrics: QualityMetrics;
  changes: string[];
}

function trackProgress(history: OptimizationHistory[]): TrendAnalysis {
  const first = history[0].metrics;
  const last = history[history.length - 1].metrics;

  return {
    overallImprovement: last.overallScore - first.overallScore,
    mostImproved: findMostImproved(first, last),
    stillWeak: findWeakBelowTarget(last, 4.0),
    trend: calculateTrend(history)  // improving, stable, degrading
  };
}
```

---

## 🚀 Decisiones de Diseño

### Por qué Escala 1-5

**Alternativas consideradas:**
- 0-100 (demasiado granular)
- 1-10 (demasiado sutil)
- 1-3 (demasiado simple)

**Por qué 1-5:**
- ✅ Suficiente resolución para diferenciar
- ✅ Fácil de interpretar mentalmente
- ✅ Compatible con estrellas/calificaciones comunes
- ✅ Buen balance entre precisión y simplicidad

### Por qué Peso Igual

**Alternativa considerada:** Pesos variables

```typescript
// Alternativa NO adoptada
overall = (clarity*0.3 + completeness*0.3 +
          structure*0.2 + examples*0.1 + guardrails*0.1)
```

**Por qué peso igual (0.2 cada uno):**
- ✅ Todas las dimensiones son importantes
- ✅ Más simple de explicar
- ✅ Evita sobre-optimización de una métrica
- ✅ Más justo para diferentes tipos de prompts

### Por qué Base Score Diferente

**Por qué cada métrica tiene base diferente:**

| Métrica | Base | Lógica |
|---------|------|--------|
| Claridad | 3.0 | Es difícil estar muy confuso |
| Completitud | 1.0 | Es fácil faltar componentes |
| Estructura | 3.0 | La organización básica es común |
| Ejemplos | 1.0 | La mayoría no incluye ejemplos |
| Guardrails | 1.0 | Muchos prompts no tienen restricciones |

---

## ⚠️ Patrones a Evitar

### 1. No Usar Scores Como Única Métrica

```typescript
// MAL: Decidir solo por score
if (promptA.overall > promptB.overall) {
  use(promptA)
}

// BIEN: Considerar contexto
if (promptA.overall > promptB.overall &&
    promptA.tokens < promptB.tokens) {
  use(promptA)  // Mejor Y más barato
}
```

### 2. No Ignorar Correlaciones

```typescript
// Las métricas están correlacionadas:
// - Mayor completitud → suele mejorar estructura
// - Más ejemplos → suele mejorar claridad

// No optimizar en aislamiento
```

### 3. No Sobre-ajustar al Score

```typescript
// MAL: Modificar solo para aumentar score
prompt.add("For example, example")  // Artificial

// BIEN: Mejoras genuinas
prompt.add("Input: 'user query' → Output: 'formatted response'")
```

---

## 📈 Benchmarks y Umbrales

### Para Prompts de Producción

| Métrica | Mínimo Aceptable | Bueno | Excelente |
|---------|------------------|-------|-----------|
| Claridad | 3.0 | 4.0 | 4.5+ |
| Completitud | 3.5 | 4.5 | 5.0 |
| Estructura | 3.0 | 4.0 | 4.5+ |
| Ejemplos | 2.0 | 3.5 | 4.5+ |
| Guardrails | 3.0 | 4.0 | 4.5+ |
| **Overall** | **3.2** | **4.0** | **4.5+** |

### Para Diferentes Casos de Uso

```
Prompts simples (one-shot):
├── Claridad: 4.0+ (crítico)
├── Ejemplos: 1.0 (opcional)
└── Overall: 3.5+

Prompts complejos (multi-step):
├── Completitud: 4.5+ (crítico)
├── Estructura: 4.0+ (crítico)
├── Ejemplos: 3.5+ (importante)
└── Overall: 4.2+

Prompts con seguridad (sensitive):
├── Guardrails: 5.0 (crítico)
├── Claridad: 4.0+ (importante)
└── Overall: 4.0+
```

---

## 🔍 Referencias del Código Fuente

### Archivos Principales

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `/services/enhancementService.ts` | Cálculo de métricas de calidad | 441-490 (calculateQualityMetrics) |
| `/services/promptOptimizationService.ts` | Optimización y métricas adicionales | 80-127 (model profiles) |

### Funciones Clave

- **Clarity:** `calculateClarityScore()` - enhancementService.ts:495-528
- **Completeness:** `calculateCompletenessScore()` - enhancementService.ts:533-549
- **Structure:** `calculateStructureScore()` - enhancementService.ts:554-571
- **Examples:** `calculateExamplesScore()` - enhancementService.ts:576-606
- **Guardrails:** `calculateGuardrailsScore()` - enhancementService.ts:611-623
- **Overall:** `calculateQualityMetrics()` - enhancementService.ts:441-490

---

## ✅ Checklist de Implementación

Para implementar este sistema en Raycast:

- [ ] Definir las 5 métricas base
- [ ] Implementar funciones de scoring
- [ ] Crear sistema de normalización (1-5)
- [ ] Añadir detección de debilidades
- [ ] Implementar comparación entre versiones
- [ ] Crear visualización de scores
- [ ] Añadir tracking histórico
- [ ] Configurar umbrales por caso de uso
- [ ] Testing con prompts reales
- [ ] Validación contra evaluación humana

---

**Próximos documentos:**
- `multi-provider-llm-abstraction.md` - Capa de abstracción LLM
- `validation-pipeline-pattern.md` - Pipeline de validación
- `template-recommendation-strategy.md` - Recomendación de templates

---

**Documentos completados:**
✅ `prompt-wizard-pattern.md` - Sistema wizard de 6 pasos
✅ `ab-testing-architecture.md` - Testing A/B completo
✅ `enhancement-engine-pattern.md` - Motor de mejora iterativa
✅ `quality-metrics-system.md` - Sistema cuantitativo de evaluación
