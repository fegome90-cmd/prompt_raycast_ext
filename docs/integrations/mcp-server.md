# 🔧 **Raycast Evaluator MCP Server**

## **📖 **Overview**

El **Raycast Evaluator MCP Server** es un servidor Model Context Protocol (MCP) que integra el sistema de quality gates del Prompt Renderer Local directamente en Zed, permitiendo análisis de código y métricas de calidad en tiempo real.

---

## **🎯 **Purpose**

Integra el potente sistema de evaluación del repositorio `dashboard/scripts/evaluator.ts` con Zed, proporcionando:

- **Quality Gates automation** directo desde el editor
- **Real-time metrics** del sistema de prompts
- **Code quality validation** personalizado
- **Failure pattern analysis** para debugging avanzado

---

## **🚀 **Installation & Setup**

### **1. MCP Server Location**
```
/Users/felipe_gonzalez/Developer/raycast_ext/mcp-server/src/index.ts
```

### **2. Zed Configuration**
```json
// ~/.config/zed/mcp.json
{
  "mcpServers": {
    "raycast-evaluator": {
      "command": "tsx",
      "args": ["/Users/felipe_gonzalez/Developer/raycast_ext/mcp-server/src/index.ts"],
      "cwd": "/Users/felipe_gonzalez/Developer/raycast_ext",
      "env": {
        "NODE_ENV": "development"
      }
    }
  }
}
```

### **3. Dependencies**
```json
// mcp-server/package.json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "tsx": "^4.21.0",
    "typescript": "^5.2.2"
  }
}
```

---

## **🛠️ **Available Tools**

### **1. `run_quality_gates`**
**Ejecuta el evaluator.ts quality gates del Prompt Renderer**

```typescript
// Usage
/mcp raycast-evaluator run_quality_gates --dataset testdata/cases.jsonl --output eval/results.json --verbose true
```

**Parameters:**
- `dataset` (string, default: "testdata/cases.jsonl"): Path al dataset JSONL
- `output` (string, default: "eval/mcp-results.json"): Path para resultados
- `verbose` (boolean, default: false): Output detallado
- `config` (object): Configuración adicional para Ollama

**Config Object:**
```typescript
{
  baseUrl: "http://localhost:11434",
  model: "qwen3-coder:30b",
  timeoutMs: 30000
}
```

---

### **2. `get_quality_metrics`**
**Analiza métricas históricas de quality gates**

```typescript
// Usage
/mcp raycast-evaluator get_quality_metrics --resultsFile eval/latest-results.json
```

**Returns:**
```typescript
{
  totalCases: 30,
  jsonValidPass1: 0.54,
  copyableRate: 0.67,
  latencyP50: 2500,
  latencyP95: 12000,
  repairTriggerRate: 0.23,
  buckets: {
    good: { total: 15, jsonValidPass1: 0.80, copyableRate: 0.87 },
    bad: { total: 10, jsonValidPass1: 0.30, copyableRate: 0.40 },
    ambiguous: { total: 5, jsonValidPass1: 0.40, copyableRate: 0.60 }
  },
  failureReasons: {
    schema_mismatch: 3,
    timeout: 2,
    invalid_json: 1
  }
}
```

---

### **3. `validate_code_quality`**
**Ejecuta ESLint y TypeScript checking**

```typescript
// Usage
/mcp raycast-evaluator validate_code_quality --fix true --checkFormat true
```

**Parameters:**
- `fix` (boolean, default: false): Intentar auto-fix de issues
- `checkFormat` (boolean, default: true): Verificar formatting con Prettier

**Commands ejecutados:**
```bash
npm run lint
npx prettier --check src/ --config .prettierrc
npm run fix-lint  # si fix=true
```

---

### **4. `analyze_failure_patterns`**
**Analiza patrones de fallo en resultados del evaluator**

```typescript
// Usage
/mcp raycast-evaluator analyze_failure_patterns --resultsFile eval/latest.json --category bad
```

**Parameters:**
- `resultsFile` (string, default: "eval/latest-results.json"): Path a resultados
- `category` (enum, default: "all"): Filtrar por bucket ("good" | "bad" | "ambiguous" | "all")

**Output Example:**
```
🔍 **Failure Pattern Analysis** from eval/latest.json

**Category:** bad
**Total Failures:** 8

**Top Failure Patterns:**
- schema_mismatch: 3
- timeout: 2
- invalid_json: 1
- chatty_output: 1

**Sample Failures:**
- bad-001: Missing clarifying_questions field
- bad-003: Confidence score too low
- bad-007: Prompt too long
```

---

## **🏗️ **Architecture**

### **Core Components**

```typescript
// MCP Server Structure
const server = new Server({
  name: "raycast-evaluator",
  version: "1.0.0",
}, {
  capabilities: { tools: {} }
});

// Tool Registration
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS
}));

// Tool Execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // Execute specific tool logic
});
```

### **Integration Points**

#### **1. Evaluator.ts Integration**
```typescript
// Direct invocation of evaluator
const cmdArgs = [
  "tsx",
  "dashboard/scripts/evaluator.ts",
  "--dataset", args.dataset,
  "--output", args.output
];

if (args.verbose) cmdArgs.push("--verbose");
```

#### **2. File System Operations**
```typescript
// Read historical results
const content = await Deno.readTextFile(fullPath);
const results = JSON.parse(content);

// Write configuration if needed
await Deno.writeTextFile(configPath, JSON.stringify(config, null, 2));
```

