# SQLite Persistence Architecture - Visual Diagrams

## Current Architecture (Without Persistence)

```
┌─────────────────────────────────────────────────────────────┐
│                         Raycast Extension                    │
│                    (TypeScript Frontend)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP POST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                       (main.py)                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              HemDov Container                          │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Settings (pydantic-settings)                   │  │  │
│  │  │  - LLM_PROVIDER                                 │  │  │
│  │  │  - LLM_MODEL                                    │  │  │
│  │  │  - API_HOST, API_PORT                           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           API Router (/api/v1/improve-prompt)         │  │
│  │                                                         │  │
│  │  1. Validate input                                     │  │
│  │  2. Get PromptImprover module (lazy loading)           │  │
│  │  3. Execute: improver(idea, context)                   │  │
│  │  4. Return response                                    │  │
│  │     ❌ NO PERSISTENCE - PROMPT IS LOST                 │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ DSPy LM calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    HemDov Domain Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PromptImprover (DSPy Module)              │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  dspy.Signature                                 │  │  │
│  │  │  - InputField: original_idea, context           │  │  │
│  │  │  - OutputField: improved_prompt, role, ...      │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  dspy.Predict                                   │  │  │
│  │  │  - forward() method                             │  │  │
│  │  │  - Calls LLM via DSPy LM                        │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  HemDov Infrastructure Layer                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           LiteLLM Adapter                             │  │
│  │  - create_anthropic_adapter()                         │  │
│  │  - create_gemini_adapter()                            │  │
│  │  - create_openai_adapter()                            │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     External LLM API                         │
│  (Anthropic Haiku 4.5 / Gemini / OpenAI / DeepSeek)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Proposed Architecture (With SQLite Persistence)

```
┌─────────────────────────────────────────────────────────────┐
│                         Raycast Extension                    │
│                    (TypeScript Frontend)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP POST /api/v1/improve-prompt
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                       (main.py)                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              HemDov Container (Extended)               │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Settings (pydantic-settings)                   │  │  │
│  │  │  - LLM_PROVIDER, LLM_MODEL                       │  │  │
│  │  │  - SQLITE_ENABLED = true                         │  │  │
│  │  │  - SQLITE_DB_PATH = "data/prompt_history.db"     │  │  │
│  │  │  - SQLITE_RETENTION_DAYS = 30                    │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Repository Factory (lazy initialization)        │  │  │
│  │  │  - Creates SQLitePromptRepository               │  │  │
│  │  │  - Singleton pattern                             │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           API Router (/api/v1/improve-prompt)         │  │
│  │                                                         │  │
│  │  1. Validate input                                     │  │
│  │  2. Get PromptImprover module                         │  │
│  │  3. Measure start_time                                │  │
│  │  4. Execute: improver(idea, context)                  │  │
│  │  5. Calculate latency_ms                              │  │
│  │  6. Create PromptHistory entity                       │  │
│  │  7. Save to repository (async, non-blocking)          │  │
│  │  8. Return response                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
                │ DSPy calls                    │ Async save
                ▼                               ▼
