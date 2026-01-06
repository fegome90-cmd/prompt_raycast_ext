# Phase 3 Completion: Few-Shot DSPy + Quality Metrics

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Few-Shot DSPy optimization with KNNFewShot compilation and implement Quality Metrics system for prompt evaluation.

**Architecture:**

1. Fix broken imports in UnifiedPipeline (phase3_fewshot → data.fewshot)
2. Integrate DSPy KNNFewShot for real similarity-based example selection
3. Port Quality Metrics from research docs to production code
4. Add API endpoints for metrics display in Raycast UI

**Tech Stack:** DSPy 3.x, LiteLLM, FastAPI, pytest

---

## Task 1: Fix Broken Imports in UnifiedPipeline

**Files:**

- Modify: `scripts/phase3_pipeline/optimizer.py`

**Step 1: Write failing test for import fix**

Create: `scripts/tests/phase3/test_pipeline_imports.py`

```python
"""Test that UnifiedPipeline imports work correctly."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_unified_pipeline_imports():
    """Test UnifiedPipeline can be imported and instantiated."""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    assert pipeline is not None
    assert hasattr(pipeline, 'dspy_optimizer')
    assert hasattr(pipeline, 'example_pool')
    assert hasattr(pipeline, 'selector')
    assert hasattr(pipeline, 'dataset_loader')


def test_unified_pipeline_has_required_methods():
    """Test UnifiedPipeline has run method."""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline()
    assert hasattr(pipeline, 'run')
    assert callable(pipeline.run)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/phase3/test_pipeline_imports.py -v`

Expected: `ImportError: cannot import name 'ExamplePool' from 'scripts.phase3_fewshot.example_pool'`

**Step 3: Fix imports in UnifiedPipeline**

Modify: `scripts/phase3_pipeline/optimizer.py`

```python
"""Unified DSPy + Few-Shot optimization pipeline."""
from typing import Dict
from scripts.phase3_dspy.optimizer import DSPOptimizer, DatasetLoader
# FIX: Import from correct path
from scripts.data.fewshot.example_pool import ExamplePool
from scripts.data.fewshot.selector import SimilaritySelector


class UnifiedPipeline:
    """Unified DSPy + Few-Shot optimization pipeline."""

    def __init__(self):
        self.dspy_optimizer = DSPOptimizer()
        self.example_pool = ExamplePool()
        self.selector = SimilaritySelector()
        self.dataset_loader = DatasetLoader()

    def run(self) -> Dict:
        """Run complete optimization pipeline.

        Returns:
            Dict with optimized prompts and few-shot examples
        """
        # Load datasets
        train, val, test = self.dataset_loader.load_datasets()

        # Build example pool
        self.example_pool.build(train)

        # Optimize with DSPy
        dspy_result = self.dspy_optimizer.optimize(train, val)

        # Select few-shot examples for test set
        few_shot_results = []
        for test_example in test:
            selected = self.selector.select(
                test_example['question'],
                self.example_pool,
                k=3
            )
            few_shot_results.append({
                'query': test_example['question'],
                'selected_examples': selected
            })

        result = {
            'optimized_prompts': dspy_result,
            'few_shot_examples': few_shot_results,
            'metrics': {
                'train_size': len(train),
                'val_size': len(val),
                'test_size': len(test),
                'pool_size': len(self.example_pool.examples)
            }
        }

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest scripts/tests/phase3/test_pipeline_imports.py -v`

Expected: `PASS test_pipeline_imports.py::test_unified_pipeline_imports`
Expected: `PASS test_pipeline_imports.py::test_unified_pipeline_has_required_methods`

**Step 5: Commit**

```bash
git add scripts/phase3_pipeline/optimizer.py scripts/tests/phase3/test_pipeline_imports.py
git commit -m "fix: correct fewshot import paths in UnifiedPipeline"
```

---

## Task 2: Implement KNNFewShot with DSPy

**Files:**

- Create: `hemdov/domain/dspy_modules/knn_fewshot_learner.py`
- Modify: `scripts/data/fewshot/selector.py`

**Step 1: Write failing test for KNNFewShot**

Create: `scripts/tests/phase3/test_knn_fewshot.py`

