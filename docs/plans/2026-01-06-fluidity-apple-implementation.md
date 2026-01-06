# Fluidez Apple Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implementar progressive feedback, micro-interacciones, y visual polish para crear percepción de fluidez Apple dentro de las limitaciones de Raycast API.

**Architecture:** Crear ProgressiveToast class que maneja un único toast con updates progresivos, integrarlo en handleGenerateFinal con checkpoints de progreso, y mejorar markdown structure con metadata visual y bullet lists.

**Tech Stack:** Raycast Extension API (React/TypeScript), Toast.Style.Animated/Success/Failure, Markdown rendering.

---

## Task 1: Create ProgressiveToast Class

**Files:**
- Create: `dashboard/src/core/design/progressiveToast.tsx`

**Step 1: Create the ProgressiveToast class file**

```typescript
import { Toast, showToast } from "@raycast/api";

/**
 * Progressive toast manager for Apple-like fluidity
 * Maintains a single toast instance that updates progressively
 * to give sense of constant forward progress
 */
export class ProgressiveToast {
  private toast?: Toast;

  /**
   * Start the progressive toast with initial message
   */
  async start(initial: string) {
    this.toast = await showToast({
      style: Toast.Style.Animated,
      title: initial,
    });
  }

  /**
   * Update the toast title to show progress
   */
  async update(message: string) {
    if (this.toast) {
      await this.toast.setTitle(message);
    }
  }

  /**
   * Transition to success state
   */
  async success(title: string, message?: string) {
    if (this.toast) {
      await this.toast.setStyle(Toast.Style.Success);
      await this.toast.setTitle(title);
      if (message) {
        await this.toast.setMessage(message);
      }
    }
  }

  /**
   * Transition to error state with hint
   */
  async error(title: string, error: Error | string, hint?: string) {
    if (this.toast) {
      await this.toast.setStyle(Toast.Style.Failure);
      await this.toast.setTitle(title);
      const errMsg = error instanceof Error ? error.message : error;
      await this.toast.setMessage(hint ? `${errMsg} — ${hint}` : errMsg);
    }
  }
}
```

**Step 2: Commit ProgressiveToast class**

```bash
git add dashboard/src/core/design/progressiveToast.tsx
git commit -m "feat: add ProgressiveToast class for Apple-like fluidity

- Maintains single toast instance with progressive updates
- Methods: start(), update(), success(), error()
- Replaces static ToastHelper for better flow control"
```

---

## Task 2: Add LoadingStage Type and State

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:169-185`

**Step 1: Add LoadingStage type before Command function**

```typescript
// Add after line 167 (before export default function Command())
type LoadingStage = 'validating' | 'connecting' | 'processing' | 'finalizing';
```

**Step 2: Add loadingState to Command component state**

```typescript
// Find line 179: const [isLoading, setIsLoading] = useState(false);
// Add after it:

const [loadingStage, setLoadingStage] = useState<LoadingStage | null>(null);
```

**Step 3: Commit LoadingStage type**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add LoadingStage type for progressive feedback

- Tracks 4 stages: validating, connecting, processing, finalizing
- Enables progressive toast updates with meaningful messages"
```

---

## Task 3: Refactor handleGenerateFinal with Progressive Updates

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:197-304`

**Step 1: Import ProgressiveToast at top of file**

```typescript
// Find line 5: import { ToastHelper } from "./core/design/toast";
// Add after it:
import { ProgressiveToast } from "./core/design/progressiveToast";
```

**Step 2: Replace ToastHelper with ProgressiveToast in handleGenerateFinal**

```typescript
// Find line 197: async function handleGenerateFinal(values: { inputText: string }) {
// Replace the entire function body with this:

async function handleGenerateFinal(values: { inputText: string }) {
  const text = values.inputText.trim();

  // Stage 1: Validating (instant, no toast)
  if (!text.length) {
    await ToastHelper.error("Empty Input", "Paste or type some text first");
    return;
  }
  if (text.length < 5) {
    await ToastHelper.error("Input Too Short", "Please enter at least 5 characters");
    return;
  }

  setIsLoading(true);
  const progress = new ProgressiveToast();

  // Stage 2: Connecting
  await progress.start("Connecting to DSPy...");

  try {
    const config = configState.config;
    const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
    const model = preferences.model?.trim() || config.ollama.model;
    const fallbackModel = preferences.fallbackModel?.trim() || config.ollama.fallbackModel || config.ollama.model;
    const preset = preferences.preset ?? config.presets.default;
    const timeoutMs = parseTimeoutMs(preferences.timeoutMs, config.ollama.timeoutMs);
    const temperature = config.ollama.temperature ?? 0.1;
    const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
    const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;

    // Stage 3: Processing
    await progress.update("Analyzing your prompt...");

    if (!dspyEnabled) {
      const health = await ollamaHealthCheck({ baseUrl, timeoutMs: Math.min(2_000, timeoutMs) });
      if (!health.ok) {
        await progress.error("Ollama is not reachable", health.error, `Check ${baseUrl}`);
        return;
      }
    }

    await progress.update("Generating improvements...");

    const result = dspyEnabled
      ? await improvePromptWithHybrid({
          rawInput: text,
          preset,
          options: {
            baseUrl,
            model,
            timeoutMs,
            temperature,
            systemPattern: getCustomPatternSync(),
            dspyBaseUrl,
            dspyTimeoutMs: config.dspy.timeoutMs,
          },
          enableDSPyFallback: false,
        })
      : await runWithModelFallback({
          baseUrl,
          model,
          fallbackModel,
          timeoutMs,
          temperature,
          rawInput: text,
          preset,
          systemPattern: getCustomPatternSync(),
        });

    // Stage 4: Finalizing
    await progress.update("Finalizing result...");

    const finalPrompt = result.improved_prompt.trim();
    await Clipboard.copy(finalPrompt);

    await progress.success("Copied to clipboard", `${finalPrompt.length} characters`);

    setPreview({
      prompt: finalPrompt,
      meta: {
        confidence: result.confidence,
        clarifyingQuestions: result.clarifying_questions,
        assumptions: result.assumptions,
      },
      source: dspyEnabled ? "dspy" : "ollama",
    });
  } catch (e) {
    const config = configState.config;
    const baseUrl = preferences.ollamaBaseUrl?.trim() || config.ollama.baseUrl;
    const model = preferences.model?.trim() || config.ollama.model;
    const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
    const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;
    const hint = dspyEnabled ? buildDSPyHint(e) : buildErrorHint(e);

    // Debug logging
    console.error("[Promptify] Error details:", {
      error: e instanceof Error ? e.message : String(e),
      preferencesModel: preferences.model,
      configModel: config.ollama.model,
      finalModel: model,
      dspyEnabled,
    });

    if (dspyEnabled) {
      await progress.error("DSPy backend not available", e instanceof Error ? e.message : String(e), `${dspyBaseUrl}${hint ? ` — ${hint}` : ""}`);
      return;
    }

    await progress.error("Prompt improvement failed", e instanceof Error ? e.message : String(e), `(${model} @ ${baseUrl})${hint ? ` — ${hint}` : ""}`);
  } finally {
    setIsLoading(false);
  }
}
```

**Step 3: Commit progressive toast integration**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: integrate ProgressiveToast into generation flow

- 4 stages: validating (instant), connecting, processing, finalizing
- Progressive updates: \"Connecting...\" → \"Analyzing...\" → \"Generating...\" → \"Finalizing...\"
- Single toast instance with transitions (Animated → Success/Failure)
- Better error handling with ProgressiveToast.error()
```

---

## Task 4: Enhance Markdown Structure with Metadata Line

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:30-50`

**Step 1: Add metadata line before the code block**

```typescript
// Find line 30-34 in PromptPreview function:
//   const sections: string[] = [];
//   sections.push("## Improved Prompt", "", "```text", props.prompt, "```");
//
// Replace with:

  const sections: string[] = [];

  // Header
  sections.push("## Improved Prompt");

  // Metadata line: source + confidence (Apple-style minimal)
  if (props.meta?.confidence || props.source) {
    const metaLine = [
      props.source === "dspy" ? "⤒ DSPy + Haiku" : "○ Ollama",
      props.meta?.confidence ? `${Math.round(props.meta.confidence)}% confidence` : null,
    ].filter(Boolean).join(" • ");

    sections.push("", `*${metaLine}*`);
  }

  // Main prompt in code block
  sections.push("", "```text", props.prompt, "```");
```

**Step 2: Commit metadata line enhancement**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add metadata line before prompt

- Shows source (⤒ DSPy + Haiku or ○ Ollama) and confidence
- Apple-style minimal format: \"*source • confidence*\"
- Provides technical context before main content"
```

---