┌───────────────────────────┐   ┌─────────────────────────────────────┐
│     HemDov Domain Layer   │   │    HemDov Domain Layer (NEW)        │
│                           │   │                                     │
│  ┌─────────────────────┐  │   │  ┌───────────────────────────────┐ │
│  │  PromptImprover     │  │   │  │  Domain Entities               │ │
│  │  (DSPy Module)      │  │   │  │  ┌─────────────────────────┐   │ │
│  │                     │  │   │  │  │ PromptHistory (dataclass)│   │ │
│  │  - forward()        │  │   │  │  │ - id, timestamp          │   │ │
│  │  - Returns result   │  │   │  │  │ - original_idea, context │   │ │
│  └─────────────────────┘  │   │  │  │ - improved_prompt, ...   │   │ │
└───────────────────────────┘   │  │  │ - backend, confidence     │   │ │
                                │  │  │ - latency_ms              │   │ │
                                │  │  │ - quality_score (property)│   │ │
                                │  │  └─────────────────────────┘   │ │
                                │  │                                 │ │
                                │  │  ┌──────────────────────────────┐ │ │
                                │  │  │ Repository Interfaces        │ │ │
                                │  │  │  ┌────────────────────────┐  │ │ │
                                │  │  │  │ PromptRepository (ABC)│  │ │ │
                                │  │  │  │ - save()              │  │ │ │
                                │  │  │  │ - find_by_id()        │  │ │ │
                                │  │  │  │ - find_recent()       │  │ │ │
                                │  │  │  │ - get_statistics()    │  │ │ │
                                │  │  │  │ - delete_old()        │  │ │ │
                                │  │  │  └────────────────────────┘  │ │ │
                                │  │  └──────────────────────────────┘ │ │
                                │  └───────────────────────────────────┘ │
                                └─────────────────────────────────────┘
                                                        │
                                                        │ Depends on
                                                        ▼
                                ┌─────────────────────────────────────┐
                                │  HemDov Infrastructure Layer (NEW)  │
                                │                                     │
                                │  ┌───────────────────────────────┐  │
                                │  │ Persistence Layer             │  │
                                │  │  ┌─────────────────────────┐  │  │
                                │  │  │SQLitePromptRepository   │  │  │
                                │  │  │ - aiosqlite for async   │  │  │
                                │  │  │ - WAL mode enabled      │  │  │
                                │  │  │ - Connection pooling    │  │  │
                                │  │  │ - Error handling        │  │  │
                                │  │  │ - Schema migrations     │  │  │
                                │  │  └─────────────────────────┘  │  │
                                │  └───────────────────────────────┘  │
                                └─────────────────────┬───────────────┘
                                                      │
                                                      ▼
                                ┌─────────────────────────────────────┐
                                │     SQLite Database                 │
                                │  ┌───────────────────────────────┐  │
                                │  │ prompt_history table          │  │
                                │  │ - id (PK)                     │  │
                                │  │ - timestamp (indexed)         │  │
                                │  │ - original_idea, context      │  │
                                │  │ - improved_prompt, ...        │  │
                                │  │ - backend, confidence         │  │
                                │  │ - latency_ms                  │  │
                                │  │ - CHECK constraints           │  │
                                │  └───────────────────────────────┘  │
                                │                                     │
                                │  Indexes:                           │
                                │  - idx_timestamp (DESC)             │
                                │  - idx_backend                     │
                                │  - idx_quality (confidence, lat)   │
                                └─────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    API Endpoint Request                      │
│              POST /api/v1/improve-prompt                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ Check SQLITE_ENABLED flag │
                └─────────┬─────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
         YES│                           │NO
            ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│ Check Circuit Breaker│    │ Skip persistence     │
│                      │    │ (proceed without DB) │
└─────────┬────────────┘    └──────────────────────┘
          │
    ┌─────┴─────┐
    │           │
  OPEN│        CLOSED│
    ▼           ▼
┌────────┐  ┌──────────────────┐
│ Skip   │  │ Get repository   │
│ DB     │  │ from container   │
└────────┘  └────────┬─────────┘
                     │
                     ▼
          ┌───────────────────────┐
          │ Save PromptHistory    │
          │ (async background)    │
          └───────────┬───────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
      SUCCESS│               FAILURE│
          │                       │
          ▼                       ▼
  ┌───────────────┐    ┌──────────────────────┐
  │ Reset failure │    │ Increment failure    │
  │ counter to 0  │    │ counter              │
  └───────────────┘    └────────┬─────────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
            Failure count < 5    Failure count >= 5
                        │                 │
                        ▼                 ▼
                ┌───────────┐    ┌───────────────────┐
                │ Log error │    │ Trip circuit       │
                └───────────┘    │ breaker            │
                                 │ Disable repo for   │
                                 │ 5 minutes          │
                                 └───────────────────┘