```python
"""Test KNNFewShot compilation with DSPy."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import dspy
from hemdov.domain.dspy_modules.knn_fewshot_learner import KNNFewShotLearner


def test_knn_learner_initialization():
    """Test KNNFewShotLearner can be initialized."""
    learner = KNNFewShotLearner(k=3)
    assert learner.k == 3
    assert learner.trainset is None


def test_knn_learner_compile():
    """Test KNNFewShotLearner compilation with examples."""
    # Create sample trainset
    trainset = [
        dspy.Example(
            original_idea="Create a prompt for code review",
            context="",
            improved_prompt="## Role\nCode Reviewer\n\n## Directive\nReview code for bugs",
            role="Code Reviewer",
            directive="Review code for bugs",
            framework="",
            guardrails=""
        ).with_inputs('original_idea', 'context'),
        dspy.Example(
            original_idea="Generate a data analyst prompt",
            context="",
            improved_prompt="## Role\nData Analyst\n\n## Directive\nAnalyze data trends",
            role="Data Analyst",
            directive="Analyze data trends",
            framework="",
            guardrails=""
        ).with_inputs('original_idea', 'context'),
    ]

    learner = KNNFewShotLearner(k=1)
    compiled = learner.compile(trainset)

    assert compiled is not None
    assert learner.trainset is not None
    assert len(learner.trainset) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/phase3/test_knn_fewshot.py -v`

Expected: `ModuleNotFoundError: hemdov.domain.dspy_modules.knn_fewshot_learner`

**Step 3: Implement KNNFewShotLearner**

Create: `hemdov/domain/dspy_modules/knn_fewshot_learner.py`

```python
"""KNNFewShot learner for DSPy compilation."""
from typing import List, Optional
import dspy


class KNNFewShotLearner:
    """KNNFewShot learner for few-shot learning with DSPy.

    Uses DSPy's KNNFewShot teleprompter to compile a module
    with k-nearest neighbors example selection.
    """

    def __init__(self, k: int = 3):
        """Initialize KNNFewShot learner.

        Args:
            k: Number of examples to retrieve for few-shot
        """
        self.k = k
        self.trainset: Optional[List[dspy.Example]] = None
        self.compiled_module: Optional[dspy.Module] = None

    def compile(
        self,
        trainset: List[dspy.Example],
        module: Optional[dspy.Module] = None
    ) -> dspy.Module:
        """Compile module with KNNFewShot.

        Args:
            trainset: Training examples for few-shot pool
            module: Optional module to compile (creates default if None)

        Returns:
            Compiled DSPy module with KNNFewShot
        """
        self.trainset = trainset

        # Create default module if not provided
        if module is None:
            # Use PromptImprover signature
            from hemdov.domain.dspy_modules.prompt_improver import PromptImprover
            module = PromptImprover()

        # Configure KNNFewShot teleprompter
        knn_teleprompter = dspy.KNNFewShot(k=self.k, trainset=trainset)

        # Compile module
        self.compiled_module = knn_teleprompter.compile(module)

        return self.compiled_module

    def retrieve(self, query: str, k: Optional[int] = None) -> List[dspy.Example]:
        """Retrieve k most similar examples for query.

        Args:
            query: Query string
            k: Number of examples (defaults to self.k)

        Returns:
            List of most similar examples
        """
        if self.trainset is None:
            raise ValueError("Must compile with trainset before retrieving")

        k = k or self.k

        # Use KNNFewShot to retrieve examples
        knn = dspy.KNNFewShot(k=k, trainset=self.trainset)
        query_example = dspy.Example(original_idea=query, context="").with_inputs('original_idea', 'context')

        # Get nearest neighbors
        neighbors = knn.retrieve([query_example])

        return neighbors[0] if neighbors else []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest scripts/tests/phase3/test_knn_fewshot.py -v`

Expected: `PASS test_knn_fewshot.py::test_knn_learner_initialization`
Expected: `PASS test_knn_fewshot.py::test_knn_learner_compile`

**Step 5: Update SimilaritySelector to use KNNFewShot**

Modify: `scripts/data/fewshot/selector.py`