#### **3. Error Handling**
```typescript
try {
  // Tool logic
  return { content: [{ type: "text", text: "Success" }] };
} catch (error) {
  throw new McpError(
    ErrorCode.InternalError,
    `Tool execution failed: ${error.message}`
  );
}
```

---

## **📊 **Quality Gates Metrics**

### **Core Metrics Tracked**

| Metric | Target | Description |
|--------|--------|-------------|
| `jsonValidPass1` | ≥ 54% | JSON válido en primer intento |
| `copyableRate` | ≥ 54% | Prompts copiables directamente |
| `latencyP95` | ≤ 12000ms | Latencia percentil 95 |
| `repairSchemaValidRate` | ≥ 50% | Tasa de éxito en reparación |
| `extractionUsedRate` | Monitor | Uso de extracción JSON |
| `attempt2Rate` | Monitor | Casos que requieren 2 intentos |

### **Bucket Classification**

| Bucket | Description | Expected Performance |
|--------|-------------|---------------------|
| **good** | Cases should pass easily | jsonValidPass1 > 80% |
| **bad** | Known problematic cases | jsonValidPass1 < 60% |
| **ambiguous** | Edge cases | jsonValidPass1 60-80% |

---

## **🔧 **Usage Examples**

### **Example 1: Daily Quality Check**
```bash
# Run complete quality gates
/mcp raycast-evaluator run_quality_gates --verbose

# Get latest metrics
/mcp raycast-evaluator get_quality_metrics

# Analyze failures
/mcp raycast-evaluator analyze_failure_patterns --category bad
```

### **Example 2: Pre-commit Validation**
```bash
# Fix any linting issues
/mcp raycast-evaluator validate_code_quality --fix true

# Run tests to ensure no regression
/mcp raycast-evaluator run_quality_gates --dataset testdata/smoke-cases.jsonl
```

### **Example 3: Performance Investigation**
```bash
# Run with custom timeout for slow model
/mcp raycast-evaluator run_quality_gates --config '{"timeoutMs": 60000}'

# Analyze timeout patterns
/mcp raycast-evaluator analyze_failure_patterns --resultsFile eval/timing-test.json
```

---

## **🚨 **Error Handling**

### **Common Errors & Solutions**

#### **File Not Found**
```
❌ Error reading results file: ENOENT: file not found
✅ Solution: Run evaluator first to generate results file
```

#### **Invalid Dataset Format**
```
❌ Error reading cases: Invalid JSON at line 1
✅ Solution: Ensure dataset is JSONL format (one JSON per line)
```

#### **Ollama Connection Error**
```
❌ Ollama not available: ECONNREFUSED
✅ Solution: Start Ollama service: ollama serve
```

#### **Permission Denied**
```
❌ Error: Permission denied
✅ Solution: Check file permissions and run from correct directory
```

---

## **🔗 **Integration with Zed**

### **Assistant Integration**
The MCP server integrates directly with Zed's assistant:

```typescript
// Ask assistant to run quality gates
"Run the quality gates for the current prompt changes and analyze any failures"

// Assistant executes:
/mcp raycast-evaluator run_quality_gates --verbose
/mcp raycast-evaluator analyze_failure_patterns

// Returns detailed analysis with recommendations
```

### **Task Integration**
Available in Zed's task panel:

```
Cmd+Shift+P → Tasks → "Run Quality Gates (evaluator.ts)"
Cmd+Shift+P → Tasks → "Fix Linting Issues"
Cmd+Shift+P → Tasks → "Build & Test"
```

### **Diagnostics Integration**
Quality gate failures can be mapped to Zed diagnostics:
- **Error**: Critical quality gate failures
- **Warning**: Performance degradation
- **Info**: Metrics summaries

---

## **📈 **Performance Considerations**

### **Resource Usage**
- **Memory**: ~50MB base + dataset size
- **CPU**: Moderate during evaluation
- **Disk**: Temporary files in /tmp

### **Optimization Tips**
1. **Use smaller datasets** for frequent checks
2. **Cache results** for repeated analysis
3. **Parallel execution** when possible
4. **Cleanup temp files** regularly

---

## **🔮 **Future Enhancements**

### **Planned Features**
1. **Real-time monitoring** with streaming updates
2. **Integration with CI/CD pipelines**
3. **Custom quality gate definitions**
4. **Multi-repository support**
5. **Historical trend analysis**

### **Extension Points**
```typescript
// Custom quality gate validation
interface CustomGate {
  name: string;
  threshold: number;
  validator: (metrics: Metrics) => boolean;
}

// Additional analysis tools
interface AnalysisTool {
  name: string;
  description: string;
  execute: (data: any) => AnalysisResult;
}
```

---

## **🎯 **Summary**

El **Raycast Evaluator MCP Server** proporciona una integración poderosa entre el sistema de quality gates del Prompt Renderer y Zed, permitiendo:

- **✅ Automated quality checks** directo desde el editor
- **✅ Real-time metrics** y análisis de patrones
- **✅ Seamless integration** con el flujo de trabajo de desarrollo
- **✅ Extensible architecture** para herramientas personalizadas

**🚀 Transforma el análisis de calidad de prompts de un proceso manual a una experiencia integrada y eficiente en Zed.**
