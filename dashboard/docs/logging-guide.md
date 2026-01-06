# Logging Guide - DSPy Prompt Improver

## Overview
This project uses structured logging with emoji prefixes for visual filtering in macOS Console.app, plus protective code comments to prevent bugs.

## Log Format

### Emoji Prefix System
All logs must use emoji prefixes for visual filtering:
- 🚀 Starting operation
- 📥 Receiving input/data
- ✅ Success/completion
- ❌ Error/failure
- ⚠️ Warning
- ⚙️ Configuration
- 🔧 Final config/values
- 🌐 Network call
- 📊 Stats/metrics
- 📋 Clipboard operation
- 🎉 Final success

### LOG_PREFIX Constant
Every file should define a LOG_PREFIX constant at the top:
```typescript
const LOG_PREFIX = "[ComponentName]";
```

All logs use: `console.log(`${LOG_PREFIX} 🚀 Message...`);`

## Four Layers of Logging

### Layer 1: Entry/Exit Logs
Log at function boundaries:
```typescript
export async function someFunction() {
  console.log(`${LOG_PREFIX} 🚀 Starting operation...`);

  try {
    // ... work ...

    console.log(`${LOG_PREFIX} ✅ Operation complete`);
  } catch (error) {
    console.error(`${LOG_PREFIX} ❌ Operation failed:`, error);
  }
}
```

### Layer 2: State Transition Logs
Log when state changes:
```typescript
if (input.source === "none") {
  console.log(`${LOG_PREFIX} ❌ No input detected`);
  return;
}

console.log(`${LOG_PREFIX} ✅ Input received: ${input.source} (${input.text.length} chars)`);
```

### Layer 3: Diagnostic Logs
Log at error-prone points:
```typescript
console.log(`${LOG_PREFIX} 🔧 Final config: timeoutMs=${timeoutMs}, model=${model}`);
console.log(`${LOG_PREFIX} 🌐 Calling backend: ${baseUrl}/api/v1/improve-prompt`);
```

### Layer 4: Performance Metrics
Log timing information:
```typescript
const t0 = Date.now();
// ... work ...
const ttv_ms = Date.now() - t0;
console.log(`${LOG_PREFIX} 🎉 Success! TTV: ${ttv_ms}ms`);
```

## Protective Code Comments

### 🔴 CRITICAL Comments
For code that must NOT be modified without deep understanding:
```typescript
/**
 * 🔴 CRITICAL: Timeout synchronization between frontend and backend
 *
 * Frontend timeout (preferences.timeoutMs) MUST match backend timeout:
 * - UI: package.json → timeoutMs preference (default: 120000ms)
 * - Frontend config: defaults.ts → dspy.timeoutMs (default: 120000ms)
 * - Backend: .env → ANTHROPIC_TIMEOUT (default: 120s)
 *
 * If mismatched:
 * - Frontend < Backend: AbortError "operation was aborted"
 * - Frontend > Backend: Unnecessary wait
 *
 * 🔴 DO NOT change timeout values without updating ALL three locations
 */
```

### ⚡ INVARIANT Comments
For relationships that must always be true:
```typescript
// ⚡ INVARIANT: Frontend timeout synchronization with DSPy backend
//
// The timeoutMs variable (from preferences.timeoutMs) MUST be used for BOTH:
// - options.timeoutMs (Ollama/local LM timeout)
// - options.dspyTimeoutMs (DSPy backend timeout - forwards to Anthropic Haiku)
//
// ⚡ DO NOT use config.dspy.timeoutMs here - it's a fallback default only
// ⚡ DO NOT use different values for timeoutMs and dspyTimeoutMs
```

### 📝 CONTEXT Comments
For historical context of decisions:
```typescript
/**
 * 📝 CONTEXT: Why 5-character minimum input requirement?
 *
 * Historical context (2025-01-06):
 * - Users would accidentally trigger "Promptify Selected" on short selections
 * - Common issues: Single character "a", clipboard fragments like "x", "test"
 * - This caused backend calls with meaningless input, wasting time and API quota
 *
 * Decision: Set minimum to 5 characters
 * - Low enough: Doesn't block legitimate single-word prompts ("help", "fix it")
 * - High enough: Prevents accidental triggers on meaningless fragments
 *
 * 🔴 DO NOT lower this minimum below 5 - will re-introduce accidental triggers
 */
```

### ⚠️ RISK Comments
For error-prone areas with mitigations:
```typescript
/**
 * ⚠️ RISK: Network operation with multiple failure modes
 *
 * This method makes HTTP calls to DSPy backend. Common failures:
 * - Network errors: ECONNREFUSED, timeout, DNS failure
 * - Backend errors: 5xx, rate limits, malformed JSON
 * - Edge cases: Empty responses, missing fields, schema changes
 *
 * Mitigations in place:
 * - fetchWithTimeout enforces timeout (prevents hangs)
 * - Response validation (checks response.ok)
 * - Comprehensive logging (request/response/latency)
 *
 * 🔴 DO NOT remove try/catch - errors must be caught and logged
 * 🔴 DO NOT remove console.log statements - critical for debugging
 */
```

## Best Practices

1. **Use LOG_PREFIX consistently** - Every file should have one
2. **Emoji prefixes are mandatory** - All logs must use them
3. **Log state changes** - When data flows between components
4. **Log network operations** - Before and after HTTP calls
5. **Log errors with context** - Include what operation failed
6. **Add protective comments** - Use CRITICAL/INVARIANT/CONTEXT/RISK as appropriate

## Filtering in macOS Console.app

The emoji prefixes make it easy to filter logs:
- Search "🚀" to see operation starts
- Search "❌" to see only errors
- Search "🌐" to see network calls
- Search "[ComponentName]" to see logs from specific component

## Examples

See these files for reference:
- `src/core/input/getInput.ts` - Input detection with logging
- `src/promptify-selected.tsx` - Full flow with emoji prefixes
- `src/core/llm/dspyPromptImprover.ts` - Network client with RISK comment
- `src/core/config/defaults.ts` - CRITICAL comment on timeout
- `src/promptify-quick.tsx` - INVARIANT comment on timeout usage
