# 📋 **Prompt Analysis Converter - MCP Server**

## **🎯 **Overview**

El **Prompt Analysis Converter** es un servidor Model Context Protocol (MCP) que convierte análisis técnicos de prompts en documentación markdown estructurada y profesional. Transforma datos de evaluación en reportes comprensibles con métricas, gráficos y recomendaciones accionables.

---

## **🚀 **Installation & Setup**

### **1. MCP Server Location**
```
/Users/felipe_gonzalez/Developer/raycast_ext/mcp-server/src/prompt-converter-server.ts
```

### **2. Zed Configuration**
```json
{
  "mcpServers": {
    "prompt-analysis-converter": {
      "command": "tsx",
      "args": ["/Users/felipe_gonzalez/Developer/raycast_ext/mcp-server/src/prompt-converter-server.ts"],
      "cwd": "/Users/felipe_gonzalez/Developer/raycast_ext/mcp-server"
    }
  }
}
```

---

## **🛠️ **Available Tools**

### **1. `convert_analysis_to_markdown`**
**Convierte datos de análisis de prompt a markdown estructurado**

```typescript
/mcp prompt-analysis-converter convert_analysis_to_markdown --analysisData '{...}' --outputPath reports/prompt-analysis.md
```

**Parámetros:**
- `analysisData` (object, required): Datos del análisis de prompt
- `outputPath` (string, optional): Path para guardar el archivo markdown

### **2. `batch_convert_analyses`**
**Convierte múltiples análisis a archivos markdown**

```typescript
/mcp prompt-analysis-converter batch_convert_analyses --analyses '[{...}, {...}]' --outputDir ./reports --generateIndex true
```

**Parámetros:**
- `analyses` (array, required): Array de datos de análisis
- `outputDir` (string, default: "./prompt-reports"): Directorio de salida
- `generateIndex` (boolean, default: true): Generar índice con resúmenes

### **3. `generate_analysis_template`**
**Genera plantilla para estructura de datos de análisis**

```typescript
/mcp prompt-analysis-converter generate_analysis_template --promptId my-prompt --category technical --complexity high
```

**Parámetros:**
- `promptId` (string, default: "prompt-001"): ID del prompt
- `category` (string, default: "general"): Categoría del prompt
- `complexity` (enum, default: "medium"): Nivel de complejidad

### **4. `validate_analysis_data`**
**Valida estructura de datos de análisis**

```typescript
/mcp prompt-analysis-converter validate_analysis_data --analysisData '{...}'
```

**Parámetros:**
- `analysisData` (object, required): Datos a validar

---

## **📊 **Data Schema**

### **Estructura de Datos de Análisis**
```typescript
{
  promptId: string,
  promptText: string,
  analysis: {
    quality: {
      score: number,           // 0-10
      strengths: string[],    // Array de fortalezas
      weaknesses: string[],   // Array de debilidades
      suggestions: string[]   // Array de sugerencias
    },
    structure: {
      clarity: number,        // 0-10
      completeness: number,   // 0-10
      conciseness: number,    // 0-10
      specificity: number     // 0-10
    },
    technical: {
      hasClearInstructions: boolean,
      hasConstraints: boolean,
      hasExamples: boolean,
      hasOutputFormat: boolean,
      hasErrorHandling: boolean
    },
    risks: Array<{
      type: "ambiguity" | "inconsistency" | "completeness" | "clarity" | "technical",
      severity: "low" | "medium" | "high" | "critical",
      description: string,
      mitigation: string
    }>
  },
  metadata: {
    category: string,
    complexity: "low" | "medium" | "high",
    estimatedTokens: number,
    processingTime?: number,
    dateAnalyzed: string
  }
}
```

---

## **📋 **Generated Markdown Structure**

### **Secciones Generadas**

1. **Header** - ID del prompt, fecha, metadata
2. **Executive Summary** - Score general, evaluación de riesgos
3. **Quality Assessment** - Métricas detalladas de calidad
4. **Structural Analysis** - Análisis de claridad, completitud, etc.
5. **Technical Analysis** - Componentes técnicos presentes
6. **Risk Assessment** - Matriz de riesgos y mitigaciones
7. **Recommendations** - Plan de mejora priorizado
8. **Metadata** - Información del análisis

### **Elementos Visuales**

```markdown
### **Quality Score:** 7.5/10
🟢 ████░░ (7.5/10)

### **Risk Assessment:** 3 (Medium)
🟡 3 risks identified

| Structural Element | Score | Status |
|-------------------|-------|--------|
| **Clarity** | 7/10 | Good ✅ |
| **Completeness** | 6/10 | Fair ⚠️ |
```

---

## **🎯 **Usage Examples**

