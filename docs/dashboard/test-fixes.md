# 🔧 **Análisis y Reparaciones para Tests Fallidos**

## **❌ Problemas Identificados**

### **1. Problem: `getTransportInstance()` no implementada**
El error `transport is not a function` ocurre porque la función `getTransportInstance()` no está definida.

### **2. Problem: Metadata tracking inconsistente**
Los tests esperan ciertos valores de metadata pero el sistema no los está generando correctamente.

### **3. Problem: Latency tracking en timeouts**
Cuando hay timeouts, la latency no se registra correctamente.

### **4. Problem: Attempt counting**
El segundo intento se marca como attempt: 1 en lugar de attempt: 2.

---

## **🛠️ **Soluciones Requeridas**

### **Fix 1: Implementar getTransportInstance()**
```typescript
// En ollamaStructured.ts - alrededor de línea 296
async function getTransportInstance(): Promise<OllamaTransport> {
  const transportOrFactory = getTransport();

  if (typeof transportOrFactory === 'function') {
    // Es un factory function
    return await transportOrFactory();
  }

  // Es un transport directo
  return transportOrFactory;
}
```

### **Fix 2: Corregir latency tracking**
```typescript
// En callOllama - necesita registrar latency incluso en timeouts
async function callOllama(prompt: string, baseUrl: string, model: string, timeoutMs: number): Promise<{ raw: string; latencyMs: number }> {
  const start = Date.now();
  try {
    const transport = await getTransportInstance();
    const result = await transport({
      baseUrl,
      model,
      prompt,
      timeoutMs,
    });

    return {
      raw: result.raw,
      latencyMs: Date.now() - start,
    };
  } catch (error) {
    const latency = Date.now() - start;
    if (error instanceof Error) {
      if (error.message.includes("timed out") || error.message.includes("Timeout") || error.name === "AbortError") {
        throw Object.assign(error, {
          failureReason: "timeout" as const,
          latencyMs: latency,
        });
      }
    }
    throw Object.assign(error, { latencyMs: latency });
  }
}
```

### **Fix 3: Corregir attempt counting en parseAndValidateAttempt2**
```typescript
// Necesita asegurarse que attempt 2 se marque correctamente
function parseAndValidateAttempt2<T>(raw2: string, schema: z.ZodType<T>, raw1: string, latencyMs: number): StructuredResult<T> {
  // ... implementación existente
  // Asegurarse que el resultado tenga attempt: 2
  return {
    ok: false,
    attempt: 2, // Asegurar que sea 2
    usedRepair: true,
    // ... resto del resultado
  };
}
```

### **Fix 4: Actualizar firma de callOllama**
```typescript
// Cambiar todas las llamadas a callOllama para manejar latency
const attempt1 = await callOllama(prompt, baseUrl, model, timeoutMs);
const raw1 = attempt1.raw;
const latency1 = attempt1.latencyMs; // Ahora disponible
```

---

## **📋 **Prioridades de Reparación**

1. **🔥 Crítico**: Implementar `getTransportInstance()` - causa el error "transport is not a function"
2. **⚡ Alto**: Corregir latency tracking - todos los tests de timeout fallan
3. **📊 Medio**: Corregir attempt counting - tests de repair fallan
4. **🔧 Bajo**: Mejorar extraction metadata detection

---

## **🎯 **Acción Inmediata**

Necesito implementar estas reparaciones en los archivos fuente para que los tests pasen correctamente.