```python
"""Similarity-based example selector for few-shot learning."""
from typing import List, Dict
import dspy


class SimilaritySelector:
    """Similarity-based example selector using DSPy KNNFewShot."""

    def __init__(self, k: int = 3):
        """Initialize selector.

        Args:
            k: Number of examples to retrieve
        """
        self.k = k
        self.trainset: List[dspy.Example] = []

    def _convert_to_dspy_examples(self, examples: List[Dict]) -> List[dspy.Example]:
        """Convert dict examples to DSPy Examples.

        Args:
            examples: List of dict examples with 'question' and 'answer'

        Returns:
            List of dspy.Example
        """
        dspy_examples = []
        for ex in examples:
            dspy_ex = dspy.Example(
                question=ex['question'],
                answer=ex.get('answer', '')
            ).with_inputs('question')
            dspy_examples.append(dspy_ex)
        return dspy_examples

    def select(self, query: str, pool, k: int = None) -> List[Dict]:
        """Select top-k most similar examples to query using KNNFewShot.

        Args:
            query: Query string
            pool: ExamplePool to search
            k: Number of examples to return (defaults to self.k)

        Returns:
            List of top-k similar examples
        """
        k = k or self.k

        # Convert pool examples to DSPy format
        if not self.trainset and pool.examples:
            self.trainset = self._convert_to_dspy_examples(pool.examples)

        # Create query example
        query_example = dspy.Example(question=query).with_inputs('question')

        # Use KNNFewShot to retrieve
        knn = dspy.KNNFewShot(k=k, trainset=self.trainset)
        neighbors = knn.retrieve([query_example])

        # Convert back to dict format
        if neighbors and neighbors[0]:
            return [
                {
                    'question': n.question,
                    'answer': n.answer
                }
                for n in neighbors[0]
            ]

        # Fallback to simple selection if KNN fails
        return pool.examples[:k]
```

**Step 6: Run tests to verify changes**

Run: `uv run pytest scripts/tests/phase3/test_knn_fewshot.py scripts/tests/phase3/test_selector.py -v`

Expected: All tests pass

**Step 7: Commit**

```bash
git add hemdov/domain/dspy_modules/knn_fewshot_learner.py scripts/data/fewshot/selector.py scripts/tests/phase3/test_knn_fewshot.py
git commit -m "feat: implement KNNFewShot learner with DSPy"
```

---

## Task 3: Implement Quality Metrics System

**Files:**

- Create: `hemdov/domain/quality_metrics.py`
- Create: `scripts/tests/phase3/test_quality_metrics.py`

**Step 1: Write failing test for quality metrics**

Create: `scripts/tests/phase3/test_quality_metrics.py`

````python
"""Test Quality Metrics implementation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hemdov.domain.quality_metrics import QualityMetrics, PromptQuality


def test_clarity_score_base():
    """Test clarity score base calculation."""
    metrics = QualityMetrics()
    prompt = "Simple prompt"

    score = metrics.score_clarity(prompt)
    assert score == 3.0  # Base score


def test_clarity_score_with_role():
    """Test clarity score with role section."""
    metrics = QualityMetrics()
    prompt = "## Role\nYou are an expert."

    score = metrics.score_clarity(prompt)
    assert score == 4.0  # Base + 1


def test_completeness_score():
    """Test completeness score calculation."""
    metrics = QualityMetrics()
    prompt = "## Role\nExpert\n\n## Directive\nDo this"

    score = metrics.score_completeness(prompt)
    # Base 1.0 + 0.5 (role) + 0.5 (directive) = 2.0
    assert score == 2.0


def test_full_quality_score():
    """Test full quality score with all metrics."""
    metrics = QualityMetrics()

    prompt = """
## Role
You are a Python expert.

## Directive
Write clean code following PEP 8.

## Framework
1. Use type hints
2. Add docstrings

## Examples
Example of good code:
```python
def greet(name: str) -> str:
    return f"Hello, {name}"
````

## Guardrails

- No global variables
- Maximum complexity 10
  """

      quality = metrics.evaluate(prompt)

      assert quality.clarity >= 3.0
      assert quality.completeness >= 1.0
      assert quality.structure >= 3.0
      assert quality.examples >= 1.0
      assert quality.guardrails >= 1.0

      # Total score should be 5-dimensional
      assert 0 <= quality.total_score <= 5.0

````

**Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/phase3/test_quality_metrics.py -v`

