# Ollama Quick Reference for Raycast Extension

## The Critical Fix

### Before (Broken)
```typescript
// ❌ Using /api/generate - No system/user separation
fetch('http://localhost:11434/api/generate', {
  body: JSON.stringify({
    model: 'llama3.1',
    prompt: `You are an expert. ${userInput}`  // Concatenated!
  })
})
```

### After (Fixed)
```typescript
// ✅ Using /api/chat - Proper message structure
fetch('http://localhost:11434/api/chat', {
  body: JSON.stringify({
    model: 'llama3.1',
    messages: [
      { role: 'system', content: 'You are an expert...' },
      { role: 'user', content: userInput }
    ]
  })
})
```

## Complete Working Example

```typescript
interface OllamaMessage {
  role: 'system' | 'user';
  content: string;
}

async function improvePrompt(userPrompt: string): Promise<string> {
  const response = await fetch('http://localhost:11434/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama3.1',
      messages: [
        {
          role: 'system',
          content: 'You are an expert prompt engineer. Transform rough prompts into structured, high-quality prompts with: Objective, Role, Directive, Framework, Guardrails.'
        },
        {
          role: 'user',
          content: `Improve this prompt:\n\n"${userPrompt}"`
        }
      ],
      stream: false,
      temperature: 0.7
    })
  });

  const data = await response.json();
  return data.message.content;
}
```

## Quality Metrics (Copy-Paste)

```typescript
function calculateQuality(prompt: string): {
  clarity: number;
  completeness: number;
  conciseness: number;
  overall: number;
} {
  const words = prompt.split(/\s+/);

  // Clarity: 10-200 words is optimal
  let clarity = words.length >= 10 && words.length <= 200 ? 1 : 0.5;
  if (words.length < 5 || words.length > 300) clarity = 0;

  // Completeness: Check for key components
  let completeness = 0;
  if (/objective|goal/i.test(prompt)) completeness += 0.33;
  if (/role|persona/i.test(prompt)) completeness += 0.33;
  if (/directive|instruction/i.test(prompt)) completeness += 0.34;

  // Conciseness: Penalize excessive length
  let conciseness = 1;
  if (words.length > 500) conciseness = 0.5;
  if (words.length > 1000) conciseness = 0.2;

  const overall = (clarity * 0.4 + completeness * 0.4 + conciseness * 0.2) * 5;

  return { clarity, completeness, conciseness, overall };
}
```

## Ollama API Endpoints

| Endpoint | Purpose | Request Format |
|----------|---------|----------------|
| `/api/generate` | Single prompt (❌ Don't use) | `{ model, prompt, stream }` |
| `/api/chat` | Message array (✅ Use this) | `{ model, messages, stream }` |
| `/api/tags` | List models | GET |
| `/api/version` | Get version | GET |

## Message Structure Reference

```typescript
// System message - Sets AI behavior
{
  role: 'system',
  content: 'You are a prompt engineering expert...'
}

// User message - The actual task
{
  role: 'user',
  content: 'Improve this prompt:...'
}

// Full request
{
  model: 'llama3.1',
  messages: [systemMessage, userMessage],
  stream: false,
  temperature: 0.7
}
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Output same as input | Using `/api/generate` | Switch to `/api/chat` |
| Model ignores instructions | No system message | Add system message to messages array |
| Connection refused | Ollama not running | Start Ollama: `ollama serve` |
| Model not found | Wrong model name | Check with `/api/tags` |

## Testing Checklist

- [ ] Switched to `/api/chat` endpoint
- [ ] Using messages array (not single prompt)
- [ ] System message contains instructions
- [ ] User message contains the prompt to improve
- [ ] Quality metrics calculated and displayed
- [ ] Error handling for Ollama unavailable
- [ ] Result copied to clipboard
- [ ] Toast shows quality improvement

## Quick Test

```typescript
// Test the fix
async function test() {
  const result = await improvePrompt("write a blog post");
  console.log('Improved:', result);
  console.log('Quality:', calculateQuality(result));
}
```

---

**For full details:** See `prompt-engineering-investigation.md`
