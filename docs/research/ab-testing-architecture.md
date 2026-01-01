# A/B Testing Architecture - Sistema de Evaluación Comparativa

**Prioridad:** 🔴 CRÍTICA - ROI MUY ALTO
**Fuente:** Architect v3.2.0 - `/components/EvaluationSuite.tsx`, `/constants.ts`
**Complejidad:** Alta
**Adaptabilidad:** Alta para Raycast

---

## 🎯 Concepto Core

Sistema completo de testing A/B para comparar múltiples prompts mediante test cases automatizados, criterios de evaluación configurables, scoring AI-powered, y análisis estadístico con comparación contra baseline.

**El problema que resuelve:**
- ¿Cuál prompt funciona mejor para un caso de uso?
- ¿Cómo medir objetivamente la calidad de un prompt?
- ¿Cómo comparar variaciones de forma sistemática?
- ¿Cuándo una mejora es significativa vs ruido?

**La solución:**
- Suite de evaluación configurable
- Test cases reproducibles
- Criterios de evaluación predefinidos
- Scoring automatizado con AI judge
- Análisis estadístico (media, desviación estándar)
- Comparación contra baseline

---

## 🏗️ Arquitectura del Sistema

### Flujo Principal de Evaluación

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     A/B TESTING EVALUATION FLOW                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CONFIGURACIÓN                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Evaluation Suite                                                  │  │
│  │ ├── Prompts a probar (2+)                                        │  │
│  │ ├── Test cases (inputs)                                          │  │
│  │ ├── Criterios de evaluación                                      │  │
│  │ └── Configuración (model, runs, baseline)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         ↓                                                               │
│                                                                         │
│  2. EJECUCIÓN                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ For each test case:                                              │  │
│  │   For each prompt:                                               │  │
│  │     For each run (1-3-5):                                         │  │
│  │       ├─ Ejecutar prompt con test case                           │  │
│  │       ├─ Capturar output y métricas                              │  │
│  │       └─ Evaluar con AI judge                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         ↓                                                               │
│                                                                         │
│  3. ANÁLISIS                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Aggregate Results                                                 │  │
│  │ ├── Score promedio por prompt                                   │  │
│  │ ├── Consistencia (std dev)                                       │  │
│  │ ├── Tiempo de ejecución                                          │  │
│  │ ├── Tokens consumidos                                            │  │
│  │ └── Comparación vs baseline (delta)                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         ↓                                                               │
│                                                                         │
│  4. VISUALIZACIÓN                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ├── Gráfico de barras (scores)                                   │  │
│  │ ├── Tabla comparativa                                             │  │
│  │ ├── Comparación lado a lado (modal)                              │  │
│  │ └── Exportar CSV                                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes Clave

### 1. **Evaluation Suite - Configuración Central**

**Estructura de datos:**

```typescript
interface EvaluationSuite {
  id: string;
  name: string;
  createdAt: string;

  // Qué probar
  promptIds: string[];           // Prompts a comparar (2+)
  testCases: TestCase[];         // Inputs de prueba
  criteria: EvaluationCriteria[]; // Criterios de evaluación

  // Resultados (post-ejecución)
  results?: EvaluationResult;    // Scores por test case

  // Configuración de ejecución
  config: {
    modelForRun: "gemini-2.5-pro" | "gemini-2.5-flash";
    judgeModel: "gemini-2.5-pro" | "gemini-2.5-flash";
    temperature: number;         // 0-1
    baselinePromptId?: string;   // Prompt de referencia
    runsPerTestCase: 1 | 3 | 5;  // Repeticiones para consistencia
  }
}
```

**Concepto clave:** La suite es la unidad de trabajo
- Contiene todo lo necesario para una evaluación
- Es persistente y reutilizable
- Puede ejecutarse múltiples veces
- Almacena resultados históricos

### 2. **Test Cases - Inputs Reproducibles**

**Estructura:**

```typescript
interface TestCase {
  id: string;
  input: string;  // El input que se pasa al prompt
}
```

**Patrones de diseño:**

