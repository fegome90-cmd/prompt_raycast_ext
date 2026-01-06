# Fluidez Apple - Design Document

> **Para Claude:** Este documento valida el diseño co-creado con el usuario usando brainstorming + design-principles skill.

**Fecha:** 2026-01-06
**Objetivo:** Mejorar la percepción de fluidez Apple en Prompt Improver dentro de las limitaciones de Raycast API

---

## Filosofía de Diseño

Aunque Raycast **no permite CSS customizado, animaciones, o fondos personalizados**, podemos crear **percepción de fluidez** a través de:

1. **Progressive Feedback** — Toasts que evolucionan con mensajes específicos
2. **Micro-Interactions** — Timings Apple-calibrados y transiciones de estado optimizadas
3. **Visual Polish** — Markdown structure intencional con metadata visual

**Apple se especializa** en hacer que las limitaciones técnicas se sientan como decisiones de diseño intencionales.

---

## Componentes a Crear

### 1. ProgressiveToast Class

**Archivo:** `dashboard/src/core/design/progressiveToast.tsx`

**Responsabilidad:** Manejar un único toast con updates progresivos para dar sensación de progreso constante.

**API:**
```typescript
class ProgressiveToast {
  private toast?: Toast;

  async start(initial: string)           // Inicia toast animado
  async update(message: string)          // Actualiza título del toast
  async success(title: string, message?: string)  // Transición a Success
  async error(title: string, error: Error | string, hint?: string)  // Transición a Failure
}
```

**Flow en handleGenerateFinal:**
1. "Connecting to DSPy..." (iniciando conexión)
2. "Analyzing your prompt..." (validando input)
3. "Generating improvements..." (procesando)
4. "Finalizing result..." (recibiendo respuesta)
5. Success: "Copied to clipboard" (resultado listo)

---

### 2. LoadingStage Type

**Archivo:** Modificar `dashboard/src/promptify-quick.tsx`

**Type:**
```typescript
type LoadingStage =
  | 'validating'      // Input validation (<100ms)
  | 'connecting'      // Backend connection (200-500ms)
  | 'processing'      // DSPy improvement (1-3s)
  | 'finalizing';     // Response handling (200-500ms)
```

---

### 3. Markdown Visual Enhancements

**Archivo:** Modificar `PromptPreview` component en `promptify-quick.tsx`

**Cambios en markdown structure:**

1. **Metadata line antes del código:**
   ```markdown
   ## Improved Prompt

   ⤒ DSPy + Haiku • 87% confidence

   ```text
   [prompt mejorado]
   ```
   ```

2. **Bullet lists en lugar de numbered:**
   ```markdown
   ### Clarifying Questions
   - What is the primary goal?
   - Who is the target audience?

   ### Assumptions
   - User has technical background
   ```

3. **Separador visual final:**
   ```markdown
   ---
   ```

---

## Timings Apple-Calibrados

| Stage | Duration | Toast Message |
|-------|----------|---------------|
| Input validation | <100ms | (sin toast, instantáneo) |
| Backend connection | 200-500ms | "Connecting to DSPy..." |
| DSPy processing | 1-3s | "Generating improvements..." |
| Finalization | 200-500ms | "Finalizing result..." |

**Micro-feedbacks sin toast:**
- Input validation: Error toast solo cuando falla (ya implementado)
- Button states: `disabled={isLoading}` con `title` dinámico
- Try again transition: 50ms delay intencional para naturalidad

---

## Error Handling

**Misma estrategia ProgressiveToast:**

| Error | Toast Title | Message + Hint |
|-------|-------------|----------------|
| Network | "DSPy backend unavailable" | `error message — Check ${baseUrl}` |
| Timeout | "Request timed out" | `error — Try increasing timeout (ms)` |
| Parse error | "Invalid response" | `error — Check backend logs` |

**Recovery UX:**
- Si falla DSPy: "Retrying with Ollama..." (si fallback enabled)
- Si falla todo: "Check DSPy backend is running"

---

## Testing Strategy

**Tests manuales (Raycast no tiene test runner UI):**

1. ✅ Happy path con DSPy → Verificar progressive toast updates (4 mensajes)
2. ✅ Error de conexión → Verificar error toast con hint
3. ✅ Timeout → Verificar timeout hint actionable
4. ✅ Try again → Verificar transición suave preview → form
5. ✅ Markdown render → Verificar bullet lists y separador `---`

**Comando de prueba:**
```bash
# En Raycast, abrir la extensión y:
# 1. Pegar texto corto (<5 chars) → Ver validation error
# 2. Pegar texto válido → Ver progressive toasts
# 3. Probar "Try again" → Ver transición suave
```

---

## Success Criteria

- [ ] Progressive toast actualiza 4 veces durante el flow completo
- [ ] Metadata line aparece antes del prompt (⤒ DSPy + Haiku • XX% confidence)
- [ ] Bullet lists reemplazan numbered lists
- [ ] Separador `---` aparece al final
- [ ] Error toasts incluyen hints actionables
- [ ] Transición try again se siente natural (50ms delay)

---

## Archivos a Modificar

1. **Crear:** `dashboard/src/core/design/progressiveToast.tsx`
2. **Modificar:** `dashboard/src/promptify-quick.tsx` (PromptPreview + handleGenerateFinal)
3. **Modificar:** `dashboard/src/promptify-quick.tsx` (markdown structure)

---

## Referencias

- **Design-Principles Skill:** `/Users/felipe_gonzalez/.claude/skills/design-principles/skill.md`
- **Previous Work:** Visual Hierarchy Improvements (2026-01-05)
- **Apple HIG:** https://developer.apple.com/design/human-interface-guidelines/
