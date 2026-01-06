# SQLite Persistence Implementation Checklist

**Project:** DSPy Prompt Improver
**Date:** 2026-01-04
**Path:** `/Users/felipe_gonzalez/Developer/raycast_ext`

---

## Phase 1: Preparation ✅

- [ ] **Review architecture analysis**
  - [ ] Read `sqlite-persistence-analysis.md`
  - [ ] Review visual diagrams in `sqlite-persistence-architecture.md`
  - [ ] Understand hexagonal architecture principles

- [ ] **Verify current state**
  - [ ] Confirm no existing persistence layer
  - [ ] Check HemDov structure: `domain/`, `infrastructure/`, `interfaces.py`
  - [ ] Verify FastAPI + DSPy setup is working

- [ ] **Set up environment**
  - [ ] Create backup of current code
  - [ ] Create new branch for persistence feature
  - [ ] Ensure `.env` file exists

---

## Phase 2: Domain Layer ✅

### 2.1 Domain Entities
- [ ] Create `hemdov/domain/entities/__init__.py`
- [ ] Create `hemdov/domain/entities/prompt_history.py`
  - [ ] `BackendType` enum (ZERO_SHOT, FEW_SHOT)
  - [ ] `PromptHistory` frozen dataclass
  - [ ] `__post_init__` validation
  - [ ] `quality_score` property
  - [ ] Test immutability

### 2.2 Repository Interfaces
- [ ] Create `hemdov/domain/repositories/__init__.py`
- [ ] Create `hemdov/domain/repositories/prompt_repository.py`
  - [ ] `PromptRepository` abstract base class
  - [ ] `save()` method
  - [ ] `find_by_id()` method
  - [ ] `find_recent()` method with pagination
  - [ ] `find_by_date_range()` method
  - [ ] `get_statistics()` method
  - [ ] `delete_old()` method
  - [ ] Custom exceptions (`RepositoryError`, `RepositoryConnectionError`, `RepositoryConstraintError`)

---

## Phase 3: Infrastructure Layer ✅

### 3.1 Configuration
- [ ] Edit `hemdov/infrastructure/config/__init__.py`
  - [ ] Add `SQLITE_ENABLED: bool = True`
  - [ ] Add `SQLITE_DB_PATH: str = "data/prompt_history.db"`
  - [ ] Add `SQLITE_POOL_SIZE: int = 1`
  - [ ] Add `SQLITE_RETENTION_DAYS: int = 30`
  - [ ] Add `SQLITE_AUTO_CLEANUP: bool = True`
  - [ ] Add `SQLITE_ASYNC_ENABLED: bool = True`
  - [ ] Add `SQLITE_WAL_MODE: bool = True`

### 3.2 Repository Implementation
- [ ] Create `hemdov/infrastructure/persistence/__init__.py`
- [ ] Create `hemdov/infrastructure/persistence/sqlite_prompt_repository.py`
  - [ ] `SQLitePromptRepository` class
  - [ ] `__init__(settings)` constructor
  - [ ] `_get_connection()` with aiosqlite
  - [ ] `_initialize_schema()` with migrations
  - [ ] `save()` implementation
  - [ ] `find_by_id()` implementation
  - [ ] `find_recent()` implementation
  - [ ] `find_by_date_range()` implementation
  - [ ] `get_statistics()` implementation
  - [ ] `delete_old()` implementation
  - [ ] `_row_to_entity()` helper
  - [ ] WAL mode enabled
  - [ ] Proper error handling
  - [ ] Comprehensive logging

---

## Phase 4: Dependency Injection ✅

- [ ] Edit `hemdov/interfaces.py`
  - [ ] Add `register_factory()` method to `Container`
  - [ ] Add `register_singleton()` method to `Container`
  - [ ] Update `get()` to support factories
  - [ ] Add `clear()` method for testing
  - [ ] Test factory lazy initialization

---

## Phase 5: Application Integration ✅

### 5.1 Main Application
- [ ] Edit `main.py`
  - [ ] Import `PromptRepository` and `SQLitePromptRepository`
  - [ ] Add repository initialization to `lifespan()`
  - [ ] Register repository factory in container
  - [ ] Create `data/` directory if missing
  - [ ] Run auto-cleanup on startup if enabled
  - [ ] Add `/health/repository` endpoint
  - [ ] Test graceful initialization failure

