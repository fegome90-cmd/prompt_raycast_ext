# Prompt Wizard Pattern - Sistema Guiado de Creación de Prompts

**Prioridad:** 🔴 CRÍTICA - ROI MUY ALTO
**Fuente:** Architect v3.2.0 - `/components/PromptWizard.tsx`
**Complejidad:** Media
**Adaptabilidad:** Perfecta para Raycast

---

## 🎯 Concepto Core

Sistema wizard modular de 6 pasos que guía al usuario a través de la creación estructurada de prompts, desde un objetivo inicial hasta un prompt completo con roles, directivas, frameworks y guardrailas.

**El problema que resuelve:**
- Los usuarios no saben estructurar prompts efectivos
- Crear prompts desde cero es abrumador
- Se olvidan componentes críticos (roles, restricciones, frameworks)
- La calidad del prompt depende de conocimiento experto

**La solución:**
- Flujo guiado paso a paso
- Recomendaciones de templates basadas en el objetivo
- Validación progresiva por paso
- Vista previa final antes de guardar

---

## 🏗️ Arquitectura del Sistema

### Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PROMPT WIZARD FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ STEP 0:      │ →  │ STEP 1:      │ →  │ STEP 2:      │             │
│  │ Discovery    │    │ Objective    │    │ Role         │             │
│  │              │    │              │    │              │             │
│  │ • Search     │    │ • What goal? │    │ • Who is AI? │             │
│  │ • Recommend  │    │ • Target     │    │ • Expertise  │             │
│  │ • Skip       │    │ • Context    │    │ • Persona    │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         ↓                   ↓                   ↓                       │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ STEP 3:      │ →  │ STEP 4:      │ →  │ STEP 5:      │             │
│  │ Directive    │    │ Framework    │    │ Guardrails   │             │
│  │              │    │              │    │              │             │
│  │ • What do?   │    │ • How think? │    │ • Limits     │             │
│  │ • Actions    │    │ • CoT/ToT    │    │ • Safety     │             │
│  │ • Format     │    │ • Method     │    │ • Quality    │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         ↓                                                                 │
│                                                                         │
│  ┌──────────────┐                                                       │
│  │ STEP 6:      │                                                       │
│  │ Plan View    │                                                       │
│  │              │                                                       │
│  │ • Review     │                                                       │
│  │ • Name       │                                                       │
│  │ • Save       │                                                       │
│  └──────────────┘                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estado Compartido

El wizard mantiene un estado unificado que se va construyendo progresivamente:

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
}
```

---

## 🔧 Componentes Clave

### 1. **Step Discovery (Paso 0) - Búsqueda Inteligente**

**Propósito:** Encontrar templates existentes que coincidan con el objetivo del usuario

**Patrones:**

```
Usuario ingresa objetivo
        ↓
   ¿Longitud >= 5?
        ↓
   Búsqueda en templates
        ↓
   Algoritmo de similitud
        ↓
   Recomendaciones top 3
        ↓
   Usuario puede:
   - Aplicar recomendación
   - Crear desde cero
```

**Concepto clave: Búsqueda semántica**
- No es búsqueda exacta de texto
- Usa similitud semántica entre objetivos
- Retorna mejores coincidencias con scores
- Permite partir de base existente

**Validación:**
- Mínimo 5 caracteres para buscar
- Si no hay coincidencias, permitir crear desde cero
- No bloquear el flujo si falla la búsqueda

### 2. **Step Objective (Paso 1) - Definición de Meta**

**Propósito:** Establecer el objetivo claro y medible

**Patrones de validación:**
- Longitud mínima: 5 caracteres
- Debe comenzar con verbo de acción
- Ideal: 10-100 palabras
- Score de calidad: longitud + claridad

**Ejemplos de buenos objetivos:**
```
✅ "Diseñar un proceso escalable para crear ADRs"
✅ "Generar documentación técnica para APIs REST"
✅ "Crear un sistema de análisis de sentimiento para reviews"
```

**Ejemplos de malos objetivos:**
```
❌ "ayuda con código" (demasiado vago)
❌ "algo de IA" (sin contexto)
❌ "" (vacío)
```

### 3. **Step Role (Paso 2) - Asignación de Persona**

**Propósito:** Definir quién será el AI para cumplir el objetivo

**Patrones:**
- Sugerencias basadas en el objetivo (AI-powered)
- Roles predefinidos comunes
- Opción de rol personalizado
- El rol debe justificarse con el objetivo

**Validación:**
- Longitud mínima: 3 palabras
- Debe incluir expertise específico
- Score de calidad: relevancia con objetivo + especificidad

**Ejemplos:**
```
Objetivo: "Diseñar ADRs"
Rol sugerido: "Arquitecto de software especializado en
               documentación técnica y patrones de diseño"
