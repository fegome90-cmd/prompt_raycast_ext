#!/usr/bin/env python3
"""Analyze prompt diversity and coverage gaps in the unified pool."""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re


def load_unified_pool():
    """Load the unified few-shot pool."""
    pool_path = Path(__file__).parent.parent / 'datasets/exports/unified-fewshot-pool.json'
    with open(pool_path) as f:
        return json.load(f)


def classify_prompt(idea: str) -> dict:
    """Classify a prompt by type and category."""
    idea_lower = idea.lower()

    # Type classification
    is_meta_prompt = any(p in idea_lower for p in [
        'crea un prompt para', 'genera prompt de', 'prompt para',
        'sprint-prompt', 'codemachine-agent', 'agent-creator'
    ])

    # Category classification (for real tasks only)
    category = "Uncategorized"
    confidence = "low"

    if not is_meta_prompt:
        if any(p in idea_lower for p in ['documenta', 'doc ', 'documentación']):
            category = "Documentación"
            confidence = "high"
        elif any(p in idea_lower for p in ['react', 'vue', 'angular', 'hook', 'componente', 'frontend', 'ui']):
            category = "Frontend"
            confidence = "high"
        elif any(p in idea_lower for p in ['api', 'endpoint', 'servicio', 'backend', 'servidor']):
            category = "Backend/API"
            confidence = "high"
        elif any(p in idea_lower for p in ['test', 'prueba', 'spec', 'validación']):
            category = "Testing"
            confidence = "medium"
        elif any(p in idea_lower for p in ['base de datos', 'sql', 'migración', 'schema']):
            category = "Database"
            confidence = "medium"
        elif any(p in idea_lower for p in ['seguridad', 'auth', 'autenticación', 'permission']):
            category = "Seguridad"
            confidence = "medium"
        elif any(p in idea_lower for p in ['docker', 'deploy', 'ci/cd', 'infra', 'kubernetes']):
            category = "DevOps/Infra"
            confidence = "medium"
        elif any(p in idea_lower for p in ['performance', 'optimiza', 'caché']):
            category = "Performance"
            confidence = "low"
        elif any(p in idea_lower for p in ['arquitectura', 'diseño del sistema']):
            category = "Arquitectura"
            confidence = "low"
        elif any(p in idea_lower for p in ['función', 'clase', 'módulo', 'helper', 'utilidad']):
            category = "Código genérico"
            confidence = "low"

    return {
        "is_meta_prompt": is_meta_prompt,
        "category": category,
        "confidence": confidence
    }


def analyze_frameworks(data):
    """Analyze framework distribution."""
    frameworks = data['metadata']['statistics']['by_framework']
    total = sum(frameworks.values())

    # Group similar frameworks
    grouped = {
        "Decomposition": 0,
        "Chain-of-Thought": 0,
        "Tree-of-Thoughts": 0,
        "ReAct": 0,
        "Reflexion": 0,
        "Zero-Shot": 0,
        "Other": 0
    }

    for fw, count in frameworks.items():
        fw_lower = fw.lower()
        if 'decomposition' in fw_lower or 'descomposición' in fw_lower:
            grouped["Decomposition"] += count
        elif 'chain-of-thought' in fw_lower:
            grouped["Chain-of-Thought"] += count
        elif 'tree-of-thought' in fw_lower:
            grouped["Tree-of-Thoughts"] += count
        elif 'react' in fw_lower:
            grouped["ReAct"] += count
        elif 'reflexion' in fw_lower:
            grouped["Reflexion"] += count
        else:
            grouped["Other"] += count

    return grouped, total


def print_framework_analysis(grouped, total):
    """Print framework analysis."""
    print("=" * 70)
    print("ANÁLISIS DE FRAMEWORKS")
    print("=" * 70)

    for fw, count in sorted(grouped.items(), key=lambda x: -x[1]):
        if count > 0:
            pct = (count / total) * 100
            bar = "█" * int(pct / 2)
            print(f"{pct:5.1f}% {count:2d} {fw:15s} {bar}")


def print_coverage_analysis(examples):
    """Print coverage analysis by category."""
    print("\n" + "=" * 70)
    print("ANÁLISIS DE COBERTURA POR CATEGORÍA")
    print("=" * 70)

    # Classify all prompts
    categories = defaultdict(list)
    meta_count = 0

    for ex in examples:
        idea = ex['inputs']['original_idea']
        classification = classify_prompt(idea)

        if classification['is_meta_prompt']:
            meta_count += 1
        elif classification['category'] != "Uncategorized":
            categories[classification['category']].append(idea)

    # Print coverage
    total_real = len(examples) - meta_count

    print(f"\nMeta-prompts (crear prompts): {meta_count}")
    print(f"Tareas reales: {total_real}")

    print(f"\n{'Categoría':<20} {'Cuenta':>6} {'%':>5} {'Cobertura':>10}")
    print("-" * 50)

    # All categories we want to cover
    desired_categories = [
        "Frontend", "Backend/API", "Documentación", "Testing",
        "Database", "Seguridad", "Performance", "DevOps/Infra",
        "Arquitectura", "Código genérico"
    ]

    for cat in desired_categories:
        count = len(categories[cat])
        pct = (count / total_real * 100) if total_real > 0 else 0

        # Coverage assessment
        if count == 0:
            coverage = "❌ FALTA"
        elif count < 3:
            coverage = "⚠️  Bajo"
        elif count < 5:
            coverage = "✅ Medio"
        else:
            coverage = "✅ Bueno"

        print(f"{cat:<20} {count:>6} {pct:>4.0f}% {coverage:>10}")

    return categories


