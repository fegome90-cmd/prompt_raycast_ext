# Quality Validation System - Sistema de Calidad

**Prioridad:** 🟡 IMPORTANTE - Asegura prompts de alta calidad
**Fuente:** Architect v3.2.0 - `services/promptOptimizationService.ts`
**Aplicabilidad:** Directamente aplicable a validación DSPy

---

## 📋 Índice

1. [Overview](#overview)
2. [5 Dimensiones de Calidad](#5-dimensiones-de-calidad)
3. [Fórmulas de Cálculo](#fórmulas-de-cálculo)
4. [Validation Pipeline](#validation-pipeline)
5. [Improvement Suggestions](#improvement-suggestions)
6. [DSPy Integration](#dspy-integration)

---

## Overview

### El Sistema de Calidad

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      QUALITY VALIDATION SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT: PlanData                                                        │
│      ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    QUALITY ANALYZER                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │ │
│  │  │   CLARITY     │  │ COMPLETENESS │  │  CONCISENESS  │           │ │
│  │  │    0-5       │  │     0-5      │  │     0-5      │           │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │ │
│  │  ┌──────────────┐  ┌──────────────┐                             │ │
│  │  │   EXAMPLES    │  │  GUARDRAILS   │                             │ │
│  │  │    0-5       │  │     0-5      │                             │ │
│  │  └──────────────┘  └──────────────┘                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│      ↓                                                                  │
│  OVERALL SCORE: (Clarity*0.3 + Completeness*0.3 + Conciseness*0.2 +    │
│                  Examples*0.1 + Guardrails*0.1)                         │
│      ↓                                                                  │
│  OUTPUT: Quality Report + Suggestions                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5 Dimensiones de Calidad

### 1. Claridad (Clarity)

**Definición:** Qué tan claro y entendible es el prompt.

```typescript
function calculateClarityScore(components: PlanData): number {
  let score = 3.0; // Base score

  // Role clarity
  if (components.role.length > 20) score += 0.5;
  if (hasExpertiseKeyword(components.role)) score += 0.5;
  if (hasExperienceLevel(components.role)) score += 0.3;

  // Directive clarity
  if (components.directive.length > 50) score += 0.5;
  if (hasActionVerb(components.directive)) score += 0.5;
  if (hasSpecificOutcome(components.directive)) score += 0.3;

  // Framework clarity
  if (components.framework !== null) score += 0.3;

  // Cap at 5.0
  return Math.min(5.0, score);
}

// Helper functions
function hasExpertiseKeyword(role: string): boolean {
  const keywords = [
    "expert", "specialist", "professional", "architect",
    "engineer", "strategist", "scientist"
  ];
  return keywords.some(kw => role.toLowerCase().includes(kw));
}

function hasExperienceLevel(role: string): boolean {
  const patterns = [
    /\d+\+?\s*years?/i,
    /senior/i,
    /lead/i,
    /principal/i
  ];
  return patterns.some(p => p.test(role));
}

function hasActionVerb(directive: string): boolean {
  const verbs = [
    "design", "create", "develop", "implement", "build",
    "analyze", "generate", "optimize", "establish"
  ];
  return verbs.some(v => directive.toLowerCase().startsWith(v));
}

function hasSpecificOutcome(directive: string): boolean {
  const indicators = [
    /\d+/,  // Contains numbers (metrics)
    /within/i,  // Time constraint
    /%/  // Percentage
  ];
  return indicators.some(i => i.test(directive));
}
```

### 2. Completitud (Completeness)

**Definición:** Presencia de todos los componentes necesarios.

```typescript
function calculateCompletenessScore(components: PlanData): number {
  let score = 0.0;
  const maxScore = 5.0;
  const componentCount = 5;

  // Objective (required)
  if (components.objective && components.objective.length >= 5) {
    score += 1.0;
  }

  // Role (required)
  if (components.role && components.role.length >= 10) {
    score += 1.0;
  }

  // Directive (required)
  if (components.directive && components.directive.length >= 20) {
    score += 1.0;
  }

  // Framework (required)
  if (components.framework) {
    score += 1.0;
  }

  // Guardrails (optional but recommended)
  if (components.guardrails && components.guardrails.length >= 2) {
    score += 1.0;
  } else if (components.guardrails && components.guardrails.length >= 1) {
    score += 0.5;
  }

  return Math.min(maxScore, score);
}
```

### 3. Concisión (Conciseness)

**Definición:** Eficiencia en el uso de tokens (sin redundancias).

```typescript
function calculateConcisenessScore(components: PlanData): number {
  let score = 5.0;

  // Check for repetitions
  const allText = [
    components.objective,
    components.role,
    components.directive,
    ...components.guardrails
  ].join(" ");

  // Penalize repetition
  const repetitionScore = detectRepetition(allText);
  score -= repetitionScore * 2.0;

  // Optimal length ranges
  const totalWords = allText.split(/\s+/).length;

  if (totalWords < 50) {
    score -= 1.0; // Too short
  } else if (totalWords > 500) {
    score -= 1.0; // Too long
  }

  // Bonus for optimal range (100-300 words)
  if (totalWords >= 100 && totalWords <= 300) {
    score += 0.5;
  }

  return Math.max(0.0, Math.min(5.0, score));
}

function detectRepetition(text: string): number {
  const words = text.toLowerCase().split(/\s+/);
  const unique = new Set(words);
  const repetition = 1 - (unique.size / words.length);

  // Repetition > 30% is bad
  return Math.max(0, repetition - 0.3);
}
```

### 4. Ejemplos (Examples)

**Definición:** Presencia de ejemplos o casos de uso específicos.

```typescript
function calculateExamplesScore(components: PlanData): number {
  let score = 0.0;

  // Check for specific numbers/metrics
  if (hasMetrics(components.directive)) {
    score += 1.0;
  }

  // Check for specific technologies/tools
  if (hasSpecificTools(components.directive)) {
    score += 1.0;
  }

  // Check for context/scenario
  if (hasScenario(components.objective)) {
    score += 1.0;
  }

  // Check for time constraints
  if (hasTimeConstraint(components.directive)) {
    score += 1.0;
  }

  // Check for format specification
  if (hasFormatSpec(components.directive)) {
    score += 1.0;
  }

  return Math.min(5.0, score);
}

function hasMetrics(text: string): boolean {
  return /\d+/.test(text) || /\$[\d,]+/.test(text);
}

function hasSpecificTools(text: string): boolean {
  const tools = [
    "git", "docker", "aws", "kubernetes", "api", "sql",
    "python", "javascript", "react", "node.js"
  ];
  return tools.some(t => text.toLowerCase().includes(t));
}

function hasScenario(text: string): boolean {
  const scenarios = ["for my team", "in my company", "for our project"];
  return scenarios.some(s => text.toLowerCase().includes(s));
}

function hasTimeConstraint(text: string): boolean {
  return /\d+\s*(day|week|month|hour)/i.test(text);
}

function hasFormatSpec(text: string): boolean {
  const formats = ["markdown", "json", "csv", "pdf", "html"];
  return formats.some(f => text.toLowerCase().includes(f));
}
```

### 5. Guardrails (Guardrails)

**Definición:** Presencia y calidad de restricciones.

```typescript
function calculateGuardrailsScore(components: PlanData): number {
  if (!components.guardrails || components.guardrails.length === 0) {
    return 0.0;
  }

  let score = 0.0;
  const guardrails = components.guardrails;

  // Quantity: Ideal 3-5 guardrails
  if (guardrails.length >= 3 && guardrails.length <= 5) {
    score += 2.0;
  } else if (guardrails.length >= 1) {
    score += 1.0;
  }

  // Quality: Check for actionable guardrails
  const actionableCount = guardrails.filter(g => isActionable(g)).length;
  score += (actionableCount / guardrails.length) * 2.0;

  // Diversity: Different types of guardrails
  const categories = new Set(
    guardrails.map(g => categorizeGuardrail(g))
  );
  score += (categories.size / 4) * 1.0; // Max 4 categories

  return Math.min(5.0, score);
}

function isActionable(guardrail: string): boolean {
  // Actionable guardrails have clear do/don't
  const actionable = [
    /^(must|should|do|don't|avoid|prioritize)/i,
    /not/i
  ];
  return actionable.some(p => p.test(guardrail));
}

function categorizeGuardrail(guardrail: string): string {
  const lower = guardrail.toLowerCase();

  if (lower.includes("jargon") || lower.includes("simple")) {
    return "clarity";
  } else if (lower.includes("format") || lower.includes("markdown")) {
    return "format";
  } else if (lower.includes("step") || lower.includes("think")) {
    return "process";
  } else if (lower.includes("security") || lower.includes("safe")) {
    return "safety";
  } else {
    return "general";
  }
}
```

---

## Fórmulas de Cálculo

### Overall Score

```typescript
function calculateOverallScore(components: PlanData): QualityScore {
  const clarity = calculateClarityScore(components);
  const completeness = calculateCompletenessScore(components);
  const conciseness = calculateConcisenessScore(components);
  const examples = calculateExamplesScore(components);
  const guardrails = calculateGuardrailsScore(components);

  // Weighted average
  const overall = (
    clarity * 0.30 +
    completeness * 0.30 +
    conciseness * 0.20 +
    examples * 0.10 +
    guardrails * 0.10
  );

  return {
    clarity,
    completeness,
    conciseness,
    examples,
    guardrails,
    overall: Math.round(overall * 100) / 100  // Round to 2 decimals
  };
}

interface QualityScore {
  clarity: number;        // 0-5
  completeness: number;  // 0-5
  conciseness: number;   // 0-5
  examples: number;      // 0-5
  guardrails: number;    // 0-5
  overall: number;       // 0-5
}
```

### Quality Levels

```typescript
function getQualityLevel(score: number): {
  level: string;
  color: string;
  description: string;
} {
  if (score >= 4.5) {
    return {
      level: "Excellent",
      color: "green",
      description: "Prompt is well-structured and ready to use"
    };
  } else if (score >= 3.5) {
    return {
      level: "Good",
      color: "blue",
      description: "Prompt is solid with minor improvements possible"
    };
  } else if (score >= 2.5) {
    return {
      level: "Fair",
      color: "yellow",
      description: "Prompt needs some improvements"
    };
  } else {
    return {
      level: "Poor",
      color: "red",
      description: "Prompt requires significant improvements"
    };
  }
}
```

---

## Validation Pipeline

### Pipeline Completo

```typescript
class QualityValidator {
  async validate(components: PlanData): Promise<ValidationResult> {
    // 1. Calculate all scores
    const scores = calculateOverallScore(components);

    // 2. Determine quality level
    const level = getQualityLevel(scores.overall);

    // 3. Generate suggestions
    const suggestions = this.generateSuggestions(components, scores);

    // 4. Check for critical issues
    const issues = this.checkCriticalIssues(components);

    // 5. Generate recommendations
    const recommendations = this.generateRecommendations(components, scores);

    return {
      scores,
      level,
      suggestions,
      issues,
      recommendations,
      isValid: issues.length === 0,
      canProceed: scores.overall >= 2.5
    };
  }

  private generateSuggestions(
    components: PlanData,
    scores: QualityScore
  ): Suggestion[] {
    const suggestions: Suggestion[] = [];

    // Clarity suggestions
    if (scores.clarity < 3.0) {
      suggestions.push({
        category: "Clarity",
        message: "Add more specific details to the role",
        action: "Include years of experience and specific expertise",
        priority: "high"
      });
    }

    // Completeness suggestions
    if (scores.completeness < 3.0) {
      if (!components.framework) {
        suggestions.push({
          category: "Completeness",
          message: "Select a reasoning framework",
          action: "Choose between CoT, ToT, Decomposition, or Role-Playing",
          priority: "high"
        });
      }
      if (!components.guardrails || components.guardrails.length < 2) {
        suggestions.push({
          category: "Completeness",
          message: "Add more guardrails",
          action: "Include at least 2-3 constraints",
          priority: "medium"
        });
      }
    }

    // Conciseness suggestions
    if (scores.conciseness < 3.0) {
      suggestions.push({
        category: "Conciseness",
        message: "Remove redundant information",
        action: "Check for repeated phrases or ideas",
        priority: "low"
      });
    }

    // Examples suggestions
    if (scores.examples < 3.0) {
      suggestions.push({
        category: "Examples",
        message: "Add specific metrics or tools",
        action: "Include concrete numbers, tools, or technologies",
        priority: "medium"
      });
    }

    // Guardrails suggestions
    if (scores.guardrails < 3.0) {
      suggestions.push({
        category: "Guardrails",
        message: "Add more diverse constraints",
        action: "Include guardrails for clarity, format, and process",
        priority: "medium"
      });
    }

    return suggestions;
  }

  private checkCriticalIssues(components: PlanData): CriticalIssue[] {
    const issues: CriticalIssue[] = [];

    // Critical: Missing required components
    if (!components.objective || components.objective.length < 5) {
      issues.push({
        severity: "critical",
        message: "Objective is missing or too short",
        field: "objective"
      });
    }

    if (!components.role || components.role.length < 10) {
      issues.push({
        severity: "critical",
        message: "Role is missing or too short",
        field: "role"
      });
    }

    if (!components.directive || components.directive.length < 20) {
      issues.push({
        severity: "critical",
        message: "Directive is missing or too short",
        field: "directive"
      });
    }

    return issues;
  }

  private generateRecommendations(
    components: PlanData,
    scores: QualityScore
  ): string[] {
    const recommendations: string[] = [];

    // Overall recommendation
    if (scores.overall >= 4.5) {
      recommendations.push("✅ Prompt is excellent and ready to use!");
    } else if (scores.overall >= 3.5) {
      recommendations.push("👍 Good prompt! Consider the suggested improvements for optimal results.");
    } else if (scores.overall >= 2.5) {
      recommendations.push("⚠️ Prompt needs some improvements before use.");
    } else {
      recommendations.push("🚨 Prompt requires significant improvements.");
    }

    // Specific recommendations
    if (scores.clarity < scores.overall) {
      recommendations.push("Focus on improving clarity by adding specific details.");
    }
    if (scores.completeness < scores.overall) {
      recommendations.push("Ensure all required components are present.");
    }
    if (scores.guardrails < 3.0) {
      recommendations.push("Add more guardrails to constrain the AI's response.");
    }

    return recommendations;
  }
}

interface ValidationResult {
  scores: QualityScore;
  level: {
    level: string;
    color: string;
    description: string;
  };
  suggestions: Suggestion[];
  issues: CriticalIssue[];
  recommendations: string[];
  isValid: boolean;
  canProceed: boolean;
}

interface Suggestion {
  category: string;
  message: string;
  action: string;
  priority: "high" | "medium" | "low";
}

interface CriticalIssue {
  severity: "critical";
  message: string;
  field: string;
}
```

---

## Improvement Suggestions

### Auto-Improvement

```typescript
class PromptImprover {
  improve(components: PlanData, validation: ValidationResult): PlanData {
    const improved = { ...components };
    const suggestions = validation.suggestions;

    for (const suggestion of suggestions) {
      switch (suggestion.category) {
        case "Clarity":
          if (suggestion.priority === "high") {
            improved.role = this.improveRole(improved.role);
          }
          break;

        case "Completeness":
          if (suggestion.message.includes("framework")) {
            improved.framework = this.suggestFramework(improved);
          }
          if (suggestion.message.includes("guardrails")) {
            improved.guardrails = this.suggestGuardrails(improved);
          }
          break;

        case "Conciseness":
          improved = this.removeRedundancy(improved);
          break;

        case "Examples":
          improved.directive = this.addExamples(improved.directive);
          break;

        case "Guardrails":
          improved.guardrails = this.addGuardrails(improved.guardrails);
          break;
      }
    }

    return improved;
  }

  private improveRole(role: string): string {
    // Add expertise if missing
    if (!this.hasExpertise(role)) {
      role = role.replace(
        /^(You are a)/i,
        "$1n expert-level"
      );
    }

    // Add experience if missing
    if (!this.hasExperience(role)) {
      role = role.replace(
        /^(You are an expert-level)/i,
        "$1 with over 10 years of experience"
      );
    }

    return role;
  }

  private suggestFramework(components: PlanData): ReasoningFramework {
    // Analyze complexity
    const words = components.directive.split(/\s+/).length;

    if (words < 30) {
      return "role-playing";  // Simple scenarios
    } else if (words < 60) {
      return "chain-of-thought";  // Sequential problems
    } else {
      return "tree-of-thoughts";  // Complex problems
    }
  }

  private suggestGuardrails(components: PlanData): string[] {
    const base = components.guardrails || [];
    const suggestions: string[] = [];

    // Always suggest clarity
    if (!base.some(g => g.includes("jargon") || g.includes("simple"))) {
      suggestions.push("Avoid jargon where possible. Explain complex ideas simply.");
    }

    // Suggest pragmatism for technical tasks
    if (components.objective.toLowerCase().includes("code") ||
        components.objective.toLowerCase().includes("architecture")) {
      suggestions.push("Prioritize what works in practice over theoretical perfection.");
    }

    // Suggest actionability
    if (!base.some(g => g.includes("actionable"))) {
      suggestions.push("Every recommendation must be a concrete, actionable step.");
    }

    return [...base, ...suggestions];
  }

  private hasExpertise(role: string): boolean {
    return /expert|specialist|professional/i.test(role);
  }

  private hasExperience(role: string): boolean {
    return /\d+.*year|senior|lead|principal/i.test(role);
  }

  private removeRedundancy(components: PlanData): PlanData {
    // Remove duplicate phrases
    const seen = new Set<string>();
    const cleaned: typeof components = { ...components };

    cleaned.directive = components.directive
      .split(". ")
      .filter(sentence => {
        const lower = sentence.toLowerCase();
        if (seen.has(lower)) return false;
        seen.add(lower);
        return true;
      })
      .join(". ");

    return cleaned;
  }

  private addExamples(directive: string): string {
    // Add metrics if missing
    if (!/\d+/.test(directive)) {
      directive += " Include specific metrics and success criteria.";
    }

    return directive;
  }

  private addGuardrails(guardrails: string[]): string[] {
    const added = [...guardrails];

    if (added.length < 3) {
      added.push("Structure the output in Markdown.");
    }

    if (added.length < 4) {
      added.push("Think step-by-step before answering.");
    }

    return added;
  }
}
```

---

## DSPy Integration

### DSPy Quality Validator

```python
import dspy

class QualityValidatorSignature(dspy.Signature):
    """Validar calidad de un prompt generado"""

    # Input
    prompt = dspy.InputField(desc="Prompt to validate")
    objective = dspy.InputField(desc="Original objective")

    # Output
    quality_score = dspy.OutputField(desc="Overall quality score (0-5)")
    clarity_score = dspy.OutputField(desc="Clarity score (0-5)")
    completeness_score = dspy.OutputField(desc="Completeness score (0-5)")
    suggestions = dspy.OutputField(desc="List of improvement suggestions")

class QualityValidator(dspy.Module):
    """Módulo DSPy para validar calidad"""

    def __init__(self):
        super().__init__()
        self.validator = dspy.Predict(QualityValidatorSignature)

    def forward(self, prompt: str, objective: str) -> dspy.Prediction:
        # Validar usando LLM
        result = self.validator(
            prompt=prompt,
            objective=objective
        )

        # Parse scores
        return dspy.Prediction(
            quality_score=float(result.quality_score),
            clarity_score=float(result.clarity_score),
            completeness_score=float(result.completeness_score),
            suggestions=result.suggestions.split("\n")
        )

# Usar el validator
validator = QualityValidator()
result = validator(
    prompt=generated_prompt,
    objective="Design ADR process"
)

print(f"Quality Score: {result.quality_score}/5")
print(f"Suggestions: {result.suggestions}")
```

---

**Documentos Completados en `/docs/research/wizard/`:**
1. ✅ `01-wizard-complete-flow.md` - Flujo completo del wizard
2. ✅ `02-template-library-analysis.md` - Análisis de biblioteca de templates
3. ✅ `03-dspy-integration-guide.md` - Guía de integración DSPy
4. ✅ `04-prompt-assembly-patterns.md` - Patrones de ensamblaje
5. ✅ `05-quality-validation-system.md` - Sistema de validación de calidad
