#!/usr/bin/env python3
"""Regenerate converted DSPy format with clean templates."""

import json
import sys
from pathlib import Path

# Add langchain directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'langchain'))

from convert_to_dspy_format import FormatConverter


def main():
    """Regenerate converted fields with clean templates."""
    print("=" * 70)
    print("REGENERATING CONVERTED DSPY FORMAT WITH CLEAN TEMPLATES")
    print("=" * 70)

    # Load existing candidates file
    candidates_file = Path(__file__).parent.parent.parent.parent / 'datasets/exports/langchain-candidates.json'

    if not candidates_file.exists():
        print(f"\n❌ Error: Candidates file not found: {candidates_file}")
        return 1

    print(f"\n📂 Loading candidates from {candidates_file.name}...")
    with open(candidates_file, 'r') as f:
        data = json.load(f)

    candidates = data.get('candidates', [])

    # Regenerate converted fields
    converter = FormatConverter()
    regenerated_count = 0

    for candidate in candidates:
        # Get the clean template
        template = candidate.get('template', '')
        handle = candidate.get('handle', '')

        # Skip if template is dirty (shouldn't happen after our fix)
        if template.startswith('input_variables='):
            print(f"\n⚠️  Warning: {handle} still has dirty template, skipping...")
            continue

        print(f"\n🔄 Regenerating converted format for: {handle}")

        # Create prompt data structure for converter
        prompt_data = {
            'handle': handle,
            'name': candidate.get('name', handle),
            'template': template,
            'tags': candidate.get('tags', [])
        }

        # Convert to DSPy format
        converted = converter.to_dspy_format(prompt_data)

        # Update the candidate
        candidate['converted'] = converted
        regenerated_count += 1

        # Verify it's clean
        improved_prompt = converted.get('outputs', {}).get('improved_prompt', '')
        if improved_prompt.startswith('input_variables='):
            print(f"   ❌ ERROR: Converted prompt is still dirty!")
        else:
            print(f"   ✅ Converted successfully!")

    print(f"\n" + "=" * 70)
    print(f"SUMMARY:")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  Regenerated: {regenerated_count}")
    print("=" * 70)

    # Save the updated version
    print(f"\n💾 Saving updated candidates...")
    with open(candidates_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated file saved to: {candidates_file}")

    # Verify all converted prompts are clean
    print(f"\n🔍 Verifying all converted prompts are clean...")
    all_clean = True
    for candidate in candidates:
        improved_prompt = candidate.get('converted', {}).get('outputs', {}).get('improved_prompt', '')
        if improved_prompt.startswith('input_variables='):
            print(f"   ❌ {candidate['handle']}: DIRTY")
            all_clean = False

    if all_clean:
        print(f"   ✅ All converted prompts are CLEAN!")
    else:
        print(f"   ❌ Some converted prompts are still dirty")

    return 0 if all_clean else 1


if __name__ == '__main__':
    sys.exit(main())
