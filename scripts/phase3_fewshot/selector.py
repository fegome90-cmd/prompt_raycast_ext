"""Similarity-based example selector for few-shot learning."""
from typing import List, Dict


class SimilaritySelector:
    """Similarity-based example selector for few-shot."""

    def select(self, query: str, pool, k: int = 3) -> List[Dict]:
        """Select top-k most similar examples to query.

        Args:
            query: Query string
            pool: ExamplePool to search
            k: Number of examples to return

        Returns:
            List of top-k similar examples
        """
        # For now, use simple keyword matching
        # Real similarity with embeddings comes later

        query_lower = query.lower()
        scored = []

        for ex in pool.examples:
            question_lower = ex['question'].lower()

            # Simple similarity: keyword overlap
            query_words = set(query_lower.split())
            ex_words = set(question_lower.split())
            overlap = len(query_words & ex_words)
            similarity = overlap / len(query_words) if query_words else 0

            scored.append({
                'example': ex,
                'similarity': similarity
            })

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top-k examples only
        top_k = [item['example'] for item in scored[:k]]

        return top_k
