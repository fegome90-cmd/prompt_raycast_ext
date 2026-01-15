"""Configuration module for synthetic examples."""


# Component catalog location
DEFAULT_CATALOG_PATH = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/ComponentCatalog.json"

# Quality thresholds
# NOTE: ComponentCatalog.json has max confidence of 0.425, so we use 0.2 as threshold
CONFIDENCE_THRESHOLD = 0.2

# Output directory for generated datasets
DEFAULT_OUTPUT_DIR = (
    "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/synthetic/"
)
