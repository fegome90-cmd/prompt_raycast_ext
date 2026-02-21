# P0 Engine Stabilization WorkOrders Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan step-by-step.

## Goal
Cerrar P0 del motor de Prompt Improver antes de reactivar NLaC en produccion, manteniendo `executionMode` operativo siempre.

## Guardrails
- Mantener `executionMode` operativo de extremo a extremo.
- No activar cambios de producto NLaC hasta cerrar y medir P0.
- Priorizar reversibilidad y evidencia (tests + verificaciones) sobre velocidad.
- No paralelizar WOs con dependencias compartidas.

## WO Summary Table
| WO | P0 | Dependency | Risk | Effort | Exit State |
|---|---|---|---|---|---|
| WO-001 | P0-1 executionMode real | None | High | 4-6h | Frontend envia `mode` real (`legacy`/`nlac`) al backend |
| WO-002 | P0-2 persistencia framework | WO-001 | High | 3-5h | `prompt_history` persiste en todos los casos validos |
| WO-003 | P0-3 observabilidad persistencia | WO-002 | Medium | 3-4h | Fallas de persistencia quedan visibles y medibles |

---

## WO-001 - Propagacion real de executionMode

### P0 Reference
P0-1

### Scope (in/out)
- In: eliminar hardcode `legacy` en cliente DSPy y respetar `mode` desde `improvePromptWithHybrid`.
- In: cubrir con tests unitarios e integracion de frontend.
- Out: cualquier cambio de UX de comandos o activacion de rollout NLaC.

### Affected Files
- Modify: `dashboard/src/core/llm/dspyPromptImprover.ts`
- Modify: `dashboard/src/core/llm/improvePrompt.ts`
- Modify/Add: `dashboard/src/core/llm/__tests__/dspyPromptImprover.test.ts`
- Modify/Add: `dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts`

### Implementation Approach (step-by-step)
1. Escribir test que falle demostrando que `mode=nlac` llega al payload HTTP del cliente DSPy.
2. Ejecutar test aislado y confirmar fallo.
3. Cambiar `dspyPromptImprover.ts` para usar `request.mode ?? "legacy"` en body/log.
4. Revisar `improvePrompt.ts` para asegurar que `args.options.mode` se propaga sin override.
5. Añadir tripwire E2E: assert no solo del body `mode`, sino del enrutamiento efectivo (`strategy` en respuesta backend) para `legacy` y `nlac`.
6. Si falta señal explícita de enrutamiento, agregar campo técnico mínimo (`effective_mode`) en respuesta API solo para observabilidad interna/tests.
7. Ejecutar suite de tests de LLM frontend + test backend de enrutamiento.
8. Documentar comportamiento esperado en comentarios puntuales del cliente DSPy.

### Test Strategy
- Unit:
  - `cd dashboard && npm run test -- src/core/llm/__tests__/dspyPromptImprover.test.ts`
  - `cd dashboard && npm run test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`
- Integration (frontend core):
  - `cd dashboard && npm run test -- src/core/llm/__tests__/integration-fetch.test.ts`
- Backend integration:
  - `pytest tests/test_api_integration.py -k "mode or strategy" -v`
- Manual:
  - Llamar comando Improve Prompt con `executionMode=legacy` y `executionMode=nlac`.
  - Verificar en respuesta backend `strategy` coherente por modo (tripwire de realidad).
  - Verificar en logs backend `Mode: legacy` / `Mode: nlac`.

### Exit Criteria
- Payload HTTP incluye `mode` real elegido.
- Respuesta backend evidencia enrutamiento real por modo (`strategy`/`effective_mode`).
- Logs backend muestran el `mode` correcto por request.
- Tests nuevos pasan y previenen regresion.

### Risk Assessment
- Riesgo: romper compatibilidad de defaults.
- Mitigacion: default explicito `legacy` cuando `mode` no venga definido.

### Rollback Procedure
- Revert commit de WO-001.
- Verificar que tests vuelven al estado previo y backend recibe `legacy` por defecto.

### Verification Commands
- `cd dashboard && npm run test -- src/core/llm/__tests__/dspyPromptImprover.test.ts`
- `cd dashboard && npm run test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`
- `cd dashboard && npm run test`

### Observability Checkpoints
- Log cliente DSPy incluye `mode` enviado.
- Log backend `Mode: ... | Strategy: ...` consistente por request.
- Tripwire: mismatch `mode != effective route` falla tests.

### Dependencies
- None.

### Estimated Effort
4-6 horas.

---