Expected: `ModuleNotFoundError: hemdov.domain.quality_metrics`

**Step 3: Implement QualityMetrics domain**

Create: `hemdov/domain/quality_metrics.py`

```python
"""Quality Metrics system for prompt evaluation.

Implements 5-dimensional quality scoring:
- Clarity (base 3.0)
- Completeness (base 1.0)
- Structure (base 3.0)
- Examples (base 1.0)
- Guardrails (base 1.0)

Reference: docs/research/quality-metrics-system.md
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class PromptQuality:
    """Quality scores for a prompt."""

    clarity: float
    completeness: float
    structure: float
    examples: float
    guardrails: float

    @property
    def total_score(self) -> float:
        """Calculate weighted total score (1-5 scale)."""
        # Weights from research docs
        weights = {
            'clarity': 0.25,
            'completeness': 0.25,
            'structure': 0.20,
            'examples': 0.15,
            'guardrails': 0.15
        }

        total = (
            self.clarity * weights['clarity'] +
            self.completeness * weights['completeness'] +
            self.structure * weights['structure'] +
            self.examples * weights['examples'] +
            self.guardrails * weights['guardrails']
        )

        return min(5.0, max(1.0, total))


class QualityMetrics:
    """Quality metrics evaluator for prompts."""

    # Section patterns
    ROLE_PATTERN = re.compile(r'^##?\s*Role\s*$', re.MULTILINE | re.IGNORECASE)
    DIRECTIVE_PATTERN = re.compile(r'^##?\s*Directive\s*$', re.MULTILINE | re.IGNORECASE)
    FRAMEWORK_PATTERN = re.compile(r'^##?\s*Framework\s*$', re.MULTILINE | re.IGNORECASE)
    EXAMPLES_PATTERN = re.compile(r'^##?\s*Examples?\s*$', re.MULTILINE | re.IGNORECASE)
    GUARDRAILS_PATTERN = re.compile(r'^##?\s*Guardrails?\s*$', re.MULTILINE | re.IGNORECASE)

    # Code block pattern
    CODE_BLOCK_PATTERN = re.compile(r'```[\w]*\n[\s\S]*?```', re.MULTILINE)

    # Bullet/list pattern
    BULLET_PATTERN = re.compile(r'^[\s]*[-*•]\s+', re.MULTILINE)

    def score_clarity(self, prompt: str) -> float:
        """Score prompt clarity (base 3.0, max 5.0).

        +1.0 for role section
        +1.0 for clear directive structure

        Args:
            prompt: Prompt text to score

        Returns:
            Clarity score (1-5)
        """
        score = 3.0  # Base score

        # Check for role section
        if self.ROLE_PATTERN.search(prompt):
            score += 1.0

        # Check for directive section
        if self.DIRECTIVE_PATTERN.search(prompt):
            score += 1.0

        return min(5.0, score)

    def score_completeness(self, prompt: str) -> float:
        """Score prompt completeness (base 1.0, max 5.0).

        +0.5 for role
        +0.5 for directive
        +1.0 for framework
        +1.0 for examples
        +1.0 for guardrails

        Args:
            prompt: Prompt text to score

        Returns:
            Completeness score (1-5)
        """
        score = 1.0  # Base score

        # Check each section
        if self.ROLE_PATTERN.search(prompt):
            score += 0.5

        if self.DIRECTIVE_PATTERN.search(prompt):
            score += 0.5

        if self.FRAMEWORK_PATTERN.search(prompt):
            score += 1.0

        if self.EXAMPLES_PATTERN.search(prompt):
            score += 1.0

        if self.GUARDRAILS_PATTERN.search(prompt):
            score += 1.0

        return min(5.0, score)

    def score_structure(self, prompt: str) -> float:
        """Score prompt structure (base 3.0, max 5.0).

        +1.0 for proper section headers (##)
        +1.0 for organized lists/bullets

        Args:
            prompt: Prompt text to score

        Returns:
            Structure score (1-5)
        """
        score = 3.0  # Base score

        # Check for proper headers
        header_count = len(re.findall(r'^##\s+\w+', prompt, re.MULTILINE))
        if header_count >= 2:
            score += 1.0

        # Check for structured content (bullets)
        bullet_count = len(self.BULLET_PATTERN.findall(prompt))
        if bullet_count >= 3:
            score += 1.0

        return min(5.0, score)

    def score_examples(self, prompt: str) -> float:
        """Score prompt examples (base 1.0, max 5.0).

        +1.0 for examples section
        +1.0 per code block example (max +3.0)

        Args:
            prompt: Prompt text to score

        Returns:
            Examples score (1-5)
        """
        score = 1.0  # Base score

        # Check for examples section
        if self.EXAMPLES_PATTERN.search(prompt):
            score += 1.0

        # Count code blocks
        code_blocks = len(self.CODE_BLOCK_PATTERN.findall(prompt))
        score += min(3.0, code_blocks)

        return min(5.0, score)

    def score_guardrails(self, prompt: str) -> float:
        """Score prompt guardrails (base 1.0, max 5.0).

        +1.0 for guardrails section
        +0.5 per bullet point (max +3.0)

        Args:
            prompt: Prompt text to score

        Returns:
            Guardrails score (1-5)
        """
        score = 1.0  # Base score

        # Check for guardrails section
        if self.GUARDRAILS_PATTERN.search(prompt):
            score += 1.0

        # Count bullets in guardrails section
        guardrails_match = self.GUARDRAILS_PATTERN.search(prompt)
        if guardrails_match:
            # Get text after guardrails header
            guardrails_text = prompt[guardrails_match.end():]
            # Limit to next section or end
            next_section = re.search(r'^##', guardrails_text, re.MULTILINE)
            if next_section:
                guardrails_text = guardrails_text[:next_section.start()]

            # Count bullets
            bullet_count = len(self.BULLET_PATTERN.findall(guardrails_text))
            score += min(3.0, bullet_count * 0.5)

        return min(5.0, score)

    def evaluate(self, prompt: str) -> PromptQuality:
        """Evaluate prompt quality across all dimensions.

        Args:
            prompt: Prompt text to evaluate

        Returns:
            PromptQuality with all scores
        """
        return PromptQuality(
            clarity=self.score_clarity(prompt),
            completeness=self.score_completeness(prompt),
            structure=self.score_structure(prompt),
            examples=self.score_examples(prompt),
            guardrails=self.score_guardrails(prompt)
        )
````

**Step 4: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/phase3/test_quality_metrics.py -v`

