#!/usr/bin/env python3
"""Test unified few-shot pool merge functionality."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'data'))

from merge_unified_pool import (
    compute_io_hash,
    normalize_example,
    load_dataset,
    merge_datasets,
    generate_statistics
)


def test_compute_io_hash_nested():
    """Test hash computation with nested schema (inputs/outputs)."""
    example = {
        'inputs': {'original_idea': 'test input'},
        'outputs': {'improved_prompt': 'test output'}
    }
    hash_val = compute_io_hash(example)
    expected = '25aeadca568ceb044cef7ed1fe5c247ad09c2e1817c3da6d9c298613d822ea84'
    assert hash_val == expected, f"Expected {expected}, got {hash_val}"
    print("✓ test_compute_io_hash_nested passed")


def test_compute_io_hash_flat():
    """Test hash computation with flat schema (input/output)."""
    example = {
        'input': 'test input',
        'output': 'test output'
    }
    hash_val = compute_io_hash(example)
    expected = '25aeadca568ceb044cef7ed1fe5c247ad09c2e1817c3da6d9c298613d822ea84'
    assert hash_val == expected, f"Expected {expected}, got {hash_val}"
    print("✓ test_compute_io_hash_flat passed")


def test_normalize_example_nested():
    """Test normalization of already-nested example."""
    example = {
        'inputs': {'original_idea': 'test'},
        'outputs': {'improved_prompt': 'result'},
        'metadata': {'key': 'value'}
    }
    normalized = normalize_example(example)
    assert normalized == example, "Nested example should be returned unchanged"
    print("✓ test_normalize_example_nested passed")


def test_normalize_example_flat():
    """Test normalization of flat example."""
    example = {
        'input': 'test input',
        'output': 'test output',
        'metadata': {'framework': 'cot'}
    }
    normalized = normalize_example(example)
    assert 'inputs' in normalized, "Should have inputs field"
    assert 'outputs' in normalized, "Should have outputs field"
    assert normalized['inputs']['original_idea'] == 'test input', "Input should be mapped correctly"
    assert normalized['outputs']['improved_prompt'] == 'test output', "Output should be mapped correctly"
    assert normalized['outputs']['framework'] == 'cot', "Framework should be preserved"
    print("✓ test_normalize_example_flat passed")


def test_load_dataset_missing():
    """Test loading non-existent dataset returns empty list."""
    with TemporaryDirectory() as tmpdir:
        result = load_dataset(Path(tmpdir) / 'nonexistent.json')
        assert result == [], f"Expected empty list, got {result}"
    print("✓ test_load_dataset_missing passed")


def test_load_dataset_valid():
    """Test loading valid JSON dataset."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / 'test.json'
        test_data = [{'input': 'test'}]
        test_file.write_text(json.dumps(test_data))

        result = load_dataset(test_file)
        assert result == test_data, f"Expected {test_data}, got {result}"
    print("✓ test_load_dataset_valid passed")


def test_merge_datasets_deduplication():
    """Test cross-source deduplication."""
    datasets = {
        'source1.json': [
            {'inputs': {'original_idea': 'same'}, 'outputs': {'improved_prompt': 'result'}}
        ],
        'source2.json': [
            {'inputs': {'original_idea': 'same'}, 'outputs': {'improved_prompt': 'result'}}
        ]
    }

    merged = merge_datasets(datasets)
    assert len(merged) == 1, f"Expected 1 unique example, got {len(merged)}"
    assert merged[0]['metadata']['duplication_status'] == 'unique', "Should be marked as unique"
    assert 'io_hash' in merged[0]['metadata'], "Should have io_hash"
    print("✓ test_merge_datasets_deduplication passed")


def test_merge_datasets_source_tracking():
    """Test that source metadata is tracked correctly."""
    datasets = {
        'source1.json': [
            {'inputs': {'original_idea': 'test1'}, 'outputs': {'improved_prompt': 'result1'}}
        ],
        'source2.json': [
            {'inputs': {'original_idea': 'test2'}, 'outputs': {'improved_prompt': 'result2'}}
        ]
    }

    merged = merge_datasets(datasets)
    assert len(merged) == 2, f"Expected 2 examples, got {len(merged)}"

    sources = {ex['metadata']['source_file'] for ex in merged}
    assert sources == {'source1.json', 'source2.json'}, f"Expected both sources, got {sources}"
    print("✓ test_merge_datasets_source_tracking passed")


def test_generate_statistics():
    """Test statistics generation."""
    pool = [
        {
            'metadata': {'source_file': 'source1.json'},
            'outputs': {'framework': 'cot'}
        },
        {
            'metadata': {'source_file': 'source1.json'},
            'outputs': {'framework': 'react'}
        },
        {
            'metadata': {'source_file': 'source2.json'},
            'outputs': {'framework': 'cot'}
        }
    ]

    stats = generate_statistics(pool)
    assert stats['total_examples'] == 3, f"Expected 3 total, got {stats['total_examples']}"
    assert stats['by_source']['source1.json'] == 2, f"Expected 2 from source1, got {stats['by_source']['source1.json']}"
    assert stats['by_source']['source2.json'] == 1, f"Expected 1 from source2, got {stats['by_source']['source2.json']}"
    assert stats['by_framework']['cot'] == 2, f"Expected 2 cot, got {stats['by_framework']['cot']}"
    assert stats['by_framework']['react'] == 1, f"Expected 1 react, got {stats['by_framework']['react']}"
    print("✓ test_generate_statistics passed")


def test_schema_normalization_mixed():
    """Test normalization with mixed schemas."""
    datasets = {
        'nested.json': [
            {'inputs': {'original_idea': 'test1'}, 'outputs': {'improved_prompt': 'result1'}}
        ],
        'flat.json': [
            {'input': 'test2', 'output': 'result2', 'metadata': {'framework': 'cot'}}
        ]
    }

    merged = merge_datasets(datasets)

    # All should be normalized to nested schema
    for ex in merged:
        assert 'inputs' in ex, "All examples should have inputs"
        assert 'outputs' in ex, "All examples should have outputs"
        assert 'metadata' in ex, "All examples should have metadata"

    # Check flat example was normalized correctly
    flat_ex = [ex for ex in merged if ex['metadata']['source_file'] == 'flat.json'][0]
    assert flat_ex['inputs']['original_idea'] == 'test2', "Flat input should be normalized"
    assert flat_ex['outputs']['improved_prompt'] == 'result2', "Flat output should be normalized"
    assert flat_ex['outputs']['framework'] == 'cot', "Framework should be preserved"
    print("✓ test_schema_normalization_mixed passed")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_compute_io_hash_nested,
        test_compute_io_hash_flat,
        test_normalize_example_nested,
        test_normalize_example_flat,
        test_load_dataset_missing,
        test_load_dataset_valid,
        test_merge_datasets_deduplication,
        test_merge_datasets_source_tracking,
        test_generate_statistics,
        test_schema_normalization_mixed
    ]

    print("=" * 70)
    print("RUNNING UNIFIED POOL TESTS")
    print("=" * 70)
    print()

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print()
    print("=" * 70)
    if failed == 0:
        print(f"✅ ALL {len(tests)} TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print(f"❌ {failed}/{len(tests)} TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
