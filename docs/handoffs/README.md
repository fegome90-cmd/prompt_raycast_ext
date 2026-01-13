# Handoffs - Sesiones de Desarrollo

> **Propósito:** Documentar puntos de pausa entre sesiones para facilitar la continuidad del trabajo.

---

## 📁 Estructura

```
docs/handoffs/
├── README.md                    # Este archivo
├── nlac-integration-tests.md    # Ejemplo: NLaC integration tests
├── <feature-name>.md            # Formato: <nombre-feature>-<descripción>.md
└── archive/                     # Handoffs de features completadas
```

---

## 🎯 Convención de Nombres

**Formato:** `<feature>-<descripción-corta>.md`

**Ejemplos:**
- `nlac-integration-tests.md` - Tests de integración NLaC
- `prompt-cache-optimization.md` - Optimización de cache
- `knn-fewshot-refactor.md` - Refactor de KNN few-shot
- `oprop-optimizer-v2.md` - V2 del optimizador OPRO

**Reglas:**
- Usar **kebab-case** (guiones medios)
- Nombre descriptivo de la feature/PR
- Corto pero identificable (máx 3-4 palabras)
- Inglés preferible para consistencia

---

## 📝 Plantilla de Handoff

Cada handoff debe incluir:

### 1. Contexto Inmediato
```markdown
> **Fecha:** DD/MM/YYYY
> **Estado:** Qué tan completado está el trabajo
> **Objetivo:** Qué se busca en la próxima sesión
```

### 2. Logros Recientes
- Qué se completó en esta sesión
- Tests agregados/fijados
- Commits realizados

### 3. Tareas Pendientes
- **Alta Prioridad:** Bloqueantes o críticos
- **Media Prioridad:** Mejoras y optimizaciones
- **Baja Prioridad:** Nice-to-have

### 4. Archivos Clave
- Dominio: Servicios principales modificados
- Tests: Tests creados/modificados
- Docs: Documentación agregada

### 5. Issues Conocidos
- Bugs identificados
- Workarounds si existen
- Soluciones propuestas

### 6. Next Steps
- Opciones A/B/C para continuar
- Success criteria claros
- Comandos útiles para quick start

---

## 🔄 Ciclo de Vida

```
1. Desarrollo Activo
   docs/handoffs/<feature>.md
   ↓
2. Feature Completada
   Mover a docs/handoffs/archive/
   ↓
3. Referencia Futura
   Buscar en archive por nombre o fecha
```

---

## 📖 Uso

### Durante el Desarrollo
```bash
# Crear nuevo handoff
cat > docs/handoffs/my-feature.md << 'EOF'
# Handoff - My Feature
> **Fecha:** $(date +%Y-%m-%d)
...
EOF

# Editar handoff existente
nvim docs/handoffs/nlac-integration-tests.md

# Listar handoffs activos
ls -la docs/handoffs/*.md | grep -v README
```

### Al Completar Feature
```bash
# Mover a archive
mkdir -p docs/handoffs/archive
mv docs/handoffs/completed-feature.md docs/handoffs/archive/

# Opcional: Agregar fecha al archivo archivado
mv docs/handoffs/archive/completed-feature.md \
   docs/handoffs/archive/$(date +%Y-%m-%d)-completed-feature.md
```

### Al Continuar Trabajo
```bash
# Leer handoff activo
cat docs/handoffs/nlac-integration-tests.md

# O ver todos los handoffs activos
for f in docs/handoffs/*.md; do
  if [[ "$f" != *"README.md" ]]; then
    echo "=== $f ==="
    head -20 "$f"
    echo ""
  fi
done
```

---

## 🎓 Tips

1. **Un handoff por feature activa** - Evita confusión
2. **Actualizar al final de cada sesión** - No dejar para después
3. **Ser específico en next steps** - Opciones claras con success criteria
4. **Incluir comandos útiles** - Make targets, pytest commands, etc.
5. **Mencionar commits relevantes** - Hash para reference rápida
6. **Archivar pronto** - Una vez completada, mover a archive

---

## 📚 Ejemplos de Handoffs

### Handoff Activo (En Desarrollo)
Ver `nlac-integration-tests.md` para un ejemplo completo de trabajo en progreso.

### Handoff Archivado (Completado)
Ejemplo de estructura para features completadas:
```markdown
# Feature X - Handoff Final

> **Completado:** 2026-01-07
> **PR:** #123
> **Status:** ✅ Merged

## Logros Finales
- Todo implementado
- Tests passing
- Documentación completa

## Lecciones Aprendidas
- Lo que funcionó bien
- Lo que haríamos diferente
- Technical debt identificado
```

---

## 🔍 Búsqueda

```bash
# Buscar por palabra clave en handoffs
grep -r "KNN" docs/handoffs/

# Buscar handoffs por fecha
grep -l "2026-01-07" docs/handoffs/*.md

# Ver últimos handoffs modificados
ls -lt docs/handoffs/*.md | head -5
```

---

*Para crear un nuevo handoff, copia esta plantilla y adapta según la feature.*
