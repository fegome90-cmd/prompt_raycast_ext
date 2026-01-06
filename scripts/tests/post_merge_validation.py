#!/usr/bin/env python3
"""
Post-merge validation tests for LangChain Hub integration.

Tests that the RAG prompt was correctly merged into the unified few-shot pool
and that DSPy KNNFewShot can load the updated pool successfully.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from hashlib import sha256

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from dspy.primitives.example import Example
    from dspy.teleprompt import KNNFewShot
except ImportError:
    print("Warning: DSPy not available, skipping DSPy tests")
    Example = None
    KNNFewShot = None


class PostMergeValidator:
    """Validate unified few-shot pool after LangChain Hub merge."""

    def __init__(self, pool_path: Path):
        """Initialize validator with pool path."""
        self.pool_path = pool_path
        self.pool_data = None
        self.examples = []
        self.test_results = []

    def load_pool(self) -> bool:
        """Load the unified pool from JSON."""
        try:
            with open(self.pool_path, 'r', encoding='utf-8') as f:
                self.pool_data = json.load(f)
            self.examples = self.pool_data.get('examples', [])
            return True
        except Exception as e:
            self._record_test("load_pool", False, f"Failed to load pool: {e}")
            return False

    def _record_test(self, name: str, passed: bool, details: str = ""):
        """Record a test result."""
        self.test_results.append({
            'name': name,
            'passed': passed,
            'details': details
        })
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {details}")

    def test_pool_size(self, expected_min: int = 108) -> bool:
        """Test 1: Pool size increased correctly."""
        actual_size = len(self.examples)
        passed = actual_size >= expected_min
        self._record_test(
            "pool_size",
            passed,
            f"Expected ≥ {expected_min}, got {actual_size}"
        )
        return passed

    def test_rag_framework_present(self) -> bool:
        """Test 2: RAG framework exists in pool."""
        rag_count = 0
        rag_example = None

        for ex in self.examples:
            framework = ex.get('outputs', {}).get('framework', '')
            if framework.lower() == 'rag':
                rag_count += 1
                if rag_example is None:
                    rag_example = ex

        passed = rag_count > 0
        self._record_test(
            "rag_framework_present",
            passed,
            f"Found {rag_count} RAG example(s)"
        )
        return passed

    def test_rag_prompt_structure(self) -> bool:
        """Test 3: RAG prompt has correct structure."""
        rag_examples = [
            ex for ex in self.examples
            if ex.get('outputs', {}).get('framework', '').lower() == 'rag'
        ]

        if not rag_examples:
            self._record_test("rag_prompt_structure", False, "No RAG examples found")
            return False

        rag = rag_examples[0]
        outputs = rag.get('outputs', {})

        # Check required fields
        has_role = bool(outputs.get('role'))
        has_directive = bool(outputs.get('directive'))
        has_framework = outputs.get('framework', '').lower() == 'rag'
        has_guardrails = bool(outputs.get('guardrails'))
        has_improved_prompt = bool(outputs.get('improved_prompt'))

        passed = all([has_role, has_directive, has_framework, has_guardrails, has_improved_prompt])

        details = f"role={has_role}, directive={has_directive}, framework={has_framework}, guardrails={has_guardrails}, improved_prompt={has_improved_prompt}"
        self._record_test("rag_prompt_structure", passed, details)
        return passed

    def test_no_duplicates(self) -> bool:
        """Test 4: No duplicate examples (SHA256)."""
        hashes = set()
        duplicates = []

        for ex in self.examples:
            # Compute hash of (input, output) pair
            inputs = ex.get('inputs', {})
            outputs = ex.get('outputs', {})

            input_text = inputs.get('original_idea', '')
            output_text = outputs.get('improved_prompt', '')

            combined = f"{input_text}|||{output_text}"
            hash_val = sha256(combined.encode()).hexdigest()

            if hash_val in hashes:
                duplicates.append(hash_val)
            else:
                hashes.add(hash_val)

        passed = len(duplicates) == 0
        self._record_test(
            "no_duplicates",
            passed,
            f"Found {len(duplicates)} duplicate(s)"
        )
        return passed

    def test_all_examples_have_metadata(self) -> bool:
        """Test 5: All examples have required metadata."""
        missing_metadata = []

        for i, ex in enumerate(self.examples):
            metadata = ex.get('metadata', {})

            if not metadata.get('source_file'):
                missing_metadata.append(f"example_{i}: missing source_file")

            if not metadata.get('io_hash'):
                missing_metadata.append(f"example_{i}: missing io_hash")

        passed = len(missing_metadata) == 0
        self._record_test(
            "all_examples_have_metadata",
            passed,
            f"{len(missing_metadata)} examples with missing metadata"
        )
        return passed

    def test_rag_source_tracking(self) -> bool:
        """Test 6: RAG example has correct source tracking."""
        rag_examples = [
            ex for ex in self.examples
            if ex.get('outputs', {}).get('framework', '').lower() == 'rag'
        ]

        if not rag_examples:
            self._record_test("rag_source_tracking", False, "No RAG examples found")
            return False

        rag = rag_examples[0]
        metadata = rag.get('metadata', {})
        source = metadata.get('source_file', '')

        # Should come from langchain-validated.json
        passed = 'langchain' in source.lower() or 'validated' in source.lower()

        self._record_test(
            "rag_source_tracking",
            passed,
            f"Source: {source}"
        )
        return passed

    def test_dspy_knnfewshot_load(self) -> bool:
        """Test 7: DSPy KNNFewShot can load the pool."""
        if KNNFewShot is None:
            self._record_test("dspy_knnfewshot_load", None, "DSPy not installed, skipped")
            return True

        try:
            # Convert examples to DSPy Examples
            dspy_examples = []
            for ex in self.examples[:10]:  # Test with first 10
                inputs = ex.get('inputs', {})
                outputs = ex.get('outputs', {})

                dspy_ex = Example(
                    question=inputs.get('original_idea', ''),
                    improved_prompt=outputs.get('improved_prompt', ''),
                    framework=outputs.get('framework', ''),
                    role=outputs.get('role', ''),
                    directive=outputs.get('directive', '')
                )
                dspy_examples.append(dspy_ex)

            # Try to create KNNFewShot with the examples
            knn = KNNFewShot(k=3, trainset=dspy_examples)

            passed = knn is not None and len(knn.trainset) == len(dspy_examples)

            self._record_test(
                "dspy_knnfewshot_load",
                passed,
                f"KNNFewShot loaded {len(knn.trainset)} examples"
            )
            return passed

        except Exception as e:
            self._record_test("dspy_knnfewshot_load", False, f"Error: {e}")
            return False

    def test_rag_variables_present(self) -> bool:
        """Test 8: RAG prompt has required variables."""
        rag_examples = [
            ex for ex in self.examples
            if ex.get('outputs', {}).get('framework', '').lower() == 'rag'
        ]

        if not rag_examples:
            self._record_test("rag_variables_present", False, "No RAG examples found")
            return False

        rag = rag_examples[0]
        improved_prompt = rag.get('outputs', {}).get('improved_prompt', '')

        # Check for RAG-specific variables
        has_context_var = '{context}' in improved_prompt
        has_question_var = '{question}' in improved_prompt

        passed = has_context_var and has_question_var

        self._record_test(
            "rag_variables_present",
            passed,
            f"{{context}}={has_context_var}, {{question}}={has_question_var}"
        )
        return passed

    def test_framework_distribution(self) -> bool:
        """Test 9: Framework distribution is reasonable."""
        framework_counts = {}
        for ex in self.examples:
            fw = ex.get('outputs', {}).get('framework', 'unknown')
            framework_counts[fw] = framework_counts.get(fw, 0) + 1

        # Check that RAG is present
        has_rag = 'rag' in [k.lower() for k in framework_counts.keys()]

        # Check that no single framework dominates > 80%
        total = len(self.examples)
        max_pct = max(framework_counts.values()) / total if total > 0 else 0
        reasonable_dist = max_pct < 0.8

        passed = has_rag and reasonable_dist

        self._record_test(
            "framework_distribution",
            passed,
            f"RAG present: {has_rag}, Max framework %: {max_pct:.1%}"
        )
        return passed

    def test_json_valid(self) -> bool:
        """Test 10: Pool JSON is valid."""
        # Already loaded, just check structure
        has_metadata = 'metadata' in self.pool_data
        has_examples = 'examples' in self.pool_data
        has_total = self.pool_data.get('metadata', {}).get('total_examples') is not None

        passed = has_metadata and has_examples and has_total

        self._record_test(
            "json_valid",
            passed,
            f"metadata={has_metadata}, examples={has_examples}, total={has_total}"
        )
        return passed

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("=" * 80)
        print("POST-MERGE VALIDATION TESTS")
        print("=" * 80)
        print(f"\nPool: {self.pool_path}")
        print(f"Loading pool...")

        if not self.load_pool():
            print("\n❌ Failed to load pool, aborting tests")
            return {'success': False, 'passed': 0, 'failed': 0, 'skipped': 0}

        print(f"Loaded {len(self.examples)} examples\n")
        print("Running tests:\n")

        # Run all tests
        tests = [
            self.test_json_valid,
            self.test_pool_size,
            self.test_rag_framework_present,
            self.test_rag_prompt_structure,
            self.test_no_duplicates,
            self.test_all_examples_have_metadata,
            self.test_rag_source_tracking,
            self.test_rag_variables_present,
            self.test_framework_distribution,
            self.test_dspy_knnfewshot_load,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"  [ERROR] {test.__name__}: {e}")

        # Summary
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = sum(1 for r in self.test_results if r['passed'] is False)
        skipped = sum(1 for r in self.test_results if r['passed'] is None)

        print(f"\n{'=' * 80}")
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Success Rate: {passed / len(self.test_results) * 100:.1f}%")

        if failed == 0:
            print(f"\n✅ All tests passed! Pool is ready for production.")
        else:
            print(f"\n❌ {failed} test(s) failed. Review and fix issues.")

        return {
            'success': failed == 0,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'results': self.test_results
        }


def main():
    """Run post-merge validation."""
    base_path = Path(__file__).parent.parent.parent
    pool_path = base_path / 'datasets/exports/unified-fewshot-pool.json'

    validator = PostMergeValidator(pool_path)
    results = validator.run_all_tests()

    return 0 if results['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