```

---

## Dependency Injection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Startup                      │
│                      (main.py)                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ Initialize HemDov Container│
                └───────────┬───────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ Register Settings         │
                │ container.register(       │
                │   Settings, settings      │
                │ )                         │
                └───────────┬───────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ Check SQLITE_ENABLED      │
                └───────────┬───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
             YES│                       │NO
                ▼                       ▼
    ┌───────────────────┐      ┌────────────────┐
    │ Register factory  │      │ Skip repository│
    │ container.register│      │ registration   │
    │ _factory(         │      └────────────────┘
    │   PromptRepository│
    │   lambda:         │
    │     SQLitePrompt  │
    │     Repository(   │
    │       settings    │
    │     )             │
    │ )                 │
    └─────────┬─────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Runtime Request Flow                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ API endpoint needs repo   │
                │ repository = container.get│
                │   (PromptRepository)      │
                └───────────┬───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
          Factory exists        Factory already ran
                │                  (singleton cached)
                ▼                       │
    ┌───────────────────┐              │
    │ Execute factory   │              │
    │ Create SQLitePrompt│             │
    │ Repository instance│             │
    │                   │              │
    │ - Initialize DB   │              │
    │ - Create schema   │              │
    │ - Set up indexes  │              │
    └─────────┬─────────┘              │
              │                        │
              └────────────┬───────────┘
                           │
                           ▼
              ┌───────────────────────────┐
              │ Cache as singleton        │
              │ container._singletons[    │
              │   PromptRepository       │
              │ ] = instance             │
              └───────────┬───────────────┘
                          │
                          ▼
              ┌───────────────────────────┐
              │ Return instance to caller│
              └───────────────────────────┘
```

---

## Data Flow Diagram

```
User Request Flow:

┌──────┐   POST   ┌────────┐   Parse   ┌──────────┐
│Raycast├────────>│ FastAPI├──────────>│ Pydantic │
│Client│          │        │ <─────────│ Request  │
└──────┘          └───┬────┘           └──────────┘
                      │
                      │ Validate
                      ▼
              ┌───────────────┐
              │ PromptImprover│
              │ (DSPy Module) │
              └───────┬───────┘
                      │
                      │ Call LLM
                      ▼
              ┌───────────────┐
              │  Anthropic    │
              │  Haiku 4.5    │
              └───────┬───────┘
                      │
                      │ Return result
                      ▼
              ┌───────────────┐
              │ Calculate     │
              │ latency_ms    │
              └───────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        │ Create PromptHistory      │
        │ (domain entity)           │
        │                           │
        │ ┌─────────────────────┐   │
        │ │ id=None             │   │
        │ │ timestamp=now()     │   │
        │ │ original_idea="..." │   │
        │ │ improved_prompt=".."│   │
        │ │ backend="zero-shot" │   │
        │ │ confidence=0.87     │   │
        │ │ latency_ms=1500     │   │
        │ └─────────────────────┘   │
        └─────────────┬─────────────┘
                      │
                      │ asyncio.create_task()
                      │ (non-blocking)
                      ▼
              ┌───────────────┐
              │ Save to       │
              │ Repository    │
              └───────┬───────┘
                      │
                      │ repository.save()
                      ▼
              ┌───────────────┐
              │ SQLitePrompt  │
              │ Repository    │
              └───────┬───────┘
                      │
                      │ INSERT INTO prompt_history
                      ▼
              ┌───────────────┐
              │ SQLite DB     │
              │ (data/*.db)   │
              └───────┬───────┘
                      │
                      │ Returns history with ID
                      ▼
              ┌───────────────┐
              │ Log success   │
              └───────────────┘

┌─────────────────────────────────────┐
│     Meanwhile (parallel path)       │
│                                     │
│  ┌───────────────┐                  │
│  │ Return HTTP   │                  │
│  │ Response to   │                  │
│  │ Raycast       │                  │
│  │ (don't wait   │                  │
│  │  for DB save) │                  │
│  └───────────────┘                  │
└─────────────────────────────────────┘
```

---

## Hexagonal Architecture Layers

