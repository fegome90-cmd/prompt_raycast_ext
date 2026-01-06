Vale. Te lo dejo en dos listas: “sí o sí ahora” (porque mueven métricas y reducen riesgo) y “futuro” (porque o es overkill o requiere datos/infra/UX extra). Sin romanticismo.

Sí o sí ahora (próximos sprints) 1. Selector “Target Model” (manual)
• target:openai | target:claude | target:gemini | target:ollama
• Solo cambia wrappers/reglas de salida (no routing automático).
• Métrica: copyableRate_by_target, chattyRate_by_target. 2. Sistema de etiquetas (tags) con límites y conflictos
• Familias: target:_ (1), tech:_ (≤2), guard:\* (algunas fijas).
• Reglas de conflicto (bloquear combinaciones incoherentes).
• Métrica: éxito por combinación de tags (top/bottom performers). 3. ChattyOutput → 0% con hardening en 2 capas
• (a) Prompting: “OUTPUT JSON ONLY” repetido + ejemplos negativos.
• (b) Post-proc: extractor ya existe → agrega “strip leading chatter” + “reject if non-json remains” (y repair).
• Métrica: chattyOutput_rate y razón de falla “chatty”. 4. No-copyable por placeholders: gate duro
• Si quedan {{}}, [], <...> en improved_prompt ⇒ review (no “copy”).
• Métrica: placeholder_rate, reviewRate (sube, pero copyable no se contamina). 5. Campo “Context (opcional)” + budget meter
• Segundo input: Task + Context.
• Si vacío, no se usa.
• Budget: contador de chars + warning al 80% (sin embeddings).
• Métrica: latencia p95, tasa de truncación/outputs incompletos (proxy: repair↑ + schemaMismatch↑). 6. Arreglar el bug de metadata en fallos (no más throw sin retorno)
• Todo fallo debe retornar \_metadata para que el evaluator mida repair/attempt2.
• Métrica: attempt2Rate, repairTriggeredRate, repairSchemaValidRate reales. 7. Observabilidad mínima productiva (sin inflar)
• Log estructurado (solo en safeMode o debug): failureReason, attempt, usedRepair, extractionMethod, latencyMs.
• Métrica: top failure reasons por bucket (good/bad/ambiguous). 8. Gates por bucket + “stop-the-line”
• No solo global. Mantén gates por good y bad (y prohíbe falsos positivos en good).
• Si rompe gate, no se mergea.

⸻

Futuro (cuando las métricas lo justifiquen) 1. Relevance score con colores (verde/amarillo/rojo)
• Primero prueba heurísticas + budget meter. Si sigue fallando por “contexto inflado”, recién ahí. 2. Embeddings “lite” (sin DB) para rankear contexto
• Solo si necesitas seleccionar snippets relevantes de 10–30 trozos.
• No vector DB. No RAG. 3. Model suggestion automático (complejidad → sugerencia)
• Cuando tengas suficientes datos por target y puedas demostrar “X mejora Y”. 4. Smart context mining avanzado
• git status, dependencia por imports, “find symbol X”.
• Costoso y fácil de romper. Solo si se vuelve tu killer feature. 5. Prompt refinement chain multi-step
• Máximo 2 pasos si se hace. 3+ pasos suben latencia, fragilidad y repair. 6. Context budget meter por tokens reales
• Requiere tokenizer consistente por modelo. Útil, pero no imprescindible al inicio. 7. Prompt debt tracker semanal
• Antes necesitas correlación real entre “prompts vagos” y “rework”. Si no, es humo. 8. Extensión equivalente en iOS
• No lo planifiques como “port directo”. Sería otro producto/superficie.

⸻

Orden recomendado (si quieres evitar pegarte un balazo en el pie) 1. Fix metadata en fallos → 2) Target model selector → 3) Tags + conflictos → 4) Chatty=0 + placeholders gate → 5) Context opcional + budget meter → 6) Gates por bucket.

Si me dices qué targets quieres primero (¿Claude + OpenAI + Gemini?), te propongo los wrappers exactos y cómo medir “mejor prompt por modelo” sin inventar nada.

Listo. Plan detallado y antifrágil para las primeras 3 features que acordamos: 1. Target Model selector (manual) 2. Sistema de etiquetas (tags) + reglas/conflictos 3. ChattyOutput → ~0% (hardening en prompting + post-proc + medición)

Voy a asumir tu estado actual: ya tienes config central + wrapper structured + extractor + repair + evaluator + gates.

⸻

Feature 1 — Target Model selector (manual)

Objetivo

