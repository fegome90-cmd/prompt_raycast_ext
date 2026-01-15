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

    for history in histories:
        if history.framework not in valid_frameworks:
            invalid_records.append({
                "id": history.created_at.isoformat() if history.created_at else "unknown",
                "invalid_framework": history.framework,
                "suggested_fix": "chain-of-thought"
            })

    return invalid_records


if __name__ == "__main__":
    # Example usage
    print("Checking for invalid frameworks in PromptHistory records...")
    print("Run this against your data store before deploying Task 2 fix.")
    print("\nTo use with actual data:")
    print("  1. Load your PromptHistory records")
    print("  2. Call find_invalid_frameworks(your_records)")
    print("  3. Review and fix invalid data before deploying")