```
┌───────────────────────────────────────────────────────────────┐
│                     HEXAGONAL ARCHITECTURE                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 DOMAIN LAYER (Core)                     │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  Business Logic (DSPy Modules)                    │  │  │
│  │  │  - PromptImprover                                  │  │  │
│  │  │  - PromptImproverWithFewShot                       │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  Domain Entities (NEW)                            │  │  │
│  │  │  - PromptHistory (frozen dataclass)               │  │  │
│  │  │  - BackendType (Enum)                             │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  Repository Interfaces (NEW)                      │  │  │
│  │  │  - PromptRepository (ABC)                         │  │  │
│  │  │  - RepositoryError, RepositoryConnectionError     │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                            ▲ DEPENDS ON                        │
│                            │ (inverted)                        │
│  ┌─────────────────────────┴─────────────────────────────┐    │
│  │                 INFRASTRUCTURE LAYER                   │    │
│  │  ┌───────────────────────────────────────────────────┐│    │
│  │  │  Adapters (External Integrations)                 ││    │
│  │  │  - LiteLLM Adapter                                 ││    │
│  │  │    - create_anthropic_adapter()                    ││    │
│  │  │    - create_gemini_adapter()                       ││    │
│  │  │  - SQLite Repository Implementation (NEW)         ││    │
│  │  │    - SQLitePromptRepository                        ││    │
│  │  │    - aiosqlite for async                           ││    │
│  │  │    - Schema migrations                             ││    │
│  │  └───────────────────────────────────────────────────┘│    │
│  │  ┌───────────────────────────────────────────────────┐│    │
│  │  │  Configuration (Settings)                         ││    │
│  │  │  - LLM settings                                    ││    │
│  │  │  - SQLite settings (NEW)                          ││    │
│  │  │    - SQLITE_ENABLED                                ││    │
│  │  │    - SQLITE_DB_PATH                                ││    │
│  │  │    - SQLITE_RETENTION_DAYS                         ││    │
│  │  └───────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                            ▲ DEPENDS ON                        │
│                            │ (inverted)                        │
│  ┌─────────────────────────┴─────────────────────────────┐    │
│  │                 INTERFACES LAYER (DI)                 │    │
│  │  ┌───────────────────────────────────────────────────┐│    │
│  │  │  HemDov Container (Dependency Injection)           ││    │
│  │  │  - register(interface, implementation)            ││    │
│  │  │  - register_factory(interface, factory) (NEW)     ││    │
│  │  │  - get(interface) -> instance                      ││    │
│  │  └───────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                            ▲ DEPENDS ON                        │
│                            │                                   │
│  ┌─────────────────────────┴─────────────────────────────┐    │
│  │                 API LAYER (FastAPI)                   │    │
│  │  ┌───────────────────────────────────────────────────┐│    │
│  │  │  Routes / Endpoints                                ││    │
│  │  │  - POST /api/v1/improve-prompt                     ││    │
│  │  │    - Depends(get_settings)                         ││    │
│  │  │    - Depends(get_repository) (NEW)                ││    │
│  │  │  - GET /health/repository (NEW)                    ││    │
│  │  └───────────────────────────────────────────────────┘│    │
│  │  ┌───────────────────────────────────────────────────┐│    │
│  │  │  Application (main.py)                            ││    │
│  │  │  - lifespan() context manager                     ││    │
│  │  │    - Initialize DSPy LM                           ││    │
│  │  │    - Register repository factory (NEW)            ││    │
│  │  │  - CORS middleware                                ││    │
│  │  └───────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘

DEPENDENCY RULE:
  - Dependencies ALWAYS point inward (toward domain)
  - Domain layer has NO dependencies on infrastructure
  - Infrastructure implements interfaces defined in domain
  - API layer orchestrates everything through DI container
```

---

## Error Recovery Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Repository Save Error                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Exception caught in   │
                │ _save_history_async() │
                └───────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
    RepositoryConnectionError   Other RepositoryError
                │                       │
                │                       │
                ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ Log: WARNING     │    │ Log: WARNING     │
    │ "Connection      │    │ "Repository      │
    │  failed"         │    │  error"          │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             │                       │
             ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ Increment        │    │ Increment        │
    │ failure_counter  │    │ failure_counter  │
    │ (global)         │    │ (global)         │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             │                       │
             ▼                       ▼
    ┌────────────────────────────────────────┐
    │ Check: failure_counter >= 5?           │
    └────────────┬───────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
        YES             NO
         │               │
         ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│ Trip circuit     │  │ Continue         │
