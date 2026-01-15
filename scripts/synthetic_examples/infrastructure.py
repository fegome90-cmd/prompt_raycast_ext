"""Infrastructure module for loading component catalogs."""

import json
from pathlib import Path

from scripts.legacy_curation.models import Component, Domain
from scripts.synthetic_examples.config import CONFIDENCE_THRESHOLD, DEFAULT_CATALOG_PATH


def load_component_catalog(path: str | None = None) -> list[Component]:
    """Load and validate component catalog from JSON file.

    Args:
        path: Path to ComponentCatalog.json file. If None, uses DEFAULT_CATALOG_PATH.

    Returns:
        List of Component objects with confidence >= threshold

    Raises:
        ValueError: If file not found, invalid JSON, or validation fails
    """
    if path is None:
        path = DEFAULT_CATALOG_PATH

    file_path = Path(str(path))

    if not file_path.exists():
        raise ValueError(f"File not found: {path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

    if "components" not in data:
        raise ValueError("Invalid catalog format: missing 'components' field")

    components = []
    for comp_data in data["components"]:
        try:
            # Extract only fields Component model accepts
            # Convert domain string to Domain enum
            domain_str = comp_data["domain"]
            try:
                domain = Domain(domain_str)
            except ValueError:
                # Default to OTHER if domain is invalid
                domain = Domain.OTHER

            component_data = {
                "source_file": comp_data["source_file"],
                "domain": domain,
                "role": comp_data["role"],
                "directive": comp_data["directive"],
                "framework": comp_data["framework"],
                "guardrails": comp_data["guardrails"],
                "confidence": comp_data["confidence"],
            }
            component = Component(**component_data)
            if component.confidence >= CONFIDENCE_THRESHOLD:
                components.append(component)
        except Exception as e:
            raise ValueError(f"Invalid component data: {e}")

    return components
