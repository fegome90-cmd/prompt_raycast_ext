"""Database schema migrations for prompt history and NLaC API."""

SCHEMA_VERSION = 2

# ============================================================================
# TABLE: prompt_history (legacy)
# ============================================================================

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    original_idea TEXT NOT NULL,
    context TEXT DEFAULT '',
    improved_prompt TEXT NOT NULL,
    role TEXT NOT NULL,
    directive TEXT NOT NULL,
    framework TEXT NOT NULL,
    guardrails TEXT NOT NULL,
    reasoning TEXT,
    confidence REAL,
    backend TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    latency_ms INTEGER,

    CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    CHECK(latency_ms IS NULL OR latency_ms >= 0)
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_created_at ON prompt_history(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_backend ON prompt_history(backend);",
    "CREATE INDEX IF NOT EXISTS idx_provider ON prompt_history(provider);",
    "CREATE INDEX IF NOT EXISTS idx_confidence ON prompt_history(confidence);",
]

# ============================================================================
# TABLES: NLaC API (Natural Language as Code)
# ============================================================================

NLAC_TABLES_SQL = """
-- Tabla Maestra: prompts
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,              -- UUID v4
    version TEXT NOT NULL,
    intent_type TEXT NOT NULL,        -- 'generate', 'debug', 'refactor', 'explain'
    template TEXT NOT NULL,
    strategy_meta JSON,               -- Metadata: strategy used, complexity, etc.
    constraints JSON,                 -- Restricciones: max_tokens, format, etc.
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Casos de Prueba: test_cases
CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    input_context TEXT,
    expected_output TEXT,
    test_type TEXT,                   -- 'unit', 'integration', 'e2e'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
);

-- Historial OPRO: opro_trajectory
CREATE TABLE IF NOT EXISTS opro_trajectory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    iteration_number INTEGER NOT NULL,
    meta_prompt_used TEXT,
    generated_instruction TEXT,
    score REAL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    UNIQUE(prompt_id, iteration_number)
);

-- Cache de Prompts: prompt_cache
CREATE TABLE IF NOT EXISTS prompt_cache (
    cache_key TEXT PRIMARY KEY,        -- SHA256(idea + context + mode)
    prompt_id TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id)
);
"""

NLAC_INDEXES_SQL = [
    # Prompts table indexes
    "CREATE INDEX IF NOT EXISTS idx_prompts_intent_type ON prompts(intent_type);",
    "CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_prompts_created_at ON prompts(created_at DESC);",
    # test_cases table indexes
    "CREATE INDEX IF NOT EXISTS idx_test_cases_prompt_id ON test_cases(prompt_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_cases_type ON test_cases(test_type);",
    # opro_trajectory table indexes
    "CREATE INDEX IF NOT EXISTS idx_opro_prompt_id ON opro_trajectory(prompt_id);",
    "CREATE INDEX IF NOT EXISTS idx_opro_iteration ON opro_trajectory(iteration_number);",
    "CREATE INDEX IF NOT EXISTS idx_opro_prompt_iteration ON opro_trajectory(prompt_id, iteration_number);",
    "CREATE INDEX IF NOT EXISTS idx_opro_score ON opro_trajectory(score DESC);",
    # prompt_cache table indexes
    "CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON prompt_cache(last_accessed DESC);",
    "CREATE INDEX IF NOT EXISTS idx_cache_hit_count ON prompt_cache(hit_count DESC);",
]

async def run_migrations(conn):
    """Run database migrations to latest version."""
    # Create legacy prompt_history table
    await conn.execute(CREATE_TABLE_SQL)

    # Create legacy indexes
    for index_sql in CREATE_INDEXES_SQL:
        await conn.execute(index_sql)

    # Create NLaC tables (v2)
    await conn.executescript(NLAC_TABLES_SQL)

    # Create NLaC indexes
    for index_sql in NLAC_INDEXES_SQL:
        await conn.execute(index_sql)

    # Store schema version
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_info (version INTEGER PRIMARY KEY)"
    )
    await conn.execute(
        f"INSERT OR REPLACE INTO schema_info (version) VALUES ({SCHEMA_VERSION})"
    )
