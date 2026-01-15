"""Demo script for PromptMetodizer.

Shows how to use the PromptMetodizer to convert LangChain Hub prompts
to DSPy Architect format with intelligent analysis.
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from scripts.langchain.prompt_metodizer import PromptMetodizer


def demo_metodizer():
    """Demonstrate PromptMetodizer with the 4 LangChain prompts."""
    print("=" * 80)
    print("PromptMetodizer Demo - Converting LangChain Prompts to DSPy Architect Format")
    print("=" * 80)

    metodizer = PromptMetodizer()

    # The 4 LangChain Hub prompts
    prompts = {
        "hwchase17/react": {
            "template": """Answer the following questions as best you can. You have access to the following tools:

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
Thought:{agent_scratchpad}""",
            "tags": ["agent", "react"]
        },
        "rlm/rag-prompt": {
            "template": """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question}
Context: {context}
Answer:""",
            "tags": ["rag", "retrieval"]
        },
        "hwchase17/openai-tools-agent": {
            "template": """You are a helpful assistant

{input}""",
            "tags": ["agent", "tools"]
        },
        "hwchase17/self-ask-with-search": {
            "template": """Question: Who lived longer, Muhammad Ali or Alan Turing?
Are follow up questions needed here: Yes.
Follow up: How old was Muhammad Ali when he died?
Intermediate answer: Muhammad Ali was 74 years old when he died.
Follow up: How old was Alan Turing when he died?
Intermediate answer: Alan Turing was 41 years old when he died.
So the final answer is: Muhammad Ali

Question: {input}
Are followup questions needed here:{agent_scratchpad}""",
            "tags": ["agent", "self-ask"]
        }
    }

    results = []

    for handle, prompt_data in prompts.items():
        print(f"\n{'=' * 80}")
        print(f"Processing: {handle}")
        print("=" * 80)

        result = metodizer.metodize_prompt(
            handle=handle,
            template=prompt_data["template"],
            tags=prompt_data["tags"]
        )

        results.append(result)

        # Display results
        print("\n📋 ORIGINAL IDEA (Synthetic Input):")
        print(f"   {result['inputs']['original_idea']}")

        print("\n🎭 ROLE:")
        print(f"   {result['outputs']['role']}")

        print("\n🎯 DIRECTIVE:")
        directive = result['outputs']['directive']
        if len(directive) > 100:
            print(f"   {directive[:100]}...")
        else:
            print(f"   {directive}")

        print("\n🧠 FRAMEWORK:")
        framework = result['outputs']['framework']
        if framework:
            print(f"   {framework} (confidence: {result['metadata']['quality_scores']['framework_confidence']:.2f})")
            # Show evidence
            if result['metadata']['framework_detections']:
                evidence = result['metadata']['framework_detections'][0]['evidence']
                print(f"   Evidence: {', '.join(evidence[:3])}")
        else:
            print("   (none detected)")

        print("\n🛡️ GUARDRAILS:")
        guardrails = result['outputs']['guardrails']
        if guardrails:
            if len(guardrails) > 150:
                print(f"   {guardrails[:150]}...")
            else:
                print(f"   {guardrails}")
        else:
            print("   (none detected)")

        print("\n📊 QUALITY SCORES:")
        scores = result['metadata']['quality_scores']
        print(f"   Role clarity:          {scores['role_clarity']:.2f}")
        print(f"   Directive specificity:  {scores['directive_specificity']:.2f}")
        print(f"   Framework confidence:  {scores['framework_confidence']:.2f}")
        print(f"   Guardrails measurability: {scores['guardrails_measurability']:.2f}")
        print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   Overall quality:        {scores['overall_quality']:.2f}")

        print("\n🔍 DETECTED PATTERNS:")
        patterns = result['metadata']['detected_patterns']
        for pattern in patterns[:5]:
            print(f"   • {pattern}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)

    frameworks = [r['outputs']['framework'] for r in results if r['outputs']['framework']]
    print(f"\n✓ Processed {len(results)} prompts")
    print(f"✓ Detected {len(set(frameworks))} different frameworks: {', '.join(set(frameworks))}")

    avg_quality = sum(r['metadata']['quality_scores']['overall_quality'] for r in results) / len(results)
    print(f"✓ Average quality score: {avg_quality:.2f}")

    # Save results to JSON
    output_file = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/metodized-langchain-prompts.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    print(f"\n{'=' * 80}")
    print("Demo Complete!")
    print("=" * 80)

    return results


if __name__ == "__main__":
    demo_metodizer()