## Task 5: Convert Numbered Lists to Bullet Lists

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:37-48`

**Step 1: Replace numbered lists with bullet lists**

```typescript
// Find lines 37-48 in PromptPreview function:
//   if (props.meta?.clarifyingQuestions?.length) {
//     sections.push("", "", "### Clarifying Questions", "");
//     props.meta.clarifyingQuestions.forEach((q, i) => {
//       sections.push(`${i + 1}. ${q}`);
//     });
//   }
//
//   if (props.meta?.assumptions?.length) {
//     sections.push("", "", "### Assumptions", "");
//     props.meta.assumptions.forEach((a, i) => {
//       sections.push(`${i + 1}. ${a}`);
//     });
//   }
//
// Replace with:

  if (props.meta?.clarifyingQuestions?.length) {
    sections.push("", "", "### Clarifying Questions", "");
    props.meta.clarifyingQuestions.forEach((q) => {
      sections.push(`- ${q}`);
    });
  }

  if (props.meta?.assumptions?.length) {
    sections.push("", "", "### Assumptions", "");
    props.meta.assumptions.forEach((a) => {
      sections.push(`- ${a}`);
    });
  }
```

**Step 2: Commit bullet list conversion**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: use bullet lists instead of numbered

- Cleaner visual hierarchy for questions/assumptions
- Better markdown rendering in Raycast Detail view
- Matches Apple design minimalism"
```

---

## Task 6: Add Visual Separator at End

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:50-56`

**Step 1: Add horizontal rule after metadata sections**

```typescript
// Find the end of the PromptPreview markdown building (around line 50-56)
// After the assumptions section, before the stats calculation:
//
//   sections.push("", "", "### Assumptions", "");
//   props.meta.assumptions.forEach((a) => {
//     sections.push(`- ${a}`);
//   });
//
// Add after it:

  // Visual separator at end
  sections.push("", "---", "");
```

**Step 2: Commit visual separator**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: add visual separator at end of markdown

- Horizontal rule (---) provides clear end boundary
- Better visual completion of the content
- Matches Apple design attention to detail"
```

---

## Task 7: Manual Testing in Raycast

**Files:** None (manual testing)

**Step 1: Build and reload extension**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard
npm run build
```

Then in Raycast:
1. Open Raycast Preferences
2. Extensions → Prompt Improver
3. Disable → Enable (to reload)

**Step 2: Test progressive toast flow**

1. Open Prompt Improver in Raycast (⌘ + space, type "improve")
2. Paste a valid prompt (5+ characters)
3. Press ⌘⇧↵ to improve
4. **Verify:** Toast shows "Connecting to DSPy..." → "Analyzing your prompt..." → "Generating improvements..." → "Finalizing result..." → "Copied to clipboard" (Success)

**Step 3: Test error handling**

1. Stop DSPy backend: `make stop`
2. Try to improve a prompt
3. **Verify:** Toast shows error with hint: "DSPy backend not available — Check the DSPy backend is running"
4. Restart backend: `make dev`

**Step 4: Test markdown enhancements**

1. Improve a prompt that returns metadata
2. **Verify:** Detail view shows:
   - "## Improved Prompt" header
   - Metadata line: "*⤒ DSPy + Haiku • XX% confidence*"
   - Bullet lists for questions/assumptions (not numbered)
   - "---" separator at end

**Step 5: Test validation errors**

1. Type "abc" (3 characters) and try to improve
2. **Verify:** Instant error toast: "Input Too Short - Please enter at least 5 characters"

**Step 6: Test Try Again transition**

1. From preview, press ⌘⇧R (Try again)
2. **Verify:** Smooth transition back to form with loading state cleared

---

## Final Verification

**All tasks complete?**
- [x] ProgressiveToast class created
- [x] LoadingStage type added
- [x] handleGenerateFinal refactored with progressive updates
- [x] Metadata line added before prompt
- [x] Bullet lists replace numbered lists
- [x] Visual separator added at end
- [x] Manual testing passed

**Expected commits:**
1. `feat: add ProgressiveToast class for Apple-like fluidity`
2. `feat: add LoadingStage type for progressive feedback`
3. `feat: integrate ProgressiveToast into generation flow`
4. `feat: add metadata line before prompt`
5. `feat: use bullet lists instead of numbered`
6. `feat: add visual separator at end of markdown`

---

## Related Documentation

- **Design Document:** `docs/plans/2026-01-06-fluidity-apple-design.md`
- **Design Principles:** `/Users/felipe_gonzalez/.claude/skills/design-principles/skill.md`
- **Previous Work:** Visual Hierarchy Improvements (2026-01-05)
