"""Tests for FormatConverter class.

Tests cover various template formats, component extraction, framework detection,
and edge cases to ensure robust conversion from LangChain to DSPy format.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from scripts.langchain.convert_to_dspy_format import FormatConverter


def test_to_dspy_format_basic():
    """Test basic conversion with minimal prompt."""
    print("Testing basic conversion...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "test/basic",
        "name": "Basic",
        "template": "You are a helpful assistant.",
        "tags": []
    }

    result = converter.to_dspy_format(lc_prompt)

    # Verify structure
    assert "inputs" in result
    assert "outputs" in result
    assert "metadata" in result

    # Verify inputs
    assert "original_idea" in result["inputs"]
    assert "context" in result["inputs"]
    assert result["inputs"]["context"] == ""

    # Verify outputs
    assert "improved_prompt" in result["outputs"]
    assert "role" in result["outputs"]
    assert "directive" in result["outputs"]
    assert "framework" in result["outputs"]
    assert "guardrails" in result["outputs"]

    # Verify metadata
    assert result["metadata"]["source"] == "langchain-hub"
    assert result["metadata"]["source_handle"] == "test/basic"
    assert result["metadata"]["source_name"] == "Basic"

    print("✓ Basic conversion works")


def test_to_dspy_format_with_tags():
    """Test conversion with tags."""
    print("\nTesting conversion with tags...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "hwchase17/react",
        "name": "React",
        "template": "You are a ReAct agent. Think step by step.",
        "tags": ["agent", "react", "reasoning"]
    }

    result = converter.to_dspy_format(lc_prompt)

    assert result["metadata"]["tags"] == ["agent", "react", "reasoning"]
    # Framework should be detected from template/tags
    assert result["outputs"]["framework"] in ["ReAct", "Chain-of-Thought"]

    print("✓ Conversion with tags works")


def test_to_dspy_format_empty_template():
    """Test conversion with empty template."""
    print("\nTesting conversion with empty template...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "test/empty",
        "name": "Empty",
        "template": "",
        "tags": []
    }

    result = converter.to_dspy_format(lc_prompt)

    # Should handle gracefully with defaults
    assert result["outputs"]["role"] == "AI Assistant"
    assert result["outputs"]["improved_prompt"] == ""
    assert isinstance(result["inputs"]["original_idea"], str)

    print("✓ Empty template handled correctly")


def test_extract_role():
    """Test role extraction from various patterns."""
    print("\nTesting role extraction...")
    converter = FormatConverter()

    # Test "You are a..." pattern
    role1 = converter._extract_role("You are a helpful assistant. Answer questions.")
    assert role1 == "helpful assistant"

    # Test "Act as..." pattern
    role2 = converter._extract_role("Act as a software engineer. Write code.")
    assert "software engineer" in role2.lower()

    # Test "Role: ..." pattern
    role3 = converter._extract_role("Role: Data Analyst\nYour task is to analyze data.")
    assert "Data Analyst" in role3

    # Test no role found
    role4 = converter._extract_role("This is just some text without a role definition.")
    assert role4 == "AI Assistant"

    print("✓ Role extraction works")


def test_extract_directive():
    """Test directive extraction."""
    print("\nTesting directive extraction...")
    converter = FormatConverter()

    # Test task statement
    dir1 = converter._extract_directive("You are an assistant.\nYour task is to help users write better code.\nProvide examples.")
    assert "help users" in dir1.lower()

    # Test goal statement
    dir2 = converter._extract_directive("Your goal is to summarize text accurately and concisely.")
    assert "summarize" in dir2.lower()

    # Test first paragraph fallback
    dir3 = converter._extract_directive("You are a writing assistant.\n\nHelp users improve their writing.")
    assert "help users" in dir3.lower() or "writing" in dir3.lower()

    print("✓ Directive extraction works")


def test_detect_framework():
    """Test framework detection."""
    print("\nTesting framework detection...")
    converter = FormatConverter()

    # Test ReAct from template
    fw1 = converter._detect_framework("Use ReAct reasoning. Think step by step.")
    assert fw1 == "ReAct"

    # Test ReAct from tags
    fw2 = converter._detect_framework("Generic agent prompt.", tags=["react", "agent"])
    assert fw2 == "ReAct"

    # Test Chain-of-Thought
    fw3 = converter._detect_framework("Think step by step before answering.")
    assert fw3 == "Chain-of-Thought"

    # Test Decomposition
    fw4 = converter._detect_framework("Break down the problem into smaller steps.")
    assert fw4 == "Decomposition"

    # Test no framework
    fw5 = converter._detect_framework("Just answer the question directly.")
    assert fw5 == ""

    print("✓ Framework detection works")


def test_extract_guardrails():
    """Test guardrail extraction."""
    print("\nTesting guardrail extraction...")
    converter = FormatConverter()

    # Test "Do not" pattern
    guard1 = converter._extract_guardrails("Do not share personal information. Do not lie.")
    assert "personal information" in guard1.lower()
    assert "lie" in guard1.lower()

    # Test "Never" pattern
    guard2 = converter._extract_guardrails("Never make up facts. Never hallucinate.")
    assert "facts" in guard2.lower()

    # Test "Must not" pattern
    guard3 = converter._extract_guardrails("You must not disclose confidential data.")
    assert "confidential" in guard3.lower()

    # Test no guardrails
    guard4 = converter._extract_guardrails("Just help users with their questions.")
    assert guard4 == ""

    print("✓ Guardrail extraction works")


def test_generate_synthetic_idea():
    """Test synthetic idea generation."""
    print("\nTesting synthetic idea generation...")
    converter = FormatConverter()

    # Test with framework
    idea1 = converter._generate_synthetic_idea(
        template="You are a ReAct agent.",
        role="ReAct agent",
        framework="ReAct",
        handle="hwchase17/react"
    )
    assert "react" in idea1.lower()

    # Test with role
    idea2 = converter._generate_synthetic_idea(
        template="You are a data analyst.",
        role="data analyst",
        framework="",
        handle="test/analyst"
    )
    assert "data analyst" in idea2.lower()

    # Test minimal info
    idea3 = converter._generate_synthetic_idea(
        template="Help me.",
        role="AI Assistant",
        framework="",
        handle="test/basic"
    )
    assert isinstance(idea3, str)
    assert len(idea3) > 0

    print("✓ Synthetic idea generation works")


def test_full_conversion_react_agent():
    """Test full conversion with typical ReAct agent prompt."""
    print("\nTesting full conversion with ReAct agent...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "hwchase17/react",
        "name": "ReAct Agent",
        "template": """You are a ReAct agent!

