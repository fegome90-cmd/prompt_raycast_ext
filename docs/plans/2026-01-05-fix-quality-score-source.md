# Fix Quality Score Source Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Load individual ExampleValidator scores from `validation_detailed_detailed.json` instead of hardcoding 0.960 in the merge script.

**Architecture:**
- Load `validation_detailed_detailed.json` to get individual scores per prompt
- Create ID mapping from validation format (`security_security_auth_001`) to prompt format (`security_auth_001`)
- Update `merge_to_unified_pool.py` to use real scores from validation data
- Regenerate `unified-fewshot-pool-v2.json` with correct individual scores

**Tech Stack:**
- Python 3.14
- JSON parsing and ID normalization
- Existing merge script at `scripts/data/fewshot/merge_to_unified_pool.py`

---

## Context

**Problem:**
- `merge_to_unified_pool.py` hardcodes `example_validator_score: 0.960` for all 42 prompts
- Real validation scores exist in `~/Desktop/prompt_dataset/validation_detailed_detailed.json`
- ID mismatch: validation uses `security_security_auth_001`, prompts use `security_auth_001`

**Data Flow:**
```
validation_detailed_detailed.json
    ↓
results[].id → normalize → match with prompts.json
    ↓
results[].score → attach to each prompt metadata
    ↓
unified-fewshot-pool-v2.json with individual scores
```

**Files:**
- Validation data: `~/Desktop/prompt_dataset/validation_detailed_detailed.json`
- Source prompts: `~/Desktop/prompt_dataset/prompts.json`
- Merge script: `scripts/data/fewshot/merge_to_unified_pool.py`
- Output: `datasets/exports/unified-fewshot-pool-v2.json`

---

## Task 1: Add Validation Score Loading Function

**Files:**
- Modify: `scripts/data/fewshot/merge_to_unified_pool.py`

**Step 1: Add validation data loading function**

Add after line 26 (after SOURCE_TAG definitions):

```python
# Validation data path
VALIDATION_DATA = Path.home() / "Desktop/prompt_dataset/validation_detailed_detailed.json"


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

        # Normalize: remove duplicate prefix if present
        # 'security_security_auth_001' → 'security_auth_001'
        parts = val_id.split('_')

        # Check if first two parts are same (duplicate prefix)
        if len(parts) >= 4 and parts[0] == parts[1]:
            # Remove duplicate: security_security_auth_001 → security_auth_001
            normalized_id = '_'.join(parts[1:])
        else:
            normalized_id = val_id

        score = result['score']
        score_map[normalized_id] = score

    print(f"✓ Loaded {len(score_map)} validation scores")
    return score_map
```

**Step 2: Test the normalization logic**

Create test script `/tmp/test_id_normalization.py`:

```python
# Test ID normalization
test_cases = [
    ('security_security_auth_001', 'security_auth_001'),
    ('backend_backend_graphql_001', 'backend_graphql_001'),
    ('database_index_001', 'database_index_001'),  # no duplicate
]

for val_id, expected in test_cases:
    parts = val_id.split('_')
    if len(parts) >= 4 and parts[0] == parts[1]:
        normalized = '_'.join(parts[1:])
    else:
        normalized = val_id

    status = "✓" if normalized == expected else "✗"
    print(f"{status} {val_id} → {normalized} (expected: {expected})")
```

Run: `python3 /tmp/test_id_normalization.py`
Expected: All tests pass with ✓

**Step 3: Update transform function to use validation scores**

Replace `transform_to_unified_format` function (lines 45-88) with:

```python
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
```

**Step 4: Update main function to load and pass validation scores**

Update `main()` function, add after loading source prompts (around line 230):

```python
# Load validation scores
print(f"\n📊 Loading validation scores: {VALIDATION_DATA}")
validation_scores = load_validation_scores(VALIDATION_DATA)
```

Update transform loop to pass scores:

```python
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
```

**Step 5: Commit changes**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add scripts/data/fewshot/merge_to_unified_pool.py
git commit -m "feat: load individual validation scores from validation_detailed_detailed.json

- Add load_validation_scores() function with ID normalization
- Update transform_to_unified_format() to use real scores
- Remove hardcoded 0.960, use individual prompt scores
- Handle ID format: security_security_auth_001 → security_auth_001"
```

---

## Task 2: Regenerate Unified Pool with Correct Scores

**Files:**
- Run: `scripts/data/fewshot/merge_to_unified_pool.py`
- Output: `datasets/exports/unified-fewshot-pool-v2.json`

**Step 1: Backup existing v2 pool**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports
cp unified-fewshot-pool-v2.json unified-fewshot-pool-v2-backup.json
```

**Step 2: Run updated merge script**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
python3 scripts/data/fewshot/merge_to_unified_pool.py
```

Expected output includes:
```
✓ Loaded 42 validation scores
✓ Transformed 42 examples
   Validation scores: min=0.905, max=1.000, avg=0.960
```

**Step 3: Verify scores in output**

Create verification script `/tmp/verify_scores.py`:

```python
import json

with open('/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool-v2.json') as f:
    pool = json.load(f)

new_examples = [ex for ex in pool['examples'] if ex['metadata'].get('source') == 'prompt_dataset_v1']

print("🔍 Verifying example_validator_score in new prompts:")
print(f"   Total new prompts: {len(new_examples)}")