Expected: All tests pass

**Step 5: Commit**

```bash
git add hemdov/domain/quality_metrics.py scripts/tests/phase3/test_quality_metrics.py
git commit -m "feat: implement Quality Metrics system"
```

---

## Task 4: Add API Endpoint for Quality Metrics

**Files:**

- Create: `api/quality_api.py`
- Modify: `main.py`

**Step 1: Write failing test for API endpoint**

Create: `scripts/tests/test_quality_api.py`

```python
"""Test Quality Metrics API endpoint."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app


def test_quality_endpoint_returns_scores():
    """Test POST /quality returns quality scores."""
    client = TestClient(app)

    response = client.post(
        "/api/quality/evaluate",
        json={
            "prompt": "## Role\nExpert\n\n## Directive\nDo this"
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert "clarity" in data
    assert "completeness" in data
    assert "structure" in data
    assert "examples" in data
    assert "guardrails" in data
    assert "total_score" in data


def test_quality_endpoint_handles_empty_prompt():
    """Test POST /quality handles empty prompts."""
    client = TestClient(app)

    response = client.post(
        "/api/quality/evaluate",
        json={"prompt": ""}
    )

    assert response.status_code == 200

    data = response.json()
    # Empty prompt should still return scores
    assert "total_score" in data
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_quality_api.py -v`

