"""Fetch prompts from LangChain Hub for few-shot pool augmentation."""

import os
from datetime import datetime


class LangChainHubFetcher:
    """Fetch prompts from LangChain Hub by handle whitelist."""

    def __init__(self, api_key: str | None = None):
        """Initialize fetcher with LangChain API key.

        Args:
            api_key: LangChain API key (lsv2_...). If None, reads from LANGCHAIN_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LANGCHAIN_API_KEY not set. Set it as env var or pass to constructor."
            )
        os.environ["LANGCHAIN_API_KEY"] = self.api_key

    def fetch_by_handles(self, handles: list[str]) -> list[dict]:
        """Fetch prompts from LangChain Hub by handle.

        Args:
            handles: List of prompt handles (e.g., ["hwchase17/react", "hwchase17/openai-functions"])

        Returns:
            List of fetched prompts with metadata:
            [
                {
                    "handle": "hwchase17/react",
                    "name": "React",
                    "template": "You are a helpful assistant...",
                    "tags": ["agent", "react"]
                },
                ...
            ]
        """
        # Import here to avoid early import errors if langchain not installed
        try:
            from langchain import hub
        except ImportError:
            raise ImportError(
                "langchain not installed. Install with: pip install langchain"
            )

        results = []
        for handle in handles:
            try:
                print(f"Fetching {handle}...")
                prompt = hub.pull(handle)
                results.append({
                    "handle": handle,
                    "name": getattr(prompt, "name", handle),
                    "template": prompt.template,
                    "tags": getattr(prompt, "tags", [])
                })
                print(f"  ✓ Fetched: {getattr(prompt, 'name', handle)}")
            except Exception as e:
                print(f"  ✗ Failed to fetch {handle}: {e}")
                continue

        return results

    def to_candidates_file(
        self,
        fetched: list[dict],
        converter: 'FormatConverter' = None
    ) -> dict:
        """Convert fetched prompts to candidates file format.

        Args:
            fetched: List of fetched prompts from fetch_by_handles()
            converter: Optional FormatConverter to convert to DSPy format

        Returns:
            Dictionary ready for JSON serialization:
            {
                "metadata": {...},
                "candidates": [
                    {
                        "handle": "hwchase17/react",
                        "name": "React",
                        "template": "...",
                        "converted": {
                            "inputs": {...},
                            "outputs": {...},
                            "metadata": {...}
                        }
                    }
                ]
            }
        """
        metadata = {
            "fetched_at": datetime.now().isoformat(),
            "total_fetched": len(fetched),
            "handles": [p["handle"] for p in fetched]
        }

        candidates = []
        for prompt_data in fetched:
            candidate = {
                "handle": prompt_data["handle"],
                "name": prompt_data["name"],
                "template": prompt_data["template"],
                "tags": prompt_data["tags"]
            }

            # If converter provided, convert to DSPy format
            if converter:
                candidate["converted"] = converter.to_dspy_format(prompt_data)

            candidates.append(candidate)

        return {
            "metadata": metadata,
            "candidates": candidates
        }
