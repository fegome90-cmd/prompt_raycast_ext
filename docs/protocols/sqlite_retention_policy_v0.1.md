# SQLite Retention Policy v0.1

**Date:** January 5, 2026
**Purpose:** Local analytics storage with Retention D7 support
**Status:** Executable policy

---

## 1. Policy Overview

**Principle:** Two-tier retention strategy balancing D7 calculation with DB size management.

**Tier 1 (0-14 days):** Keep ALL events (full fidelity)
**Tier 2 (14-30 days):** Thinning (keep critical events only)
**Tier 3 (>30 days):** Hard delete (all events + sessions)
**Aggregates (>30 days):** Keep only daily counters (DAU, retention D7, copy rate)

**Constraint:** Minimum 14-day window required for Retention D7 calculation.

**CRITICAL:** There is NO "forever" retention of raw events. Everything has a hard delete at 30 days except aggregated counters.

---

## 2. Schema Reference

```sql
CREATE TABLE installs (
    id TEXT PRIMARY KEY,              -- install_id (UUID v4, persistente)
    created_at INTEGER NOT NULL,      -- Unix timestamp ms
    last_seen INTEGER                 -- Unix timestamp ms (nullable)
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,              -- session_id (UUID v4)
    install_id TEXT NOT NULL,         -- FK to installs
    start_time INTEGER NOT NULL,      -- Unix timestamp ms
    end_time INTEGER,                 -- Unix timestamp ms (nullable)
    mode TEXT,                        -- "fast", "default"
    input_source TEXT,                -- "selection", "clipboard", "manual"
    output_length INTEGER,
    gate1_pass INTEGER,               -- 0 or 1
    gate2_pass INTEGER                -- 0 or 1
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,       -- Unix timestamp ms
    session_id TEXT NOT NULL,         -- FK to sessions
    event_type TEXT NOT NULL,         -- session_start, input_received, etc.
    metadata TEXT,                    -- JSON string (optional)
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE daily_metrics (
    date TEXT PRIMARY KEY,            -- ISO date string (YYYY-MM-DD)
    dau INTEGER NOT NULL,             -- Daily active users
    retention_d7 REAL,               -- Retention D7 percentage
    copy_rate REAL,                  -- Copy rate percentage
    avg_ttv_ms INTEGER,              -- Average TTV in ms
    total_sessions INTEGER,           -- Total sessions that day
    successful_copies INTEGER         -- Sessions with copy_triggered
);
```

---

## 3. Two-Tier Retention Strategy

### 3.1 Tier 1: Full Fidelity (0-14 days)

**Window:** Events from `now - 14 days` to `now`

**Action:** Keep all events

**Rationale:**
- Enables Retention D7 calculation (day 0 + days 1-7)
- Full diagnostic capability for recent sessions
- TTV analysis with full event timeline

**No action needed** - events retained as-is.

---

### 3.2 Tier 2: Event Thinning (14-30 days)

**Window:** Events from `now - 30 days` to `now - 14 days`

**Action:** Keep ONLY critical events

**Critical Events (keep):**
- `session_start` - Required for DAU, session counting
- `copy_triggered` - Required for copy rate calculation
- `error` - Required for debugging
- `session_end` - Required for session duration

**Non-Critical Events (delete):**
- `input_received` - Low value after 14 days
- `mode_selected` - Low value after 14 days
- `backend_request` - Low value after 14 days
- `backend_response` - Low value after 14 days

**SQL:**
```sql
-- Delete non-critical events older than 14 days
DELETE FROM events
WHERE timestamp < strftime('%s', 'now', '-14 days') * 1000
  AND event_type NOT IN ('session_start', 'copy_triggered', 'error', 'session_end');
```

**Space Savings:** ~50% (assuming 4 critical events out of 8 total per session)

---

### 3.3 Tier 3: Hard Delete + Aggregates (>30 days)

**Window:** Events older than 30 days

**Action:**
1. **Compute daily aggregates** before deleting
2. **Delete all events** older than 30 days
3. **Delete all sessions** older than 30 days
4. **Keep `installs` table** (user identification, never expires)
5. **Keep `daily_metrics` table** (aggregates, kept indefinitely)

