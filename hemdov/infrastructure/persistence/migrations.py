"""Database schema migrations for prompt history."""

SCHEMA_VERSION = 1

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

async def run_migrations(conn):
    """Run database migrations to latest version."""
    # Create table
    await conn.execute(CREATE_TABLE_SQL)

    # Create indexes
    for index_sql in CREATE_INDEXES_SQL:
        await conn.execute(index_sql)

    # Store schema version
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_info (version INTEGER PRIMARY KEY)"
    )
    await conn.execute(
        f"INSERT OR REPLACE INTO schema_info (version) VALUES ({SCHEMA_VERSION})"
    )
