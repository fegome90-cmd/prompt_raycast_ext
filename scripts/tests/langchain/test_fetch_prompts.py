"""Simple tests for LangChainHubFetcher (no pytest required)."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from scripts.langchain.fetch_prompts import LangChainHubFetcher


def test_init_with_api_key():
    """Test initialization with explicit API key."""
    print("Testing init with API key...")
    fetcher = LangChainHubFetcher(api_key="lsv2_test_key")
    assert fetcher.api_key == "lsv2_test_key"
    assert os.environ["LANGCHAIN_API_KEY"] == "lsv2_test_key"
    print("✓ init with API key works")


def test_init_from_env():
    """Test initialization reading API key from environment."""
    print("\nTesting init from environment...")
    os.environ["LANGCHAIN_API_KEY"] = "lsv2_env_key"
    fetcher = LangChainHubFetcher()
    assert fetcher.api_key == "lsv2_env_key"
    print("✓ init from env works")


def test_init_missing_api_key():
    """Test initialization fails when no API key is available."""
    print("\nTesting init with missing API key...")
    original_key = os.environ.pop("LANGCHAIN_API_KEY", None)
    try:
        try:
            LangChainHubFetcher()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "LANGCHAIN_API_KEY not set" in str(e)
            print("✓ init with missing API key raises ValueError")
    finally:
        if original_key:
            os.environ["LANGCHAIN_API_KEY"] = original_key


def test_to_candidates_file_basic():
    """Test to_candidates_file without converter."""
    print("\nTesting to_candidates_file (basic)...")
    fetcher = LangChainHubFetcher(api_key="test_key")
    fetched = [
        {
            "handle": "test/handle1",
            "name": "Test Prompt 1",
            "template": "You are a helpful assistant.",
            "tags": ["agent", "react"]
        },
        {
            "handle": "test/handle2",
            "name": "Test Prompt 2",
            "template": "Answer the question.",
            "tags": ["qa"]
        }
    ]

    result = fetcher.to_candidates_file(fetched)

    assert "metadata" in result
    assert "candidates" in result
    assert result["metadata"]["total_fetched"] == 2
    assert result["metadata"]["handles"] == ["test/handle1", "test/handle2"]
    assert "fetched_at" in result["metadata"]
    assert len(result["candidates"]) == 2
    assert result["candidates"][0]["handle"] == "test/handle1"
    assert result["candidates"][1]["handle"] == "test/handle2"
    print("✓ to_candidates_file (basic) works")


def test_to_candidates_file_with_converter():
    """Test to_candidates_file with FormatConverter."""
    print("\nTesting to_candidates_file (with converter)...")

    class MockConverter:
        def to_dspy_format(self, prompt_data):
            return {
                "inputs": {"question": "What is the task?"},
                "outputs": {"answer": "The answer"},
                "metadata": {"source": prompt_data["handle"]}
            }

    fetcher = LangChainHubFetcher(api_key="test_key")
    fetched = [
        {
            "handle": "test/handle1",
            "name": "Test Prompt",
            "template": "You are a helpful assistant.",
            "tags": ["agent"]
        }
    ]

    converter = MockConverter()
    result = fetcher.to_candidates_file(fetched, converter)

    assert "converted" in result["candidates"][0]
    assert result["candidates"][0]["converted"]["inputs"]["question"] == "What is the task?"
    assert result["candidates"][0]["converted"]["metadata"]["source"] == "test/handle1"
    print("✓ to_candidates_file (with converter) works")


def test_to_candidates_file_structure():
    """Test that output structure matches specification."""
    print("\nTesting output structure...")
    fetcher = LangChainHubFetcher(api_key="test_key")
    fetched = [
        {
            "handle": "test/handle",
            "name": "Test",
            "template": "Template text",
            "tags": ["tag1"]
        }
    ]

    result = fetcher.to_candidates_file(fetched)

    # Check metadata structure
    assert "fetched_at" in result["metadata"]
    assert "total_fetched" in result["metadata"]
    assert "handles" in result["metadata"]

    # Check candidates structure
    candidate = result["candidates"][0]
    assert "handle" in candidate
    assert "name" in candidate
    assert "template" in candidate
    print("✓ Output structure matches specification")


if __name__ == "__main__":
    print("=" * 60)
    print("Running LangChainHubFetcher tests")
    print("=" * 60)

    try:
        test_init_with_api_key()
        test_init_from_env()
        test_init_missing_api_key()
        test_to_candidates_file_basic()
        test_to_candidates_file_with_converter()
        test_to_candidates_file_structure()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