Your task is to answer questions by using the following format:
Thought: think about what to do
Action: the action to take
Observation: the result of the action
... (repeat)

Do not make up information. Never hallucinate facts.

Use the available tools to find accurate information.""",
        "tags": ["agent", "react", "reasoning"]
    }

    result = converter.to_dspy_format(lc_prompt)

    # Verify all components extracted
    assert "ReAct" in result["outputs"]["role"]
    assert result["outputs"]["framework"] in ["ReAct", "Chain-of-Thought"]
    assert "answer questions" in result["outputs"]["directive"].lower()
    assert len(result["outputs"]["guardrails"]) > 0  # Should find constraints

    # Verify metadata
    assert result["metadata"]["source_handle"] == "hwchase17/react"

    print("✓ Full conversion with ReAct agent works")


def test_full_conversion_code_agent():
    """Test full conversion with code-related agent."""
    print("\nTesting full conversion with code agent...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "hwchase17/openai-functions",
        "name": "OpenAI Functions",
        "template": """You are an AI programming assistant.

Your role is to help users write, debug, and understand code.

Constraints:
- Do not write vulnerable code
- Must follow best practices
- Never expose sensitive data

Think through problems step by step.""",
        "tags": ["coding", "programming"]
    }

    result = converter.to_dspy_format(lc_prompt)

    # Verify extraction
    assert "programming" in result["outputs"]["role"].lower() or "assistant" in result["outputs"]["role"].lower()
    assert result["outputs"]["framework"] in ["Chain-of-Thought", ""]  # "step by step"
    assert len(result["outputs"]["guardrails"]) > 0  # Should find constraints

    print("✓ Full conversion with code agent works")


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")
    converter = FormatConverter()

    # Very long template
    long_text = "You are an assistant. " + "Provide helpful responses. " * 100
    lc_prompt1 = {
        "handle": "test/long",
        "name": "Long",
        "template": long_text,
        "tags": []
    }
    result1 = converter.to_dspy_format(lc_prompt1)
    assert result1["outputs"]["improved_prompt"] == long_text

    # Special characters
    template2 = "You are a <test> agent. Use $variables & [brackets]!"
    lc_prompt2 = {
        "handle": "test/special",
        "name": "Special",
        "template": template2,
        "tags": []
    }
    result2 = converter.to_dspy_format(lc_prompt2)
    assert result2["outputs"]["improved_prompt"] == template2

    # Unicode characters
    template3 = "You are a helpful assistant. 你好! Hola! こんにちは!"
    lc_prompt3 = {
        "handle": "test/unicode",
        "name": "Unicode",
        "template": template3,
        "tags": []
    }
    result3 = converter.to_dspy_format(lc_prompt3)
    assert result3["outputs"]["improved_prompt"] == template3

    print("✓ Edge cases handled correctly")


def test_missing_optional_fields():
    """Test conversion with missing optional fields."""
    print("\nTesting with missing optional fields...")
    converter = FormatConverter()

    lc_prompt = {
        "handle": "test/minimal"
    }

    result = converter.to_dspy_format(lc_prompt)

    # Should use defaults
    assert result["outputs"]["improved_prompt"] == ""
    assert result["outputs"]["role"] == "AI Assistant"
    assert result["metadata"]["source_name"] == "test/minimal"
    assert result["metadata"]["tags"] == []

    print("✓ Missing optional fields handled with defaults")


if __name__ == "__main__":
    print("=" * 60)
    print("Running FormatConverter tests")
    print("=" * 60)

    try:
        test_to_dspy_format_basic()
        test_to_dspy_format_with_tags()
        test_to_dspy_format_empty_template()
        test_extract_role()
        test_extract_directive()
        test_detect_framework()
        test_extract_guardrails()
        test_generate_synthetic_idea()
        test_full_conversion_react_agent()
        test_full_conversion_code_agent()
        test_edge_cases()
        test_missing_optional_fields()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
