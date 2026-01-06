# Synthetic Examples Pipeline

Pipeline para generar ejemplos sintéticos de prompts a partir de componentes extraídos de ComponentCatalog.json.

## 📋 Overview

Este pipeline genera ejemplos sintéticos de alta calidad entrenables con DSPy, utilizando como fuente un catálogo de componentes extraídos de prompts existentes.

**Features:**
- Carga y filtrado de componentes por nivel de confianza
- Generación de ejemplos con variaciones (simplify, expand, add_context, restructure)
- Validación de calidad con scoring (0.0-1.0)
- Construcción de datasets DSPy-compatible
- Exportación en train/val/test splits

## 📦 Installation

### Requirements

```bash
# Python 3.14+
# Dependencies:
- pydantic>=2.0
- pytest>=9.0
```

### Setup

```bash
# Clone o navega al proyecto
cd /Users/felipe_gonzalez/Developer/raycast_ext

# Estructura del proyecto:
scripts/
├── legacy_curation/models.py       # Component, Domain enums
├── synthetic_examples/
│   ├── config.py
│   ├── infrastructure.py
│   ├── dataset_builder.py
│   ├── validator.py
│   ├── generators/example_generator.py
│   └── generate_datasets.py
└── tests/
    └── synthetic_examples/
        ├── test_infrastructure.py
        ├── test_example_generator.py
        ├── test_dataset_builder.py
        └── test_validator.py
```

## 🚀 Usage

### Generate Synthetic Datasets

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
python3 scripts/synthetic_examples/generate_datasets.py
```

**Output:**
```
=== Synthetic Dataset Generation Pipeline ===

Step 1: Loading ComponentCatalog...
  ✓ Loaded 6 components with confidence >= 0.2

Step 2: Generating synthetic examples...
  ✓ Generated 18 synthetic examples

Step 3: Validating examples...
  ✓ Valid: 16, Invalid: 2
  ✓ Avg score: 0.651

Step 4: Building DSPy datasets...
  ✓ Total examples: 16
  ✓ Train: 11, Val: 2, Test: 3

  ✓ Saved train dataset: .../train.json
  ✓ Saved val dataset: .../val.json
  ✓ Saved test dataset: .../test.json

Step 5: Dataset Statistics
  Total examples: 16
  By task_type: {'combined_task': 16}
  By domain: {'Domain.SOFTDEV': 10, 'Domain.AIML': 6}
  Avg confidence: 0.316

=== Pipeline Completed Successfully ===
```

### Run Tests

```bash
# Run all tests
python3 -m pytest scripts/tests/ -v

# Run specific test module
python3 -m pytest scripts/tests/test_infrastructure.py -v

# Run integration test
python3 -m pytest scripts/tests/test_integration.py -v
```

**Test Results:**
```
37 tests total:
- test_infrastructure.py: 5 tests
- test_example_generator.py: 5 tests
- test_dataset_builder.py: 10 tests
- test_validator.py: 17 tests
- test_integration.py: 1 test
```

## ⚙️ Configuration

### Configuration File

Edit `scripts/synthetic_examples/config.py`:

```python
from pathlib import Path

# Component catalog location
DEFAULT_CATALOG_PATH = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/ComponentCatalog.json"

# Quality thresholds
CONFIDENCE_THRESHOLD = 0.2  # Filter components with confidence >= 0.2

# Output directory for generated datasets
DEFAULT_OUTPUT_DIR = "/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/synthetic/"
```

### Quality Thresholds

Edit `scripts/synthetic_examples/validator.py`:

```python
class ExampleValidator:
    # Question length limits
    MIN_QUESTION_LENGTH = 50      # Minimum characters
    MAX_QUESTION_LENGTH = 5000    # Maximum characters

    # Guardrail limits
    MIN_GUARDRAILS = 1
    MAX_GUARDRAILS = 10
