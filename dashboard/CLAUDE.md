# Frontend - Raycast Extension

> TypeScript/React Raycast extension for DSPy Prompt Improver

## Quick Reference

```bash
cd dashboard
npm run dev         # Run in Raycast
npm run test        # Vitest tests
npm run lint        # ESLint
npm run typecheck   # TypeScript check
```

## Architecture

### Layered Structure
```
Commands (src/*.tsx) → Core Logic (src/core/) → External Services
```

**Commands** (`src/`): Entry points for Raycast commands
- `promptify-quick.tsx` — Main prompt improvement
- `promptify-selected.tsx` — Text selection workflow
- `prompt-history.tsx` — History view
- `conversation-view.tsx` — Interactive wizard mode

**Core** (`src/core/`): Reusable business logic
- `config/` — Configuration management with safe mode fallback
- `design/` — Design tokens and UI components
- `llm/` — LLM integration and fallback logic
- `conversation/` — Wizard mode conversation handling
- `errors/` — Error handling components

## Critical Rules

| Rule | Why |
|------|-----|
| Validate config on load | Use Zod schemas, degrade to safe mode on error |
| Log with prefixes | `[PromptifyQuick]`, `[Fallback]` for filtering in Console.app |
| Use Raycast components | `@raycast/api` for all UI elements |
| Never duplicate types | Share types between Python backend via `types.ts` |
| Handle offline gracefully | Ollama fallback when backend unavailable |

## Design System

### Color Tokens (`src/core/design/tokens.ts`)

```typescript
// Semantic mapping
const colors = {
  accent: "#00D9FF",      // Electric cyan
  gray: {
    50: "#F9FAFB",  // Lightest
    400: "#9CA3AF", // Mid
    700: "#374151", // Dark
    900: "#111827", // Darkest
  },
  semantic: {
    success: "#10B981",  // Green
    warning: "#F59E0B",  // Yellow
    error: "#EF4444",    // Red
    info: "#3B82F6",     // Blue
  }
};
```

### Typography & Spacing
- **4px grid system** for all spacing
- **Font weights**: Regular (400), Medium (500), Semibold (600)
- **Line height**: 1.5 for body, 1.2 for headings

### Component Patterns
```typescript
// Progressive loading with stages
const [stage, setStage] = useState<"loading" | "processing" | "done">("loading");

// Action panels with sections
<ActionPanel.Section>
  <Action.OpenInBrowser title="View Docs" url="..." />
  <Action.CopyToClipboard title="Copy Result" content={result} />
</ActionPanel.Section>
```

## Configuration Management

### Three-Tier Merging
```typescript
// 1. Defaults (hardcoded)
const defaults = { backendUrl: "http://localhost:8000", mode: "legacy" };

// 2. Preferences (Raycast storage)
const userPrefs = await LocalStorage.getItem("config");

// 3. Runtime (computed)
const config = { ...defaults, ...userPrefs, ...runtime };
```

### Safe Mode
- Activates automatically on validation errors
- Disables optional features (metrics, KNN)
- Shows warning with actionable hints
- Logs detailed error for debugging

```typescript
if (!configSchema.safeParse(config).success) {
  enableSafeMode("Invalid configuration");
}
```

## Error Handling

### Frontend Error Classes
```typescript
class FrontendError extends Error {
  constructor(
    message: string,
    public hint?: string,      // User-friendly guidance
    public details?: unknown    // Debug info
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}
```

### HTTP Error Mapping
| Status | Frontend Action |
|--------|-----------------|
| 400 | Show validation error |
| 404 | Show "not found" with retry |
| 422 | Show field-specific errors |
| 503 | Enable Ollama fallback |
| 504 | Show timeout with retry |
| 500 | Show generic error, log details |

### User Feedback
```typescript
// Show error with action
 showToast({
   style: Toast.Style.Failure,
   title: "Improvement Failed",
   message: error.message,
   primaryAction: {
     title: "Retry",
     onAction: () => retry(),
   },
 });
```

## LLM Integration

### Execution Modes
1. **Legacy**: DSPy backend (default)
2. **NLaC**: New pipeline with OPRO + IFEval
3. **Ollama**: Local models (no backend)

### Fallback Strategy
```typescript
// Hybrid approach
try {
  result = await callBackend();
} catch (error) {
  if (error instanceof ConnectionError) {
    result = await useOllamaFallback();
  }
}
```

### Model Selection
```typescript
const models = {
  legacy: "claude-haiku-4-5-20251001",
  nlac: "claude-sonnet-4-5-20251001",
  ollama: "llama3.2",  // Local
};
```

## State Management

### Local Storage
```typescript
// Save
await LocalStorage.setItem("prompt_history", JSON.stringify(history));

// Load
const history = JSON.parse(await LocalStorage.getItem("prompt_history") || "[]");
```

### React Patterns
```typescript
// Async command
export default async function Command() {
  const { state, isLoading } = usePromise(fetchData);

  return (
    <List isLoading={isLoading}>
      {state?.map(item => <List.Item {...item} />)}
    </List>
  );
}
```

## Testing

### Vitest Setup
```typescript
// test/setup.ts
import { beforeEach } from "vitest";

beforeEach(() => {
  // Reset mocks, clear storage
});
```

### Test Patterns
```typescript
describe("JSON Extraction", () => {
  it("should extract valid JSON from markdown", () => {
    const result = extractJson(input);
    expect(result).toEqual({ prompt: "improved" });
  });
});
```

## Type Safety

### Zod Validation
```typescript
const ConfigSchema = z.object({
  backendUrl: z.string().url(),
  mode: z.enum(["legacy", "nlac", "ollama-only"]),
  timeout: z.number().min(1000).max(60000),
});

type Config = z.infer<typeof ConfigSchema>;
```

### Type Sharing with Backend
```typescript
// Keep in sync with Python IntentType enum
export enum IntentType {
  CLARIFY = "clarify",
  EXPAND = "expand",
  REFINING = "refining",
}
```

## Performance

### Timeout Synchronization
```typescript
// Frontend: 3s longer than backend
const BACKEND_TIMEOUT = 60000;  // 60s
const FRONTEND_TIMEOUT = 63000; // 63s
```

### Progressive Loading
1. **Loading**: Show spinner
2. **Processing**: Show stage name
3. **Done**: Show result

## Wizard Mode

### Conversation Flow
```typescript
interface ConversationTurn {
  question: string;
  answer: string;
  timestamp: number;
}

// Max 3 turns before auto-completion
const MAX_TURNS = 3;
```

### Auto vs Manual Mode
- **Auto**: Automatically advance when confident
- **Manual**: User controls each turn

## Documentation

- `docs/IMPLEMENTATION_TRACKING.md` — Phased development status
- `docs/WIZARD_MODE.md` — Interactive conversation system
- Raycast API: https://developers.raycast.com

## Source of Truth

- `src/core/design/tokens.ts` — Design tokens
- `src/core/config/` — Configuration management
- `src/core/llm/` — LLM integration patterns