**SQL:**
```sql
-- Step 1: Compute daily aggregates for day 30 (before deleting)
INSERT OR REPLACE INTO daily_metrics (date, dau, retention_d7, copy_rate, avg_ttv_ms, total_sessions, successful_copies)
SELECT
    strftime('%Y-%m-%d', datetime(s.start_time / 1000, 'unixepoch')) as date,
    COUNT(DISTINCT s.install_id) as dau,
    NULL,  -- retention_d7 computed separately (needs 7-day window)
    CAST(COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END) AS FLOAT) /
        NULLIF(COUNT(DISTINCT s.id), 0) * 100 as copy_rate,
    AVG(CASE WHEN e_copy.timestamp - s.start_time < 60000
        THEN e_copy.timestamp - s.start_time END) as avg_ttv_ms,
    COUNT(DISTINCT s.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END) as successful_copies
FROM sessions s
LEFT JOIN events e ON e.session_id = s.id AND e.event_type = 'session_start'
LEFT JOIN events e_copy ON e_copy.session_id = s.id AND e_copy.event_type = 'copy_triggered'
WHERE s.start_time >= strftime('%s', 'now', '-31 days') * 1000
  AND s.start_time < strftime('%s', 'now', '-30 days') * 1000
GROUP BY date;

-- Step 2: Delete all events older than 30 days
DELETE FROM events
WHERE timestamp < strftime('%s', 'now', '-30 days') * 1000;

-- Step 3: Delete orphaned sessions (older than 30 days)
DELETE FROM sessions
WHERE start_time < strftime('%s', 'now', '-30 days') * 1000;
```

**Space Savings:**
- Events >30 days: 100% deleted
- Sessions >30 days: 100% deleted
- Daily metrics: Minimal (~365 rows/year = ~20 KB/year)

**Steady State DB Size:**
- Events (0-30 days): ~240 KB
- Sessions (0-30 days): ~50 KB
- Daily metrics (indefinite): ~20 KB/year
- **Total: ~300 KB + 20 KB/year of usage**

---

## 4. Cleanup Schedule

### 4.1 Frequency

**Run:** Daily at user idle time (e.g., 3 AM local)

**Trigger:**
- Option A: Cron job (backend service)
- Option B: On app startup (if last cleanup >24h ago)

**Recommendation:** Option B (on startup) for simplicity

---

### 4.2 Complete Cleanup Script

**File:** `api/cleanup_analytics.py`

```python
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path.home() / "Library/Application Support/raycast-ext/analytics.db"

def cleanup_analytics():
    """Run two-tier cleanup strategy with aggregates"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tier 2: Thin non-critical events (14-30 days old)
    cursor.execute("""
        DELETE FROM events
        WHERE timestamp < ?
          AND event_type NOT IN ('session_start', 'copy_triggered', 'error', 'session_end')
    """, (int((datetime.now() - timedelta(days=14)).timestamp() * 1000),))

    tier2_deleted = cursor.rowcount

    # Tier 3: Compute daily aggregates BEFORE deleting
    day_30_start = int((datetime.now() - timedelta(days=31)).timestamp() * 1000)
    day_30_end = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

    cursor.execute("""
        INSERT OR REPLACE INTO daily_metrics (
            date, dau, retention_d7, copy_rate, avg_ttv_ms, total_sessions, successful_copies
        )
        SELECT
            strftime('%Y-%m-%d', datetime(s.start_time / 1000, 'unixepoch')),
            COUNT(DISTINCT s.install_id),
            NULL,  -- retention_d7 computed separately
            CAST(COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END) AS FLOAT) /
                NULLIF(COUNT(DISTINCT s.id), 0) * 100,
            AVG(CASE WHEN e_copy.timestamp - s.start_time < 60000
                THEN e_copy.timestamp - s.start_time END),
            COUNT(DISTINCT s.id),
            COUNT(DISTINCT CASE WHEN e.event_type = 'copy_triggered' THEN s.id END)
        FROM sessions s
        LEFT JOIN events e ON e.session_id = s.id AND e.event_type = 'session_start'
        LEFT JOIN events e_copy ON e_copy.session_id = s.id AND e_copy.event_type = 'copy_triggered'
        WHERE s.start_time >= ? AND s.start_time < ?
        GROUP BY strftime('%Y-%m-%d', datetime(s.start_time / 1000, 'unixepoch'))
    """, (day_30_start, day_30_end))

    aggregates_computed = cursor.rowcount

    # Tier 3: Hard delete old events (>30 days)
    cursor.execute("""
        DELETE FROM events
        WHERE timestamp < ?
    """, (int((datetime.now() - timedelta(days=30)).timestamp() * 1000),))

    tier3_events_deleted = cursor.rowcount

    # Delete orphaned sessions
    cursor.execute("""
        DELETE FROM sessions
        WHERE start_time < ?
    """, (int((datetime.now() - timedelta(days=30)).timestamp() * 1000),))

    tier3_sessions_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "tier2_deleted": tier2_deleted,
        "aggregates_computed": aggregates_computed,
        "tier3_events_deleted": tier3_events_deleted,
        "tier3_sessions_deleted": tier3_sessions_deleted
    }

if __name__ == "__main__":
    result = cleanup_analytics()
    print(f"Cleanup complete: {result}")
```

