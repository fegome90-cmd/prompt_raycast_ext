"""
Migration script to find and fix PromptHistory records with invalid frameworks.

Run this before deploying Task 2 fixes to identify affected records.
"""

from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.metrics.dimensions import FrameworkType


def find_invalid_frameworks(histories: list[PromptHistory]) -> list[dict]:
    """
    Find all PromptHistory records with invalid frameworks.

    Returns:
        List of dicts with record details for manual review
    """
    valid_frameworks = {f.value for f in FrameworkType}
    invalid_records = []

    for idx, history in enumerate(histories):
        if history.framework not in valid_frameworks:
            invalid_records.append({
                "index": idx,
                "created_at": history.created_at or "unknown",
                "invalid_framework": history.framework,
                "original_idea": history.original_idea[:50] + "..." if len(history.original_idea) > 50 else history.original_idea,
                "suggested_fix": "chain-of-thought"
            })

    return invalid_records


def fix_invalid_frameworks(histories: list[PromptHistory]) -> tuple[list[PromptHistory], list[dict]]:
    """
    Fix invalid frameworks by creating new PromptHistory instances with valid framework.

    Args:
        histories: List of PromptHistory records to fix

    Returns:
        Tuple of (fixed_histories, report of changes)
    """
    from dataclasses import replace

    valid_frameworks = {f.value for f in FrameworkType}
    fixed_histories = []
    report = []

    for history in histories:
        if history.framework not in valid_frameworks:
            # Create fixed version with chain-of-thought as default
            fixed = replace(history, framework="chain-of-thought")
            fixed_histories.append(fixed)
            report.append({
                "original_framework": history.framework,
                "new_framework": "chain-of-thought",
                "created_at": history.created_at
            })
        else:
            fixed_histories.append(history)

    return fixed_histories, report


if __name__ == "__main__":
    import sys

    print("PromptHistory Framework Migration Script")
    print("=" * 50)
    print("\nThis script helps identify and fix invalid framework values.")
    print("\nValid frameworks:", [f.value for f in FrameworkType])
    print("\nUsage:")
    print("  python scripts/migrate_prompt_history.py check <data_file>")
    print("  python scripts/migrate_prompt_history.py fix <data_file> <output_file>")
    print("\nExample with list of PromptHistory objects:")
    print("  from hemdov.domain.entities.prompt_history import PromptHistory")
    print("  histories = [...]  # Your list of PromptHistory objects")
    print("  invalid = find_invalid_frameworks(histories)")
    print("  print(f'Found {len(invalid)} invalid records')")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "help":
            print("\nFor production use:")
            print("1. Export your PromptHistory data to JSON")
            print("2. Run: python scripts/migrate_prompt_history.py check data.json")
            print("3. Review invalid records")
            print("4. Run: python scripts/migrate_prompt_history.py fix data.json fixed_data.json")
            print("5. Import fixed_data.json to your database")
