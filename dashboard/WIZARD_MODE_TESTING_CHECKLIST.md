# Wizard Mode Testing Checklist

## Automated Verification ✅

- [x] **Test Suite:** All 155 tests passing (6 skipped)
- [x] **TypeScript:** No type errors (`npx tsc --noEmit`)

---

## Manual Smoke Test Steps

### Prerequisites

```bash
# 1. Ensure backend is running
make health  # Should return "healthy"

# If not running:
make dev
```

### Test 1: Basic Wizard Flow

**Step 1:** Start the development environment
```bash
cd dashboard && npm run dev
```

**Step 2:** Open Raycast and invoke the "Prompt Conversation" command

**Step 3:** Enter ambiguous input
```
create something
```

**Step 4:** Verify wizard activates
- [ ] Conversation UI appears (not the standard quick prompt)
- [ ] Initial clarifying question is displayed
- [ ] Input field is focused
- [ ] Context shows the original idea

**Step 5:** Respond to the question
```
a blog post about AI
```

**Step 6:** Verify prompt generation
- [ ] Response is processed
- [ ] Improved prompt is generated
- [ ] Result is copied to clipboard
- [ ] Success notification appears

### Test 2: Skip Wizard (Cmd+Enter)

**Step 1:** Invoke "Prompt Conversation" command

**Step 2:** Enter ambiguous input
```
create something
```

**Step 3:** Press `Cmd+Enter` (instead of just Enter)

**Step 4:** Verify immediate generation
- [ ] Wizard is skipped
- [ ] Prompt is generated immediately
- [ ] Result is copied to clipboard

### Test 3: Always-On Mode

**Step 1:** Access wizard preferences
- Open Raycast settings
- Navigate to Promptify extension
- Find "Wizard Mode" section

**Step 2:** Set to "Always" mode
- [ ] Wizard mode toggle is ON
- [ ] Mode selector shows "Always"

**Step 3:** Test with clear input
```
Write a blog post about machine learning
```

**Step 4:** Verify wizard still activates
- [ ] Even clear input triggers wizard (because "Always" mode)
- [ ] Questions are asked

### Test 4: Off Mode

**Step 1:** Set wizard mode to "Off"
- [ ] Wizard mode toggle is OFF (or mode = "off")

**Step 2:** Test with ambiguous input
```
create something
```

**Step 3:** Verify wizard doesn't activate
- [ ] Standard quick prompt flow runs immediately
- [ ] No conversation UI
- [ ] Prompt generated and copied directly

### Test 5: Session Persistence

**Step 1:** Start a conversation
```
Input: "create something"
Question: "What type of content?"
Response: "a blog post"
```

**Step 2:** Before completion, cancel the command (Esc)

**Step 3:** Re-invoke "Prompt Conversation"

**Step 4:** Verify session restoration
- [ ] Previous conversation context is visible
- [ ] Can continue where left off

### Test 6: Multi-Turn Conversation

**Step 1:** Start with very ambiguous input
```
help me
```

**Step 2:** Answer first question
```
with writing
```

**Step 3:** Verify second question appears
- [ ] Another clarifying question is asked
- [ ] Context accumulates from previous answers

**Step 4:** Answer second question
```
a technical blog post about Go
```

**Step 5:** Verify final prompt generation
- [ ] Full conversation context is used
- [ ] Prompt is generated and copied

### Test 7: Error Handling

**Step 1:** Start a conversation

**Step 2:** Disconnect from internet (or stop backend)

**Step 3:** Try to respond to a question

**Step 4:** Verify graceful error handling
- [ ] Error message is displayed
- [ ] UI doesn't crash
- [ ] Can retry or cancel

---

## Expected Behavior Summary

| Wizard Mode | Trigger | Behavior |
|------------|---------|----------|
| **Auto** (default) | Ambiguous input + low confidence | Activates wizard |
| **Auto** | Clear input + high confidence | Skips wizard |
| **Always** | Any input | Always activates wizard |
| **Off** | Any input | Never activates wizard |

### Adaptive Max Turns

- **SIMPLE** complexity: 1 question max
- **MODERATE** complexity: 2 questions max
- **COMPLEX** complexity: 3 questions max

### Keyboard Shortcuts

- **Enter:** Submit response and continue conversation
- **Cmd+Enter:** Skip wizard and generate immediately
- **Esc:** Cancel/closes conversation (saves session)

---

## Next Phase: Backend Integration

Currently, wizard mode uses **mocked** NLaC analysis. Phase 2 will connect to the real backend:

- [ ] IntentClassifier service
- [ ] ComplexityAnalyzer service
- [ ] KNNFewShot for question generation
- [ ] Real-time confidence scoring

To enable backend integration, update the service call in `wizardService.ts`:
```typescript
// Replace mock analysis with real API call
const analysis = await analyzeInputWithNLaC(idea, context);
```

---

## Troubleshooting

### Issue: Wizard not activating
- **Check:** Preferences show "Auto" mode and toggle is ON
- **Check:** Input is sufficiently ambiguous (e.g., "create something")
- **Check:** Browser console for errors

### Issue: Session not persisting
- **Check:** LocalStorage permissions in Raycast
- **Check:** Session manager initialization logs

### Issue: Questions not relevant
- **Expected:** Currently using template questions (Phase 1)
- **Solution:** Phase 2 will integrate KNN-based question generation

### Issue: Backend not responding
- **Check:** `make health` returns "healthy"
- **Check:** Port 8000 is available
- **Check:** .env has correct API keys

---

## Success Criteria

All tests pass if:
- [x] Automated tests: 155/155 passing
- [x] TypeScript: No errors
- [ ] Manual tests: All 7 scenarios pass
- [ ] No console errors during manual testing
- [ ] Smooth UX (no jank, proper focus management)
