#!/usr/bin/env python3
"""Export SQLite prompts to DSPy KNNFewShot format."""

from pathlib import Path
import sys
import aiosqlite
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hemdov.infrastructure.config import settings
from scripts.data.utils import save_dataset


async def export_sqlite_to_dspy(
    db_path: str,
    output_path: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Export prompts from SQLite to DSPy KNNFewShot format.

    Args:
        db_path: Path to SQLite database
        output_path: Path to output JSON file
        limit: Maximum number of records to export

    Returns:
        List of examples in DSPy format
    """
    examples = []

    async with aiosqlite.connect(db_path) as conn:
        # Query prompts ordered by created_at (most recent first)
        cursor = await conn.execute(
            """
            SELECT
                original_idea,
                context,
                improved_prompt,
                role,
                directive,
                framework,
                guardrails,
                reasoning,
                confidence,
                backend,
                model,
                provider,
                latency_ms,
                created_at
            FROM prompt_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = await cursor.fetchall()

        for row in rows:
            # Combine original_idea + context as input
            input_text = row[0]  # original_idea
            if row[1]:  # context
                input_text += f"\n\nContext: {row[1]}"

            # The improved_prompt is the output
            output_text = row[2]  # improved_prompt

            examples.append({
                "input": input_text,
                "output": output_text,
                "metadata": {
                    "role": row[3],
                    "directive": row[4],
                    "framework": row[5],
                    "guardrails": row[6],
                    "reasoning": row[7],
                    "confidence": row[8],
                    "backend": row[9],
                    "model": row[10],
                    "provider": row[11],
                    "latency_ms": row[12],
                    "created_at": row[13]
                }
            })

    # Save to JSON file using shared utility
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    save_dataset(examples, str(output_file))

    print(f"✓ Exported {len(examples)} prompts to {output_path}")
    return examples


async def main():
    """Main entry point."""
    # Paths
    base_path = Path(__file__).parent.parent.parent
    db_path = settings.SQLITE_DB_PATH
    output_path = str(base_path / "datasets/exports/sqlite-export.json")

    print(f"Exporting from: {db_path}")
    print(f"Output to: {output_path}")

    # Export exactly 27 prompts as per spec
    examples = await export_sqlite_to_dspy(db_path, output_path, limit=27)

    print(f"\n✓ Export complete: {len(examples)} examples")
    print(f"  Input length: {sum(len(e['input']) for e in examples)} chars")
    print(f"  Output length: {sum(len(e['output']) for e in examples)} chars")


if __name__ == "__main__":
    asyncio.run(main())