```

### 4. **Step Directive (Paso 3) - Instrucciones Específicas**

**Propósito:** Definir qué debe hacer exactamente el AI

**Patrones:**
- Comienza con verbos de acción
- Incluye formato de salida esperado
- Específico sobre pasos o requisitos
- Puede incluir ejemplos

**Validación:**
- Longitud mínima: 10 palabras
- Debe mencionar el objetivo
- Score de calidad: alineación con objetivo + especificidad

### 5. **Step Framework (Paso 4) - Metodología de Pensamiento**

**Propósito:** Seleccionar cómo el AI debe abordar el problema

**Frameworks disponibles:**

| Framework | Caso de uso | Ejemplo |
|-----------|-------------|---------|
| **Chain-of-Thought (CoT)** | Problemas secuenciales | "Piensa paso a paso..." |
| **Tree of Thoughts (ToT)** | Exploración de opciones | "Considera múltiples caminos..." |
| **Decomposition** | Problemas complejos | "Divide en subproblemas..." |
| **Role-Playing** | Simulaciones | "Actúa como un X..." |

**Selección inteligente:**
- Sugerir framework basado en objetivo
- Explicar por qué ese framework
- Permitir cambio manual

### 6. **Step Guardrails (Paso 5) - Restricciones y Límites**

**Propósito:** Establecer qué NO debe hacer el AI

**Tipos de guardrailas:**
- **Seguridad:** No generar código malicioso
- **Calidad:** Citar fuentes, verificar datos
- **Formato:** Longitud máxima, estructura específica
- **Alcance:** Solo ciertos lenguajes, solo ciertos topics

**Patrones:**
- Lista dinámica (agregar/eliminar)
- Sugerencias basadas en objetivo
- Validación de no duplicados
- Mínimo 1 guardraila recomendada

### 7. **Plan View (Paso 6) - Revisión Final**

**Propósito:** Vista previa completa antes de guardar

**Componentes:**
- Visualización de todo el prompt estructurado
- Campo para nombre del prompt
- Indicador si es edición o creación
- Botón de guardado final

---

## 🎨 Patrones de UI/UX

### 1. **Barra de Progreso**

```
Step 1/6: [████████░░░░░░░░] 16%
```

**Conceptos:**
- Indicador visual de progreso
- Muestra paso actual y total
- Se actualiza dinámicamente
- Motiva al usuario a completar

### 2. **Validación Progresiva**

```
Botón "Next" deshabilitado hasta:
├── Step 0: Objetivo >= 5 caracteres
├── Step 1: Objetivo completo
├── Step 2: Rol definido
├── Step 3: Directiva completa
├── Step 4: Framework seleccionado
└── Step 5: Al menos 1 guardraila
```

**Patrón clave:**
- No permitir avanzar con datos inválidos
- Feedback visual inmediato
- Mensajes de error específicos
- No bloquear completamente (permitir volver)

### 3. **Navegación Flexible**

```
[Back] [Skip Discovery] [Next] [Finish]
```

**Patrones:**
- "Back" siempre disponible (excepto paso 0)
- "Skip" en discovery para crear desde cero
- "Next" cambia texto según paso
- "Finish" solo en último paso

### 4. **Sugerencias en Tiempo Real**

```
Usuario escribe: "Diseñar API REST"