```
Buenos test cases:
├── Específicos: "Analiza el sentimiento de: 'Me encanta este producto'"
├── Variados: Cubrir edge cases y casos normales
├── Reproducibles: Mismo input = misma evaluación
└── Independientes: No dependen del orden de ejecución

Malos test cases:
├── Vagos: "algo de sentimiento"
├── Consecutivos: Casos que asumen ejecución previa
└── Cambiantes: Inputs que varían cada ejecución
```

**Estrategia de selección:**

1. **Casos normales:** 60-70% de test cases
   - Representan el uso típico
   - Buenos resultados esperados

2. **Casos extremos:** 20-30% de test cases
   - Edge cases
   - Inputs inusuales
   - Casos límite

3. **Casos negativos:** 10-20% de test cases
   - Inputs inválidos
   - Casos que deben fallar
   - Verificar manejo de errores

### 3. **Criterios de Evaluación - Templates Predefinidos**

**10 Templates Predefinidos:**

| ID | Nombre | Categoría | Descripción |
|----|--------|-----------|-------------|
| `clarity` | Clarity and Coherence | clarity | ¿Es clara y comprensible la respuesta? |
| `actionability` | Actionability | actionability | ¿Proporciona pasos accionables? |
| `completeness` | Completeness | completeness | ¿Aborda todos los aspectos? |
| `accuracy` | Accuracy | accuracy | ¿Es factualmente correcta? |
| `creativity` | Creativity and Innovation | creativity | ¿Muestra pensamiento innovador? |
| `relevance` | Relevance | relevance | ¿Es relevante al input? |
| `structure` | Structure and Organization | structure | ¿Está bien organizada? |
| `conciseness` | Conciseness | clarity | ¿Es concisa sin perder detalles? |
| `evidence` | Evidence and Support | completeness | ¿Incluye evidencia o ejemplos? |
| `audience` | Audience Appropriateness | actionability | ¿Es apropiada para la audiencia? |

**Uso de criterios:**

```
Estrategia 1: Criterios predefinidos (rápido)
└── Seleccionar 2-3 templates de la lista
    └── Ventaja: No escribir criterios desde cero
    └── Ideal: Para evaluaciones rápidas

Estrategia 2: Criterios personalizados (específico)
└── Escribir criterios específicos del dominio
    └── Ventaja: Evaluación más precisa
    └── Ideal: Para casos de uso muy específicos

Estrategia 3: Híbrido (balanceado)
└── Combinar templates + personalizados
    └── 1-2 templates + 1-2 criterios específicos
    └── Mejor de ambos mundos
```

### 4. **Proceso de Scoring - AI Judge**

**Arquitectura de dos modelos:**

```
┌─────────────────────────────────────────────────────────────┐
│  MODEL FOR RUN (Ejecutor)                                  │
│  - Ejecuta el prompt con el test case                     │
│  - Genera el output a evaluar                             │
│  - Modelo más rápido (gemini-2.5-flash)                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
                  Output Generado
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  JUDGE MODEL (Evaluador)                                   │
│  - Recibe: output + input + criterios                     │
│  - Genera: score (1-10) + justificación                   │
│  - Modelo más capaz (gemini-2.5-pro)                       │
└─────────────────────────────────────────────────────────────┘
```

**Prompt del Judge:**

```
Rol: Eres un evaluador experto en calidad de respuestas AI

Input del test case: "{testCase.input}"

Criterios a evaluar:
1. "{criteria[0].description}"
2. "{criteria[1].description}"
...

Output a evaluar:
"""
{output}
"""

Tu tarea:
1. Evaluar el output contra cada criterio
2. Asignar un score del 1 al 10
3. Justificar tu puntuación

Formato de respuesta JSON:
{
  "score": <número 1-10>,
  "justification": "<explicación>"
}
```

**Estrategia de Scoring:**

- **1-3:** Pobre - No cumple el criterio
- **4-6:** Aceptable - Cumple parcialmente
- **7-8:** Bueno - Cumple bien el criterio
- **9-10:** Excelente - Supera expectativas

### 5. **Múltiples Runs - Consistencia**

**Por qué múltiples ejecuciones:**

```
Single Run (riesgoso):
Prompt A ──► Score: 7.3
Prompt B ──► Score: 7.8
¿Diferencia real? O ruido del modelo?


Multiple Runs (confiable):
Prompt A ──► [7.2, 7.4, 7.3] → Media: 7.30, SD: 0.10
Prompt B ──► [7.1, 8.5, 7.8] → Media: 7.80, SD: 0.70
                                    ↑
                         Mayor variación = menos confiable
```