---

## 5. DB Size Management

### 5.1 Estimated DB Size

**Assumptions:**
- Average session: 8 events
- Average event: 200 bytes
- Sessions per day: 10 (moderate usage)
- Daily metric row: ~100 bytes

**Calculations:**

| Component | Days | Rows | Size (KB) |
|-----------|------|------|-----------|
| Events (full fidelity) | 0-14 | 1,120 | 224 |
| Events (thinned) | 14-30 | ~480 | 96 |
| Sessions | 0-30 | 300 | 60 |
| Daily metrics | Indefinite | 365/year | 36/year |
| **Total steady state** | - | - | **~380 KB + 36 KB/year** |

**After 1 year of usage:** ~380 KB + 36 KB = ~416 KB

**After 5 years of usage:** ~380 KB + 180 KB = ~560 KB

**No unbounded growth** - events/sessions have hard 30-day delete

---

### 5.2 DB Size Triggers

**Check:** After each cleanup run

**Thresholds:**

| DB Size | Action |
|---------|--------|
| <10 MB | Normal operation |
| 10-50 MB | Warning in logs |
| >50 MB | Aggressive cleanup (reduce Tier 2 to 7 days) |

**Aggressive Cleanup SQL:**
```sql
-- If DB >50MB, reduce Tier 2 window to 7 days
DELETE FROM events
WHERE timestamp < strftime('%s', 'now', '-7 days') * 1000
  AND event_type NOT IN ('session_start', 'copy_triggered', 'error', 'session_end');
```

---

## 6. Metric Calculations

### 6.1 DAU (Daily Active Users)

**Definition:** Number of `install_id` unique with session in last 24h

**SQL:**
```sql
SELECT COUNT(DISTINCT s.install_id) as dau
FROM sessions s
WHERE s.start_time > strftime('%s', 'now', '-1 day') * 1000;
```

**Window:** Uses `sessions.start_time`, NOT `events.timestamp` (more efficient)

---

### 6.2 Retention D7

**Definition:** % of users who returned in days 1-7 after day 0

**SQL:**
```sql
WITH day0_users AS (
    SELECT DISTINCT install_id
    FROM sessions
    WHERE start_time >= strftime('%s', 'now', '-7 days') * 1000
      AND start_time < strftime('%s', 'now', '-6 days') * 1000
),
returning_users AS (
    SELECT DISTINCT s.install_id
    FROM sessions s
    JOIN day0_users d0 ON s.install_id = d0.install_id
    WHERE s.start_time >= strftime('%s', 'now', '-6 days') * 1000
      AND s.start_time < strftime('%s', 'now', '-1 days') * 1000
)
SELECT
    CAST(COUNT(DISTINCT returning_users.install_id) AS FLOAT) /
    CAST(NULLIF(COUNT(DISTINCT day0_users.install_id), 0) AS FLOAT) * 100
    AS retention_d7
FROM day0_users, returning_users;
```

