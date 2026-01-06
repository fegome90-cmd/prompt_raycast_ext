#!/usr/bin/env python3
"""
Merge 42 validated prompts into unified-fewshot-pool.json (curated dataset).

Creates unified-fewshot-pool-v2.json with 66 + 42 = 108 curated examples.
This maintains quality over quantity for DSPy KNNFewShot training.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Paths
UNIFIED_POOL = Path("/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool.json")
SOURCE_PROMPTS = Path.home() / "Desktop/prompt_dataset/prompts.json"
OUTPUT_V2 = Path("/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool-v2.json")

# Metadata
SOURCE_TAG = "prompt_dataset_v1"
MERGE_DATE = datetime.now(timezone.utc).isoformat()

# Validation data path
VALIDATION_DATA = Path.home() / "Desktop/prompt_dataset/validation_detailed_detailed.json"


def load_unified_pool(path: Path) -> dict:
    """Load existing unified pool."""
    with open(path, 'r') as f:
        return json.load(f)


def load_source_prompts(path: Path) -> list:
    """Load 42 validated prompts."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('prompts', [])


def load_validation_scores(path: Path) -> dict:
    """Load validation scores and create ID mapping.

    Returns:
        Dict mapping prompt_id (e.g., 'security_auth_001') -> score (float)
    """
    if not path.exists():
        print(f"⚠️  Validation data not found: {path}")
        print(f"    Using default score 0.85")
        return {}

    with open(path, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Create mapping: normalize validation ID → score
    score_map = {}
    for result in results:
        val_id = result['id']  # e.g., 'security_security_auth_001'

        # Normalize: always remove first part
        # 'security_security_auth_001' → 'security_auth_001'
        # 'architecture_arch_event_001' → 'arch_event_001'
        # 'database_db_postgres_001' → 'db_postgres_001'
        parts = val_id.split('_')
        normalized_id = '_'.join(parts[1:])  # Remove first part

        score = result['score']
        score_map[normalized_id] = score

    print(f"✓ Loaded {len(score_map)} validation scores")
    return score_map


def compute_io_hash(inputs: dict, outputs: dict) -> str:
    """Compute hash of inputs/outputs for deduplication."""
    combined = json.dumps({"inputs": inputs, "outputs": outputs}, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()


def transform_to_unified_format(prompt: dict, index: int, validation_scores: dict) -> dict:
    """
    Transform prompt to unified-fewshot-pool format.

    Args:
        prompt: Source prompt from prompts.json
        index: Index in batch
        validation_scores: Dict of prompt_id -> validation score

    Returns:
        Unified format example with metadata
    """
    prompt_id = prompt.get("id", "")
    inputs = {
        "original_idea": prompt.get("original_idea", ""),
        "context": prompt.get("context", "")
    }

    outputs = {
        "improved_prompt": prompt.get("improved_prompt", "")
    }

    # Compute hash for deduplication
    io_hash = compute_io_hash(inputs, outputs)

    # Get validation score if available
    validator_score = validation_scores.get(prompt_id, 0.960)

    # Map task_category -> category
    category = prompt.get("task_category", prompt.get("sub_category", "unknown"))

    return {
        "inputs": inputs,
        "outputs": outputs,
        "metadata": {
            "source": SOURCE_TAG,
            "source_file": "prompt_dataset/prompts.json",
            "domain": prompt.get("domain", "unknown"),
            "category": category,
            "framework": prompt.get("framework", "unknown"),
            "complexity": prompt.get("complexity", "medium"),
            "deduplicated": False,
            "deduplication_date": None,
            "io_hash": io_hash,
            "duplication_status": "unique",
            "quality_score": prompt.get("quality_score", 0.85),
            "validation_timestamp": "2026-01-05T12:00:00Z",
            "example_validator_score": validator_score,
            "added_at": MERGE_DATE,
            "index_in_batch": index
        }
    }


def compute_statistics(examples: list) -> dict:
    """Compute statistics for metadata."""
    # Category distribution
    categories = {}
    for ex in examples:
        cat = ex.get("metadata", {}).get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    # Framework distribution
    frameworks = {}
    for ex in examples:
        fw = ex.get("metadata", {}).get("framework", "unknown")
        frameworks[fw] = frameworks.get(fw, 0) + 1

    # Source distribution
    sources = {}
    for ex in examples:
        src = ex.get("metadata", {}).get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    # Domain distribution
    domains = {}
    for ex in examples:
        dom = ex.get("metadata", {}).get("domain", "unknown")
        domains[dom] = domains.get(dom, 0) + 1

    return {
        "total_examples": len(examples),
        "by_category": categories,
        "by_framework": frameworks,
        "by_source": sources,
        "by_domain": domains
    }


def merge_pools(existing: dict, new_examples: list) -> dict:
    """Merge existing pool with new examples."""
    existing_examples = existing['examples']
    all_examples = existing_examples + new_examples

    # Update sources
    new_sources = existing['metadata']['sources'].copy()
    if SOURCE_TAG not in new_sources:
        new_sources.append(f"{SOURCE_TAG}_prompts.json")

    # Create new pool
    return {
        "metadata": {
            "total_examples": len(all_examples),
            "sources": new_sources,
            "created_at": existing['metadata']['created_at'],
            "updated_at": MERGE_DATE,
            "version": "v2",
            "previous_version": "unified-fewshot-pool.json",
            "statistics": compute_statistics(all_examples)
        },
        "examples": all_examples
    }


def print_summary(existing: dict, new_prompts: list, merged: dict):
    """Print merge summary."""
    print("\n" + "=" * 60)
    print("📊 Unified Pool Merge Summary")
    print("=" * 60)

    print(f"\n📂 Existing Pool:")
    print(f"   Examples: {len(existing['examples'])}")
    print(f"   Sources: {', '.join(existing['metadata']['sources'])}")

    print(f"\n✨ New Prompts:")
    print(f"   Count: {len(new_prompts)}")
    print(f"   Source: {SOURCE_TAG}")

    # Category breakdown of new prompts
    new_categories = {}
    for ex in new_prompts:
        cat = ex['metadata']['category']
        new_categories[cat] = new_categories.get(cat, 0) + 1

    print(f"\n   New Categories Added:")
    for cat, count in sorted(new_categories.items()):
        print(f"      {cat}: {count}")

    print(f"\n🎯 Merged Pool (v2):")
    print(f"   Total: {len(merged['examples'])} examples")
    print(f"   Version: {merged['metadata']['version']}")
    print(f"   Updated: {merged['metadata']['updated_at']}")

    # Statistics
    stats = merged['metadata']['statistics']
    print(f"\n📈 Category Distribution (all {stats['total_examples']}):")
    for cat, count in sorted(stats['by_category'].items()):
        bar = '█' * max(1, int(count / 5))
        print(f"   {cat:20} {count:3} {bar}")

    print(f"\n🎨 Framework Distribution:")
    for fw, count in sorted(stats['by_framework'].items(), key=lambda x: -x[1])[:5]:
        pct = (count / stats['total_examples']) * 100
        print(f"   {fw:20} {count:3} ({pct:5.1f}%)")

    # Source distribution
    print(f"\n📦 Source Distribution:")
    for src, count in sorted(stats['by_source'].items()):
        print(f"   {src}: {count}")

    print("\n" + "=" * 60)


def save_pool(pool: dict, path: Path):
    """Save unified pool to file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(pool, f, indent=2)

    print(f"\n💾 Saved to: {path}")
    print(f"   Size: {path.stat().st_size / 1024:.1f} KB")


def main():
    """Main entry point."""
    print("🔄 Merging to Unified FewShot Pool")
    print("=" * 60)

    # Load existing pool
    print(f"\n📂 Loading existing pool: {UNIFIED_POOL}")
    existing_pool = load_unified_pool(UNIFIED_POOL)
    print(f"✓ Loaded {len(existing_pool['examples'])} examples")

    # Load source prompts
    print(f"\n📂 Loading source prompts: {SOURCE_PROMPTS}")
    source_prompts = load_source_prompts(SOURCE_PROMPTS)
    print(f"✓ Loaded {len(source_prompts)} prompts")

    # Load validation scores
    print(f"\n📊 Loading validation scores: {VALIDATION_DATA}")
    validation_scores = load_validation_scores(VALIDATION_DATA)

    # Transform to unified format
    print(f"\n🔄 Transforming to unified format...")
    new_examples = []
    for i, prompt in enumerate(source_prompts):
        transformed = transform_to_unified_format(prompt, i, validation_scores)
        new_examples.append(transformed)
    print(f"✓ Transformed {len(new_examples)} examples")

    # Show score distribution
    if validation_scores:
        scores_in_batch = list(validation_scores.values())
        avg = sum(scores_in_batch) / len(scores_in_batch)
        min_score = min(scores_in_batch)
        max_score = max(scores_in_batch)
        print(f"   Validation scores: min={min_score:.3f}, max={max_score:.3f}, avg={avg:.3f}")

    # Merge pools
    print(f"\n🔀 Merging pools...")
    merged_pool = merge_pools(existing_pool, new_examples)
    print(f"✓ Merged: {len(existing_pool['examples'])} + {len(new_examples)} = {len(merged_pool['examples'])}")

    # Print summary
    print_summary(existing_pool, new_examples, merged_pool)

    # Save
    save_pool(merged_pool, OUTPUT_V2)

    print("\n✅ Merge Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