### 5.2 API Endpoint
- [ ] Edit `api/prompt_improver_api.py`
  - [ ] Import `PromptRepository`, `RepositoryError`, `PromptHistory`, `BackendType`
  - [ ] Add circuit breaker state variables
  - [ ] Create `get_settings()` dependency
  - [ ] Create `get_repository()` dependency with circuit breaker
  - [ ] Update `improve_prompt()` to accept dependencies
  - [ ] Add latency measurement
  - [ ] Create `PromptHistory` entity
  - [ ] Save to repository async (non-blocking)
  - [ ] Implement `_save_history_async()` function
  - [ ] Add circuit breaker logic
  - [ ] Add comprehensive error handling
  - [ ] Add logging for all operations

---

## Phase 6: Configuration ✅

### 6.1 Dependencies
- [ ] Edit `requirements.txt`
  - [ ] Add `aiosqlite>=0.19.0`
  - [ ] Run `pip install aiosqlite>=0.19.0`

### 6.2 Environment Variables
- [ ] Edit `.env`
  - [ ] Add `SQLITE_ENABLED=true`
  - [ ] Add `SQLITE_DB_PATH=data/prompt_history.db`
  - [ ] Add `SQLITE_POOL_SIZE=1`
  - [ ] Add `SQLITE_RETENTION_DAYS=30`
  - [ ] Add `SQLITE_AUTO_CLEANUP=true`
  - [ ] Add `SQLITE_ASYNC_ENABLED=true`
  - [ ] Add `SQLITE_WAL_MODE=true`

---

## Phase 7: Testing ✅

### 7.1 Unit Tests
- [ ] Create `tests/test_sqlite_prompt_repository.py`
  - [ ] `test_save_prompt_history`
  - [ ] `test_find_by_id`
  - [ ] `test_find_recent_with_filtering`
  - [ ] `test_find_by_date_range`
  - [ ] `test_get_statistics`
  - [ ] `test_delete_old_histories`
  - [ ] `test_repository_connection_error`
  - [ ] Use pytest fixtures for test DB
  - [ ] Clean up test databases

### 7.2 Integration Tests
- [ ] Create `tests/test_prompt_improver_api_integration.py`
  - [ ] `test_improve_prompt_with_persistence`
  - [ ] `test_improve_prompt_without_persistence`
  - [ ] `test_health_check_endpoint`
  - [ ] `test_circuit_breaker_trips`
  - [ ] `test_graceful_degradation`

### 7.3 Manual Testing
- [ ] Start server: `python main.py`
- [ ] Test health check: `curl http://localhost:8000/health/repository`
- [ ] Test prompt improvement: `curl -X POST http://localhost:8000/api/v1/improve-prompt -H "Content-Type: application/json" -d '{"idea": "Test"}'`
- [ ] Verify database created: `ls -lh data/`
- [ ] Query database: `sqlite3 data/prompt_history.db "SELECT COUNT(*) FROM prompt_history;"`
- [ ] Test with persistence disabled: `SQLITE_ENABLED=false python main.py`
- [ ] Verify schema: `sqlite3 data/prompt_history.db ".schema prompt_history"`
- [ ] Check indexes: `sqlite3 data/prompt_history.db ".indexes"`

---

## Phase 8: Documentation ✅

- [ ] Update `README.md` with persistence info
- [ ] Document API endpoints
- [ ] Add troubleshooting guide
- [ ] Create database backup procedures
- [ ] Document configuration options
- [ ] Add monitoring guidelines

---

## Phase 9: Production Readiness ✅

### 9.1 Monitoring
- [ ] Set up logging aggregation
- [ ] Create dashboards for repository metrics
- [ ] Set up alerts for high error rates
- [ ] Monitor database size
- [ ] Monitor circuit breaker trips

### 9.2 Backup Strategy
- [ ] Create backup script: `scripts/backup_db.sh`
- [ ] Set up cron job for daily backups
- [ ] Test backup restoration
- [ ] Document backup retention policy

### 9.3 Performance
- [ ] Benchmark repository operations
- [ ] Optimize indexes based on query patterns
- [ ] Monitor save latency
- [ ] Tune cache sizes if needed
- [ ] Test under load

### 9.4 Security
- [ ] Set proper file permissions on `data/` directory
- [ ] Validate database paths (prevent path traversal)
- [ ] Sanitize user input before storage
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Review data retention policy

---

## Phase 10: Deployment ✅

### 10.1 Staging
- [ ] Deploy to staging environment
- [ ] Enable persistence with `SQLITE_ENABLED=true`
- [ ] Monitor for 1 week
- [ ] Check logs for errors
- [ ] Verify database growth rate
- [ ] Test circuit breaker (simulate failures)

### 10.2 Production
- [ ] Create production database backup
- [ ] Deploy with `SQLITE_ENABLED=false` initially
- [ ] Monitor for 24 hours
- [ ] Enable persistence: `SQLITE_ENABLED=true`
- [ ] Monitor closely for 1 week
- [ ] Rollback plan ready if issues arise