**Configuración de runs:**

| Runs | Caso de uso | Costo | Confianza |
|------|-------------|-------|-----------|
| 1 | Pruebas rápidas | Bajo | Baja |
| 3 | Balance costo/confianza | Medio | Media |
| 5 | Máxima confianza | Alto | Alta |

**Análisis estadístico:**

```
Media (promedio): μ = Σx / n
  - Representa el rendimiento esperado

Desviación Estándar: σ = √(Σ(x-μ)² / n)
  - Baja σ = Consistente
  - Alta σ = Variable (menos confiable)
```

### 6. **Baseline Comparison - Delta Indicators**

**Concepto de Baseline:**

```
Prompt A (Baseline) → Score: 7.0
Prompt B (Variante) → Score: 7.5 (+0.5 ▲)
Prompt C (Variante) → Score: 6.3 (-0.7 ▼)
```

**Indicadores Delta:**

```
Δ Score (mayor es mejor):
├── ▲ +0.5 = Mejora significativa
├── ±0.0 = Sin diferencia
└── ▼ -0.5 = Empeoramiento

Δ Time (menor es mejor):
├── ▲ -200ms = Más rápido (mejor)
├── ±0ms = Igual velocidad
└── ▼ +200ms = Más lento (peor)

Δ Tokens (menor es mejor):
├── ▲ -100 = Más eficiente
├── ±0 = Igual consumo
└── ▼ +100 = Más costoso
```

---

## 📊 Análisis de Resultados

### 1. **Aggregate Metrics**

**Por Prompt:**

```typescript
interface PromptMetrics {
  promptId: string;
  promptName: string;

  // Score metrics
  avgScore: number;      // Media de todos los runs
  consistency: number;   // Desviación estándar

  // Performance metrics
  avgTime: number;       // Tiempo de ejecución promedio (ms)
  avgTokens: number;     // Tokens consumidos promedio

  // Comparison (si hay baseline)
  deltaScore?: number;   // Diferencia vs baseline
  deltaTime?: number;    // Diferencia de tiempo vs baseline
  deltaTokens?: number;  // Diferencia de tokens vs baseline
}
```

### 2. **Visualización de Resultados**

**Gráfico de Barras:**

```
Prompt A (Baseline): ████████████ 7.30
Prompt B:           █████████████ 7.80 ▲ +0.5
Prompt C:           ██████████   6.30 ▼ -1.0

Colores:
├── <3.0: Rojo (pobre)
├── 3-5: Naranja (aceptable)
├── 5-7: Amarillo (bueno)
├── 7-9: Verde claro (muy bueno)
└── 9-10: Verde oscuro (excelente)
```

**Tabla Comparativa:**

| Prompt | Avg Score | Consistency (SD) | Avg Time (ms) | Avg Tokens |
|--------|-----------|------------------|---------------|------------|
| Prompt A | 7.30 | 0.10 | 1200 | 4500 |
| Prompt B | 7.80 ▲ +0.5 | 0.70 ▲ +0.6 | 1500 ▲ +300 | 4800 ▲ +300 |

**Indicadores Delta:**
- ▲ = Mejora (verde)
- ▼ = Empeor (rojo)
- ± = Sin cambio (gris)

### 3. **Detailed Results - Por Test Case**

```
Test Case: "Analiza el sentimiento de: 'Me encanta este producto'"

┌─────────────────┬──────────┬───────────────────────────────┐
│ Prompt          │ Score    │ Justification                │
├─────────────────┼──────────┼───────────────────────────────┤
│ Prompt A        │ 8.2      │ Excelente análisis de        │
│                 │          │ sentimiento positivo con     │
│                 │          │ evidencia clara.            │
├─────────────────┼──────────┼───────────────────────────────┤
│ Prompt B        │ 7.5      │ Buen análisis pero podría    │
│                 │          │ incluir más detalles sobre  │
│                 │          │ el tono emocional.          │
└─────────────────┴──────────┴───────────────────────────────┘
```

**Botón "Compare Outputs":**
- Abre modal lado a lado
- Muestra todos los outputs
- Facilita comparación cualitativa

