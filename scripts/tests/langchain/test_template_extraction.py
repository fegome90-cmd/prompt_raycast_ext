#!/usr/bin/env python3
"""Test template extraction from LangChain objects."""

import sys
from pathlib import Path

# Add langchain directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'langchain'))

from fetch_prompts import _extract_template_from_langchain_object


class MockPromptTemplate:
    """Mock PromptTemplate for testing."""

    def __init__(self, template):
        self.template = template
        self.input_variables = ['question', 'context']


class MockChatPromptTemplate:
    """Mock ChatPromptTemplate for testing."""

    def __init__(self, messages):
        self.messages = messages


class MockHumanMessagePromptTemplate:
    """Mock HumanMessagePromptTemplate for testing."""

    def __init__(self, prompt):
        self.prompt = prompt


class MockMessagesPlaceholder:
    """Mock MessagesPlaceholder for testing."""

    def __init__(self, template):
        # Simulate the bug where .template returns __str__ representation
        self.template = template  # This is the dirty string

    def __str__(self):
        """Return the dirty template string."""
        return self.template


def test_simple_prompt_template():
    """Test extraction from simple PromptTemplate."""
    print("\n=== Test 1: Simple PromptTemplate ===")

    template_text = """You are a helpful assistant.

Answer the following question: {question}"""

    mock_prompt = MockPromptTemplate(template_text)

    result = _extract_template_from_langchain_object(mock_prompt)

    print(f"Input template:\n{template_text}")
    print(f"\nExtracted template:\n{result}")

    assert result == template_text, f"Expected clean template, got: {result}"
    print("✓ PASSED")


def test_chat_prompt_template():
    """Test extraction from ChatPromptTemplate."""
    print("\n=== Test 2: ChatPromptTemplate ===")

    template_text = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

Question: {question}
Context: {context}
Answer:"""

    # Simulate the structure of ChatPromptTemplate
    inner_prompt = MockPromptTemplate(template_text)
    human_msg = MockHumanMessagePromptTemplate(inner_prompt)
    chat_prompt = MockChatPromptTemplate([human_msg])

    result = _extract_template_from_langchain_object(chat_prompt)

    print(f"Expected template:\n{template_text}")
    print(f"\nExtracted template:\n{result}")

    assert result == template_text, f"Expected clean template, got: {result}"
    print("✓ PASSED")


def test_dirty_template_attribute():
    """Test extraction when .template contains __str__ representation (the bug)."""
    print("\n=== Test 3: Dirty template attribute (THE BUG) ===")

    # Note: The actual LangChain template has " \n" (space before newline)
    # This is how it's stored in LangChain Hub
    clean_template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question}
Context: {context}
Answer:"""

    dirty_template = """input_variables=['context', 'question'] input_types={} partial_variables={} metadata={'lc_hub_owner': 'rlm', 'lc_hub_repo': 'rag-prompt', 'lc_hub_commit_hash': '50442af133e61576e74536c6556cefe1fac147cad032f4377b60c436e6cdcb6e'} messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['context', 'question'], input_types={}, partial_variables={}, template=\"You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\\nQuestion: {question} \\nContext: {context} \\nAnswer:\"), additional_kwargs={})]"""

    # Create mock object with dirty template
    mock_prompt = MockMessagesPlaceholder(dirty_template)

    result = _extract_template_from_langchain_object(mock_prompt)

    print(f"Dirty input (first 200 chars):\n{dirty_template[:200]}...")
    print(f"\nExpected clean template:\n{clean_template}")
    print(f"\nExtracted template:\n{result}")
    print("\nComparison:")
    print(f"  Expected length: {len(clean_template)}")
    print(f"  Extracted length: {len(result)}")
    print(f"  Match: {result == clean_template}")

    # Check that key parts are present
    assert "You are an assistant for question-answering tasks" in result
    assert "{question}" in result
    assert "{context}" in result
    assert "Answer:" in result
    assert not result.startswith("input_variables="), "Template should not start with 'input_variables='"
    print("✓ PASSED - Successfully extracted clean template from dirty string!")


def test_prompt_with_variables():
    """Test extraction from template with variables."""
    print("\n=== Test 4: Prompt with variables ===")

    template_text = """Answer the following questions as best you can. You have access to the following tools:

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

    mock_prompt = MockPromptTemplate(template_text)

    result = _extract_template_from_langchain_object(mock_prompt)

    print(f"Input template (first 200 chars):\n{template_text[:200]}...")
    print(f"\nExtracted template (first 200 chars):\n{result[:200]}...")

    assert result == template_text, f"Expected template with variables, got: {result}"
    print("✓ PASSED")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TESTING TEMPLATE EXTRACTION FROM LANGCHAIN OBJECTS")
    print("=" * 70)

    try:
        test_simple_prompt_template()
        test_chat_prompt_template()
        test_dirty_template_attribute()
        test_prompt_with_variables()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