---

## Verification Checklist ✅

### Architecture Compliance
- [ ] Domain entities in `hemdov/domain/entities/`
- [ ] Repository interfaces in `hemdov/domain/repositories/`
- [ ] Implementation in `hemdov/infrastructure/persistence/`
- [ ] No infrastructure imports in domain layer
- [ ] Domain entities are frozen (immutable)
- [ ] Repository pattern properly implemented

### Error Handling
- [ ] Custom exceptions defined
- [ ] Circuit breaker implemented
- [ ] Graceful degradation working
- [ ] API works without repository
- [ ] Proper logging at all levels

### Performance
- [ ] Async operations (aiosqlite)
- [ ] Non-blocking saves
- [ ] WAL mode enabled
- [ ] Indexes created
- [ ] Connection pooling configured

### Configuration
- [ ] All settings in `.env`
- [ ] Feature flag (`SQLITE_ENABLED`) works
- [ ] Database path configurable
- [ ] Retention days configurable
- [ ] Auto-cleanup configurable

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual tests pass
- [ ] Error scenarios tested
- [ ] Performance benchmarks run

### Documentation
- [ ] Code is commented
- [ ] README updated
- [ ] API documentation current
- [ ] Troubleshooting guide exists
- [ ] Backup procedures documented

---

## Rollback Plan 🔄

If critical issues arise:

1. **Disable persistence immediately**
   ```bash
   export SQLITE_ENABLED=false
   # Restart application
   ```

2. **Database is corrupt**
   ```bash
   # Restore from backup
   cp data/prompt_history.db.backup data/prompt_history.db
   # Restart application
   ```

3. **Performance degradation**
   ```bash
   # Disable persistence
   # Analyze slow queries
   # Add missing indexes
   # Re-enable when fixed
   ```

4. **Complete rollback**
   ```bash
   # Revert to previous commit
   git revert <commit-hash>
   # Restart application
   ```

---

## Success Criteria ✅

The implementation is successful when:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] API response time is unchanged (<5ms overhead)
- [ ] Repository saves don't block responses
- [ ] Circuit breaker prevents cascading failures
- [ ] API works even when database fails
- [ ] Database grows at expected rate
- [ ] Auto-cleanup prevents unbounded growth
- [ ] Health check reports accurate status
- [ ] Logs contain useful debugging info
- [ ] No security vulnerabilities
- [ ] Documentation is complete
- [ ] Backup strategy is tested
- [ ] Team is trained on troubleshooting

---

## Estimated Timeline

- **Phase 1-2 (Domain Layer):** 2-4 hours
- **Phase 3 (Infrastructure):** 4-6 hours
- **Phase 4 (DI):** 1-2 hours
- **Phase 5 (Integration):** 2-4 hours
- **Phase 6 (Config):** 1 hour
- **Phase 7 (Testing):** 4-6 hours
- **Phase 8 (Documentation):** 2-3 hours
- **Phase 9 (Production Prep):** 3-4 hours
- **Phase 10 (Deployment):** 2-3 hours

**Total Estimated Time:** 21-33 hours (3-4 days)

---

## Quick Commands Reference

```bash
# Install dependency
pip install aiosqlite>=0.19.0

# Create data directory
mkdir -p data

# Start server
python main.py

# Test health check
curl http://localhost:8000/health/repository

# Test prompt improvement
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "Design a REST API", "context": "FastAPI"}'

# Query database
sqlite3 data/prompt_history.db "SELECT * FROM prompt_history ORDER BY timestamp DESC LIMIT 10;"

# Check schema
sqlite3 data/prompt_history.db ".schema"

# Check indexes
sqlite3 data/prompt_history.db ".indexes"

# Get statistics
sqlite3 data/prompt_history.db "SELECT backend, COUNT(*) FROM prompt_history GROUP BY backend;"

# Manual cleanup
sqlite3 data/prompt_history.db "DELETE FROM prompt_history WHERE timestamp < datetime('now', '-30 days');"

# Check database size
du -h data/prompt_history.db

# Vacuum database
sqlite3 data/prompt_history.db "VACUUM;"

# Backup database
cp data/prompt_history.db data/prompt_history.db.backup.$(date +%Y%m%d)

# Run tests
pytest tests/ -v

# Run with persistence disabled
SQLITE_ENABLED=false python main.py

# Kill server
pkill -f "python main.py"
```

---

**Last Updated:** 2026-01-04
**Version:** 1.0.0
**Status:** Ready for Implementation ✅