### 4. **Export CSV - Análisis Externo**

**Columnas exportadas:**

```csv
test_case_id,test_case_input,prompt_id,prompt_name,output,score,
justification,execution_time_ms,input_tokens,output_tokens,total_tokens
```

**Uso del CSV:**
- Análisis en Excel/Google Sheets
- Visualización en herramientas de BI
- Machine Learning sobre resultados
- Reportes para stakeholders

---

## 💡 Aplicación a Raycast

### Adaptación del Concepto

**Para Extension Commands Testing:**

```
Raycast A/B Testing Suite
├── Commands a probar (2+ versiones)
│   ├── Command v1: búsqueda simple
│   └── Command v2: búsqueda con filtros
│
├── Test cases (inputs del usuario)
│   ├── "buscar issue #123"
│   ├── "buscar pr de felipe"
│   └── "buscar repositorio raycast"
│
├── Criterios de evaluación
│   ├── Precisión del resultado
│   ├── Velocidad de respuesta
│   └── Formato de salida
│
└── Configuración
    ├── Modo: local vs API
    ├── Runs: 3 por test case
    └── Baseline: Command v1
```

**Métricas específicas para Raycast:**

| Métrica | Cómo medir | Umbral |
|---------|-----------|--------|
| **Precisión** | ¿Encuentra lo que busca? | >90% |
| **Velocidad** | Tiempo de respuesta | <2s |
| **UX** | ¿Es fácil usar el resultado? | Score >7 |
| **Eficiencia** | Tokens/API calls mínimos | <1000 |

### Ejemplo Práctico

**Test Case:** GitHub Issue Search

```
Command v1:
├── Input: "issue #123 en repo X"
├── Output: Lista de issues coincidentes
└── Criterio: ¿Encuentra el issue correcto?

Command v2 (con ML):
├── Input: "issue #123 en repo X"
├── Output: Issue más probable + contexto
└── Criterio: ¿Es más preciso que v1?

Ejecución:
├── 10 test cases (inputs variados)
├── 3 runs por case (consistencia)
└── Criterio: Precisión + Velocidad

Resultado:
├── v1: Precisión 75%, Velocidad 1.2s
└── v2: Precisión 92%, Velocidad 1.8s

Decisión: v2 es más preciso pero más lento
→ Implementar v2 con opción de fallback a v1
```

---

## 🚀 Decisiones de Diseño

### Por qué Dos Modelos (Runner + Judge)

**Alternativa considerada:** Usar mismo modelo para todo

**Por qué no:**
- Runner: Necesita ser rápido (cost-sensitive)
- Judge: Necesita ser preciso (quality-sensitive)
- Trade-offs óptimos diferentes

**Por qué dos modelos:**
- **Runner (gemini-2.5-flash):**
  - Ejecuta muchos prompts
  - Velocidad crítica
  - Precisión aceptable

- **Judge (gemini-2.5-pro):**
  - Ejecuta menos evaluaciones
  - Calidad de scoring crítica
  - Mejor razonamiento

### Por qué Runs Múltiples

**Alternativa considerada:** Single run

**Por qué no:**
- AI models tienen variabilidad inherente
- Single run puede ser outlier
- No se puede medir consistencia

**Por qué múltiples runs:**
- **Promedio:** Más representativo del rendimiento real
- **Desviación estándar:** Mide confiabilidad
- **Outliers:** Se pueden identificar y eliminar

**Costo vs beneficio:**
- 1 run: Rápido pero poco confiable
- 3 runs: Balance óptimo (recomendado)
- 5 runs: Máxima confianza pero 5x el costo

### Por qué Baseline

**Alternativa considerada:** Solo scores absolutos

**Por qué no:**
- Score de 7.5 ¿es bueno o malo?
- Sin contexto, difícil de interpretar
- Diferencias pueden ser ruido

**Por qué baseline:**
- **Referencia:** Comparación contra conocido
- **Delta:** Medición de mejora real
- **Decisión:** ¿Vale la pena el cambio?

---

## 📈 Patrones a Adoptar (Conceptualmente)

### 1. **Suite como Unidad de Trabajo**