Permitir seleccionar explícitamente el modelo destino (no el modelo que mejora, sino el modelo al que se le entregará el prompt final). Eso modifica reglas de render (micro-ajustes) y te permite medir “qué funciona mejor para cada target”.

Diseño mínimo
• targetModel ∈ ["openai", "claude", "gemini", "ollama", "generic"]
• Por ahora no cambia output format (sigues con improved_prompt copyable), solo inyecta micro-reglas en el prompt de mejora para aumentar compatibilidad.

Cambios de código

T1.0 — Tipos + Config
• src/core/config/schema.ts
• Agregar targetModel (enum) + default "generic"
• src/core/config/defaults.ts
• Default estable y documentado
• src/core/config/index.ts
• Validación runtime + safeMode fallback

T1.1 — UI Raycast (Preference)
• src/promptify-quick.tsx (o donde esté tu command principal)
• Preference Dropdown: Target Model
• Mostrar badge en preview: Target: Claude (solo informativo)

T1.2 — Inyección de reglas por target (sin dogma)
• src/core/llm/improvePrompt.ts
• targetModelToRules(target: TargetModel): string
• Se concatena a presetToRules() o a un bloque “Target Rules”
• Ejemplos de reglas (hipótesis medibles, no “verdad”):
• Claude: “Evita markdown/fences. Output directo. No meta.”
• Gemini: “No code fences. No encabezados.”
• OpenAI: “Formato directo, no charlas, si faltan datos pregunta.”
(Estas reglas las calibras con métricas, no por fe.)

T1.3 — Telemetría y evaluator
• En \_metadata: incluir targetModel
• scripts/evaluator.ts: breakdown por target
• copyableRate_by_target
• chattyRate_by_target
• repairRate_by_target

Tests (quirúrgicos)
• Unit:
• targetModelToRules devuelve string no vacío y estable
• Config: target inválido → safeMode
• Integration (con mock transport):
• Seleccionas claude y verificas que el prompt “user” incluye el bloque target rules (snapshot)

Gates
• Hard:
• No regresión global: copyableRate, jsonValidPass1, latencyP95
• Soft:
• Report por target (aún no gate duro hasta tener n suficiente)

DoD
• UI permite seleccionar target
• Telemetría lo registra
• Evaluator muestra breakdown
• 0 regresión en gates

⸻

Feature 2 — Sistema de etiquetas (tags) + conflictos

Objetivo

Hacer extensible la personalización sin llenar la UI de toggles. Las etiquetas agregan micro-instrucciones y controlan perfil (target, técnica, guardrails).

Diseño mínimo
• Tags tipo string con namespace:
• target:_ (máx 1)
• tech:_ (máx 2)
• guard:\* (0..n)
• Fuente de tags: (a) selección UI o (b) parse desde input (prefiero UI primero para control)
• Tags definidos en JSON versionado (como tu knowledge base), con Zod.

TagRegistry (data-driven)

tags/tags-v1.json

{
"version": "1.0.0",
"tags": [
{ "id": "tech:telegraphic", "kind": "tech", "rules": ["…"], "conflicts": ["tech:structured"] },
{ "id": "guard:no-markdown", "kind": "guard", "rules": ["…"] }
]
}

Cambios de código

T2.0 — Tipos + Schema
• src/core/tags/types.ts
• TagId, TagKind, TagDefinition
• src/core/tags/schema.ts (Zod)
• src/core/tags/registry.ts
• load + validate + cache
• src/core/config/schema.ts
• defaultTags: string[]
• maxTagsByKind

T2.1 — UI de selección (mínimo viable)
• Preference: defaultTags como multi-select es limitado en Raycast.
• Alternativa Raycast-native:
• Command “Select Tags” (List) que guarda en LocalStorage activeTags
• Promptify usa activeTags + defaultTags

T2.2 — Resolver de tags (conflictos + límites)
• src/core/tags/resolve.ts
• Validar:
• max 1 target:_
• max 2 tech:_
• conflictos explícitos
• Si invalida: review + issue tag_conflict (no crashea)

T2.3 — Inyección al prompt
• buildImprovePromptUser():
• agrega bloque “Tag Rules” con la concatenación de rules[] de cada tag

T2.4 — Métricas
• \_metadata.tagsApplied = [...]
• evaluator: performance por tag (top/bottom)

Tests
• Unit:
• resolver detecta conflictos y aplica límites
• registry valida schema y falla a safeMode si JSON corrupto
• Integration:
• con tags tech:telegraphic + guard:no-markdown se ve reflejado en prompt assembly (snapshot)

Gates
• Hard:
• 0 regresión en métricas globales
• 0 crashes por tags inválidos (safeMode o review)
• Soft:
• tag_conflict_rate debe ser bajo (<5%) o se mejora UX