## WO-002 - Persistencia robusta de prompt_history (framework normalization)

### P0 Reference
P0-2

### Scope (in/out)
- In: normalizar `framework` de salida del modelo a enum permitido antes de crear `PromptHistory`.
- In: pruebas backend para persistencia en escenarios con `framework` libre.
- Out: rediseño de entidad de dominio o cambios de schema DB.

### Affected Files
- Modify: `api/prompt_improver_api.py`
- Modify/Add: `tests/test_prompt_improver_api_exception_handling.py`
- Add: `tests/test_prompt_history_framework_normalization.py`
- (Opcional si aplica) Modify: `hemdov/domain/entities/prompt_history.py` solo si se decide fallback controlado de dominio.

### Implementation Approach (step-by-step)
1. Escribir test backend que reproduzca fallo actual: framework tipo `"Decomposition: ..."` no persiste.
2. Ejecutar test y validar fallo.
3. Implementar helper de normalizacion en API (`normalize_framework_for_history`).
4. Usar heuristica determinista por tokens (contains): `decomp`, `chain|cot`, `tree|tot`, `role`.
5. Si no hay match, fallback seguro a `decomposition` y log warning estructurado con `framework_raw`.
6. Aplicar normalizacion unicamente en ruta de persistencia (no mutar respuesta al cliente en esta WO).
7. Contabilizar fallback de framework (counter/metric si existe; si no, al menos señal log estructurada).
8. Ejecutar tests backend relevantes.

### Test Strategy
- Unit:
  - `make test` filtrando nuevos tests si aplica (pytest -k normalization).
- Integration API:
  - POST `/api/v1/improve-prompt` con backend real y verificar incremento en `prompt_history`.
- Manual DB:
  - `sqlite3 data/prompt_history.db "select count(*) from prompt_history;"` antes/despues.

### Exit Criteria
- Requests validos incrementan `prompt_history` consistentemente.
- No se observan `ValueError` por framework en persistencia.
- Fallback de normalizacion deja evidencia trazable (`framework_raw`, frecuencia de fallback).
- Tests de normalizacion pasan.

### Risk Assessment
- Riesgo: normalizacion incorrecta distorsiona analitica de framework.
- Mitigacion: mapeo determinista + warning cuando use fallback.

### Rollback Procedure
- Revert commit de normalizacion.
- Re-ejecutar tests para volver al comportamiento previo.

### Verification Commands
- `make test`
- `make health`
- `sqlite3 data/prompt_history.db "select count(*) from prompt_history;"`

### Observability Checkpoints
- Warning estructurado en fallback de framework.
- Log de persistencia exitosa por request.
- Query de verificacion de fallback en logs disponible para operacion.

### Dependencies
- Depende de WO-001 completado (modo real ayuda trazabilidad de analitica).

### Estimated Effort
3-5 horas.

---

## WO-003 - Observabilidad de fallas de persistencia

### P0 Reference
P0-3

### Scope (in/out)
- In: exponer y registrar fallas de persistencia con señales accionables.
- In: degradacion explicitamente trazable para operaciones.
- Out: dashboards externos complejos; solo hooks y evidencia local/API.

### Affected Files
- Modify: `api/prompt_improver_api.py`
- Modify: `api/main.py` (si se agrega instrumentacion de startup/health relacionada)
- Add/Modify: `tests/test_prompt_improver_api_exception_handling.py`
- Add: `tests/test_api_integration.py` casos de persistencia degradada
- Optional docs: `docs/RUNBOOK.md` (seccion de degradacion persistencia)

### Implementation Approach (step-by-step)
1. Definir señal de degradacion para persistencia (ej. `persistence_failed`).
2. Añadir logging estructurado en `_save_history_async` con `event="persistence_failed"`, `request_id`, `backend`, `mode`, `error_type`, `latency_ms`.
3. Asegurar que falla de persistencia no rompe respuesta, pero queda auditable.
4. Si hay repositorio de metricas operativo, registrar contador persistente `persistence_failed_total`; si no, mantener log estructurado como fuente oficial.
5. Extender pruebas para fallos de DB simulados y validar bandera/log/evento.
6. Añadir comando operativo de deteccion (runbook): `rg -n "persistence_failed" logs`.
7. Validar manualmente forzando error de persistencia (path invalido o mock de exception).

### Test Strategy
- Unit:
  - pruebas de manejo de excepciones y degradacion.
- Integration:
  - test API con fallo de persistencia simulado y respuesta HTTP 200 + señal de degradacion.
- Manual:
  - revisar logs backend durante error inducido.