def identify_gaps(categories):
    """Identify coverage gaps and missing categories."""
    print("\n" + "=" * 70)
    print("GAPS IDENTIFICADOS")
    print("=" * 70)

    # Categories with zero or low coverage
    gaps = {
        "Testing": len(categories["Testing"]),
        "Database": len(categories["Database"]),
        "Seguridad": len(categories["Seguridad"]),
        "Performance": len(categories["Performance"]),
        "DevOps/Infra": len(categories["DevOps/Infra"]),
        "Arquitectura": len(categories["Arquitectura"]),
    }

    print("\nCategorías con COBERTURA CRÍTICA (< 3 ejemplos):")
    for cat, count in sorted(gaps.items(), key=lambda x: x[1]):
        if count < 3:
            print(f"  ❌ {cat}: {count} ejemplos")

    # Suggest new prompts needed
    print("\nSUGERENCIAS DE PROMPTS PARA AGREGAR:")

    suggestions = {
        "Testing": [
            "Escribe un test unitario para una función de validación de emails",
            "Crea un test de integración para un endpoint de login",
            "Genera mocks para pruebas de API externa",
            "Escribe un test E2E para un flujo de checkout"
        ],
        "Database": [
            "Diseña un schema para una tabla de usuarios con relaciones",
            "Escribe una migración SQL para agregar un campo",
            "Crea un índice para optimizar consultas de búsqueda",
            "Diseña una estrategia de partitioning para logs"
        ],
        "Seguridad": [
            "Implementa validación de JWT tokens en middleware",
            "Crea sanitizer para inputs de usuario contra XSS",
            "Diseña política de RBAC para roles y permisos",
            "Implementa rate limiting para prevenir滥用"
        ],
        "Performance": [
            "Optimiza query N+1 con eager loading",
            "Implementa caché con Redis para API lenta",
            "Agrega pagination para endpoints de listado",
            "Optimiza bundle size con code splitting"
        ],
        "DevOps/Infra": [
            "Crea Dockerfile multi-stage para app Node.js",
            "Configura CI/CD pipeline con GitHub Actions",
            "Escribe manifiesto de Kubernetes para deployment",
            "Configura monitoring con Prometheus + Grafana"
        ],
        "Arquitectura": [
            "Diseña arquitectura de microservicios para e-commerce",
            "Define patrón CQRS para aplicación de altas consultas",
            "Diseña estrategia de event-driven architecture",
            "Define estructura de monorepo para múltiples servicios"
        ]
    }

    for cat, prompts in suggestions.items():
        if gaps[cat] < 3:
            print(f"\n  {cat}:")
            for prompt in prompts[:2]:  # Show 2 examples per category
                print(f"    - {prompt}")


def main():
    """Main analysis."""
    print("🔍 ANALIZANDO DIVERSIDAD DEL POOL DE PROMPTS\n")

    # Load data
    data = load_unified_pool()
    examples = data['examples']

    # Framework analysis
    grouped, total = analyze_frameworks(data)
    print_framework_analysis(grouped, total)

    # Coverage analysis
    categories = print_coverage_analysis(examples)

    # Identify gaps
    identify_gaps(categories)

    # Summary recommendations
    print("\n" + "=" * 70)
    print("RECOMENDACIONES")
    print("=" * 70)
    print("""
1. **Aumentar variedad de frameworks**:
   - Actual: 80% Decomposition, 17% Chain-of-Thought
   - Objetivo: 40% Decomposition, 30% Chain-of-Thought, 20% ReAct, 10% otros

2. **Eliminar meta-prompts del pool**:
   - Actual: 9 meta-prompts (14%)
   - Objetivo: 0 meta-prompts, solo tareas reales

3. **Agregar prompts en categorías faltantes**:
   - Prioridad ALTA: Testing, Database, Seguridad (0-1 ejemplo cada una)
   - Prioridad MEDIA: Performance, DevOps, Arquitectura (0 ejemplos)

4. **Mejorar metadata**:
   - Agregar campo `task_category` a cada ejemplo
   - Agregar campo `complexity` (baja/media/alta)
   - Agregar campo `domain` (web/mobile/data/devops/etc)

5. **Crear script de validación**:
   - Verificar cobertura mínima por categoría
   - Alertar si hay desbalance > 60% en un framework
   - Sugerir prompts para agregar cuando se detecten gaps
    """)


if __name__ == '__main__':
    main()
