#!/usr/bin/env python3
"""ImportWorkflow CLI for LangChain Hub integration.

This CLI orchestrates the process of fetching, validating, and merging prompts
from LangChain Hub into the unified few-shot pool.

Usage:
    python scripts/langchain/import_workflow.py fetch
    python scripts/langchain/import_workflow.py validate
    python scripts/langchain/import_workflow.py merge
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from hashlib import sha256
from datetime import datetime

# Import LangChain components
from fetch_prompts import LangChainHubFetcher
from convert_to_dspy_format import FormatConverter


# Inline merge functions to avoid import issues
def compute_io_hash(example: Dict[str, Any]) -> str:
    """Compute hash of (input, output) pair for deduplication."""
    # Handle both nested (inputs.original_idea) and flat (input) schemas
    if 'inputs' in example:
        input_text = example['inputs'].get('original_idea', '')
    else:
        input_text = example.get('input', '')

    if 'outputs' in example:
        output_text = example['outputs'].get('improved_prompt', '')
    else:
        output_text = example.get('output', '')

    combined = f"{input_text}|||{output_text}"
    return sha256(combined.encode()).hexdigest()


def normalize_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize example to nested schema {inputs, outputs, metadata}."""
    # Already has nested structure
    if 'inputs' in example and 'outputs' in example:
        return example

    # Flat schema - needs normalization
    return {
        'inputs': {'original_idea': example.get('input', '')},
        'outputs': {
            'improved_prompt': example.get('output', ''),
            'framework': example.get('metadata', {}).get('framework', 'unknown')
        },
        'metadata': example.get('metadata', {})
    }