# Check score distribution
scores = [ex['metadata'].get('example_validator_score', 0) for ex in new_examples]
avg_score = sum(scores) / len(scores)

print(f"   Score range: {min(scores):.3f} - {max(scores):.3f}")
print(f"   Average: {avg_score:.3f}")

# Check for hardcoded 0.960 (bad)
all_same = all(s == 0.960 for s in scores)
print(f"   All same (hardcoded): {all_same}")

if not all_same:
    print("   ✓ Scores vary (using individual validation scores)")
else:
    print("   ✗ All scores are 0.960 (hardcoded, not fixed)")

# Sample 5 prompts
print(f"\n   Sample of 5 prompts:")
for ex in new_examples[:5]:
    score = ex['metadata'].get('example_validator_score', 0)
    category = ex['metadata'].get('category', 'unknown')
    print(f"      {category}: {score:.3f}")
```

Run: `python3 /tmp/verify_scores.py`
Expected:
```
   Score range: 0.905 - 1.000
   Average: 0.960
   All same (hardcoded): False
   ✓ Scores vary (using individual validation scores)
```

**Step 4: Update metadata timestamp**

If verification passes, update `fewshot-compiled-v2.metadata.json`:

```json
{
  "model_type": "KNNFewShot",
  "k": 3,
  "trainset_size": 108,
  "trainset_path": "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/unified-fewshot-pool-v2.json",
  "created_at": "2026-01-05 15:45:00.000000",
  "version": "v2",
  "previous_version": "fewshot-compiled.json",
  "validation_scores": {
    "source": "validation_detailed_detailed.json",
    "avg_score": 0.960,
    "min_score": 0.905,
    "max_score": 1.000,
    "individual_scores": true
  },
  "notes": "Updated with 42 prompts from prompt_dataset_v1 with individual validation scores"
}
```

**Step 5: Clean up backup**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports
rm unified-fewshot-pool-v2-backup.json
```

**Step 6: Commit regenerated pool**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add datasets/exports/unified-fewshot-pool-v2.json models/fewshot-compiled-v2.metadata.json
git commit -m "fix: regenerate unified pool v2 with individual validation scores

- Load scores from validation_detailed_detailed.json (0.905-1.000)
- Remove hardcoded 0.960, use real individual scores
- Update metadata to reflect score source"
```

---

## Task 3: Documentation and Cleanup

**Files:**
- Create: `docs/plans/2026-01-05-quality-score-fix-summary.md`

**Step 1: Create summary document**

```markdown
# Quality Score Source Fix Summary

**Date:** 2026-01-05
**Issue:** Hardcoded validation score in merge script
**Resolution:** Load individual scores from validation JSON

## Problem
- `merge_to_unified_pool.py` hardcoded `example_validator_score: 0.960`
- Real individual scores (0.905-1.000) existed in `validation_detailed_detailed.json`

## Solution
1. Added `load_validation_scores()` function to parse validation JSON
2. Implemented ID normalization: `security_security_auth_001` → `security_auth_001`
3. Updated `transform_to_unified_format()` to use real scores
4. Regenerated `unified-fewshot-pool-v2.json` with individual scores

## Results
- Before: All 42 prompts had score 0.960 (hardcoded)
- After: Individual scores 0.905-1.000 (avg 0.960)
- Source: `validation_detailed_detailed.json`

## Files Modified
- `scripts/data/fewshot/merge_to_unified_pool.py` - Added score loading
- `datasets/exports/unified-fewshot-pool-v2.json` - Regenerated with real scores
- `models/fewshot-compiled-v2.metadata.json` - Updated metadata
```

**Step 2: Verify integration works**

Test that DSPy can still use the updated pool:

```python
import json

# Load updated pool
with open('datasets/exports/unified-fewshot-pool-v2.json') as f:
    pool = json.load(f)

examples = pool['examples']

# Verify structure
print(f"Total examples: {len(examples)}")
print(f"Has metadata: {'metadata' in pool}")
print(f"Version: {pool['metadata']['version']}")

# Check a few examples have scores
new_ex = [e for e in examples if e['metadata'].get('source') == 'prompt_dataset_v1']
print(f"New examples: {len(new_ex)}")
print(f"Sample scores:")
for ex in new_ex[:3]:
    score = ex['metadata'].get('example_validator_score', 'N/A')
    print(f"  {ex['metadata']['category']}: {score}")
```

Run: `python3 -c "$(cat /tmp/test_integration.py)"`
Expected: All checks pass, individual scores shown

**Step 3: Final commit**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add docs/plans/2026-01-05-quality-score-fix-summary.md
git commit -m "docs: add quality score fix summary

Document the fix for hardcoded validation scores,
including problem, solution, and results."
```

---

## Success Criteria

✅ All 42 prompts have individual `example_validator_score` values (not all 0.960)
✅ Score range: 0.905 - 1.000
✅ Average score: 0.960
✅ Score source traceable to `validation_detailed_detailed.json`
✅ `unified-fewshot-pool-v2.json` regenerates correctly
✅ No hardcoded scores in code

---

## Testing Strategy

**Unit Tests:**
- ID normalization logic (duplicate prefix removal)
- Score loading from validation JSON
- Mapping validation IDs to prompt IDs

**Integration Tests:**
- Merge script runs without errors
- Output has correct structure
- Scores are individual, not constant

**Manual Verification:**
- Inspect output JSON for score variation
- Confirm score range matches validation data
- Verify metadata updated correctly
