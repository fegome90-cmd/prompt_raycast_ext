#!/usr/bin/env python3
"""Add NLaC-specific examples to the few-shot catalog."""

import json
from datetime import UTC, datetime

# Read existing catalog
with open('/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool-v2.json', encoding='utf-8') as f:
    catalog = json.load(f)

# New examples relevant to prompt systems and NLaC
new_examples = [
    {
        'inputs': {
            'original_idea': 'analiza el sistema de mejora de prompts NLaC',
            'context': 'Quiero entender cómo funciona el pipeline NLaC con OPRO y IFEval'
        },
        'outputs': {
            'improved_prompt': '''## Framework
Systematic Analysis with Decomposition

## Rol
Especialista en Arquitectura de Sistemas de Prompt Engineering

## Directiva
Analiza el sistema NLaC (Natural Language as Code) descomponiendo el pipeline en sus componentes fundamentales y evaluando la calidad de cada etapa.

## Guardrails
- Documenta cada componente del pipeline NLaC
- Identifica los puntos de decision (intent classification, complexity analysis)
- Evalua la calidad de ejemplos few-shot seleccionados
- Mide la latencia de cada etapa
- Propone mejoras especificas con evidencia

## Analisis Estructurado
1. **Intent Classification**: Como clasifica Debug/Refactor/Generate/Explain?
2. **Complexity Analyzer**: Como determina SIMPLE/MODERATE/COMPLEX?
3. **KNN Provider**: Como selecciona ejemplos relevantes del catalogo?
4. **OPRO Optimizer**: Como optimiza iterativamente el prompt?
5. **IFEval Validation**: Como valida constraints de formato?

## Metricas de Calidad
- Precision de clasificacion de intent
- Relevancia semantica de ejemplos few-shot
- Latencia por etapa (target: <12s P95)
- Tasa de mejora (OPRO iterations vs quality gain)

## Output Esperado
Reporte estructurado con:
- Diagrama de flujo del pipeline NLaC
- Tabla de componentes con latencias
- Analisis de calidad de ejemplos few-shot
- Recomendaciones priorizadas de mejora''',
            'role': 'Especialista en Arquitectura de Sistemas de Prompt Engineering',
            'directive': 'Analiza el sistema NLaC descomponiendo el pipeline en componentes fundamentales',
            'framework': 'Decomposition',
            'guardrails': '[-] Documenta cada componente del pipeline NLaC\n[-] Identifica los puntos de decision\n[-] Evalua la calidad de ejemplos few-shot\n[-] Mide la latencia de cada etapa\n[-] Propone mejoras especificas con evidencia'
        },
        'metadata': {
            'source': 'NLaC-System-Review',
            'domain': 'prompt-engineering',
            'category': 'system-analysis',
            'framework': 'Decomposition',
            'complexity': 'moderate',
            'intent': 'explain',
            'added_at': datetime.now(UTC).isoformat(),
            'quality_score': 0.95
        }
    },
    {
        'inputs': {
            'original_idea': 'improve the KNN few-shot selection for prompt engineering',
            'context': 'The current character bigram vectorization produces irrelevant matches'
        },
        'outputs': {
            'improved_prompt': '''## Framework
Chain-of-Thought with Systematic Decomposition

## Rol
Senior Machine Learning Engineer specializing in Semantic Search and Prompt Engineering

## Directiva
Diagnose and fix the KNN few-shot selection system to ensure relevant example retrieval for prompt improvement tasks.

## Problem Decomposition
1. **Root Cause Analysis**: Why does character bigram vectorization produce irrelevant matches?
2. **Query Construction**: Should we include user input in the semantic query?
3. **Vectorization Strategy**: Character bigrams vs word tokens vs embeddings
4. **Relevance Filtering**: Should we validate semantic similarity after retrieval?

## Analysis Steps
1. Examine current query construction in `find_examples()`
2. Review catalog for domain coverage (prompt systems, NLaC)
3. Test semantic similarity with and without user input
4. Implement relevance filtering if needed

## Guardrails
- Do not break existing tests
- Maintain backward compatibility
- Log similarity scores for debugging
- Fallback to random if KNN fails

## Expected Output
Improved KNN system with:
- Query includes user input for better semantic matching
- Word-level tokenization instead of character bigrams
- Relevance threshold filtering (cosine similarity > 0.3)
- Enhanced catalog with prompt engineering examples''',
            'role': 'Senior ML Engineer specializing in Semantic Search',
            'directive': 'Diagnose and fix the KNN few-shot selection system',
            'framework': 'Chain-of-Thought',
            'guardrails': '[-] Do not break existing tests\n[-] Maintain backward compatibility\n[-] Log similarity scores\n[-] Fallback to random if KNN fails'
        },
        'metadata': {
            'source': 'NLaC-KNN-Fix',
            'domain': 'machine-learning',
            'category': 'semantic-search',
            'framework': 'Chain-of-Thought',
            'complexity': 'moderate',
            'intent': 'refactor',
            'has_expected_output': True,
            'added_at': datetime.now(UTC).isoformat(),
            'quality_score': 0.92
        }
    },
    {
        'inputs': {
            'original_idea': 'crear un prompt para auditoria de sistemas de IA',
            'context': 'Necesito revisar la calidad del sistema NLaC'
        },
        'outputs': {
            'improved_prompt': '''## Framework
Systematic Decomposition with Layered Verification

## Rol
Auditor Especialista en Sistemas de IA y Prompt Engineering

## Directiva
Realiza una auditoria comprehensiva del sistema NLaC identificando problemas de calidad, latencia, y relevancia semantica.

## Fases de Auditoria

### Fase 1: Definicion del Alcance
- Componentes del pipeline a auditar (Intent -> Complexity -> KNN -> OPRO -> IFEval)
- Metricas clave (precision, latencia, relevancia, cobertura)
- Criterios de exito (quality gates)

### Fase 2: Mapeo de Capas
- Capa de clasificacion: Reconoce espanol? "revision" -> explain?
- Capa de busqueda: Query incluye user input?
- Capa de catalogo: Tiene ejemplos relevantes?
- Capa de validacion: Filtra por relevancia?

### Fase 3: Diseno de Escenarios de Prueba
- Input espanol con "revision/analizar/auditoria"
- Input tecnico sobre "prompt systems/NLaC/OPRO"
- Edge cases: input vacio, muy largo, ambiguo

### Fase 4: Ejecucion de Validacion
- Ejecutar pipeline con cada escenario
- Documentar outputs: intent, complexity, examples seleccionados
- Medir latencia por etapa

### Fase 5: Hallazgos y Recomendaciones
- Categorizar hallazgos: CRITICAL -> HIGH -> MEDIUM -> LOW
- Mapear cada hallazgo a fase especifica
- Recomendaciones con priorizacion y evidencia

## Guardrails
- Evidencia obligatoria para cada hallazgo (logs, screenshots, metricas)
- No asumir sin verificar
- Reproducible: misma input -> misma output

## Output Esperado
Reporte JSON + Markdown con:
- Resumen ejecutivo (1 parrafo)
- Hallazgos por categoria con evidencia
- Recomendaciones priorizadas
- Metricas de calidad del sistema''',
            'role': 'Auditor Especialista en Sistemas de IA',
            'directive': 'Realiza auditoria comprehensiva del sistema NLaC',
            'framework': 'Decomposition',
            'guardrails': '[-] Evidencia obligatoria para cada hallazgo\n[-] No asumir sin verificar\n[-] Reproducible: misma input -> misma output'
        },
        'metadata': {
            'source': 'NLaC-Audit-Template',
            'domain': 'prompt-engineering',
            'category': 'system-audit',
            'framework': 'Decomposition',
            'complexity': 'complex',
            'intent': 'explain',
            'added_at': datetime.now(UTC).isoformat(),
            'quality_score': 0.93
        }
    },
    {
        'inputs': {
            'original_idea': 'fix the Spanish intent classification for review/audit keywords',
            'context': 'The classifier falls back to "generate" for Spanish "revision del sistema"'
        },
        'outputs': {
            'improved_prompt': '''## Framework
ReAct (Reasoning + Acting)

## Rol
NLP Engineer specializing in Multilingual Intent Classification

## Directiva
Fix the intent classifier to properly recognize Spanish review/audit keywords and route them to the correct intent.

## Problem
User input: "haz una revision del sistema de prompt NLaC"
Current behavior: Falls back to "generate" intent
Expected behavior: Should classify as "explain" intent

## Analysis Steps

### Thought 1: Identify Missing Keywords
The `_explain_keywords` set in `IntentClassifier` is missing:
- "revision" / "revision" (review)
- "revisar" (to review)
- "auditoria" / "auditoria" (audit)
- "analizar" / "analisis" (analysis)
- "examinar" / "examine"

### Thought 2: Verify Classification Logic
Review `_has_explain_intent()` method:
- Should check both idea and context
- Should use word boundary matching
- Should handle Spanish accents

### Action 1: Add Missing Keywords
Update the `_explain_keywords` set in `IntentClassifier.__init__()`:
```python
self._explain_keywords = {
    "explain", "how does", "why", "que es", "como funciona",
    "explicar", "entender", "understand",
    "revision", "revisar", "revision", "review",
    "auditoria", "auditoria", "audit",
    "analizar", "analisis", "analysis", "analyze",
    "examinar", "examine",
}
```

### Action 2: Test with Spanish Input
- Input: "haz una revision del sistema NLaC"
- Expected: Intent EXPLAIN
- Verify with logging enabled

## Guardrails
- Maintain backward compatibility
- Add tests for Spanish inputs
- Log classification decisions for debugging
- Do not break English keyword matching

## Expected Output
Fixed intent classifier that correctly routes Spanish review/audit requests to EXPLAIN intent.''',
            'role': 'NLP Engineer specializing in Multilingual Intent Classification',
            'directive': 'Fix the intent classifier to recognize Spanish review/audit keywords',
            'framework': 'ReAct',
            'guardrails': '[-] Maintain backward compatibility\n[-] Add tests for Spanish inputs\n[-] Log classification decisions\n[-] Do not break English keyword matching'
        },
        'metadata': {
            'source': 'NLaC-Intent-Fix',
            'domain': 'nlp',
            'category': 'intent-classification',
            'framework': 'ReAct',
            'complexity': 'simple',
            'intent': 'debug',
            'has_expected_output': True,
            'added_at': datetime.now(UTC).isoformat(),
            'quality_score': 0.94
        }
    }
]

# Append new examples to catalog
catalog['examples'].extend(new_examples)
catalog['metadata']['total_examples'] = len(catalog['examples'])

# Update statistics
if 'by_category' not in catalog['metadata']['statistics']:
    catalog['metadata']['statistics']['by_category'] = {}
catalog['metadata']['statistics']['by_category']['system-analysis'] = catalog['metadata']['statistics']['by_category'].get('system-analysis', 0) + 1
catalog['metadata']['statistics']['by_category']['semantic-search'] = catalog['metadata']['statistics']['by_category'].get('semantic-search', 0) + 1
catalog['metadata']['statistics']['by_category']['system-audit'] = catalog['metadata']['statistics']['by_category'].get('system-audit', 0) + 1
catalog['metadata']['statistics']['by_category']['intent-classification'] = catalog['metadata']['statistics']['by_category'].get('intent-classification', 0) + 1

# Write back to file
with open('/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool-v2.json', 'w', encoding='utf-8') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f'Added {len(new_examples)} examples to catalog')
print(f'Total examples: {catalog["metadata"]["total_examples"]}')
