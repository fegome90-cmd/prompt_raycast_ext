# API for External Consumers

> Guide for integrating DSPy Prompt Improvement from external projects (sub-agents, CLIs, other services)

---

## Quick Start

**Minimal curl example:**

```bash
curl -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Build a REST API", "mode": "legacy"}'
```

**Response:**

```json
{
  "improved_prompt": "**[ROLE & PERSONA]**\nYou are a World-Class API Architect...",
  "role": "World-Class API Architect with over 15 years of experience...",
  "directive": "To design and implement a robust, scalable REST API...",
  "framework": "chain-of-thought",
  "guardrails": ["Use OpenAPI spec", "Handle errors gracefully", "Version your API"],
  "reasoning": "Selected API Architect role for expertise...",
  "confidence": 0.87,
  "backend": "zero-shot",
  "prompt_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "strategy": "simple",
  "intent": "GENERATE"
}
```

---

## Request Schema

```json
{
  "idea": "string (min 5 chars, required)",
  "context": "string (optional, max 5000 chars)",
  "mode": "legacy | nlac (required)"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `idea` | string | Yes | Raw idea to improve (minimum 5 characters) |
| `context` | string | No | Additional context (max 5000 chars) |
| `mode` | enum | Yes | `"legacy"` for DSPy CoT, `"nlac"` for NLaC pipeline |

---

## Response Schema

```json
{
  "improved_prompt": "string",
  "role": "string",
  "directive": "string",
  "framework": "string",
  "guardrails": ["string"],
  "reasoning": "string | null",
  "confidence": "float | null",
  "backend": "string | null",
  "prompt_id": "uuid",
  "strategy": "string",
  "intent": "DEBUG | REFACTOR | GENERATE | EXPLAIN",
  "metrics_warning": "string | null",
  "degradation_flags": {
    "metrics_failed": "boolean",
    "knn_disabled": "boolean",
    "complex_strategy_disabled": "boolean"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `improved_prompt` | string | Full structured prompt (ready to use) |
| `role` | string | Extracted AI persona description |
| `directive` | string | Core mission statement |
| `framework` | string | Reasoning approach (e.g., "chain-of-thought") |
| `guardrails` | string[] | List of constraints/guidelines |
| `reasoning` | string? | Explanation of prompt construction |
| `confidence` | float? | Quality confidence score (0.0-1.0) |
| `backend` | string? | Strategy used ("zero-shot" or "few-shot") |
| `prompt_id` | uuid | Unique identifier for this prompt |
| `strategy` | string | Strategy name (e.g., "simple", "complex") |
| `intent` | enum | Classified intent: DEBUG, REFACTOR, GENERATE, EXPLAIN |
| `metrics_warning` | string? | Warning if metrics calculation failed |
| `degradation_flags` | object | Flags indicating optional feature failures |

---

## Mode Selection

| Mode | Description | Latency | Best For |
|------|-------------|---------|----------|
| `legacy` | DSPy ChainOfThought | ~2-5s | Quick improvements, simple ideas |
| `nlac` | NLaC pipeline with OPRO optimization | ~5-15s | Complex ideas, needs higher quality |

**Recommendation:** Start with `legacy` for speed. Use `nlac` when quality matters more than latency.

---

## Error Handling

### HTTP Status Codes

| Status | Meaning | When It Occurs |
|--------|---------|----------------|
| 400 | Bad Request | Invalid input (idea too short, invalid mode) |
| 422 | Validation Error | Pydantic schema validation failure |
| 503 | Service Unavailable | LLM provider down, connection error |
| 504 | Gateway Timeout | Request exceeded 120s timeout |
| 500 | Internal Error | Unexpected server error |

### Error Response Format

```json
{
  "detail": "Metrics calculation failed: AttributeError"
}
```

### Graceful Degradation

The API may return successful responses with degradation flags when optional features fail:

```json
{
  "improved_prompt": "**[ROLE]** ...",
  "metrics_warning": "Metrics calculation skipped: TypeError",
  "degradation_flags": {
    "metrics_failed": true,
    "knn_disabled": false,
    "complex_strategy_disabled": false
  }
}
```

**Important:** Always check `degradation_flags` before relying on optional response fields.

---

## Client Examples

### Python (requests)

```python
import requests
from typing import Optional

API_BASE = "http://localhost:8000"

def improve_prompt(
    idea: str,
    context: str = "",
    mode: str = "legacy",
    timeout: int = 120
) -> dict:
    """
    Improve a prompt using DSPy.

    Args:
        idea: Raw idea to improve (min 5 chars)
        context: Additional context (optional)
        mode: "legacy" or "nlac"
        timeout: Request timeout in seconds

    Returns:
        dict with improved_prompt, role, directive, etc.

    Raises:
        requests.HTTPError: On non-2xx responses
    """
    response = requests.post(
        f"{API_BASE}/api/v1/improve-prompt",
        json={"idea": idea, "context": context, "mode": mode},
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def health_check() -> bool:
    """Check if backend is healthy."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


# Usage example
if __name__ == "__main__":
    if not health_check():
        print("Backend not available. Start with: make dev")
        exit(1)

    result = improve_prompt(
        idea="Implement caching for high-traffic API",
        context="Using Redis as cache backend",
        mode="legacy"
    )

    print(f"Improved Prompt:\n{result['improved_prompt']}")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
```

### Python (httpx - async)

```python
import httpx

async def improve_prompt_async(
    idea: str,
    context: str = "",
    mode: str = "legacy"
) -> dict:
    """Async version using httpx."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/improve-prompt",
            json={"idea": idea, "context": context, "mode": mode}
        )
        response.raise_for_status()
        return response.json()
```

### TypeScript (fetch)

```typescript
interface ImprovePromptRequest {
  idea: string;
  context?: string;
  mode: "legacy" | "nlac";
}

interface ImprovePromptResponse {
  improved_prompt: string;
  role: string;
  directive: string;
  framework: string;
  guardrails: string[];
  reasoning: string | null;
  confidence: number | null;
  backend: string | null;
  prompt_id: string;
  strategy: string;
  intent: "DEBUG" | "REFACTOR" | "GENERATE" | "EXPLAIN";
  metrics_warning: string | null;
  degradation_flags: {
    metrics_failed: boolean;
    knn_disabled: boolean;
    complex_strategy_disabled: boolean;
  };
}

const API_BASE = "http://localhost:8000";

async function improvePrompt(
  idea: string,
  context = "",
  mode: "legacy" | "nlac" = "legacy"
): Promise<ImprovePromptResponse> {
  const response = await fetch(`${API_BASE}/api/v1/improve-prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea, context, mode } as ImprovePromptRequest),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(`HTTP ${response.status}: ${error.detail}`);
  }

  return response.json();
}