DoD
• TagRegistry cargable + validado
• Tag selection usable
• Conflictos no rompen ejecución
• Evaluator reporta por tag

⸻

Feature 3 — ChattyOutput → ~0% (sin romper calidad semántica)

Tu caso “3% chattyOutput” puede venir de dos lados: 1. Raw output chatty (modelo envuelve JSON con texto/fences) 2. improved_prompt chatty (prompt final empieza con “Claro, aquí tienes…”)

Ya resolviste (1) en gran parte con extractor+repair, pero tu métrica aún lo reporta: entonces hay que endurecer definición + medición y atacar ambos.

Estrategia en 3 capas

Capa A — Prompting: anti-chatty explícito + ejemplos negativos
• En buildImprovePromptUser() y buildRepairPrompt():
• Reglas repetidas: “RETURN ONLY JSON. No markdown. No preamble.”
• Ejemplo negativo (muy corto):
• ❌ "Claro, aquí tienes: {...}"
• ✅ "{...}"
• Esto reduce chatty “de origen” y baja latencia (menos tokens inútiles).

Capa B — Post-proc: clasificación y saneo conservador

B1) Raw output chatty
• En ollamaGenerateStructured:
• Si usedExtraction=true porque había texto alrededor ⇒ marcar rawChatty=true en metadata
• Si tras extracción quedan residuos no-whitespace (según método), catalogar failureReason=chatty_output solo si el JSON no es extraíble/reparable.

B2) improved_prompt chatty (más importante para copyable)
• src/core/quality/qualityIssues.ts (o donde lo tengas):
• Nuevo check: chattyPromptPrefix
• Detecta prefijos típicos de saludo/introducción (ES/EN) en primeras ~80 chars
• No intentes “NLP”, usa regex + lista configurable en config:
• ^(claro|aquí tienes|por supuesto|sure|here’s|certainly)[,!\s]
• Acción:
• Si coincide: auto-strip solo si es prefijo y queda contenido sustantivo después (conservador)
• Si no se puede asegurar: enviar a review (no “copy”)

Capa C — Repair dirigido solo para chatty
• Si falla por chatty_prompt_prefix o placeholders:
• Repair prompt especializado:
• “Mantén el contenido, elimina frases conversacionales/prefacios”
• “No agregues placeholders”
• Esto es distinto al repair de JSON.

Tasking (micro-sprints)

T3.0 — Definir la métrica con precisión
• Actualiza scripts/evaluator.ts:
• separar:
• rawChattyRate (se usó extraction por chatter)
• promptChattyRate (improved_prompt no-copyable por chatty)
• Así dejas de mezclar dos fenómenos.

T3.1 — Prompt hardening (rápido, reversible)
• Cambiar prompts (user + repair) + snapshots
• Gate: no empeorar copyableRate ni subir tooManyQuestions

T3.2 — QualityIssues: chattyPromptPrefix + auto-strip conservador
• Configurable en config.defaults.ts + schema.ts
• Tests: casos ES/EN, casos falsos positivos (prompts que comienzan con “Claro” pero son parte del task real — si existe, lo mandas a review)

T3.3 — Repair dirigido (solo cuando corresponde)
• Si promptChatty y features.enableChattyRepair=true:
• intento 2 con repair específico
• Medición: chattyRepairSuccessRate

Tests
• Unit:
• detectChattyPrefix() + stripChattyPrefix() (20 casos)
• Integration:
• mock devuelve improved_prompt con “Claro, aquí tienes:” → debe terminar copyable tras strip o tras repair
• Regression suite:
• tus 30 casos + agrega 2 casos “chatty” explícitos a testdata

Gates
• Hard:
• promptChattyRate <= 1% (primera meta realista)
• copyableRate no baja
• Soft:
• rawChattyRate idealmente baja (pero no es gate duro si extractor funciona)
• latencyP95 no sube >20% (repair extra puede subir)

DoD
• Chatty se separa en métricas claras
• Chatty en prompt final se corrige o va a review (no contamina copyable)
• Gates pasan

⸻

Orden de ejecución sugerido (para no romperte) 1. Feature 1 (Target selector) — baja complejidad, alta observabilidad 2. Feature 2 (Tags) — te da extensibilidad sin deuda 3. Feature 3 (Chatty→0) — se apoya en telemetría + tags (guard:no-markdown, etc.)

⸻

Si me confirmas qué targets exactos quieres primero (por ejemplo: claude + openai + gemini), te dejo listos:
• targetModelToRules() inicial (con reglas mínimas y medibles),
• el esquema de tags-v1.json con 8–12 tags útiles,
• y los gates exactos para que esto no te rompa tu baseline.