Sugerencias que aparecen:
├── Role: "Arquitecto de APIs..."
├── Framework: "Decomposition (por ser estructurado)"
└── Guardrails: "Documentar endpoints, seguir REST"
```

---

## 🔗 Integración con Servicios

### 1. **Template Recommendation Service**

**Cuándo se llama:**
- Usuario ingresa objetivo en Step 0
- Trigger: longitud >= 5 caracteres
- Debounce: 500ms después de último input

**Qué retorna:**
```typescript
interface TemplateRecommendation {
  template: {
    components: {
      role: { content: string }
      directive: { content: string }
      framework: { content: string }
      constraints: Array<{ content: string }>
    }
  }
  similarityScore: number
  relevanceReason: string
}
```

**Flujo de aplicación:**
1. Usuario selecciona recomendación
2. Extraer componentes del template
3. Mantener objetivo del usuario
4. Prellenar pasos siguientes
5. Saltar al paso de Role (paso 2)

### 2. **Quality Validation Service**

**Cuándo se llama:**
- En cada paso para validar datos
- Antes de habilitar botón "Next"
- En vista final para score total

**Métricas calculadas:**
- Claridad: longitud + estructura
- Completitud: componentes presentes
- Concisión: sin redundancias
- Score general: (claridad*0.4 + completitud*0.4 + concisión*0.2)

---

## 💡 Aplicación a Raycast

### Adaptación del Concepto

**Para Extension/Command Creation:**

```
Wizard de Creación de Extensión Raycast
├── Paso 0: Discovery (recomendar extensiones similares)
├── Paso 1: Objective (¿qué hace la extensión?)
├── Paso 2: Role (qué tipo de extensión: tool, command, etc.)
├── Paso 3: Directive (qué acciones específicas)
├── Paso 4: Framework (patrón de implementación)
├── Paso 5: Guardrails (límites y permisos)
└── Paso 6: Plan View (código generado + nombre)
```

**Patrones específicos para Raycast:**

1. **Paso 1 (Objective):**
   - "Crear extensión que busque en GitHub"
   - "Comando que formatee JSON"
   - "Herramienta que gestione tareas"

2. **Paso 2 (Role/Tipo):**
   - Command (con o sin argumentos)
   - Tool (con menú de acciones)
   - List (desplegar lista de opciones)

3. **Paso 4 (Framework):**
   - Simple fetch (llamada API simple)
   - Interactive flow (flujo con pasos)
   - Data transformation (procesamiento de datos)
   - AI-powered (usar LLM)

4. **Paso 5 (Guardrails):**
   - Permisos API necesarios
   - Rate limiting
   - Manejo de errores
   - Caché de resultados

### Diferencias Clave

| Architect | Raycast |
|-----------|---------|
| Prompt creation | Extension creation |
| Text-based output | Code-based output |
| LLM-focused | API + LLM |
| Generic prompts | Specific actions |

---

## 🚀 Decisiones de Diseño

### Por qué 6 pasos (no más, no menos)

**Menos de 5 pasos:**
- ❌ Demasiado contenido por paso
- ❌ Abrumador para el usuario
- ❌ Difícil de validar correctamente

**Más de 7 pasos:**
- ❌ Abandono por fatiga
- ❌ Percepción de complejidad
- ❌ Más oportunidades de error

**6 pasos ideal:**
- ✅ Balance entre profundidad y usabilidad
- ✅ Cada paso tiene propósito claro
- ✅ Progreso visible y motivador

### Por qué Discovery al inicio

**Alternativa considerada:** Discovery después de Objective

**Por qué no:**
- Usuario ya invirtió tiempo escribiendo
- Puede sentirse ignorado si se recomienda algo diferente
- Más fricción para aceptar recomendación

**Por qué al inicio:**
- Usuario aún no tiene compromiso emocional
- Recomendación guía el resto del flujo
- Opción de skip mantiene flexibilidad

### Por qué Plan View al final

**Alternativa considerada:** Vista previa en cada paso

**Por qué no:**
- Añade complejidad a UI
- Puede distraer del paso actual
- Más código a mantener

**Por qué solo al final:**
- Momento de "truth" antes de guardar
- Contexto completo del prompt
- Oportunidad de hacer cambios finales

---

## 📊 Patrones a Adoptar (Conceptualmente)

### 1. **Estado Centralizado**

```typescript
// NO: Estado disperso en múltiples componentes
const [objective, setObjective] = useState()
const [role, setRole] = useState()
// ... en diferentes archivos

