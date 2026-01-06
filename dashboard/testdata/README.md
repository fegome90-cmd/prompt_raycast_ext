# Testdata (manual)

Casos de prueba manuales para validar:
- `Prompt Improver (Local)` → `Improve Prompt (Ollama)`

## Cómo usar

1. Abre Raycast → `Prompt Improver (Local)`.
2. Pega `input` desde `testdata/prompt-improver-cases.json`.
3. Ejecuta `Improve Prompt (Ollama)` (`⌘↵`) y revisa:
   - el texto copiado es un prompt “pasteable”
   - no contiene meta-instrucciones (“output rules”, “json schema”, etc.)
   - no contiene preguntas (van a `Clarifying Questions` en el preview)
4. Repite con diferentes inputs para medir consistencia.
