# Runbook

> Deployment, monitoring, and troubleshooting for DSPy Prompt Improver

**Last Updated:** 2026-02-14

## Service Overview

| Service | Port | Type | Health Endpoint |
|---------|------|------|-----------------|
| FastAPI Backend | 8000 | Python | `GET /health` |
| Raycast Extension | - | TypeScript | N/A (desktop app) |

## Deployment

### Local Development

```bash
# Start backend
make dev

# Verify
make health

# Start frontend
cd dashboard && npm run dev
```

### PM2 Production

```bash
# Initial setup
pm2 start ecosystem.config.cjs

# Subsequent starts
pm2 start all

# Management
pm2 stop all
pm2 restart all
pm2 save          # Save process list
pm2 resurrect     # Restore saved list
```

### Health Check

```bash
# Quick check
curl -s http://localhost:8000/health | python3 -m json.tool

# Using make
make health

# Full status
make status
```

Expected response:
```json
{
  "status": "healthy",
  "llm_provider": "anthropic",
  "model": "claude-haiku-4-5-20251001",
  "sqlite_enabled": true
}
```

## Monitoring

### Backend Logs

```bash
# Tail logs
make logs

# Or directly
tail -f .logs/backend.log

# PM2 logs
pm2 logs raycast-backend-8000
```

### Raycast Dev Server Logs

```bash
make ray-logs

# Or directly
tail -f dashboard/.raycast/dev-server.log
```

### Status Checks

```bash
# Backend status
make status

# Raycast dev server status
make ray-status

# PM2 status
pm2 status
```

## Troubleshooting

### Backend Not Responding

**Symptom:** `curl: (7) Failed to connect to localhost port 8000`

**Diagnosis:**
```bash
make status
# Check if process is running
ps aux | grep "api/main.py"
# Check port usage
lsof -i :8000
```

**Resolution:**
```bash
# Stop any stale processes
make stop

# Restart
make dev

# Verify
make health
```

### LLM Provider Errors

**Anthropic API Errors:**

| Error | Cause | Resolution |
|-------|-------|------------|
| 401 Unauthorized | Invalid API key | Check `ANTHROPIC_API_KEY` in .env |
| 429 Rate Limited | Too many requests | Wait and retry, or upgrade plan |
| 500/503 API Error | Provider issue | Check status.anthropic.com |

**Ollama Errors:**

| Error | Cause | Resolution |
|-------|-------|------------|
| Connection refused | Ollama not running | `ollama serve` |
| Model not found | Model not pulled | `ollama pull <model>` |

**Resolution:**
```bash
# Test Anthropic connection
curl -s http://localhost:8000/health

# Test Ollama connection
curl -s http://localhost:11434/api/tags
```

### SQLite Issues

**Symptom:** Database locked or corruption errors

**Diagnosis:**
```bash
# Check database file
ls -la data/prompt_history.db

# Check WAL mode
sqlite3 data/prompt_history.db "PRAGMA journal_mode;"
```

**Resolution:**
```bash
# Disable WAL if issues persist
# In .env: SQLITE_WAL_MODE=false

# Recreate database (WARNING: loses history)
rm data/prompt_history.db
make restart
```

### Timeout Errors

**Symptom:** `Error: timed out` after 120s

**Diagnosis:**
- Check `ANTHROPIC_TIMEOUT` in .env
- Verify frontend timeout matches (dashboard/package.json)

**Resolution:**
```bash
# Increase timeout in .env
ANTHROPIC_TIMEOUT=180

# Restart backend
make restart
```

### Raycast Extension Issues

**"DSPy backend not available"**

**Diagnosis:**
```bash
# Check localhost permission
make ray-check

# Verify backend is running
make health
```

**Resolution:**
1. Ensure `package.json` has `"localhost": true`
2. Restart Raycast dev server: `make ray-dev`

**Safe Mode Activated**

**Symptom:** Toast "Invalid Configuration - Using safe mode"

**Resolution:**
1. Check Raycast Console.app for logs
2. Verify `package.json` has valid values
3. Restart Raycast app

### DSPy Compilation Errors

**Symptom:** Few-shot compilation fails

**Diagnosis:**
```bash
# Test few-shot
make test-fewshot

# Check training data
ls -la datasets/exports/unified-fewshot-pool.json
```

**Resolution:**
```bash
# Regenerate training data
make regen-all

# Test again
make test-fewshot
```

## Degradation Flags

When optional features fail, the API includes `degradation_flags`:

```json
{
  "improved_prompt": "...",
  "degradation_flags": {
    "metrics_failed": false,
    "knn_disabled": false,
    "complex_strategy_disabled": false
  }
}
```

**Actions:**
- `metrics_failed`: Quality scoring unavailable, prompt still valid
- `knn_disabled`: Falling back to zero-shot mode
- `complex_strategy_disabled`: Using simple improvement strategy

## Error Response Format

```json
{
  "error": {
    "type": "ValueError",
    "message": "Invalid input format",
    "details": "Expected JSON with 'idea' field"
  }
}
```

### HTTP Error Mapping

| Status | Frontend Action |
|--------|-----------------|
| 400 | Show validation error |
| 404 | Show "not found" with retry |
| 422 | Show field-specific errors |
| 503 | Enable Ollama fallback |
| 504 | Show timeout with retry |
| 500 | Show generic error, log details |

## Recovery Procedures

### Full Service Restart

```bash
# Stop everything
pm2 stop all
make stop

# Clear stale files
make clean

# Restart
make dev
pm2 start all

# Verify
make health
make status
```

### Database Recovery

```bash
# Backup existing
cp data/prompt_history.db data/prompt_history.db.backup

# If corrupted, delete and restart
rm data/prompt_history.db
make restart

# Verify new database created
ls -la data/prompt_history.db
```

### Configuration Reset

```bash
# Backup existing
cp .env .env.backup

# Reset to defaults
cp .env.example .env

# Edit with your keys
nano .env

# Restart
make restart
```

## Alerts and Thresholds

### Quality Gates

| Metric | Target | Alert If |
|--------|--------|----------|
| JSON Valid Pass 1 | >=54% | < 50% |
| Copyable Rate | >=54% | < 50% |
| Latency P95 | <=12s | > 15s |

### System Health

| Metric | Target | Alert If |
|--------|--------|----------|
| Backend Uptime | 99.9% | < 99% |
| Response Time P95 | <3s | > 5s |
| Error Rate | <1% | > 5% |

## Contact and Escalation

1. Check logs: `make logs`
2. Check health: `make health`
3. Review this runbook
4. Check provider status pages:
   - Anthropic: https://status.anthropic.com
   - OpenAI: https://status.openai.com
5. Review `docs/backend/README.md` for architecture details

## Related Documentation

- Contributing Guide: `docs/CONTRIB.md`
- Backend Architecture: `docs/backend/README.md`
- API Error Handling: `docs/api-error-handling.md`
- Frontend Guide: `dashboard/CLAUDE.md`