// SÍ: Estado unificado en wizard padre
const [wizardState, setWizardState] = useState({
  objective: '', role: '', directive: '',
  framework: default, guardrails: []
})
```

### 2. **Validación por Paso**

```typescript
// Cada paso sabe validar sus propios datos
interface StepConfig {
  validate: (data: any) => boolean
  canProceed: () => boolean
  errorMessages: string[]
}
```

### 3. **Recomendaciones Contextuales**

```typescript
// No sugerir lo mismo siempre
const suggestions = {
  role: generateFromObjective(objective),
  framework: selectByComplexity(objective),
  guardrails: inferFromDomain(objective)
}
```

### 4. **Progresividad**

```typescript
// No mostrar todo de golpe
// Revelar información según necesidad
// Permitir saltarse pasos opcionales
```

---

## ⚠️ Patrones a Evitar

### 1. **No Bloquear el Flujo**

```typescript
// MAL: Validación excesivamente estricta
if (!hasPerfectGrammar(objective)) {
  disableNext()  // Frustrante
}

// BIEN: Validación razonable
if (objective.length < 5) {
  disableNext()  // Justificado
}
```

### 2. **No Perder Estado al Navegar**

```typescript
// MAL: Recargar página o reiniciar wizard
// Usuario pierde todo el trabajo

// BIEN: Persistir estado
// Permitir volver atrás sin perder datos
```

### 3. **No Sobrecargar con Opciones**

```typescript
// MAL: 20 opciones de framework
// Parálisis por análisis

// BIEN: 4-5 frameworks bien explicados
// Con recomendación inteligente
```

---

## 📈 Métricas de Éxito

### Para Medir Adopción

- **Tasa de completación:** % que completa los 6 pasos
- **Tasa de abandono:** % que abandona en cada paso
- **Tiempo por paso:** Duración promedio
- **Uso de recomendaciones:** % que acepta sugerencias

### Para Medir Calidad

- **Score promedio de prompts:** Quality metrics
- **Satisfacción post-creación:** Encuesta o rating
- **Tasa de reutilización:** % que edita vs crea nuevo
- **Guardrails agregados:** Promedio por prompt

### Benchmarks Sugerertos

| Métrica | Bueno | Excelente |
|---------|-------|-----------|
| Completación | >70% | >85% |
| Tiempo total | <5 min | <3 min |
| Quality score | >3.5/5 | >4.2/5 |
| Recomendaciones aceptadas | >30% | >50% |

---

## 🔍 Referencias del Código Fuente

### Archivos Principales

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `/components/PromptWizard.tsx` | Wizard principal | 62-327 |
| `/components/StepObjective.tsx` | Paso 1 | 8-25 |
| `/components/StepRole.tsx` | Paso 2 | - |
| `/components/StepDirective.tsx` | Paso 3 | - |
| `/components/StepFramework.tsx` | Paso 4 | - |
| `/components/StepGuardrails.tsx` | Paso 5 | - |
| `/components/StepDiscovery.tsx` | Paso 0 | - |
| `/components/PlanView.tsx` | Vista final | - |
| `/types.ts` | PlanData interface | 28-34 |

### Servicios Relacionados

| Archivo | Propósito |
|---------|-----------|
| `/services/templateRecommendationService.ts` | Búsqueda de templates |
| `/services/validationService.ts` | Validación de prompts |
| `/services/promptQualityService.ts` | Métricas de calidad |

---

## ✅ Checklist de Implementación

Para implementar este patrón en Raycast:

- [ ] Definir estructura de datos centralizada
- [ ] Crear pasos modulares independientes
- [ ] Implementar validación por paso
- [ ] Añadir barra de progreso
- [ ] Configurar navegación flexible
- [ ] Integrar sistema de recomendaciones
- [ ] Implementar vista previa final
- [ ] Añadir persistencia de estado
- [ ] Configurar métricas de tracking
- [ ] Testing de cada paso independientemente

---

**Próximos documentos:**
- `ab-testing-architecture.md` - Cómo comparar variaciones de prompts
- `enhancement-engine-pattern.md` - Mejora iterativa automática
- `quality-metrics-system.md` - Métricas cuantitativas de calidad