```

### Example Variations

The generator supports 4 variation types:

1. **base**: Original template without modifications
2. **expand**: Adds more descriptive language
   - "You are a {role}" → "You act as a highly experienced and knowledgeable {role}"
3. **add_context**: Adds explanation requirements
   - Appends: "Provide detailed explanations with step-by-step reasoning..."
4. **simplify**: Removes extra sentences
   - Keeps only the first sentence
5. **restructure**: Reorders sentence structure
   - "As a {role}, your task is to {directive}" → "Your task is to {directive}. As a {role}."

### Domain-Specific Templates

Each domain has custom templates:

**SOFTDEV:**
- "You are an expert {role}."
- "As a {role}, your task is to {directive}."
- "You specialize in {role} with expertise in {domain_lower}."

**PRODUCTIVITY:**
- "You are a {role} focused on efficiency."
- "Your primary goal is {directive}."

**AIML:**
- "You are a {role} with deep understanding of {domain_lower}."
- "As a {role}, help with {directive}."

**SECURITY:**
- "You are a security-focused {role}."
- "Apply {framework} to {directive}."

**OTHER:**
- "You are a {role}."
- "Your task is to {directive}."

## 📊 Output Format

### DSPy Dataset Format

```json
{
  "dataset_name": "synthetic_examples_train",
  "split": "train",
  "total_examples": 11,
  "examples": [
    {
      "question": "You are an expert performance optimization expert...",
      "metadata": {
        "task_type": "combined_task",
        "domain": "Domain.SOFTDEV",
        "confidence": 0.425,
        "source_component_id": "docs/research/...:Domain.SOFTDEV",
        "variation": "base"
      }
    }
  ]
}
```

### Summary Statistics

```json
{
  "pipeline_stats": {
    "total_examples": 16,
    "by_task_type": {"combined_task": 16},
    "by_domain": {"Domain.SOFTDEV": 10, "Domain.AIML": 6},
    "avg_confidence": 0.316
  },
  "validation_stats": {
    "total": 18,
    "valid": 16,
    "invalid": 2,
    "avg_score": 0.651,
    "min_score": 0.417,
    "max_score": 0.740
  },
  "splits": {
    "train": 11,
    "val": 2,
    "test": 3
  },
  "total_components": 6,
  "total_examples_generated": 18,
  "total_valid_examples": 16
}
```

## 🔍 Component Catalog

The pipeline loads components from `ComponentCatalog.json` with the following structure:

```json
{
  "components": [
    {
      "source_file": "path/to/file.md",
      "domain": "softdev",
      "category": "prompt",
      "size_tokens": 500,
      "role": "Software Engineer",
      "directive": "Build scalable systems",
      "framework": "Chain-of-Thought",
      "guardrails": ["No hallucinations", "Be specific"],
      "guardrails_count": 2,
      "confidence": 0.425,
      "metadata": {}
    }
  ],
  "total_components": 847,
  "avg_confidence": 0.002
}
```

**Domains:**
- `softdev`: Software Development
- `productivity`: Productivity Tools
- `aiml`: AI/ML
- `security`: Security
- `other`: Other

## 🎯 Quality Scoring

The validator calculates quality scores (0.0-1.0) based on:

### Positive Factors:
- **Length score**: Ideal length ~200 characters
- **Context indicators**: Words like "explain", "describe", "analyze", "provide", "example"
- **Action verbs**: Words like "create", "build", "implement", "design", "develop"
- **Constraints**: Words like "constraint", "limit", "must", "should", "require"
- **Confidence**: Component confidence (0.0-1.0)
- **Task type**: Valid task_type in TASK_TYPES

### Negative Factors (Errors):
- Empty fields
- Framework mentions (Chain-of-Thought, Tree-of-Thoughts)
- Excessive special characters (>30%)
- Unbalanced parentheses
- Repetitive words (>3 occurrences)
- Question too short (<50) or too long (>5000)

### Quality Thresholds:
- **Valid**: Score >= 0.5 AND no errors
- **High Quality**: Score >= 0.7
- **Excellent**: Score >= 0.9

## 📈 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ComponentCatalog.json                                   │
│  (847 components, confidence 0.0-0.425)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Infrastructure │
              │  (Load & Filter) │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ ExampleGenerator │
              │  (Generate with  │
              │   variations)    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ ExampleValidator │
              │  (Quality score)  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ DSPyDatasetBuilder │
              │  (Build dataset) │
              └────────┬────────┘
                       │
                       ▼
         ┌──────────────────────────┐
         │  DSPy Dataset (JSON)    │
         │  train/val/test splits  │
         └──────────────────────────┘
```

## 🔧 Troubleshooting

### No components loaded

**Problem:** `✓ Loaded 0 components`

**Solutions:**
1. Check `DEFAULT_CATALOG_PATH` in `config.py`
2. Verify `CONFIDENCE_THRESHOLD` is not too high
3. Ensure `ComponentCatalog.json` exists and is valid JSON

### All examples invalid

**Problem:** `✓ Valid: 0, Invalid: 100`

**Solutions:**
1. Check if components have valid `role` and `directive` fields
2. Verify `MIN_QUESTION_LENGTH = 50` is appropriate
3. Review validation errors in output

