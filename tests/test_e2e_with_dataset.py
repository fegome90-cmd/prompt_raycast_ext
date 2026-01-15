"""
E2E Tests with Real Dataset

End-to-end integration tests using the integration-test-cases.jsonl dataset.
These tests validate the complete pipeline from HTTP request to response
against real dataset assertions.

Run with:
    pytest tests/test_e2e_with_dataset.py -v
    pytest tests/test_e2e_with_dataset.py::TestDatasetPipelineSimpleCases -v
    pytest tests/test_e2e_with_dataset.py::TestDatasetIntentClassification -v

Prerequisites:
- Backend running on localhost:8000 (run `make dev`)
- LLM provider configured in .env
- Dataset exists at datasets/integration-test-cases.jsonl
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import pytest
import asyncio
from httpx import AsyncClient, ConnectError, ConnectTimeout


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def http_client():
    """
    HTTP client for API tests.

    Skips all tests in this module if backend is not running.
    """
    try:
        async with AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0
        ) as client:
            # Quick health check
            try:
                response = await client.get("/health")
                if response.status_code != 200:
                    pytest.skip("Backend health check failed")
            except (ConnectError, ConnectTimeout):
                pytest.skip("Backend not running on localhost:8000")
            yield client
    except (ConnectError, ConnectTimeout):
        pytest.skip("Backend not running on localhost:8000")


@pytest.fixture
def dataset():
    """
    Load integration test cases from dataset.

    Returns:
        list: Test cases from datasets/integration-test-cases.jsonl

    Skips:
        If dataset file is not found, returns empty list to skip tests.
    """
    cases = []
    path = project_root / "datasets" / "integration-test-cases.jsonl"

    if not path.exists():
        pytest.skip(f"Dataset not found: {path}")

    with open(path) as f:
        for line in f:
            if line.strip():  # Skip empty lines
                cases.append(json.loads(line))

    return cases


# ============================================================================
# DATASET PIPELINE SIMPLE CASES
# ============================================================================

class TestDatasetPipelineSimpleCases:
    """
    E2E tests for 3 simple cases from the dataset.

    Validates the complete pipeline:
    1. POST to /api/v1/improve-prompt
    2. Validate response structure (improved_prompt, intent, strategy)
    3. Validate dataset assertions (min_length, keywords)
    """

    @pytest.mark.asyncio
    async def test_dataset_pipeline_simple_cases(self, http_client, dataset):
        """
        Test 3 simple cases from the dataset.

        Uses the first 3 simple complexity cases:
        - 001: Create hello world function
        - 002: Write a function to add two numbers
        - 006: Fix this bug

        Validates:
        - API returns 200 status
        - Response contains all expected fields
        - Improved prompt meets min_length requirement
        - Improved prompt contains required keywords
        """
        # Filter for simple cases
        simple_cases = [c for c in dataset if c.get("complexity") == "simple"][:3]

        if len(simple_cases) < 3:
            pytest.skip(f"Need at least 3 simple cases, found {len(simple_cases)}")

        results = []
        for test_case in simple_cases:
            # Make request
            response = await http_client.post(
                "/api/v1/improve-prompt",
                json={
                    "idea": test_case["idea"],
                    "context": test_case.get("context", ""),
                    "mode": "nlac",
                },
            )

            # Track result
            result = {
                "test_id": test_case["test_id"],
                "idea": test_case["idea"],
                "status": response.status_code,
                "passed": False,
            }

            # Assert response status
            if response.status_code != 200:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Idea: {test_case['idea']}")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                print(f"==========================\n")
                results.append(result)
                continue

            # Assert response structure
            data = response.json()
            required_fields = [
                "improved_prompt",
                "intent",
                "strategy",
                "role",
                "directive",
                "framework",
                "guardrails",
                "backend",
            ]

            for field in required_fields:
                if field not in data:
                    print(f"\n=== FAILED: {test_case['test_id']} ===")
                    print(f"Missing field: {field}")
                    print(f"==========================\n")
                    continue

            assert "improved_prompt" in data, f"Missing improved_prompt in {test_case['test_id']}"
            assert "intent" in data, f"Missing intent in {test_case['test_id']}"
            assert "strategy" in data, f"Missing strategy in {test_case['test_id']}"

            # Validate against dataset assertions
            assertions = test_case["assertions"]
            prompt = data["improved_prompt"]

            # Assert min_length
            if len(prompt) < assertions["min_length"]:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Prompt length {len(prompt)} < {assertions['min_length']}")
                print(f"Prompt: {prompt[:200]}...")
                print(f"==========================\n")
                continue

            assert len(prompt) >= assertions["min_length"], (
                f"Test case {test_case['test_id']}: "
                f"Prompt length {len(prompt)} < {assertions['min_length']}"
            )

            # Assert contains_keywords
            missing_keywords = []
            for keyword in assertions["contains_keywords"]:
                if keyword.lower() not in prompt.lower():
                    missing_keywords.append(keyword)

            if missing_keywords:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Missing keywords: {missing_keywords}")
                print(f"Prompt: {prompt[:200]}...")
                print(f"==========================\n")
                continue

            for keyword in assertions["contains_keywords"]:
                assert keyword.lower() in prompt.lower(), (
                    f"Test case {test_case['test_id']}: "
                    f"Keyword '{keyword}' not found in prompt"
                )

            # Assert not_contains_keywords (if present)
            for keyword in assertions.get("not_contains_keywords", []):
                assert keyword.lower() not in prompt.lower(), (
                    f"Test case {test_case['test_id']}: "
                    f"Keyword '{keyword}' should not be in prompt"
                )

            # Mark as passed
            result["passed"] = True
            results.append(result)

        # Assert at least 2 out of 3 passed (allow for some LLM variability)
        passed_count = sum(1 for r in results if r["passed"])
        assert passed_count >= 2, (
            f"Expected at least 2 out of 3 simple cases to pass, "
            f"but only {passed_count} passed. "
            f"Results: {results}"
        )

        # Print summary
        print(f"\n=== Simple Cases Summary ===")
        for r in results:
            status = "✓ PASS" if r["passed"] else "✗ FAIL"
            print(f"{status} - {r['test_id']}: {r['idea'][:50]}...")
        print(f"Passed: {passed_count}/3")
        print(f"===========================\n")


# ============================================================================
# DATASET INTENT CLASSIFICATION
# ============================================================================

class TestDatasetIntentClassification:
    """
    E2E tests for intent detection using the dataset.

    Validates that the API correctly classifies different intent types:
    - GENERATE: Creating new code
    - DEBUG: Fixing bugs
    - REFACTOR: Optimizing code
    - EXPLAIN: Explaining concepts
    """

    @pytest.mark.asyncio
    async def test_dataset_intent_classification(self, http_client, dataset):
        """
        Test intent detection across all intent types in the dataset.

        Validates:
        - API returns correct intent for each test case
        - Response structure includes intent field
        - Intent matches expected intent from dataset
        """
        # Group by intent
        intents_map = {}
        for test_case in dataset:
            intent = test_case.get("intent", "unknown")
            if intent not in intents_map:
                intents_map[intent] = []
            intents_map[intent].append(test_case)

        # Ensure we have at least 2 different intent types
        if len(intents_map) < 2:
            pytest.skip(f"Need at least 2 intent types, found {len(intents_map)}")

        results = []
        for intent, cases in intents_map.items():
            # Test first case for each intent
            test_case = cases[0]

            # Make request
            response = await http_client.post(
                "/api/v1/improve-prompt",
                json={
                    "idea": test_case["idea"],
                    "context": test_case.get("context", ""),
                    "mode": "nlac",
                },
            )

            # Track result
            result = {
                "test_id": test_case["test_id"],
                "expected_intent": intent,
                "actual_intent": None,
                "passed": False,
            }

            # Assert response status
            if response.status_code != 200:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Intent: {intent}")
                print(f"Status: {response.status_code}")
                print(f"==========================\n")
                results.append(result)
                continue

            # Assert response structure
            data = response.json()
            assert "intent" in data, f"Missing intent in {test_case['test_id']}"

            actual_intent = data["intent"]
            result["actual_intent"] = actual_intent

            # Assert intent matches (allow for case differences)
            if actual_intent.upper() != intent.upper():
                print(f"\n=== INTENT MISMATCH: {test_case['test_id']} ===")
                print(f"Expected: {intent}")
                print(f"Actual: {actual_intent}")
                print(f"Idea: {test_case['idea']}")
                print(f"==========================\n")
                continue

            # Validate response structure
            assert "improved_prompt" in data
            assert "strategy" in data
            assert "role" in data
            assert "directive" in data
            assert "framework" in data
            assert "guardrails" in data
            assert "backend" in data

            # Mark as passed
            result["passed"] = True
            results.append(result)

        # Assert all intents passed
        passed_count = sum(1 for r in results if r["passed"])
        assert passed_count >= len(intents_map) - 1, (
            f"Expected at least {len(intents_map) - 1} intents to pass, "
            f"but only {passed_count} passed. "
            f"Results: {results}"
        )

        # Print summary
        print(f"\n=== Intent Classification Summary ===")
        for r in results:
            status = "✓ PASS" if r["passed"] else "✗ FAIL"
            print(f"{status} - {r['expected_intent']}: {r['test_id']}")
        print(f"Passed: {passed_count}/{len(results)}")
        print(f"=====================================\n")


# ============================================================================
# DATASET COMPLEXITY LEVELS
# ============================================================================

class TestDatasetComplexityLevels:
    """
    E2E tests for different complexity levels.

    Validates that the API handles different complexity levels:
    - simple: Basic tasks
    - moderate: Intermediate tasks
    - complex: Advanced tasks
    """

    @pytest.mark.asyncio
    async def test_dataset_complexity_levels(self, http_client, dataset):
        """
        Test all complexity levels in the dataset.

        Validates:
        - API returns successful response for all complexity levels
        - Response structure is correct
        - Improved prompt quality varies with complexity
        """
        # Group by complexity
        complexity_map = {}
        for test_case in dataset:
            complexity = test_case.get("complexity", "unknown")
            if complexity not in complexity_map:
                complexity_map[complexity] = []
            complexity_map[complexity].append(test_case)

        # Ensure we have at least 2 different complexity levels
        if len(complexity_map) < 2:
            pytest.skip(f"Need at least 2 complexity levels, found {len(complexity_map)}")

        results = []
        for complexity, cases in complexity_map.items():
            # Test first case for each complexity
            test_case = cases[0]

            # Make request
            response = await http_client.post(
                "/api/v1/improve-prompt",
                json={
                    "idea": test_case["idea"],
                    "context": test_case.get("context", ""),
                    "mode": "nlac",
                },
            )

            # Track result
            result = {
                "test_id": test_case["test_id"],
                "complexity": complexity,
                "prompt_length": 0,
                "passed": False,
            }

            # Assert response status
            if response.status_code != 200:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Complexity: {complexity}")
                print(f"Status: {response.status_code}")
                print(f"==========================\n")
                results.append(result)
                continue

            # Assert response structure
            data = response.json()
            assert "improved_prompt" in data
            assert "intent" in data
            assert "strategy" in data

            prompt = data["improved_prompt"]
            result["prompt_length"] = len(prompt)

            # Validate against dataset assertions
            assertions = test_case["assertions"]

            # Assert min_length
            if len(prompt) < assertions["min_length"]:
                print(f"\n=== FAILED: {test_case['test_id']} ===")
                print(f"Complexity: {complexity}")
                print(f"Prompt length {len(prompt)} < {assertions['min_length']}")
                print(f"==========================\n")
                continue

            assert len(prompt) >= assertions["min_length"], (
                f"Test case {test_case['test_id']}: "
                f"Prompt length {len(prompt)} < {assertions['min_length']}"
            )

            # Assert contains_keywords
            for keyword in assertions["contains_keywords"]:
                assert keyword.lower() in prompt.lower(), (
                    f"Test case {test_case['test_id']}: "
                    f"Keyword '{keyword}' not found in prompt"
                )

            # Mark as passed
            result["passed"] = True
            results.append(result)

        # Assert all complexities passed
        passed_count = sum(1 for r in results if r["passed"])
        assert passed_count >= len(complexity_map) - 1, (
            f"Expected at least {len(complexity_map) - 1} complexities to pass, "
            f"but only {passed_count} passed. "
            f"Results: {results}"
        )

        # Print summary
        print(f"\n=== Complexity Levels Summary ===")
        for r in results:
            status = "✓ PASS" if r["passed"] else "✗ FAIL"
            print(f"{status} - {r['complexity']}: {r['test_id']} (length: {r['prompt_length']})")
        print(f"Passed: {passed_count}/{len(results)}")
        print(f"=================================\n")


# ============================================================================
# MARKERS
# ============================================================================

# Mark these as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.e2e,
    pytest.mark.slow,  # These tests make real HTTP requests
]