### Exit Criteria
- Falla de persistencia deja traza clara en logs y señal de degradacion.
- Respuesta funcional al usuario se mantiene estable.
- Pruebas de error path pasan.
- Deteccion operativa reproducible con comando/documentacion.

### Risk Assessment
- Riesgo: ruido excesivo en logs.
- Mitigacion: logs estructurados con niveles adecuados (`warning` vs `error`).

### Rollback Procedure
- Revert cambios de observabilidad.
- Confirmar que flujo funcional base sigue estable.

### Verification Commands
- `make test`
- `make health`
- `make dev` (ver logs)
- `rg -n "persistence_failed" /tmp/hemdov.log` (o log file configurado)

### Observability Checkpoints
- Evento de falla contiene contexto minimo: `error_type`, `backend`, `mode`, `latency_ms`.
- Señal de degradacion detectable en respuesta o trazas segun diseño final.

### Dependencies
- Depende de WO-002.

### Estimated Effort
3-4 horas.

---

## Final Integration Validation Plan (legacy vs nlac)

### Preconditions
- WO-001/002/003 cerrados.
- Backend healthy (`make health`).
- Sin activar cambios de producto NLaC (solo validacion tecnica controlada).

### Dataset and Runs
1. Ejecutar dataset en `legacy`:
- `cd dashboard && npm run eval -- --dataset testdata/cases.jsonl --backend dspy --output eval/p0-legacy.json`
2. Ejecutar dataset en `nlac`:
- `cd dashboard && npm run eval -- --dataset testdata/cases.jsonl --backend dspy --output eval/p0-nlac.json`
  Nota: confirmar que `mode` se propaga real en esta ruta de eval; si no, ejecutar benchmark API directo por modo.

### Metrics to compare
- Latencia: p50, p95.
- Calidad: jsonValidPass1, copyableRate, reviewRate.
- Persistencia: incremento de `prompt_history` durante corrida.
- Degradacion: tasa de `persistence_failed` (debe tender a 0).
- Real routing: distribucion de `strategy/effective_mode` coherente con modo ejecutado.

### SQL Checks
- `sqlite3 data/prompt_history.db "select count(*) from prompt_history;"`
- `sqlite3 data/prompt_history.db "select backend, count(*) from prompt_history group by backend;"`

### Reality Gate (must-have)
1. En cada corrida de eval, validar que `prompt_history` aumenta en `N` (o `N - allowed_failures` documentado).
2. Validar `persistence_failed` = 0 (o <= 0.5%) con evidencia en logs/metrica.
3. Validar que distribucion de modo real coincide con corrida:
   - corrida `legacy`: no entradas `effective_mode=nlac` (o `strategy=nlac`)
   - corrida `nlac`: no entradas `effective_mode=legacy` para requests de prueba.

### Release Decision Gate
- Mantener NLaC sin activacion de producto si cualquiera de estas falla:
  - p95 > 90s en entorno objetivo.
  - tasa de persistencia fallida > 0.5%.
  - calidad (`jsonValidPass1`) por debajo de baseline legacy acordado.

### Recommended commit cadence
- 1 commit por WO (o 2 si test+impl estan claramente separados).
- Mensajes sugeridos:
  - `fix(frontend): propagate executionMode to DSPy backend request`
  - `fix(api): normalize framework before prompt_history persistence`
  - `feat(observability): add persistence failure degradation signals`

---

## Pendientes Fuera De Alcance (deuda base)

Estos pendientes no bloquean avance por WO, pero deben resolverse al cierre del plan para evitar perdida de trazabilidad.

### Suite pendiente detectada
1. `scripts/tests/langchain/test_fetch_prompts.py`
2. `tests/test_api_integration.py::TestAPIErrorHandling::test_improve_prompt_internal_error`
3. `tests/test_error_handling_edge_cases.py::TestKNNProviderErrorHandling::test_knn_provider_with_zero_k`
4. `tests/test_integration_real_prompts.py::test_reflexion_iterates_on_error`
5. `tests/test_integration_real_prompts.py::test_empty_idea_returns_error`
6. `tests/test_integration_real_prompts.py::test_missing_mode_returns_error`
7. `tests/test_opro_knn_integration.py::test_opro_knn_failure_tracked`
8. `tests/test_prompt_validator_edge_cases.py::test_llm_client_exception_handling`

### Regla operativa
- Ejecutar WOs por alcance y evidencia primero.
- Atacar esta deuda al final del plan en un bloque dedicado de estabilizacion de test suite.