### Import errors

**Problem:** `ModuleNotFoundError: No module named 'scripts'`

**Solution:**
```bash
# Make sure you're in the correct directory
cd /Users/felipe_gonzalez/Developer/raycast_ext

# Run from there
python3 scripts/synthetic_examples/generate_datasets.py
```

### Test failures

**Problem:** Tests failing after code changes

**Solution:**
```bash
# Re-run all tests
python3 -m pytest scripts/tests/ -v

# Run integration test specifically
python3 scripts/tests/test_integration.py
```

## 📝 Development

### Running Individual Modules

```python
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path.cwd()))

# Import modules
from scripts.synthetic_examples.infrastructure import load_component_catalog
from scripts.synthetic_examples.generators.example_generator import ExampleGenerator
from scripts.synthetic_examples.dataset_builder import DSPyDatasetBuilder
from scripts.synthetic_examples.validator import ExampleValidator

# Load components
components = load_component_catalog()

# Generate examples
generator = ExampleGenerator(seed=42)
examples = generator.generate_batch(components, examples_per_component=3)

# Validate examples
validator = ExampleValidator()
valid_examples, stats = validator.validate_batch(examples, min_quality_score=0.5)

# Build dataset
builder = DSPyDatasetBuilder()
for example in valid_examples:
    builder.add_examples([{
        'question': example['question'],
        'metadata': example['metadata']
    }])

# Get statistics
stats = builder.get_statistics()
print(f"Total examples: {stats['total_examples']}")
print(f"By domain: {stats['by_domain']}")
print(f"Avg confidence: {stats['avg_confidence']}")
```

### Adding Custom Variations

Edit `scripts/synthetic_examples/generators/example_generator.py`:

```python
def _apply_variation(self, template: str, variation: str, component: Component) -> str:
    """Apply a variation to a template."""
    if variation == "custom_variation":
        # Add your custom variation logic here
        return f"{template} Your custom modification."
    # ... rest of variations
    return template
```

### Adding Custom Quality Checks

Edit `scripts/synthetic_examples/validator.py`:

```python
def _check_patterns(self, question: str) -> List[Dict]:
    """Check question against quality patterns."""
    errors = []

    # Add your custom pattern check
    if "PROHIBITED_WORD" in question.lower():
        errors.append({
            "field": "question",
            "message": "Question contains prohibited word",
            "severity": "error",
        })

    # ... rest of checks
    return errors
```

## 📚 References

- **DSPy:** https://github.com/stanfordnlp/dspy
- **Pydantic:** https://docs.pydantic.dev/
- **pytest:** https://docs.pytest.org/

## 📄 File Structure

```
Developer/raycast_ext/
├── scripts/
│   ├── legacy_curation/
│   │   ├── __init__.py
│   │   └── models.py                    # Component, Domain enums
│   ├── synthetic_examples/
│   │   ├── __init__.py
│   │   ├── config.py                     # Configuration
│   │   ├── infrastructure.py              # load_component_catalog()
│   │   ├── dataset_builder.py            # DSPyDatasetBuilder
│   │   ├── validator.py                 # ExampleValidator
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   └── example_generator.py  # ExampleGenerator
│   │   └── generate_datasets.py         # Pipeline script
│   └── tests/
│       ├── __init__.py
│       ├── test_infrastructure.py           # 5 tests
│       ├── test_example_generator.py         # 5 tests
│       ├── test_dataset_builder.py          # 10 tests
│       ├── test_validator.py              # 17 tests
│       └── test_integration.py            # 1 test
├── prompt_research/
│   └── HANDOFF.md
└── datasets/exports/synthetic/
    ├── train.json                            # Training examples
    ├── val.json                              # Validation examples
    ├── test.json                             # Test examples
    └── summary.json                          # Statistics
```

## ✅ Status

**Phase 1:** ✅ COMPLETE (Legacy Curation Pipeline)
**Phase 2:** ✅ COMPLETE (Synthetic Examples Pipeline)

**Tasks Completed:**
- ✅ Task 1: Infrastructure & Data Loading
- ✅ Task 2: Synthetic Example Generator
- ✅ Task 3: DSPy Dataset Builder
- ✅ Task 4: Quality Validation Pipeline
- ✅ Task 5: CLI Entry Point
- ✅ Task 6: Integration Testing & Documentation
- ✅ Task 7: Final Validation & Export

**Test Coverage:**
- 38 tests total (37 unit + 1 integration)
- 100% pass rate
- All functionality verified

**Production Ready:** ✅
