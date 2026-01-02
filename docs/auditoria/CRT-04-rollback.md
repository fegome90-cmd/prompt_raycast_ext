# CRT-04 Rollback Procedure

If issues arise with DeepSeek, use this procedure to revert to Ollama.

## Quick Rollback

```bash
# 1. Stop backend
# Ctrl+C in the terminal where main.py is running

# 2. Restore Ollama configuration
cd /Users/felipe_gonzalez/Developer/raycast_ext
cp .env.backup.ollama .env

# 3. Verify Ollama is running
ollama list

# 4. Restart backend
python main.py
```

## Verify Rollback

```bash
curl http://localhost:8000/health
# Should show: "provider": "ollama"
```

## Troubleshooting

If rollback fails:

1. **Check Ollama status:**
   ```bash
   ollama ps
   ```

2. **Check model availability:**
   ```bash
   ollama list | grep Novaeus
   ```

3. **Pull model if needed:**
   ```bash
   ollama pull hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M
   ```

## Re-applying DeepSeek

After rollback, to re-apply DeepSeek:

```bash
# Option 1: Use git to restore DeepSeek configuration
git checkout HEAD -- .env

# Option 2: Manually update .env
# Set LLM_PROVIDER=deepseek and DEEPSEEK_API_KEY=sk-...
```

## Notes

- Backup file location: `.env.backup.ollama`
- This backup was created on 2026-01-02 during DeepSeek migration
- Rollback should be instantaneous - just restart the backend after swapping .env