Expected: `404 Not Found` (endpoint doesn't exist yet)

**Step 3: Create Quality API endpoint**

Create: `api/quality_api.py`

```python
"""Quality metrics API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from hemdov.domain.quality_metrics import QualityMetrics


router = APIRouter(prefix="/api/quality", tags=["quality"])


class QualityRequest(BaseModel):
    """Request model for quality evaluation."""

    prompt: str
    context: Optional[str] = None


class QualityResponse(BaseModel):
    """Response model for quality evaluation."""

    clarity: float
    completeness: float
    structure: float
    examples: float
    guardrails: float
    total_score: float


@router.post("/evaluate", response_model=QualityResponse)
async def evaluate_quality(request: QualityRequest) -> QualityResponse:
    """Evaluate prompt quality.

    Args:
        request: QualityRequest with prompt text

    Returns:
        QualityResponse with scores for each dimension
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    metrics = QualityMetrics()
    quality = metrics.evaluate(request.prompt)

    return QualityResponse(
        clarity=quality.clarity,
        completeness=quality.completeness,
        structure=quality.structure,
        examples=quality.examples,
        guardrails=quality.guardrails,
        total_score=quality.total_score
    )
```

**Step 4: Register router in main app**

Modify: `main.py`

```python
# ... existing imports ...

from api.quality_api import router as quality_router

# ... existing code ...

@app.get("/")
async def root():
    return {"message": "DSPy HemDov Backend", "version": "0.3.0"}

# Include quality router
app.include_router(quality_router)

# ... rest of file ...
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/test_quality_api.py -v`

Expected: All tests pass

**Step 6: Manual test**

Run: `uv run python main.py`

Then test:

```bash
curl -X POST http://localhost:8000/api/quality/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "## Role\nYou are a Python expert.\n\n## Directive\nWrite clean code.\n\n## Examples\nprint(\"hello\")"
  }'
```

Expected response:

```json
{
  "clarity": 5.0,
  "completeness": 2.5,
  "structure": 4.0,
  "examples": 3.0,
  "guardrails": 1.0,
  "total_score": 3.15
}
```

**Step 7: Commit**

```bash
git add api/quality_api.py main.py scripts/tests/test_quality_api.py
git commit -m "feat: add Quality Metrics API endpoint"
```

---

## Task 5: Update UnifiedPipeline to Use KNNFewShot

**Files:**

- Modify: `scripts/phase3_pipeline/optimizer.py`
- Create: `scripts/tests/phase3/test_pipeline_integration.py`

**Step 1: Write failing integration test**

Create: `scripts/tests/phase3/test_pipeline_integration.py`

```python
"""Integration test for UnifiedPipeline with KNNFewShot."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.phase3_pipeline.optimizer import UnifiedPipeline


def test_pipeline_uses_knn_fewshot():
    """Test UnifiedPipeline uses KNNFewShot for example selection."""
    pipeline = UnifiedPipeline()

    # Mock dataset loading
    pipeline.dataset_loader.load_datasets = lambda: (
        [
            {'question': 'Test question 1', 'answer': 'Answer 1', 'metadata': {'domain': 'test'}},
            {'question': 'Test question 2', 'answer': 'Answer 2', 'metadata': {'domain': 'test'}},
        ],
        [{'question': 'Val question', 'answer': 'Val answer', 'metadata': {'domain': 'test'}}],
        [{'question': 'Test query', 'answer': 'Test answer', 'metadata': {'domain': 'test'}}]
    )

    result = pipeline.run()

    assert 'few_shot_examples' in result
    assert len(result['few_shot_examples']) > 0

    # Check that examples were selected
    first_result = result['few_shot_examples'][0]
    assert 'selected_examples' in first_result
    assert 'query' in first_result
```

**Step 2: Run test to verify current state**

Run: `uv run pytest scripts/tests/phase3/test_pipeline_integration.py -v`

Expected: May pass or fail depending on current implementation

**Step 3: Update UnifiedPipeline to use KNNFewShot**

Modify: `scripts/phase3_pipeline/optimizer.py`

```python
"""Unified DSPy + Few-Shot optimization pipeline."""
from typing import Dict, List
from scripts.phase3_dspy.optimizer import DSPOptimizer, DatasetLoader
from scripts.data.fewshot.example_pool import ExamplePool
from hemdov.domain.dspy_modules.knn_fewshot_learner import KNNFewShotLearner
import dspy


class UnifiedPipeline:
    """Unified DSPy + Few-Shot optimization pipeline with KNNFewShot."""

    def __init__(self, k: int = 3):
        """Initialize pipeline.

        Args:
            k: Number of few-shot examples to retrieve
        """
        self.dspy_optimizer = DSPOptimizer()
        self.example_pool = ExamplePool()
        self.knn_learner = KNNFewShotLearner(k=k)
        self.dataset_loader = DatasetLoader()
        self.k = k

    def _convert_to_dspy_examples(self, examples: List[Dict]) -> List[dspy.Example]:
        """Convert dict examples to DSPy format.

        Args:
            examples: List of dict examples

        Returns:
            List of dspy.Example
        """
        dspy_examples = []
        for ex in examples:
            dspy_ex = dspy.Example(
                question=ex['question'],
                answer=ex.get('answer', '')
            ).with_inputs('question')
            dspy_examples.append(dspy_ex)
        return dspy_examples

    def run(self) -> Dict:
        """Run complete optimization pipeline.

        Returns:
            Dict with optimized prompts and few-shot examples
        """
        # Load datasets
        train, val, test = self.dataset_loader.load_datasets()

        # Build example pool
        self.example_pool.build(train)

        # Convert to DSPy examples
        trainset_dspy = self._convert_to_dspy_examples(train)

        # Compile KNNFewShot learner
        self.knn_learner.compile(trainset_dspy)

        # Optimize with DSPy
        dspy_result = self.dspy_optimizer.optimize(train, val)

        # Select few-shot examples for test set using KNN
        few_shot_results = []
        for test_example in test:
            # Use KNNFewShot to retrieve similar examples
            retrieved = self.knn_learner.retrieve(test_example['question'], k=self.k)

            few_shot_results.append({
                'query': test_example['question'],
                'selected_examples': [
                    {
                        'question': ex.question,
                        'answer': ex.answer
                    }
                    for ex in retrieved
                ],
                'method': 'knn_fewshot'
            })

        result = {
            'optimized_prompts': dspy_result,
            'few_shot_examples': few_shot_results,
            'metrics': {
                'train_size': len(train),
                'val_size': len(val),
                'test_size': len(test),
                'pool_size': len(self.example_pool.examples),
                'method': 'knn_fewshot',
                'k': self.k
            }
        }

        return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/phase3/test_pipeline_integration.py -v`

Expected: All tests pass

**Step 5: Update existing tests**

Update: `scripts/tests/phase3/test_pipeline.py`

```python
"""Test UnifiedPipeline with KNNFewShot."""

# Add test for KNN method
def test_pipeline_uses_knn_method():
    """Test pipeline reports KNN method in metrics."""
    from scripts.phase3_pipeline.optimizer import UnifiedPipeline

    pipeline = UnifiedPipeline(k=3)

    # Mock datasets
    pipeline.dataset_loader.load_datasets = lambda: (
        [{'question': 'Q1', 'answer': 'A1', 'metadata': {'domain': 'test'}}],
        [{'question': 'QV', 'answer': 'AV', 'metadata': {'domain': 'test'}}],
        [{'question': 'QT', 'answer': 'AT', 'metadata': {'domain': 'test'}}]
    )

    result = pipeline.run()

    assert result['metrics']['method'] == 'knn_fewshot'
    assert result['metrics']['k'] == 3
```

**Step 6: Commit**

```bash
git add scripts/phase3_pipeline/optimizer.py scripts/tests/phase3/test_pipeline.py scripts/tests/phase3/test_pipeline_integration.py
git commit -m "feat: integrate KNNFewShot into UnifiedPipeline"
```

---

## Task 6: Documentation and Cleanup

**Files:**

- Create: `docs/backend/phase3-implementation.md`
- Update: `CLAUDE.md`

**Step 1: Create Phase 3 documentation**

Create: `docs/backend/phase3-implementation.md`

````markdown
# Phase 3 Implementation Guide

## Overview

Phase 3 completes the DSPy + Few-Shot optimization system with:

- KNNFewShot compilation for semantic example retrieval
- Quality Metrics system for prompt evaluation
- Unified pipeline end-to-end

## Components

### KNNFewShot Learner

Location: `hemdov/domain/dspy_modules/knn_fewshot_learner.py`

Provides semantic example retrieval using DSPy's KNNFewShot teleprompter.

Usage:

```python
from hemdov.domain.dspy_modules.knn_fewshot_learner import KNNFewShotLearner

learner = KNNFewShotLearner(k=3)
compiled = learner.compile(trainset)
neighbors = learner.retrieve("Create a Python prompt", k=3)
```
````

### Quality Metrics

Location: `hemdov/domain/quality_metrics.py`

5-dimensional quality scoring:

- Clarity (base 3.0): Role + Directive
- Completeness (base 1.0): All sections present
- Structure (base 3.0): Headers + Bullets
- Examples (base 1.0): Code blocks
- Guardrails (base 1.0): Constraints

Usage:

```python
from hemdov.domain.quality_metrics import QualityMetrics

metrics = QualityMetrics()
quality = metrics.evaluate(prompt)
print(f"Total: {quality.total_score}/5.0")
```

### API Endpoint

`POST /api/quality/evaluate`

Request:

```json
{
  "prompt": "## Role\\nExpert..."
}
```

Response:

```json
{
  "clarity": 5.0,
  "completeness": 4.0,
  "structure": 4.0,
  "examples": 3.0,
  "guardrails": 3.0,
  "total_score": 3.9
}
```

### Unified Pipeline

Location: `scripts/phase3_pipeline/optimizer.py`

End-to-end pipeline:

1. Load datasets (train/val/test)
2. Build example pool
3. Compile KNNFewShot learner
4. Optimize with DSPy
5. Retrieve few-shot examples for queries

Usage:

```bash
uv run python -m scripts.phase3_pipeline.main
```

## Testing

All tests:

```bash
uv run pytest scripts/tests/phase3/ -v
```

Specific modules:

```bash
uv run pytest scripts/tests/phase3/test_knn_fewshot.py -v
uv run pytest scripts/tests/phase3/test_quality_metrics.py -v
uv run pytest scripts/tests/phase3/test_pipeline_integration.py -v
```

## Architecture

```
scripts/phase3_pipeline/
├── main.py              # CLI entry point
└── optimizer.py         # UnifiedPipeline (KNNFewShot + DSPy)

hemdov/domain/
├── dspy_modules/
│   ├── prompt_improver.py
│   └── knn_fewshot_learner.py  # KNNFewShot compilation
└── quality_metrics.py   # 5-dimensional scoring

scripts/data/fewshot/
├── example_pool.py      # Example pool management
├── selector.py          # KNNFewShot-based selector
└── component_normalizer.py
```

## Next Steps

- [ ] A/B Testing framework
- [ ] Enhancement Engine iteration
- [ ] Raycast UI integration for quality display

````

**Step 2: Update CLAUDE.md**

Modify: `CLAUDE.md`

Add to Quickstart section:
```bash
# Phase 3 Pipeline (Few-Shot + Quality Metrics)
uv run python -m scripts.phase3_pipeline.main
uv run pytest scripts/tests/phase3/  # Phase 3 tests
curl -X POST http://localhost:8000/api/quality/evaluate -d '{"prompt": "..."}'
````

**Step 3: Commit**

```bash
git add docs/backend/phase3-implementation.md CLAUDE.md
git commit -m "docs: add Phase 3 implementation guide"
```

---

## Summary

**Total estimated time:** 11-16 hours

**Tasks completed:**

1. ✅ Fixed broken imports in UnifiedPipeline (1h)
2. ✅ Implemented KNNFewShot learner (4-6h)
3. ✅ Implemented Quality Metrics system (6-10h)
4. ✅ Added Quality API endpoint (2-3h)
5. ✅ Integrated KNNFewShot into pipeline (2-3h)
6. ✅ Documentation and cleanup (1h)

**Testing coverage:**

- KNNFewShot compilation
- Quality metrics scoring
- API endpoint behavior
- End-to-end pipeline integration

**Next phase:** A/B Testing framework
