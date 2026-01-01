#!/usr/bin/env python3
"""
Test script para DSPy PromptImprover - Prueba con prompts genéricos
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_prompt(prompt: str, description: str) -> dict:
    """Prueba un prompt y retorna resultados."""
    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/improve-prompt", json={"idea": prompt}, timeout=30
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "prompt": prompt,
                "description": description,
                "latency_ms": round(elapsed * 1000, 2),
                "improved_length": len(result.get("improved_prompt", "")),
                "has_role": "ROLE" in result.get("improved_prompt", "").upper(),
                "has_directive": "DIRECTIVE"
                in result.get("improved_prompt", "").upper(),
                "has_framework": "FRAMEWORK"
                in result.get("improved_prompt", "").upper(),
                "has_guardrails": "GUARDRAILS"
                in result.get("improved_prompt", "").upper(),
            }
        else:
            return {
                "success": False,
                "prompt": prompt,
                "description": description,
                "error": f"HTTP {response.status_code}",
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "prompt": prompt,
            "description": description,
            "error": str(e),
            "latency_ms": round(elapsed * 1000, 2),
        }


def main():
    """Ejecutar tests con prompts genéricos."""
    print("🧪 Testing DSPy PromptImprover con Prompts Genéricos\n")

    # Prompts genéricos para probar
    test_cases = [
        {"prompt": "Write hello world", "description": "Simple - Básico"},
        {"prompt": "Create marketing campaign", "description": "Marketing - Medio"},
        {"prompt": "Design database schema", "description": "Técnico - Alto"},
        {"prompt": "Plan project timeline", "description": "Management - Medio"},
        {"prompt": "Build API documentation", "description": "Documentation - Alto"},
        {"prompt": "Debug Python function", "description": "Debugging - Básico"},
        {"prompt": "Optimize SQL query", "description": "Performance - Alto"},
        {"prompt": "Create user flow diagram", "description": "Design - Medio"},
        {"prompt": "Write unit tests", "description": "Testing - Alto"},
        {"prompt": "Analyze customer feedback", "description": "Analytics - Medio"},
    ]

    results = []
    successes = 0
    failures = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(test_cases)}")
        print(f"Prompt: {test_case['prompt']}")
        print(f"Descripción: {test_case['description']}")
        print(f"{'=' * 60}")

        result = test_prompt(test_case["prompt"], test_case["description"])
        results.append(result)

        if result["success"]:
            successes += 1
            print(f"✅ ÉXITO - Latency: {result['latency_ms']}ms")
            print(f"   Longitud prompt mejorado: {result['improved_length']} chars")
            print(f"   Tiene ROLE: {result['has_role']}")
            print(f"   Tiene DIRECTIVE: {result['has_directive']}")
            print(f"   Tiene FRAMEWORK: {result['has_framework']}")
            print(f"   Tiene GUARDRAILS: {result['has_guardrails']}")
        else:
            failures += 1
            print(f"❌ FALLO - Error: {result.get('error', 'Unknown')}")

        time.sleep(1)  # Evitar rate limiting

    # Resumen
    print(f"\n{'=' * 60}")
    print("📊 RESUMEN DE RESULTADOS")
    print(f"{'=' * 60}")
    print(f"Total tests: {len(results)}")
    print(f"✅ Exitosos: {successes} ({100 * successes // len(results)}%)")
    print(f"❌ Fallados: {failures} ({100 * failures // len(results)}%)")

    if successes > 0:
        successful_results = [r for r in results if r["success"]]
        avg_latency = sum(r["latency_ms"] for r in successful_results) / len(
            successful_results
        )
        avg_length = sum(r["improved_length"] for r in successful_results) / len(
            successful_results
        )

        print(f"\n📈 Métricas de Exitosos:")
        print(f"   Latencia promedio: {avg_latency:.2f}ms")
        print(f"   Longitud promedio output: {avg_length:.0f} chars")
        print(
            f"   Promedio con ROLE: {100 * sum(r['has_role'] for r in successful_results) // len(successful_results)}%"
        )
        print(
            f"   Promedio con DIRECTIVE: {100 * sum(r['has_directive'] for r in successful_results) // len(successful_results)}%"
        )
        print(
            f"   Promedio con FRAMEWORK: {100 * sum(r['has_framework'] for r in successful_results) // len(successful_results)}%"
        )
        print(
            f"   Promedio con GUARDRAILS: {100 * sum(r['has_guardrails'] for r in successful_results) // len(successful_results)}%"
        )

    # Variabilidad - revisar si outputs son diferentes para inputs similares
    print(f"\n🔄 Análisis de Variabilidad:")
    print(f"   ¿Cambian outputs para inputs similares? Need revisión manual")

    # Consistencia - revisar si estructura es consistente
    print(f"\n🎯 Consistencia de Estructura:")
    print(f"   ¿Todos los exitosos tienen ROLE/DIRECTIVE/FRAMEWORK/GUARDRAILS?")
    consistent_structure = all(
        [
            r["has_role"]
            and r["has_directive"]
            and r["has_framework"]
            and r["has_guardrails"]
            for r in results
            if r["success"]
        ]
    )
    print(f"   {consistent_structure and '✅ SÍ' or '❌ NO'}")

    # Calidad - outputs deben ser significativamente más largos que inputs
    print(f"\n✨ Mejora de Calidad:")
    if successful_results:
        avg_improvement = avg_length / sum(
            len(test_case["prompt"]) for test_case in test_cases
        )
        print(f"   Ratio improvement promedio: {avg_improvement:.1f}x")


if __name__ == "__main__":
    # Primero check si backend está corriendo
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ Backend DSPy está corriendo")
            main()
        else:
            print(f"❌ Backend respondió con HTTP {health.status_code}")
    except Exception as e:
        print(f"❌ No se pudo conectar al backend: {e}")
        print("💡 Asegúrate de ejecutar: python main.py")