def merge_datasets(datasets: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merge multiple datasets with cross-source deduplication."""
    all_examples = []

    for source_name, examples in datasets.items():
        print(f"  Loading {source_name}: {len(examples)} examples")

        for ex in examples:
            # Normalize schema
            normalized = normalize_example(ex)

            # Add source metadata
            if 'metadata' not in normalized:
                normalized['metadata'] = {}
            normalized['metadata']['source_file'] = source_name

            all_examples.append(normalized)

    print(f"\n  Total examples before deduplication: {len(all_examples)}")

    # Deduplicate by I/O hash
    seen_hashes: Set[str] = set()
    deduped = []
    duplicates_removed = 0

    for example in all_examples:
        io_hash = compute_io_hash(example)

        if io_hash not in seen_hashes:
            seen_hashes.add(io_hash)
            example['metadata']['io_hash'] = io_hash
            example['metadata']['duplication_status'] = 'unique'
            deduped.append(example)
        else:
            duplicates_removed += 1

    print(f"  Total examples after deduplication: {len(deduped)}")
    print(f"  Duplicates removed: {duplicates_removed}")

    return deduped


def generate_statistics(pool: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics about the unified pool."""
    stats = {
        'total_examples': len(pool),
        'by_source': {},
        'by_framework': {}
    }

    for ex in pool:
        source = ex.get('metadata', {}).get('source_file', 'unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

        framework = ex.get('outputs', {}).get('framework', 'unknown')
        stats['by_framework'][framework] = stats['by_framework'].get(framework, 0) + 1

    return stats


# Inline validator to avoid import issues
class ExampleValidator:
    """Validates quality of prompt examples."""

    def __init__(self):
        """Initialize validator."""
        pass

    def validate_single_example(self, example: Dict) -> Dict:
        """Validate a single example.

        Args:
            example: Dictionary with inputs/outputs/metadata fields

        Returns:
            Dict with 'is_valid', 'score', 'errors', 'warnings'
        """
        errors = []
        warnings = []

        # Check required fields
        if "inputs" not in example:
            errors.append({
                "field": "inputs",
                "message": "Missing 'inputs' field",
                "severity": "error",
            })

        if "outputs" not in example:
            errors.append({
                "field": "outputs",
                "message": "Missing 'outputs' field",
                "severity": "error",
            })

        if "metadata" not in example:
            errors.append({
                "field": "metadata",
                "message": "Missing 'metadata' field",
                "severity": "error",
            })

        # Calculate quality score
        score = self._calculate_quality_score(example, errors, warnings)

        is_valid = len(errors) == 0 and score > 0.5

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "warnings": warnings,
        }

    def _calculate_quality_score(
        self, example: Dict, errors: List[Dict], warnings: List[Dict]
    ) -> float:
        """Calculate quality score for an example.

        Args:
            example: Example dictionary
            errors: List of errors
            warnings: List of warnings

        Returns:
            Quality score between 0.0 and 1.0
        """
        if "outputs" not in example:
            return 0.0

        improved_prompt = example['outputs'].get('improved_prompt', '')

        if not improved_prompt:
            return 0.0

        # Check for low character diversity
        unique_chars = len(set(improved_prompt))
        total_chars = len(improved_prompt)

        if total_chars > 0:
            char_diversity = unique_chars / total_chars
            if char_diversity < 0.05:
                return 0.2

        # Check for low lexical diversity
        words = improved_prompt.split()
        unique_words = len(set(words))
        total_words = len(words)

        if total_words > 0:
            lexical_diversity = unique_words / total_words
            if lexical_diversity < 0.2:
                return 0.3

        score = 0.5  # Base score

        # Length score
        ideal_length = 200
        length_score = min(1.0, len(improved_prompt) / ideal_length)
        score += length_score * 0.2

        # Context keywords bonus
        context_keywords = [
            "explain", "describe", "analyze", "discuss", "provide",
            "example", "context", "background", "detail", "reasoning",
        ]
        context_count = sum(
            1 for keyword in context_keywords
            if keyword.lower() in improved_prompt.lower()
        )
        score += min(0.15, context_count * 0.03)

        # Action verbs bonus
        action_verbs = [
            "create", "build", "implement", "design", "develop",
            "write", "generate", "construct", "formulate",
        ]
        verb_count = sum(
            1 for verb in action_verbs
            if verb.lower() in improved_prompt.lower()
        )
        score += min(0.1, verb_count * 0.02)

        # Metadata bonus
        if "metadata" in example:
            metadata = example["metadata"]

            # Source bonus
            if metadata.get("source") == "langchain-hub":
                score += 0.1

        # Penalty for errors
        error_penalty = len(errors) * 0.2
        score -= error_penalty

        # Penalty for warnings
        warning_penalty = len(warnings) * 0.05
        score -= warning_penalty

        # Clamp score to [0.0, 1.0]
        return max(0.0, min(1.0, score))


class ImportWorkflow:
    """Orchestrator for LangChain Hub import workflow."""

    def __init__(self, base_path: Path = None):
        """Initialize workflow with paths.

        Args:
            base_path: Base project path. Defaults to repository root.
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent

        self.base_path = base_path
        self.config_path = base_path / 'scripts/config/langchain_whitelist.json'
        self.exports_path = base_path / 'datasets/exports'

        # Output file paths
        self.candidates_file = self.exports_path / 'langchain-candidates.json'
        self.approved_file = self.exports_path / 'langchain-approved.json'
        self.validated_file = self.exports_path / 'langchain-validated.json'
        self.unified_pool = self.exports_path / 'unified-fewshot-pool.json'
        self.updated_pool = self.exports_path / 'unified-fewshot-pool-updated.json'

        # Ensure exports directory exists
        self.exports_path.mkdir(parents=True, exist_ok=True)

    def fetch(self) -> int:
        """Fetch prompts from LangChain Hub via whitelist.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("=" * 70)
        print("FETCHING PROMPTS FROM LANGCHAIN HUB")
        print("=" * 70)

        # Load whitelist
        if not self.config_path.exists():
            print(f"\n❌ Error: Config file not found: {self.config_path}")
            print("   Create scripts/config/langchain_whitelist.json with handle list.")
            return 1

        print(f"\n📋 Loading whitelist from {self.config_path.name}...")
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            handles = config.get('handles', [])
        except json.JSONDecodeError as e:
            print(f"\n❌ Error: Invalid JSON in config file: {e}")
            return 1

        if not handles:
            print("\n❌ Error: No handles found in whitelist")
            return 1

        print(f"   Found {len(handles)} handles to fetch")

        # Fetch prompts
        print("\n🌐 Fetching prompts from LangChain Hub...")
        try:
            fetcher = LangChainHubFetcher()
            converter = FormatConverter()
            fetched = fetcher.fetch_by_handles(handles)

            if not fetched:
                print("\n⚠️  Warning: No prompts were successfully fetched")
                print("   Saving empty candidates file...")

                # Save empty candidates file with metadata
                output_data = fetcher.to_candidates_file([], converter)
            else:
                print(f"\n✓ Successfully fetched {len(fetched)}/{len(handles)} prompts")

                # Convert to candidates format
                print("\n🔄 Converting to DSPy format...")
                output_data = fetcher.to_candidates_file(fetched, converter)

                print(f"   Converted {len(output_data['candidates'])} candidates")

        except ValueError as e:
            print(f"\n❌ Error: {e}")
            return 1
        except ImportError as e:
            print(f"\n❌ Error: {e}")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error during fetch: {e}")
            return 1

        # Save candidates file
        print(f"\n💾 Saving candidates to {self.candidates_file.name}...")
        with open(self.candidates_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Fetch mode complete!")
        print(f"   Total fetched: {output_data['metadata']['total_fetched']}")
        print(f"   Output: {self.candidates_file}")

        return 0

    def validate(self) -> int:
        """Validate candidates with ExampleValidator.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("=" * 70)
        print("VALIDATING LANGCHAIN CANDIDATES")
        print("=" * 70)

        # Check for approved file (after manual review)
        if not self.approved_file.exists():
            print(f"\n⚠️  Approved file not found: {self.approved_file.name}")
            print(f"   Expected {self.candidates_file.name} → manual review → {self.approved_file.name}")
            print("\n   Using candidates file directly for validation...")

            source_file = self.candidates_file
        else:
            source_file = self.approved_file

        if not source_file.exists():
            print(f"\n❌ Error: Source file not found: {source_file}")
            return 1

        # Load candidates
        print(f"\n📂 Loading candidates from {source_file.name}...")
        try:
            with open(source_file, 'r') as f:
                data = json.load(f)
            candidates = data.get('candidates', [])
        except json.JSONDecodeError as e:
            print(f"\n❌ Error: Invalid JSON in candidates file: {e}")
            return 1

        if not candidates:
            print("\n⚠️  Warning: No candidates to validate")
            print("   Saving empty validated file...")

            validated_data = {
                'metadata': {
                    'total_validated': 0,
                    'total_passed': 0,
                    'total_failed': 0,
                    'min_score': 0.5
                },
                'candidates': []
            }
        else:
            print(f"   Loaded {len(candidates)} candidates")

            # Validate with ExampleValidator
            print("\n🔍 Validating candidates (score ≥ 0.5)...")
            validator = ExampleValidator()

            validated_candidates = []
            scores = []

            for i, candidate in enumerate(candidates, 1):
                # Get the converted DSPy format
                example = candidate.get('converted', {})

                # Validate the example
                result = validator.validate_single_example(example)

                score = result.get('score', 0.0)
                scores.append(score)

                # Include score in candidate
                candidate['validation_score'] = score
                candidate['validation_passed'] = result.get('is_valid', False)

                # Only keep candidates with score ≥ 0.5
                if score >= 0.5:
                    validated_candidates.append(candidate)
                    print(f"   [{i}/{len(candidates)}] {candidate.get('name', candidate.get('handle'))}: ✓ {score:.2f}")
                else:
                    print(f"   [{i}/{len(candidates)}] {candidate.get('name', candidate.get('handle'))}: ✗ {score:.2f}")

            # Calculate statistics
            avg_score = sum(scores) / len(scores) if scores else 0.0
            min_score = min(scores) if scores else 0.0
            max_score = max(scores) if scores else 0.0

            print(f"\n📊 Validation Results:")
            print(f"   Total candidates: {len(candidates)}")
            print(f"   Passed (≥0.5): {len(validated_candidates)}")
            print(f"   Failed: {len(candidates) - len(validated_candidates)}")
            print(f"   Avg score: {avg_score:.2f}")
            print(f"   Score range: [{min_score:.2f}, {max_score:.2f}]")

            validated_data = {
                'metadata': {
                    'total_validated': len(candidates),
                    'total_passed': len(validated_candidates),
                    'total_failed': len(candidates) - len(validated_candidates),
                    'avg_score': avg_score,
                    'min_score': min_score,
                    'max_score': max_score,
                    'min_threshold': 0.5
                },
                'candidates': validated_candidates
            }

        # Save validated file
        print(f"\n💾 Saving validated candidates to {self.validated_file.name}...")
        with open(self.validated_file, 'w', encoding='utf-8') as f:
            json.dump(validated_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Validate mode complete!")
        print(f"   Validated: {validated_data['metadata']['total_validated']}")
        print(f"   Passed: {validated_data['metadata']['total_passed']}")
        print(f"   Output: {self.validated_file}")

        return 0

    def merge(self) -> int:
        """Merge validated prompts with existing unified pool.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("=" * 70)
        print("MERGING VALIDATED PROMPTS INTO UNIFIED POOL")
        print("=" * 70)

        # Load validated candidates
        if not self.validated_file.exists():
            print(f"\n❌ Error: Validated file not found: {self.validated_file}")
            print("   Run 'validate' mode first.")
            return 1

        print(f"\n📂 Loading validated candidates from {self.validated_file.name}...")
        try:
            with open(self.validated_file, 'r') as f:
                validated_data = json.load(f)
            validated_candidates = validated_data.get('candidates', [])
        except json.JSONDecodeError as e:
            print(f"\n❌ Error: Invalid JSON in validated file: {e}")
            return 1

        if not validated_candidates:
            print("\n⚠️  Warning: No validated candidates to merge")
            print("   Unified pool will remain unchanged.")
            return 0

        print(f"   Loaded {len(validated_candidates)} validated candidates")

        # Convert validated candidates to example format
        validated_examples = []
        for candidate in validated_candidates:
            converted = candidate.get('converted', {})
            if converted:
                # Add validation metadata
                if 'metadata' not in converted:
                    converted['metadata'] = {}
                converted['metadata']['validation_score'] = candidate.get('validation_score', 0.0)
                converted['metadata']['source_file'] = 'langchain-validated.json'
                validated_examples.append(converted)

        # Load existing unified pool
        if not self.unified_pool.exists():
            print(f"\n⚠️  Unified pool not found: {self.unified_pool.name}")
            print("   Creating new unified pool from validated candidates...")

            existing_examples = []
        else:
            print(f"\n📂 Loading existing unified pool from {self.unified_pool.name}...")
            try:
                with open(self.unified_pool, 'r') as f:
                    pool_data = json.load(f)
                existing_examples = pool_data.get('examples', [])
                existing_count = len(existing_examples)
            except json.JSONDecodeError as e:
                print(f"\n❌ Error: Invalid JSON in unified pool: {e}")
                return 1

            print(f"   Loaded {existing_count} existing examples")

        # Merge datasets
        print("\n🔀 Merging validated candidates with existing pool...")

        datasets = {
            'unified-fewshot-pool.json': existing_examples,
            'langchain-validated.json': validated_examples
        }

        merged_examples = merge_datasets(datasets)

        # Generate statistics
        print("\n📊 Generating statistics...")
        stats = generate_statistics(merged_examples)

        print(f"\n  By source:")
        for source, count in sorted(stats['by_source'].items()):
            print(f"    {source}: {count}")

        print(f"\n  By framework:")
        for framework, count in sorted(stats['by_framework'].items(), key=lambda x: -x[1])[:5]:
            print(f"    {framework}: {count}")

        # Save updated unified pool
        print(f"\n💾 Saving updated unified pool to {self.updated_pool.name}...")

        with open(self.updated_pool, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'total_examples': len(merged_examples),
                    'sources': list(datasets.keys()),
                    'created_at': str(datetime.now()),
                    'statistics': stats,
                    'langchain_added': len(validated_examples)
                },
                'examples': merged_examples
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Merge mode complete!")
        print(f"   Examples added: {len(validated_examples)}")
        print(f"   Total examples: {len(merged_examples)}")
        print(f"   Output: {self.updated_pool}")

        return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ImportWorkflow CLI for LangChain Hub integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/langchain/import_workflow.py fetch
      Fetch prompts from LangChain Hub whitelist

  python scripts/langchain/import_workflow.py validate
      Validate candidates (score ≥ 0.5)

  python scripts/langchain/import_workflow.py merge
      Merge validated prompts with existing pool

Workflow:
  1. fetch → datasets/exports/langchain-candidates.json
  2. Manual review: candidates.json → approved.json
  3. validate → datasets/exports/langchain-validated.json
  4. merge → datasets/exports/unified-fewshot-pool-updated.json
        """
    )

    parser.add_argument(
        'mode',
        choices=['fetch', 'validate', 'merge'],
        help='Workflow mode to execute'
    )

    parser.add_argument(
        '--base-path',
        type=Path,
        default=None,
        help='Base project path (default: repository root)'
    )

    args = parser.parse_args()

    # Initialize workflow
    workflow = ImportWorkflow(base_path=args.base_path)

    # Execute mode
    if args.mode == 'fetch':
        return workflow.fetch()
    elif args.mode == 'validate':
        return workflow.validate()
    elif args.mode == 'merge':
        return workflow.merge()
    else:
        print(f"❌ Unknown mode: {args.mode}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