async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

// Usage example
(async () => {
  if (!(await healthCheck())) {
    console.error("Backend not available. Start with: make dev");
    process.exit(1);
  }

  const result = await improvePrompt(
    "Implement user authentication",
    "Web app with OAuth2 support",
    "legacy"
  );

  console.log(`Improved Prompt:\n${result.improved_prompt}`);
  console.log(`Intent: ${result.intent}`);
  console.log(`Confidence: ${result.confidence}`);
})();
```

### curl

```bash
# Basic request
curl -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Build a REST API", "mode": "legacy"}'

# With context
curl -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Design a caching system",
    "context": "High-traffic web application using Redis",
    "mode": "nlac"
  }'

# Health check
curl http://localhost:8000/health

# Pretty print response
curl -s -X POST "http://localhost:8000/api/v1/improve-prompt" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a CLI tool", "mode": "legacy"}' | jq .
```

---

## Configuration

### Backend URL

| Environment | URL |
|-------------|-----|
| Local development | `http://localhost:8000` |
| Custom port | `http://localhost:{API_PORT}` (check `.env`) |

### Timeout Recommendations

| Mode | Recommended Timeout |
|------|---------------------|
| `legacy` | 30-60 seconds |
| `nlac` | 60-120 seconds |
| Maximum allowed | 120 seconds (hard limit) |

**Note:** The backend enforces a 120-second timeout. Setting a higher client timeout won't help.

### Health Check Endpoint

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "provider": "anthropic",
  "model": "claude-haiku-4-5-20251001",
  "dspy_configured": true
}
```

---

## Sub-Agent Integration Pattern

For AI agents calling this API:

```python
# Example: Sub-agent using prompt improvement
def agent_task(user_idea: str) -> str:
    """Sub-agent that improves prompts before processing."""

    # 1. Improve the prompt
    improved = improve_prompt(idea=user_idea, mode="legacy")

    # 2. Use the improved prompt
    system_prompt = improved["improved_prompt"]

    # 3. Continue with your agent logic...
    return system_prompt
```

### Best Practices for Sub-Agents

1. **Always check health first** - Avoid hanging on unavailable backend
2. **Handle degradation gracefully** - Check `degradation_flags`
3. **Use appropriate mode** - `legacy` for speed, `nlac` for quality
4. **Set reasonable timeouts** - 60s for legacy, 120s for nlac
5. **Log prompt_id** - Useful for debugging and tracking

---

## Troubleshooting

### Backend Not Responding

```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend
make dev

# Or with PM2
pm2 start all
```

### Timeout Errors

- Ensure client timeout >= expected latency
- Use `legacy` mode for faster responses
- Check backend logs: `pm2 logs raycast-backend-8000`

### Validation Errors (422)

- Ensure `idea` has at least 5 characters
- Ensure `mode` is exactly `"legacy"` or `"nlac"`
- Check JSON format is valid

---

## Related Documentation

- [API Error Handling](./api-error-handling.md) - Detailed error handling guide
- [Backend README](./backend/README.md) - DSPy architecture and configuration
- [CLAUDE.md](../CLAUDE.md) - Project overview and quality gates
