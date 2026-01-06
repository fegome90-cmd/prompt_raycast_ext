# Pipeline Architecture Overview

Complete understanding of the DSPy Prompt Improver system components and their interactions.

---

## 1. DSPy Framework

**Role:** Few-shot learning compiler and prompt optimization framework

**What it does:**
- Takes raw user ideas (original_idea + context)
- Finds similar examples from ComponentCatalog using **KNN vector similarity**
- Compiles optimized prompts using the Architect pattern
- Returns structured outputs with role, directive, framework, guardrails

**Key files:**
- `hemdov/domain/dspy_modules/prompt_improver.py` - DSPy signature definition
- `eval/src/dspy_prompt_improver_fewshot.py` - KNNFewShot implementation
- `main.py` - Backend integration with LM configuration

**Interaction with ComponentCatalog:**
```python
# DSPy uses ComponentCatalog as training data
KNNFewShot(
    k=3,  # Find 3 most similar examples
    trainset=ComponentCatalog.examples  # 109+ curated examples
)
```

---

## 2. LLM (Haiku)

**Role:** Primary prompt generation engine

**Configuration:**
- **Model:** `claude-haiku-4-5-20251001`
- **Provider:** Anthropic via LiteLLM adapter
- **Temperature:** `0.0` (maximum consistency)
- **Timeout:** `120s` (Haiku takes 30-50s per request)
- **Fallback:** Ollama, Gemini, OpenAI

**What Haiku does:**
- Receives few-shot examples + user input
- Generates improved prompt following Architect pattern
- Returns structured response (role, directive, framework, guardrails)

**Flow:**
```
User Input → DSPy (KNN finds examples) → Haiku (with few-shot) → Improved Prompt
```

---

## 3. Dataset (Few-Shot Pool)

**Role:** Curated training data for few-shot learning

**Location:** `datasets/exports/unified-fewshot-pool-v2.json`

**Structure:**
```json
{
  "examples": [
    {
      "input": {
        "original_idea": "Create a REST API",
        "context": "For todo app"
      },
      "output": {
        "improved_prompt": "# Role\nYou are an API Architect...",
        "role": "API Architect",
        "directive": "Design RESTful endpoints",
        "framework": "decomposition",
        "guardrails": ["Include error handling", "Document endpoints"]
      },
      "metadata": {
        "domain": "Backend",
        "quality_score": 0.95,
        "framework": "decomposition"
      }
    }
    // ... 108 more examples
  ]
}
```

**Generation process:**
1. Run DSPy PromptImprover on training cases
2. Merge ComponentCatalog + prompts.json + SQLite exports
3. Normalize components and validate quality
4. Deduplicate by input-output hashes

**Domains covered:** Security, DevOps, Architecture, Frontend, Backend, Data Science

---

## 4. SQL Database (SQLite)

**Role:** Persistence layer for history and caching

**Location:** SQLite database with WAL mode, 64MB cache

**Key tables:**

### prompt_history
Stores all prompt improvement sessions:
- `original_idea` - User's raw input
- `improved_prompt` - Generated result
- `llm_provider` - Haiku, Ollama, etc.
- `confidence_score` - Quality metric (0-1)
- `latency_ms` - Performance tracking
- `created_at` - Timestamp

### prompt_cache
Caches improved prompts to avoid redundant API calls:
- `cache_key` - SHA256(idea + context + mode)
- `prompt_id` - Reference to prompt
- `improved_prompt` - Cached result
- `hit_count` - Usage tracking
- `last_accessed` - Cache management

### NLaC tables
- `nlac_prompts` - Template storage
- `nlac_test_cases` - Evaluation data
- `nlac_trajectories` - OPRO optimization history

**Repository layer:** Async operations with automatic migrations

---

## 5. NLaC (Natural Language as Code)

**Role:** Structured prompt optimization through iterative refinement

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│  NLaC Pipeline (without ComponentCatalog)              │
├─────────────────────────────────────────────────────────┤
│  1. IntentClassifier → debug/refactor/generate/explain  │
│  2. ComplexityAnalyzer → SIMPLE/MODERATE/COMPLEX        │
│  3. NLaCBuilder → Role injection (MultiAIGCD)           │
│  4. RaR (complex only) → Rephrase and Respond          │
│  5. OPOROptimizer → 3 iterations, early stopping       │
│  6. PromptValidator → IFEval validation + autocorrect   │
│  7. PromptCache → SHA256-based caching                  │
└─────────────────────────────────────────────────────────┘
```

**Services:**

| Service | Purpose | Current Implementation |
|---------|---------|------------------------|
| IntentClassifier | Route requests by intent | Keyword + semantic rules |
| ComplexityAnalyzer | Categorize input complexity | Token count, technical terms |
| NLaCBuilder | Construct PromptObject | Role hierarchy + RaR |
| OPOROptimizer | Iterative refinement | Meta-prompt evolution |
| PromptValidator | Quality validation | IFEval constraints check |
| PromptCache | Performance | SHA256 key → SQLite |

**Role Injection (MultiAIGCD):**
```
SIMPLE    → Developer
MODERATE  → Senior Developer
COMPLEX   → Software Engineer + RaR
```

**Current limitation:** Does NOT use ComponentCatalog for few-shot examples

---

## Pipeline Flow Comparison

### DSPy Legacy Flow
```
User Input
    ↓
DSPy KNN → Find 3 similar examples from ComponentCatalog
    ↓
Haiku (with few-shot examples)
    ↓
Improved Prompt (Architect pattern)
    ↓
SQLite Cache
```

### NLaC Flow (Current)
```
User Input
    ↓
IntentClassifier + ComplexityAnalyzer
    ↓
NLaCBuilder (role injection, NO few-shot)
    ↓
OPOROptimizer (3 iterations)
    ↓
PromptValidator (IFEval)
    ↓
Improved Prompt (structured)
    ↓
SQLite Cache
```

### Proposed Integrated Flow
```
User Input
    ↓
IntentClassifier + ComplexityAnalyzer
    ↓
DSPy KNN → Find examples from ComponentCatalog
    ↓
NLaCBuilder (role injection + few-shot examples)
    ↓
OPOROptimizer (examples as reference)
    ↓
PromptValidator (IFEval)
    ↓
Improved Prompt (best of both worlds)
    ↓
SQLite Cache
```

---

## Key Insight

**Current Problem:** NLaC doesn't use the 109 curated examples in ComponentCatalog

**Solution:** Integrate ComponentCatalog into NLaCBuilder as few-shot injection point

**Benefits:**
- NLaC gets real-world examples (not just templates)
- DSPy KNN provides semantic similarity search
- OPRO optimizes using proven patterns as baseline
- System maintains "memory" of successful prompts
