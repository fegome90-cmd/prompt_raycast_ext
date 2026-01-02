# Índice de Auditoría - Pipeline de Prompts

**Fecha:** 2026-01-02
**Estado:** Completado

---

## Informes Disponibles

### Informe General
| Archivo | Descripción |
|---------|-------------|
| [`pipeline-prompts.md`](./pipeline-prompts.md) | Auditoría completa del pipeline con todos los hallazgos |

### Informes Críticos Detallados
| ID | Archivo | Título | Severidad | Estado |
|----|---------|--------|-----------|--------|
| **CRT-01** | [`CRT-01-puerto-dspy-inconsistente.md`](./CRT-01-puerto-dspy-inconsistente.md) | Inconsistencia de Puerto DSPy (8000 vs 8001) | 🟡 Media | ✅ Resuelto |
| **CRT-02** | [`CRT-02-falta-persistencia-prompts.md`](./CRT-02-falta-persistencia-prompts.md) | Falta de Persistencia de Prompts | 🔴 Alta | ⚠️ Activo |
| **CRT-03** | [`CRT-03-variabilidad-semantica-ambiguedad.md`](./CRT-03-variabilidad-semantica-ambiguedad.md) | Variabilidad Semántica por Ambigüedad | 🔴 Crítica | ⚠️ Requiere acción inmediata |
| **CRT-04** | [`CRT-04-migracion-deepseek-chat.md`](./CRT-04-migracion-deepseek-chat.md) | Migración a DeepSeek Chat via LiteLLM | 🟢 Oportunidad | 📋 Propuesta |
| **CRT-05** | [`CRT-05-comparativa-agent-h-raycast.md`](./CRT-05-comparativa-agent-h-raycast.md) | Comparativa Agent_H vs Raycast | 📊 Análisis | ✅ Completado |

### Seguimiento
| Archivo | Descripción |
|---------|-------------|
| [`SEGUIMIENTO.md`](./SEGUIMIENTO.md) | Checklist y tracking de progreso |

---

## Resumen de Hallazgos Críticos

### ✅ CRT-01: Puerto DSPy Inconsistente (RESUELTO)

**Problema:** El `.env` definía `API_PORT=8001` pero el backend corría en `8000` (default del código) y el frontend estaba harcodeado a `8000`.

**Impacto:** Bajo - el sistema funcionaba porque ambos usaban 8000

**Resolución aplicada:**
- Cambiado `.env` a `API_PORT=8000`
- Agregada validación de puerto al startup
- Agregado logging explícito de configuración

**Fecha de resolución:** 2026-01-02

---

### 🔴 CRT-03: Variabilidad Semántica (CRÍTICO - Requiere acción inmediata)

**Problema:** El sistema tiene inconsistencia intrínseca - 60-70% tasa de fallo y 34-48% similitud semántica.

**Test ejecutado:** Variability test script (10 runs × 2 casos)

**Resultados empíricos:**
- **Tasa de fallo JSON:** 60-70% (CRÍTICO)
- **Similitud semántica:** 34-48% (muy baja)
- **Consistencia estructura:** 0% (verbos, objetos)
- **Incluso inputs específicos son variables** - No es solo ambigüedad

**Hipótesis original refutada:**
- ✗ "Ambigüedad causa variabilidad" - NO, inputs específicos también variables
- ✗ "Detectar ambigüedad resolvería" - NO, problema más profundo

**Nueva hipótesis:**
"El modelo Novaeus-Promptist-7B tiene inconsistencia intrínseca que NO se controla con temperature 0.1."

**Acciones recomendadas:**
1. Inmediato: Cambiar temperature 0.1 → 0.0 y re-evaluar
2. Corto plazo: Evaluar modelos alternativos
3. NO usar en producción hasta resolver

**Esfuerzo estimado:** 1 semana para solución completa

---

### CRT-02: Falta de Persistencia

**Problema:** No hay base de datos ni logs estructurados - todos los prompts se pierden después de procesarlos.

**Impacto:** Alto - imposibilita análisis, debugging post-mortem, y mejora continua

**Resolución:** Implementar SQLite para historial de prompts

**Esfuerzo estimado:** 1-2 días (MVP)

---

## Próximos Pasos Recomendados

### Inmediatos (Hoy)
1. ✅ Leer informes CRT-01 y CRT-02
2. ⏳ Corregir `.env`: `API_PORT=8000`
3. ⏳ Decidir sobre implementación de persistencia

### Corto Plazo (Esta semana)
4. ⏳ Implementar SQLite MVP (CRT-02)
5. ⏳ Agregar logging estructurado
6. ⏳ Crear endpoints de analytics básicos

### Medio Plazo (Este mes)
7. ⏳ Dashboard de análisis en Raycast
8. ⏳ Búsqueda y filtrado de historial
9. ⏳ Export de datos (CSV/JSON)

---

## Convención de Nomenclatura

**CRT:** Critical Technical Report
- CRT-01: Problemas de configuración/infraestructura
- CRT-02: Problemas de arquitectura/diseño
- CRT-03: Problemas de performance (futuro)
- CRT-04: Problemas de seguridad (futuro)

---

## Actualización de Informes

Al resolver un CRT:
1. Cambiar estado a "✅ Resuelto"
2. Agregar fecha de resolución
3. Breve descripción de la solución aplicada
4. Actualizar este índice

---

**Última actualización:** 2026-01-02