│ breaker          │  │ (retry on next   │
│                  │  │  request)        │
│ Set:             │  └──────────────────┘
│  _REPOSITORY_    │
│  DISABLED_UNTIL  │
│  = now() + 5min  │
│                  │
│ Log: ERROR       │
│ "Circuit breaker│
│  tripped"        │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Next 5 minutes:  │
│                  │
│ All requests     │
│ skip persistence │
│ (no DB calls)    │
│                  │
│ Log: INFO        │
│ "Repository      │
│  disabled due    │
│  to circuit      │
│  breaker"        │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ After 5 minutes: │
│                  │
│ Next request     │
│ checks circuit   │
│ breaker state    │
│                  │
│ If passed,       │
│ reset:           │
│  failure_counter │
│  = 0             │
│  disabled_until  │
│  = None          │
└──────────────────┘
```

---

## Performance Optimization Strategies

```
┌─────────────────────────────────────────────────────────────┐
│              Latency Breakdown (Target: <100ms)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
    ┌────┴────┐                          ┌─────┴─────┐
    │ DSPy    │                          │ Repository│
    │ Module  │                          │ Save      │
    │         │                          │           │
    │ ~1-3s   │                          │ ~5-15ms   │
    │ (LLM    │                          │           │
    │  call)  │                          │           │
    └────┬────┘                          └─────┬─────┘
         │                                     │
         │                                     │
         ▼                                     ▼
  ┌───────────────┐                  ┌──────────────┐
  │ OPTIMIZATION: │                  │ OPTIMIZATION:│
  │ Few-shot      │                  │ Async save   │
  │ caching       │                  │ (non-blocking│
  │               │                  │  to response) │
  │ - Compile once│                  │              │
  │ - Cache demos │                  │              │
  │ - Result:     │                  │              │
  │   500ms       │                  │              │
  └───────────────┘                  └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Repository Optimization                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Current: ~5-15ms      │
                │ per save              │
                └───────────┬───────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                     │
    ┌───┴────┐                          ┌─────┴────┐
    │ Read   │                          │ Write    │
    │ Heavy  │                          │ Heavy    │
    │        │                          │          │
    │ OPTIMIZE:                    │ OPTIMIZE: │
    │ - Cache stats                │ - Buffer  │
    │   (TTL=60s)                  │   writes  │
    │ - LRU cache for             │   in memory│
    │   recent queries            │ - Flush   │
    │ - Result:                   │   every   │
    │   <1ms (cached)             │   5s or   │
    │                              │   100 recs│
    │                              │ - Result: │
    │                              │   Batch   │
    │                              │   writes  │
    └──────────────────────────────────────────┘
```

---

## Monitoring and Observability

```
┌─────────────────────────────────────────────────────────────┐
│                   Metrics Collection                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌───────────────┐       ┌──────────────┐
        │ API Metrics   │       │ DB Metrics   │
        │               │       │              │
        │ - Request     │       │ - Save       │
        │   count       │       │   latency    │
        │ - Response    │       │ - Error rate │
        │   time (p50,  │       │ - Connection │
        │   p95, p99)   │       │   pool       │
        │ - Backend     │       │ - Row count  │
        │   distribution│       │ - DB size    │
        │ - Confidence  │       │ - Index hit  │
        │   scores      │       │   rate       │
        └───────┬───────┘       └──────┬───────┘
                │                       │
                │                       │
                ▼                       ▼
        ┌───────────────────────────────────────┐
        │       Prometheus / Grafana            │
        │   (Optional - future enhancement)     │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │         Health Check Endpoints        │
        │                                       │
        │  GET /health                          │
        │   - LLM provider status               │
        │   - Model version                     │
        │                                       │
        │  GET /health/repository (NEW)         │
        │   - Persistence enabled?              │
        │   - Total records                     │
        │   - Database path                     │
        │   - Connection status                 │
        └───────────────────────────────────────┘
```

---

This visual architecture document complements the detailed analysis in
`sqlite-persistence-analysis.md` by providing diagrams for:

1. Current vs proposed architecture
2. Error handling and circuit breaker flow
3. Dependency injection patterns
4. Data flow through the system
5. Hexagonal architecture layer boundaries
6. Error recovery strategies
7. Performance optimization strategies
8. Monitoring and observability

Use these diagrams to communicate the design to stakeholders and guide implementation.
