"""Compare FormatConverter vs PromptMetodizer.

Shows the improvements in extraction quality and analysis depth.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from scripts.langchain.convert_to_dspy_format import FormatConverter
from scripts.langchain.prompt_metodizer import PromptMetodizer


def compare_converters():
    """Compare FormatConverter and PromptMetodizer side-by-side."""
    print("=" * 100)
    print("FormatConverter vs PromptMetodizer - Comparison")
    print("=" * 100)

    # Test with ReAct prompt
    handle = "hwchase17/react"
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    print(f"\n📝 Testing with: {handle}")
    print("=" * 100)

    # FormatConverter
    print("\n🔧 FormatConverter (Basic):")
    print("-" * 100)
    fc = FormatConverter()
    fc_result = fc.to_dspy_format({
        "handle": handle,
        "name": handle,
        "template": template,
        "tags": ["agent", "react"]
    })

    print(f"Role:       {fc_result['outputs']['role']}")
    print(f"Directive:  {fc_result['outputs']['directive']}")
    print(f"Framework:  {fc_result['outputs']['framework']}")
    print(f"Guardrails: {fc_result['outputs']['guardrails'] or '(none)'}")
    print(f"Idea:       {fc_result['inputs']['original_idea']}")

    # PromptMetodizer
    print("\n🧠 PromptMetodizer (Advanced):")
    print("-" * 100)
    pm = PromptMetodizer()
    pm_result = pm.metodize_prompt(
        handle=handle,
        template=template,
        tags=["agent", "react"]
    )

    print(f"Role:       {pm_result['outputs']['role']}")
    print(f"Directive:  {pm_result['outputs']['directive']}")
    print(f"Framework:  {pm_result['outputs']['framework']} (confidence: {pm_result['metadata']['quality_scores']['framework_confidence']:.2f})")
    print(f"Guardrails: {pm_result['outputs']['guardrails'][:80]}..." if len(pm_result['outputs']['guardrails']) > 80 else f"Guardrails: {pm_result['outputs']['guardrails'] or '(none)'}")
    print(f"Idea:       {pm_result['inputs']['original_idea']}")

    print("\nQuality Scores:")
    scores = pm_result['metadata']['quality_scores']
    print(f"  Role clarity:          {scores['role_clarity']:.2f}")
    print(f"  Directive specificity:  {scores['directive_specificity']:.2f}")
    print(f"  Framework confidence:  {scores['framework_confidence']:.2f}")
    print(f"  Guardrails measurability: {scores['guardrails_measurability']:.2f}")
    print(f"  Overall quality:        {scores['overall_quality']:.2f}")

    print("\nDetected Patterns:")
    for pattern in pm_result['metadata']['detected_patterns'][:5]:
        print(f"  • {pattern}")

    print("\nFramework Evidence:")
    evidence = pm_result['metadata']['framework_detections'][0]['evidence']
    for ev in evidence[:3]:
        print(f"  • {ev}")

    # Comparison summary
    print("\n" + "=" * 100)
    print("📊 Key Differences:")
    print("=" * 100)

    improvements = [
        ("Role Extraction",
         fc_result['outputs']['role'],
         pm_result['outputs']['role'],
         "More specific role detection"),

        ("Framework Detection",
         fc_result['outputs']['framework'],
         f"{pm_result['outputs']['framework']} (confidence: {pm_result['metadata']['quality_scores']['framework_confidence']:.2f})",
         "Confidence scoring + evidence"),

        ("Guardrails",
         fc_result['outputs']['guardrails'] or "(none)",
         pm_result['outputs']['guardrails'][:60] + "...",
         "Categorized extraction"),

        ("Quality Metrics",
         "Not available",
         f"Overall: {pm_result['metadata']['quality_scores']['overall_quality']:.2f}",
         "4-dimensional quality scoring"),

        ("Pattern Detection",
         "Not available",
         f"{len(pm_result['metadata']['detected_patterns'])} patterns detected",
         "Variable/structure detection"),
    ]

    for feature, old_val, new_val, benefit in improvements:
        print(f"\n{feature}:")
        print(f"  Old: {old_val}")
        print(f"  New: {new_val}")
        print(f"  ✓ {benefit}")

    print("\n" + "=" * 100)
    print("✨ PromptMetodizer provides deeper analysis and quality metrics!")
    print("=" * 100)


if __name__ == "__main__":
    compare_converters()