```typescript
// NO: Evaluaciones ad-hoc dispersas
evaluate(promptA, testCases)
evaluate(promptB, testCases)

// SÍ: Suite configurada y reutilizable
const suite = {
  prompts: [promptA, promptB],
  testCases: [tc1, tc2, tc3],
  criteria: [clarity, accuracy]
}
runEvaluation(suite)
```

### 2. **Separación de Responsabilidades**

```
Runner Service:
└── Ejecuta prompts con test cases
    └── No sabe de evaluación

Judge Service:
└── Evalúa outputs según criterios
    └── No sabe de ejecución

Coordinator:
└── Orquesta runner + judge
    └── Conoce ambos servicios
```

### 3. **Resultados Inmutables**

```typescript
// NO: Modificar resultados existentes
suite.results[testCaseId].push(newRun)

// SÍ: Crear nueva versión
const newSuite = {
  ...suite,
  results: {
    ...suite.results,
    [testCaseId]: [...suite.results[testCaseId], newRun]
  }
}
```

### 4. **Estimación de Costos**

**Antes de ejecutar:**

```typescript
const estimatedTokens = (
  numTestCases *
  numPrompts *
  runsPerTestCase *
  (avgPromptTokens + avgOutputTokens)
)

// Mostrar al usuario
"Esta evaluación consumirá ~50K tokens ($0.15)"
"¿Continuar?"
```

---

## ⚠️ Patrones a Evitar

### 1. **No Asumir Normalidad de Datos**

```typescript
// MAL: Asumir distribución normal
const pValue = calculatePValue(scores) // Requiere normalidad

// BIEN: Usar pruebas no paramétricas
const winner = sortByMean(scores) // Solo requiere orden
```

### 2. **No Ignorar Consistencia**

```typescript
// MAL: Solo mirar media
if (promptB.avgScore > promptA.avgScore) {
  winner = promptB
}

// BIEN: Considerar consistencia
if (promptB.avgScore > promptA.avgScore &&
    promptB.consistency < MAX_SD) {
  winner = promptB
}
```

### 3. **No Ollear Dimensión Temporal**

```typescript
// MAL: Un solo punto en el tiempo
const winner = compare(now)

// BIEN: Tendencia en el tiempo
const winner = compare([t1, t2, t3])
```

---

## 📈 Métricas de Éxito

### Para Medir Calidad de Evaluación

- **Tiempo de ejecución:** <5 min para 10 test cases
- **Costo por evaluación:** <$0.50
- **Consistencia de scoring:** SD < 0.5
- **Satisfacción del usuario:** >4/5

### Benchmarks Sugeridos

| Métrica | Bueno | Excelente |
|---------|-------|-----------|
| Test cases por suite | 5-10 | 10+ |
| Prompts por suite | 2-3 | 3+ |
| Tiempo de ejecución | <10 min | <5 min |
| Precisión de scoring | 70% | 85%+ |
| Tasa de re-ejecución | >20% | >50% |

---

## 🔍 Referencias del Código Fuente

### Archivos Principales

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `/components/EvaluationSuite.tsx` | Suite de evaluación A/B | 383-1211 |
| `/constants.ts` | Templates de criterios | 57-118 |
| `/services/geminiService.ts` | Runner y Judge AI | evaluatePromptOutput, runSotaPrompt |

### Secciones Clave

- **Cost estimation:** 100-167 (EvaluationCostEstimator)
- **Aggregate metrics:** 169-307 (AggregateResultsCard)
- **Execution loop:** 527-625 (handleRunEvaluation)
- **CSV export:** 645-709 (handleExportCsv)

---

## ✅ Checklist de Implementación

Para implementar este patrón en Raycast:

- [ ] Definir estructura de EvaluationSuite
- [ ] Crear configuración de test cases
- [ ] Implementar sistema de criterios
- [ ] Configurar runner service (ejecutar comandos)
- [ ] Configurar judge service (evaluar resultados)
- [ ] Implementar análisis estadístico
- [ ] Crear visualización de resultados
- [ ] Añadir export CSV
- [ ] Implementar comparación baseline
- [ ] Testing de suites múltiples

---

**Próximos documentos:**
- `enhancement-engine-pattern.md` - Mejora iterativa automática
- `quality-metrics-system.md` - Métricas cuantitativas
- `multi-provider-llm-abstraction.md` - Abstracción de múltiples LLMs
