"""Fetch prompts from LangChain Hub for few-shot pool augmentation."""

import os
import re
from datetime import datetime


def _extract_template_from_langchain_object(prompt_data) -> str:
    """Extract clean template string from various LangChain prompt objects.

    Handles different prompt types:
    - PromptTemplate: Direct template attribute
    - ChatPromptTemplate: Extract and combine all message templates
    - MessagesPlaceholder: Extract from nested template

    Args:
        prompt_data: LangChain prompt object (PromptTemplate, ChatPromptTemplate, etc.)

    Returns:
        Clean template string without metadata.
    """
    # Try direct template attribute first (works for PromptTemplate)
    if hasattr(prompt_data, 'template'):
        template = prompt_data.template
        # Check if it's the actual template (not the __str__ representation)
        if template and not template.startswith('input_variables='):
            return template

    # Try ChatPromptTemplate structure
    if hasattr(prompt_data, 'messages') and len(prompt_data.messages) > 0:
        # Try to extract from messages
        combined_template = []
        for msg in prompt_data.messages:
            if hasattr(msg, 'prompt') and hasattr(msg.prompt, 'template'):
                template = msg.prompt.template
                if template and not template.startswith('input_variables='):
                    combined_template.append(template)

        if combined_template:
            return '\n\n'.join(combined_template)

    # Fallback: Try to extract template from string representation
    # This handles cases where .template contains the __str__ representation
    str_repr = str(prompt_data)

    # Look for all template="..." or template='...' patterns in the string representation
    # This handles ChatPromptTemplate with multiple messages
    template_matches = re.findall(r'template="([^"]*(?:\\.[^"]*)*)"', str_repr)
    if not template_matches:
        template_matches = re.findall(r"template='([^']*(?:\\.[^']*)*)'", str_repr)

    if template_matches:
        # Decode escaped characters and combine
        decoded_templates = []
        for match in template_matches:
            # Skip if it's just a placeholder like '{input}'
            if match.strip() not in ['{input}', '{context}', '{question}']:
                # Replace common escape sequences (must be done in this order)
                decoded = match.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                decoded_templates.append(decoded)

        if decoded_templates:
            return '\n\n'.join(decoded_templates)

    # Last resort: return the string representation (might be dirty)
    return str_repr


class LangChainHubFetcher:
    """Fetch prompts from LangChain Hub by handle whitelist."""

    def __init__(self, api_key: str | None = None):
        """Initialize fetcher with LangSmith API key.

        Args:
            api_key: LangSmith API key (lsv2_...). If None, reads from LANGSMITH_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LANGSMITH_API_KEY not set. Set it as env var or pass to constructor."
            )
        # Set both for compatibility
        os.environ["LANGSMITH_API_KEY"] = self.api_key
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
        # Import here to avoid early import errors if langchain-classic not installed
        try:
            from langchain_classic import hub
        except ImportError as e:
            raise ImportError(
                f"langchain-classic not installed. Install with: pip install langchain-classic. Error: {e}"
            )

        results = []

        # Temporarily unset env vars to force hub to use public Hub API
        langchain_key = os.environ.pop("LANGCHAIN_API_KEY", None)
        langsmith_key = os.environ.pop("LANGSMITH_API_KEY", None)

        try:
            for handle in handles:
                try:
                    print(f"Fetching {handle}...")
                    # Use hub.pull() to get prompt from LangChain Hub
                    # With env vars unset, hub will use public Hub API
                    prompt_data = hub.pull(handle)

                    # Extract prompt information using the helper function
                    # This handles PromptTemplate, ChatPromptTemplate, etc.
                    template = _extract_template_from_langchain_object(prompt_data)
                    input_variables = prompt_data.input_variables if hasattr(prompt_data, 'input_variables') else []
                    partial_variables = prompt_data.partial_variables if hasattr(prompt_data, 'partial_variables') else {}

                    # Try to get metadata
                    tags = getattr(prompt_data, 'tags', [])
                    metadata = getattr(prompt_data, 'metadata', {})

                    results.append({
                        "handle": handle,
                        "name": handle,
                        "template": template,
                        "input_variables": input_variables,
                        "partial_variables": partial_variables,
                        "tags": tags,
                        "metadata": metadata
                    })
                    print(f"  ✓ Fetched: {handle}")
                except Exception as e:
                    print(f"  ✗ Failed to fetch {handle}: {e}")
                    continue
        finally:
            # Restore environment variables
            if langchain_key:
                os.environ["LANGCHAIN_API_KEY"] = langchain_key
            if langsmith_key:
                os.environ["LANGSMITH_API_KEY"] = langsmith_key

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
                "template": prompt_data["template"]
            }

            # If converter provided, convert to DSPy format
            if converter:
                candidate["converted"] = converter.to_dspy_format(prompt_data)

            candidates.append(candidate)

        return {
            "metadata": metadata,
            "candidates": candidates
        }