**Required:** 14-day window (day 0 + days 1-7)

---

### 6.3 TTV (Time-to-Value)

**Definition:** `t_copy - t_start` per session

**SQL:**
```sql
SELECT
    s.id as session_id,
    (e_copy.timestamp - s.start_time) as ttv_ms
FROM sessions s
JOIN events e_start ON e_start.session_id = s.id AND e_start.event_type = 'session_start'
JOIN events e_copy ON e_copy.session_id = s.id AND e_copy.event_type = 'copy_triggered'
WHERE e_copy.timestamp - s.start_time < 60000  -- Within 60s
ORDER BY ttv_ms;
```

**P95 Calculation:** Application-level (sort and pick 95th percentile)

---

## 7. Export Functionality

### 7.1 Manual Export Command

**CLI:** `npm run export-analytics -- --days 14 --output analytics.jsonl`

**Implementation:**
```python
import json
import sqlite3
from datetime import datetime, timedelta

def export_analytics(days: int, output_path: str):
    """Export events to JSONL"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.timestamp, e.session_id, e.event_type, e.metadata
        FROM events e
        WHERE e.timestamp >= ?
        ORDER BY e.timestamp
    """, (int((datetime.now() - timedelta(days=days)).timestamp() * 1000),))

    with open(output_path, 'w') as f:
        for row in cursor.fetchall():
            timestamp, session_id, event_type, metadata = row
            record = {
                "timestamp": timestamp,
                "session_id": session_id,
                "event_type": event_type,
                "metadata": json.loads(metadata) if metadata else {}
            }
            f.write(json.dumps(record) + '\n')

    conn.close()
```

---

## 8. Privacy & Security

### 8.1 Data Storage

**Location:** `~/Library/Application Support/raycast-ext/analytics.db` (macOS)

**Access:** User-only (permissions: 600)

**Opt-out:** User can delete DB file at any time

---

### 8.2 No Telemetry

**Policy:** No data sent to external servers

**Export:** Manual user-initiated action only

**Sharing:** User-controlled (user decides to share exported data)

---

## 9. Testing

### 9.1 Test Cases

| Test | Expected Result |
|------|-----------------|
| Insert 100 sessions, run cleanup | 100 sessions remain (<14 days) |
| Insert sessions 40 days old, run cleanup | Old sessions deleted |
| Check DB size after 30 days | <1 MB (with thinning) |
| Calculate DAU with 5 users today | Returns 5 |
| Calculate Retention D7 with 3 returning | Returns ~43% (3/7) |

---

### 9.2 Test Script

**File:** `tests/test_retention_policy.py`

```python
import pytest
import sqlite3
from api.cleanup_analytics import cleanup_analytics

def test_tier2_thinning():
    """Test that non-critical events are deleted after 14 days"""
    # Insert test data
    # Run cleanup
    # Assert non-critical events deleted, critical kept
    pass

def test_tier3_hard_delete():
    """Test that all events deleted after 30 days"""
    pass

def test_retention_d7_calculation():
    """Test Retention D7 SQL query"""
    pass

def test_dau_calculation():
    """Test DAU SQL query"""
    pass
```

---

## 10. Rollout Plan

### Phase 1: Schema Setup (Week 1)

- [ ] Create `analytics.db` on first run
- [ ] Create tables (installs, sessions, events)
- [ ] Generate `install_id` if not exists

### Phase 2: Event Tracking (Week 1-2)

- [ ] Instrument session_start
- [ ] Instrument input_received, mode_selected
- [ ] Instrument backend_request, backend_response
- [ ] Instrument copy_triggered, error, session_end

### Phase 3: Cleanup Implementation (Week 2)

- [ ] Implement cleanup_analytics()
- [ ] Run on app startup (if >24h since last run)
- [ ] Log cleanup results

### Phase 4: Export & Metrics (Week 2-3)

- [ ] Implement export_analytics()
- [ ] Implement DAU query
- [ ] Implement Retention D7 query
- [ ] Implement TTV query

---

**v0.1 Policy - Ready for implementation**
