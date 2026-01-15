#!/usr/bin/env python3
"""Test rápido de DSPy PromptImprover con prompts genéricos"""

import time

import requests

API_URL = "http://localhost:8001/api/v1/improve-prompt"


def test_prompt(prompt_text: str, test_name: str):
    """Prueba un prompt"""
    try:
        start = time.time()
        resp = requests.post(API_URL, json={"idea": prompt_text}, timeout=30)
        elapsed = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            improved = data.get("improved_prompt", "")
            has_all_sections = all(
                [
                    "ROLE" in improved.upper(),
                    "DIRECTIVE" in improved.upper(),
                    "FRAMEWORK" in improved.upper(),
                    "GUARDRAILS" in improved.upper(),
                ]
            )
            print(
                f"✅ {test_name}: {elapsed:.0f}ms | {len(improved)} chars | Secciones: {has_all_sections}"
            )
            return {
                "success": True,
                "has_sections": has_all_sections,
                "length": len(improved),
            }
        else:
            print(f"❌ {test_name}: HTTP {resp.status_code}")
            return {"success": False}
    except Exception as e:
        print(f"❌ {test_name}: {e}")
        return {"success": False}


def main():
    print("🧪 Testing DSPy PromptImprover\n")

    # Health check
    try:
        health = requests.get("http://localhost:8001/health", timeout=5)
        if health.status_code == 200:
            print("✅ Backend online\n")
    except:
        print("❌ Backend offline. Inicia: python main.py\n")
        return

    # Tests
    tests = [
        ("Write hello world", "Simple"),
        ("Create marketing campaign", "Marketing"),
        ("Design database schema", "Tech - SQL"),
        ("Plan project timeline", "Project mgmt"),
        ("Build API documentation", "Docs"),
        ("Debug Python function", "Debugging"),
        ("Optimize SQL query", "Performance"),
        ("Create user flow", "Design"),
        ("Write unit tests", "Testing"),
    ]

    results = []
    for prompt, name in tests:
        results.append(test_prompt(prompt, name))

    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    success_count = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"Exitosos: {success_count}/{total} ({success_count * 100 // total}%)")

    if success_count > 0:
        successful = [r for r in results if r["success"]]
        avg_len = sum(r["length"] for r in successful) / len(successful)
        all_sections = all(r["has_sections"] for r in successful)

        print(f"Longitud promedio: {avg_len:.0f} chars")
        print(f"Todos con ROLE/DIRECTIVE/FRAMEWORK/GUARDRAILS: {all_sections}")

        if all_sections and avg_len > 300:
            print("\n✅ MVP FUNCIONA - Estructura consistente y calidad aceptable")
        elif avg_len > 300:
            print("\n⚠️ MVP FUNCIONA - Longitud OK pero estructura inconsistente")
        else:
            print("\n❌ MVP NECESITA MEJORAS - Longitud o estructura insuficiente")


if __name__ == "__main__":
    main()