### **Example 1: Convert Single Analysis**
```typescript
const analysisData = {
  promptId: "customer-support-prompt",
  promptText: "Help customers with technical issues...",
  analysis: {
    quality: { score: 8, strengths: ["Clear instructions"], weaknesses: ["No examples"], suggestions: ["Add examples"] },
    // ... resto del análisis
  }
};

/mcp prompt-analysis-converter convert_analysis_to_markdown --analysisData '${JSON.stringify(analysisData)}' --outputPath reports/customer-support.md
```

### **Example 2: Batch Conversion with Index**
```typescript
const analyses = [
  { promptId: "prompt-1", analysis: {...} },
  { promptId: "prompt-2", analysis: {...} },
  { promptId: "prompt-3", analysis: {...} }
];

/mcp prompt-analysis-converter batch_convert_analyses --analyses '${JSON.stringify(analyses)}' --outputDir ./prompt-reports --generateIndex true
```

### **Example 3: Generate Template**
```typescript
/mcp prompt-analysis-converter generate_analysis_template --promptId technical-prompt --category engineering --complexity high
```

---

## **📈 **Output Features**

### **Quality Metrics**
- **Overall Score**: 0-10 con visualización gráfica
- **Strengths/Weaknesses Balance**: Análisis comparativo
- **Recommendations Priority**: High/Medium/Low

### **Risk Assessment**
- **Risk Matrix**: Severidad vs Tipo de riesgo
- **Critical Risks**: Priorizados con mitigaciones
- **Risk Score**: Cálculo automático (0-10)

### **Technical Evaluation**
- **Component Checklist**: Presence/absence de elementos técnicos
- **Completeness Percentage**: % de componentes presentes
- **Technical Recommendations**: Mejoras específicas

### **Visual Elements**
- **Progress Bars**: Para scores y métricas
- **Tables**: Comparaciones estructuradas
- **Emojis**: Indicadores visuales rápidos
- **Code Blocks**: Para prompts y ejemplos

---

## **🔧 **Integration with Zed**

### **Assistant Integration**
```typescript
// Ask assistant to convert analysis
"Convert this prompt analysis to markdown with detailed metrics and recommendations"

// Assistant executes:
/mcp prompt-analysis-converter convert_analysis_to_markdown --analysisData '{...}' --outputPath reports/analysis.md
```

### **Validation Workflow**
```typescript
// 1. Generate template
/mcp prompt-analysis-converter generate_analysis_template

// 2. Fill analysis data
// (Manual or automated process)

// 3. Validate structure
/mcp prompt-analysis-converter validate_analysis_data --analysisData '{...}'

// 4. Convert to markdown
/mcp prompt-analysis-converter convert_analysis_to_markdown --analysisData '{...}'
```

---

## **📊 **Sample Output**

### **Generated Report Preview**
```markdown
# 📋 Prompt Analysis Report

**Prompt ID:** `customer-support-prompt`
**Quality Score:** 8.2/10 🟢
**Risk Assessment:** 2 (Low) 🟢

## 🎯 Executive Summary

### **Quality Score:** 8.2/10
🟢 ████░ (8.2/10) Excellent

### **Key Findings**
**✅ Strengths (3):**
- Clear and unambiguous instructions
- Comprehensive coverage of scenarios
- Appropriate technical detail level

**⚠️ Weaknesses (1):**
- Missing examples for complex cases

### **Top Recommendations** 🎯
- Add concrete examples for edge cases
- Include troubleshooting flow
- Specify escalation procedures
```

---

## **🚨 **Error Handling**

### **Common Errors & Solutions**

#### **Invalid Analysis Structure**
```
❌ Missing required field: promptId
✅ Solution: Include all required fields in analysis data
```

#### **Invalid Score Range**
```
❌ Quality score must be between 0 and 10
✅ Solution: Use valid score range (0-10)
```

#### **Unrecognized Risk Type**
```
⚠️ Risk has unrecognized type: unknown_type
✅ Solution: Use valid risk types: ambiguity, inconsistency, completeness, clarity, technical
```

---

## **🔮 **Enhancements**

### **Future Features**
1. **Custom Templates**: Plantillas personalizadas por dominio
2. **Integration with Metrics**: Conexión con sistemas de monitoring
3. **Automated Analysis**: Integración con AI para auto-análisis
4. **Export Formats**: Soporte para PDF, HTML, Word
5. **Collaboration**: Comentarios y revisiones en markdown

### **Extension Points**
```typescript
interface CustomReportGenerator {
  name: string;
  generate: (analysis: PromptAnalysis) => string;
}

interface ValidationRule {
  name: string;
  validate: (data: any) => ValidationResult;
}
```

---

## **🎯 **Summary**

El **Prompt Analysis Converter MCP Server** proporciona:

- **✅ Automated markdown generation** desde datos técnicos
- **✅ Professional documentation** con métricas y visualizaciones
- **✅ Batch processing** para análisis múltiples
- **✅ Validation y template generation** para consistency
- **✅ Seamless integration** con workflow de Zed

**🚀 Transforma datos de análisis técnicos en documentación profesional sin esfuerzo manual.**
