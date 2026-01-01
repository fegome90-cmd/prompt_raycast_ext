# 🔍 Investigation Report: Prompt Engineering Patterns for Raycast + Ollama

**Date:** 2025-01-01
**Source:** Architect (Enterprise AI Prompt Engineering Platform)
**Target:** Prompt Renderer Local (Raycast Extension)

---

## Executive Summary

**Problem Identified:** The Raycast extension uses Ollama's `/api/generate` endpoint which concatenates system instructions with user input, preventing the model from distinguishing between instructions and data.

**Solution:** Switch to Ollama's `/api/chat` endpoint with proper message array structure separating system and user content.

---

## Table of Contents

1. [Critical Fix: API Endpoint](#1-critical-fix-api-endpoint)
2. [Prompt Structure Pattern](#2-prompt-structure-pattern)
3. [Quality Validation System](#3-quality-validation-system)
4. [Complete Implementation](#4-complete-implementation)
5. [Key Files Reference](#5-key-files-reference)

---

## 1. Critical Fix: API Endpoint

### ❌ Current Problem (Your Code)

```typescript
// Using /api/generate with concatenated prompt
const response = await fetch('http://localhost:11434/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    model: 'llama3.1',
    prompt: `You are a prompt engineer. Rewrite this: ${userPrompt}`, // System + User concatenated
    stream: false
  })
});
```

**Issue:** The model cannot distinguish between system instructions and user input.

### ✅ Correct Approach

```typescript
// Using /api/chat with separate messages
const response = await fetch('http://localhost:11434/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'llama3.1',
    messages: [
      {
        role: 'system',
        content: 'You are an expert prompt engineer specializing in transforming rough prompts into structured, high-quality prompts.'
      },
      {
        role: 'user',
        content: `Rewrite this prompt to be more effective: ${userPrompt}`
      }
    ],
    stream: false,
    temperature: 0.7
  })
});
```

**Why This Works:**
- Ollama's `/api/chat` endpoint uses the same message format as OpenAI's Chat Completions API
- System messages set the AI's behavior and role
- User messages contain the actual task/prompt to improve
- The model clearly distinguishes between instructions and data

---

## 2. Prompt Structure Pattern

### The PlanData Interface (From Architect)

```typescript
interface PlanData {
  objective: string;      // What you want to achieve
  role: string;           // AI's persona/expertise
  directive: string;      // Specific instructions
  framework: string;      // How the AI should think (CoT, ToT, etc.)
  guardrails: string[];   // Constraints and boundaries
}

enum ReasoningFramework {
  CHAIN_OF_THOUGHT = "Chain-of-Thought (CoT)",
  TREE_OF_THOUGHTS = "Tree of Thoughts (ToT)",
  DECOMPOSITION = "Decomposition",
  ROLE_PLAYING = "Role-Playing Simulation"
}
```

### Adapting for Raycast Extension

```typescript
function buildStructuredPrompt(userInput: string): { system: string; user: string } {
  const systemPrompt = `You are an expert prompt engineer. Your task is to transform rough user prompts into well-structured, effective prompts using the following framework:
- Clear objective definition
- Appropriate role assignment
- Specific directive formulation
- Reasoning framework application
- Guardrail identification

Always output the improved prompt in the structured format shown below.`;

  const userPrompt = `Please rewrite and improve this prompt:

"${userInput}"

Provide the enhanced prompt in this structured format:

**Objective:** [What the prompt should achieve]
**Role:** [The AI persona to adopt]
**Directive:** [Specific instructions for the AI]
**Framework:** [Reasoning approach (Chain-of-Thought, etc.)]
**Guardrails:** [List of constraints/limitations]`;

  return { system: systemPrompt, user: userPrompt };
}
```

---

## 3. Quality Validation System

### Quality Metrics (From Architect's `promptOptimizationService.ts`)

```typescript
interface QualityScore {
  clarity: number;      // 0-1: How clear the prompt is
  completeness: number; // 0-1: All components present
  conciseness: number;  // 0-1: Not too verbose
}

function calculateClarityScore(prompt: string): number {
  let score = 0;
  let total = 0;

  const words = prompt.split(/\s+/);

  // Optimal length: 10-200 words
  if (words.length >= 10 && words.length <= 200) {
    score += 1;
  } else if (words.length > 5 && words.length < 300) {
    score += 0.5;
  }
  total += 1;

  // Has clear objective indicators
  if (/objective|goal|target|aim/i.test(prompt)) {
    score += 1;
  }
  total += 1;

  // Has role indicators
  if (/role|act as|persona|you are/i.test(prompt)) {
    score += 1;
  }
  total += 1;

  return total > 0 ? score / total : 0;
}

function calculateCompletenessScore(prompt: string): number {
  let score = 0;
  let total = 5;

  // Check for each component
  if (/objective|goal|target/i.test(prompt)) score += 1;
  if (/role|act as|persona/i.test(prompt)) score += 1;
  if (/directive|instruction|should|must/i.test(prompt)) score += 1;
  if (/framework|approach|method/i.test(prompt)) score += 1;
  if (/guardrail|constraint|limit|not/i.test(prompt)) score += 1;

  return score / total;
}

function calculateConcisenessScore(prompt: string): number {
  const words = prompt.split(/\s+/);

  // Penalize excessive length
  if (words.length > 1000) return 0.2;
  if (words.length > 500) return 0.5;
  if (words.length > 200) return 0.8;
  return 1.0;
}

// Overall quality score (0-5 scale)
function calculatePromptQuality(prompt: string): number {
  const clarity = calculateClarityScore(prompt);
  const completeness = calculateCompletenessScore(prompt);
  const conciseness = calculateConcisenessScore(prompt);

  // Weighted average
  return (clarity * 0.4 + completeness * 0.4 + conciseness * 0.2) * 5;
}
```

### Token Estimation

```typescript
function estimateTokens(text: string): number {
  // Conservative estimation: ~1.3 tokens per word
  return Math.ceil(text.split(/\s+/).length * 1.3);
}
```

---

## 4. Complete Implementation

### Full Ollama Service for Raycast

```typescript
// ollama-service.ts

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface OllamaRequest {
  model: string;
  messages: OllamaMessage[];
  stream: boolean;
  temperature?: number;
}

export interface OllamaResponse {
  model: string;
  message: {
    role: string;
    content: string;
  };
  done: boolean;
}

export interface PromptImprovementResult {
  originalPrompt: string;
  improvedPrompt: string;
  qualityScore: {
    before: number;
    after: number;
  };
  metrics: {
    clarity: number;
    completeness: number;
    conciseness: number;
  };
}

export class OllamaService {
  private baseUrl = 'http://localhost:11434';
  private defaultModel = 'llama3.1';

  async improvePrompt(userPrompt: string): Promise<PromptImprovementResult> {
    // Calculate original quality
    const beforeQuality = this.calculatePromptQuality(userPrompt);

    // Build messages
    const systemPrompt = this.buildSystemPrompt();
    const userPromptEnhanced = this.buildUserPrompt(userPrompt);

    const request: OllamaRequest = {
      model: this.defaultModel,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPromptEnhanced }
      ],
      stream: false,
      temperature: 0.7
    };

    // Call Ollama API
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
    }

    const data: OllamaResponse = await response.json();
    const improvedPrompt = data.message.content;

    // Calculate improved quality
    const afterQuality = this.calculatePromptQuality(improvedPrompt);

    return {
      originalPrompt: userPrompt,
      improvedPrompt,
      qualityScore: {
        before: beforeQuality,
        after: afterQuality
      },
      metrics: {
        clarity: this.calculateClarityScore(improvedPrompt),
        completeness: this.calculateCompletenessScore(improvedPrompt),
        conciseness: this.calculateConcisenessScore(improvedPrompt)
      }
    };
  }

  private buildSystemPrompt(): string {
    return `You are an expert prompt engineer specializing in transforming rough user prompts into structured, high-quality prompts.

Your expertise includes:
- CLARITY: Making objectives unambiguous and specific
- COMPLETENESS: Ensuring role, directive, framework, and guardrails are present
- CONCISION: Removing filler words and redundancies while preserving meaning
- STRUCTURE: Applying the PlanData framework for optimal AI performance

When improving prompts:
1. Preserve the user's core intent
2. Add missing structural elements
3. Clarify vague instructions
4. Remove redundant or filler phrases
5. Suggest appropriate reasoning frameworks
6. Identify relevant guardrails

Output ONLY the improved prompt in the structured format shown below. No explanations or meta-commentary.

**Output Format:**
**Objective:** [clear, specific goal]
**Role:** [AI persona/expertise]
**Directive:** [specific instructions]
**Framework:** [reasoning approach: Chain-of-Thought, Tree-of-Thoughts, Decomposition, or Role-Playing]
**Guardrails:** [constraint 1, constraint 2, ...]`;
  }

  private buildUserPrompt(userInput: string): string {
    return `Improve this prompt:

"${userInput}"

Provide the enhanced prompt in the structured format specified.`;
  }

  // Quality validation methods
  private calculatePromptQuality(prompt: string): number {
    const clarity = this.calculateClarityScore(prompt);
    const completeness = this.calculateCompletenessScore(prompt);
    const conciseness = this.calculateConcisenessScore(prompt);

    return (clarity * 0.4 + completeness * 0.4 + conciseness * 0.2) * 5;
  }

  private calculateClarityScore(prompt: string): number {
    let score = 0;
    let total = 0;

    const words = prompt.split(/\s+/);

    // Optimal length: 10-200 words
    if (words.length >= 10 && words.length <= 200) score += 1;
    else if (words.length > 5 && words.length < 300) score += 0.5;
    total += 1;

    // Has clear indicators
    if (/objective|goal|target/i.test(prompt)) score += 1;
    total += 1;

    if (/role|act as|persona/i.test(prompt)) score += 1;
    total += 1;

    return total > 0 ? score / total : 0;
  }

  private calculateCompletenessScore(prompt: string): number {
    let score = 0;
    const total = 5;

    if (/objective|goal|target/i.test(prompt)) score += 1;
    if (/role|act as|persona/i.test(prompt)) score += 1;
    if (/directive|instruction|should|must/i.test(prompt)) score += 1;
    if (/framework|approach|method/i.test(prompt)) score += 1;
    if (/guardrail|constraint|limit/i.test(prompt)) score += 1;

    return score / total;
  }

  private calculateConcisenessScore(prompt: string): number {
    const words = prompt.split(/\s+/);

    if (words.length > 1000) return 0.2;
    if (words.length > 500) return 0.5;
    if (words.length > 200) return 0.8;
    return 1.0;
  }

  // Token estimation
  estimateTokens(text: string): number {
    return Math.ceil(text.split(/\s+/).length * 1.3);
  }

  // Check Ollama availability
  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Get available models
  async getAvailableModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (!response.ok) return [];

      const data = await response.json();
      return data.models?.map((m: any) => m.name) || [];
    } catch {
      return [];
    }
  }
}

// Export singleton
export const ollamaService = new OllamaService();
```

### Raycast Command Implementation

```typescript
// commands/improve-prompt.ts

import { ollamaService } from '../ollama-service';

export default async function improvePrompt() {
  // Get user input
  const userPrompt = await argue({
    placeholder: 'Enter your rough prompt...',
    title: 'Improve Prompt'
  });

  if (!userPrompt || userPrompt.trim().length === 0) {
    showToast({ title: 'No prompt provided', style: Toast.Style.Failure });
    return;
  }

  // Show loading
  const toast = await showToast({
    title: 'Improving prompt...',
    message: 'Analyzing and restructuring your prompt',
    style: Toast.Style.Animated
  });

  try {
    // Check Ollama availability
    const isAvailable = await ollamaService.isAvailable();
    if (!isAvailable) {
      toast.title = 'Ollama not available';
      toast.message = 'Make sure Ollama is running';
      toast.style = Toast.Style.Failure;
      return;
    }

    // Improve the prompt
    const result = await ollamaService.improvePrompt(userPrompt);

    // Update toast
    toast.title = 'Prompt improved!';
    toast.message = `Quality: ${result.qualityScore.before.toFixed(1)} → ${result.qualityScore.after.toFixed(1)}`;
    toast.style = Toast.Style.Success;

    // Copy to clipboard
    await Clipboard.copy(result.improvedPrompt);

    // Show detailed result
    showToast({
      title: 'Improved prompt copied to clipboard',
      message: `Clarity: ${(result.metrics.clarity * 100).toFixed(0)}% | Completeness: ${(result.metrics.completeness * 100).toFixed(0)}% | Conciseness: ${(result.metrics.conciseness * 100).toFixed(0)}%`,
      style: Toast.Style.Success
    });

    // Optionally show in a list for comparison
    const listChoice = await confirm({
      title: 'Prompt Improved',
      message: 'View comparison?',
      primaryAction: {
        title: 'Show Comparison',
        onAction: () => {
          // Show side-by-side comparison
          // Implementation depends on your UI preference
        }
      }
    });

  } catch (error) {
    toast.title = 'Failed to improve prompt';
    toast.message = error instanceof Error ? error.message : 'Unknown error';
    toast.style = Toast.Style.Failure;
  }
}
```

---

## 5. Key Files Reference

### Source Repository Files

| File | Location | Purpose |
|------|----------|---------|
| `llmService.ts` | `/services/llmService.ts` | Multi-provider LLM service with prompt construction patterns |
| `promptOptimizationService.ts` | `/services/promptOptimizationService.ts` | Quality validation metrics and optimization logic |
| `OpenAIProvider.js` | `/backend/services/llm/providers/OpenAIProvider.js` | Chat API message structure pattern |
| `wizardService.ts` | `/services/wizardService.ts` | Structured prompt building and API integration |

### Key Code Patterns Found

1. **System/User Message Separation** (`OpenAIProvider.js:106-114`)
   ```javascript
   const response = await this.client.chat.completions.create({
     model,
     messages: [{ role: "user", content: prompt }],
     temperature: 0.7,
     stream: false,
   });
   ```

2. **Prompt Construction by Provider** (`llmService.ts:593-697`)
   ```typescript
   private constructPrompt(prompt: PlanData, model: LLMModel): string {
     switch (model.provider) {
       case "google":
         return this.constructGooglePrompt(prompt);
       case "openai":
         return this.constructOpenAIPrompt(prompt);
       case "anthropic":
         return this.constructAnthropicPrompt(prompt);
       default:
         return this.constructGenericPrompt(prompt);
     }
   }
   ```

3. **Quality Scoring** (`promptOptimizationService.ts:762-861`)
   - Clarity score based on length and keyword presence
   - Completeness score based on component detection
   - Conciseness score based on length penalties

---

## Summary of Recommendations

1. **Switch to `/api/chat` endpoint** - Critical for proper system/user separation
2. **Use messages array format** - Same structure as OpenAI's Chat Completions API
3. **Implement quality validation** - Use clarity/completeness/conciseness metrics
4. **Structure prompt output** - Use PlanData-style format (Objective, Role, Directive, Framework, Guardrails)
5. **Add error handling** - Check Ollama availability, handle timeouts gracefully

---

**Report Generated:** 2025-01-01
**Source Repository:** Architect v3.2.0
**Investigation Method:** Code pattern analysis and extraction
