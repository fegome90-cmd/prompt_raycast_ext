#!/usr/bin/env python3
"""Verify the template extraction fix works on existing data."""

import json
import sys
from pathlib import Path

# Add langchain directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'langchain'))

from fetch_prompts import _extract_template_from_langchain_object


class MockPromptObject:
    """Mock object to test extraction from dirty template strings."""

    def __init__(self, template_str):
        self.template = template_str

    def __str__(self):
        return self.template


def main():
    """Test the fix on existing candidates file."""
    print("=" * 70)
    print("VERIFYING TEMPLATE EXTRACTION FIX")
    print("=" * 70)

    # Load existing candidates file
    candidates_file = Path(__file__).parent.parent.parent.parent / 'datasets/exports/langchain-candidates.json'

    if not candidates_file.exists():
        print(f"\n❌ Error: Candidates file not found: {candidates_file}")
        return 1

    print(f"\n📂 Loading candidates from {candidates_file.name}...")
    with open(candidates_file) as f:
        data = json.load(f)

    candidates = data.get('candidates', [])

    # Find and fix dirty templates
    fixed_count = 0
    dirty_count = 0

    for candidate in candidates:
        template = candidate.get('template', '')

        if template.startswith('input_variables='):
            dirty_count += 1
            handle = candidate.get('handle', 'unknown')

            print(f"\n🔧 Fixing dirty template: {handle}")
            print(f"   Before (first 100 chars): {template[:100]}...")

            # Create mock object and extract clean template
            mock_obj = MockPromptObject(template)
            clean_template = _extract_template_from_langchain_object(mock_obj)

            print(f"   After (first 100 chars): {clean_template[:100]}...")

            # Verify it's actually clean
            if clean_template.startswith('input_variables='):
                print("   ❌ FAILED: Template is still dirty!")
                continue

            # Update the candidate
            candidate['template'] = clean_template
            fixed_count += 1
            print("   ✅ Fixed!")

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  Dirty templates found: {dirty_count}")
    print(f"  Successfully fixed: {fixed_count}")
    print("=" * 70)

    if fixed_count > 0:
        # Save the fixed version
        output_file = candidates_file.parent / 'langchain-candidates-fixed.json'
        print(f"\n💾 Saving fixed candidates to {output_file.name}...")

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Fixed version saved to: {output_file}")
        print("\n📝 To replace the original file:")
        print(f"   mv {output_file} {candidates_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
