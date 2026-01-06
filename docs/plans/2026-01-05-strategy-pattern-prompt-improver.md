# Strategy Pattern for PromptImprover Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Strategy Pattern architecture for prompt improvement with complexity-based routing, replacing the simple router with a flexible, extensible system.

**Architecture:** Strategy Pattern with 3 concrete implementations (Simple/Moderate/Complex) selected by a ComplexityAnalyzer that uses multi-dimensional scoring (length + technical terms + structure + context).

**Tech Stack:** Python 3.14, DSPy 2.6, FastAPI, pytest, dataclasses/enums for type safety

---

## Task 1: Create ComplexityLevel Enum

**Files:**
- Create: `eval/src/complexity_analyzer.py`

**Step 1: Write the enum definition**

```python
# eval/src/complexity_analyzer.py
from enum import Enum

class ComplexityLevel(Enum):
    """Complexity levels for prompt classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
```

**Step 2: Write a simple test**

```python
# tests/test_complexity_analyzer.py
from eval.src.complexity_analyzer import ComplexityLevel

def test_complexity_level_enum():
    assert ComplexityLevel.SIMPLE.value == "simple"
    assert ComplexityLevel.MODERATE.value == "moderate"
    assert ComplexityLevel.COMPLEX.value == "complex"
```

**Step 3: Run test to verify it passes**

```bash
pytest tests/test_complexity_analyzer.py::test_complexity_level_enum -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add eval/src/complexity_analyzer.py tests/test_complexity_analyzer.py
git commit -m "feat: add ComplexityLevel enum"
```

---

## Task 2: Create ComplexityAnalyzer with Basic Length Analysis

**Files:**
- Modify: `eval/src/complexity_analyzer.py`
- Test: `tests/test_complexity_analyzer.py`

**Step 1: Write failing test for length-based classification**

```python
# tests/test_complexity_analyzer.py
from eval.src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel

def test_analyzer_simple_by_length():
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze("hola mundo", "")
    assert result == ComplexityLevel.SIMPLE

def test_analyzer_complex_by_length():
    analyzer = ComplexityAnalyzer()
    long_input = "diseña " * 100  # > 150 chars
    result = analyzer.analyze(long_input, "")
    assert result == ComplexityLevel.COMPLEX
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_complexity_analyzer.py::test_analyzer_simple_by_length -v
pytest tests/test_complexity_analyzer.py::test_analyzer_complex_by_length -v
```
Expected: FAIL with "ComplexityAnalyzer not defined"

**Step 3: Implement ComplexityAnalyzer**

```python
# eval/src/complexity_analyzer.py
from enum import Enum

class ComplexityLevel(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ComplexityAnalyzer:
    """Analyzes prompt complexity using multi-dimensional scoring."""

    # Thresholds for length-based classification
    SIMPLE_MAX_LENGTH = 50
    MODERATE_MAX_LENGTH = 150

    # Technical terms that indicate complexity
    TECHNICAL_TERMS = [
        "framework", "arquitectura", "arquitectura", "patrón", "diseño",
        "metrics", "metrica", "evaluación", "calidad", "optimización",
        "sistema", "componente", "integración", "pipeline", "api",
        "repositorio", "adaptador", "dominio", "infraestructura"
    ]

    def analyze(self, original_idea: str, context: str) -> ComplexityLevel:
        """
        Analyze input complexity across multiple dimensions.

        Returns:
            ComplexityLevel: SIMPLE, MODERATE, or COMPLEX
        """
        total_length = len(original_idea) + len(context)

        # 1. Length analysis (primary signal)
        if total_length <= self.SIMPLE_MAX_LENGTH:
            return ComplexityLevel.SIMPLE
        elif total_length <= self.MODERATE_MAX_LENGTH:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_complexity_analyzer.py -v
```
Expected: PASS for both tests

**Step 5: Commit**

```bash
git add eval/src/complexity_analyzer.py tests/test_complexity_analyzer.py
git commit -m "feat: add ComplexityAnalyzer with length-based classification"
```

---

## Task 3: Add Technical Term Detection to ComplexityAnalyzer

**Files:**
- Modify: `eval/src/complexity_analyzer.py`
- Test: `tests/test_complexity_analyzer.py`

**Step 1: Write failing test for technical term detection**

```python
# tests/test_complexity_analyzer.py
def test_analyzer_detects_technical_terms():
    analyzer = ComplexityAnalyzer()
    # Short input but with technical terms should be MODERATE
    result = analyzer.analyze("crea un framework de diseño", "")
    assert result == ComplexityLevel.MODERATE
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_complexity_analyzer.py::test_analyzer_detects_technical_terms -v
```
Expected: FAIL (returns SIMPLE because length < 50)

**Step 3: Enhance ComplexityAnalyzer with term detection**

```python
# eval/src/complexity_analyzer.py (modify the analyze method)
    def analyze(self, original_idea: str, context: str) -> ComplexityLevel:
        """
        Analyze input complexity across multiple dimensions.

        Returns:
            ComplexityLevel: SIMPLE, MODERATE, or COMPLEX
        """
        total_length = len(original_idea) + len(context)
        combined_text = (original_idea + " " + context).lower()

        # 1. Length analysis (40% weight)
        if total_length <= self.SIMPLE_MAX_LENGTH:
            length_score = 0.0
        elif total_length <= self.MODERATE_MAX_LENGTH:
            length_score = 0.5
        else:
            length_score = 1.0

        # 2. Technical term detection (30% weight)
        technical_count = sum(1 for term in self.TECHNICAL_TERMS if term.lower() in combined_text)
        technical_score = min(technical_count * 0.3, 1.0)

        # 3. Structure analysis (20% weight) - multiple sentences/commas
        sentence_count = combined_text.count('.') + combined_text.count(',') + combined_text.count(';')
        structure_score = min(sentence_count * 0.1, 1.0)

        # 4. Context provided (10% weight)
        context_score = 1.0 if context.strip() else 0.0

        # Combine scores
        total_score = (
            length_score * 0.4 +
            technical_score * 0.3 +
            structure_score * 0.2 +
            context_score * 0.1
        )

        # Map to complexity levels
        if total_score < 0.3:
            return ComplexityLevel.SIMPLE
        elif total_score < 0.7:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_complexity_analyzer.py -v
```
Expected: PASS for all tests

**Step 5: Commit**

```bash
git add eval/src/complexity_analyzer.py tests/test_complexity_analyzer.py
git commit -m "feat: add multi-dimensional scoring to ComplexityAnalyzer"
```

---

## Task 4: Create Strategy Base Interface

**Files:**
- Create: `eval/src/strategies/__init__.py`
- Create: `eval/src/strategies/base.py`
- Test: `tests/test_strategies/test_base.py`

**Step 1: Write the base strategy interface**

```python
# eval/src/strategies/base.py
from abc import ABC, abstractmethod
import dspy


class PromptImproverStrategy(ABC):
    """Base strategy for prompt improvement."""

    @abstractmethod
    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Improve prompt according to strategy.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging."""
        pass
```

**Step 2: Write test for base interface**

```python
# tests/test_strategies/test_base.py
from eval.src.strategies.base import PromptImproverStrategy

def test_base_strategy_is_abstract():
    """Verify base strategy cannot be instantiated."""
    try:
        strategy = PromptImproverStrategy()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        assert True
```

**Step 3: Run test to verify it passes**

```bash
pytest tests/test_strategies/test_base.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add eval/src/strategies/ tests/test_strategies/
git commit -m "feat: add PromptImproverStrategy base interface"
```

---

## Task 5: Implement SimpleStrategy

**Files:**
- Create: `eval/src/strategies/simple_strategy.py`
- Test: `tests/test_strategies/test_simple_strategy.py`

**Step 1: Write failing test for SimpleStrategy**

```python
# tests/test_strategies/test_simple_strategy.py
from eval.src.strategies.simple_strategy import SimpleStrategy

def test_simple_strategy_has_name():
    strategy = SimpleStrategy()
    assert strategy.name == "simple"

def test_simple_strategy_produces_short_output():
    strategy = SimpleStrategy()
    result = strategy.improve("hola mundo", "")
    assert len(result.improved_prompt) <= 800
    assert hasattr(result, 'role')
    assert hasattr(result, 'directive')
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_strategies/test_simple_strategy.py -v
```
Expected: FAIL with "SimpleStrategy not defined"

**Step 3: Implement SimpleStrategy**

```python
# eval/src/strategies/simple_strategy.py
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature
from .base import PromptImproverStrategy


class SimpleStrategy(PromptImproverStrategy):
    """Ultra-concise strategy for simple/trivial inputs."""

    def __init__(self, max_length: int = 800):
        """
        Initialize simple strategy.

        Args:
            max_length: Maximum output length in characters
        """
        self.improver = dspy.Predict(PromptImproverSignature)
        self._max_length = max_length

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """Generate concise prompt improvement."""
        result = self.improver(original_idea=original_idea, context=context)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(result.improved_prompt)

        return result

    @property
    def name(self) -> str:
        return "simple"

    def _truncate_at_sentence(self, text: str) -> str:
        """Truncate at last complete sentence within limit."""
        truncated = text[:self._max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        # Use the last sentence boundary
        if last_period > self._max_length * 0.7:
            return truncated[:last_period + 1]
        elif last_newline > self._max_length * 0.7:
            return truncated[:last_newline]
        else:
            return truncated + "..."
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_strategies/test_simple_strategy.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add eval/src/strategies/simple_strategy.py tests/test_strategies/test_simple_strategy.py
git commit -m "feat: add SimpleStrategy with 800-char limit"
```

---

## Task 6: Implement ModerateStrategy

**Files:**
- Create: `eval/src/strategies/moderate_strategy.py`
- Test: `tests/test_strategies/test_moderate_strategy.py`

**Step 1: Write failing test**

```python
# tests/test_strategies/test_moderate_strategy.py
from eval.src.strategies.moderate_strategy import ModerateStrategy

def test_moderate_strategy_has_name():
    strategy = ModerateStrategy()
    assert strategy.name == "moderate"

def test_moderate_strategy_allows_more_length():
    strategy = ModerateStrategy()
    result = strategy.improve("crea un prompt para evaluar calidad de software", "")
    # Moderate allows up to 2000 chars
    assert len(result.improved_prompt) <= 2000
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_strategies/test_moderate_strategy.py -v
```
Expected: FAIL with "ModerateStrategy not defined"

**Step 3: Implement ModerateStrategy**

```python
# eval/src/strategies/moderate_strategy.py
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature
from .base import PromptImproverStrategy


class ModerateStrategy(PromptImproverStrategy):
    """Balanced strategy for moderate inputs with ChainOfThought."""

    def __init__(self, max_length: int = 2000):
        """
        Initialize moderate strategy.

        Args:
            max_length: Maximum output length in characters
        """
        self.improver = dspy.ChainOfThought(PromptImproverSignature)
        self._max_length = max_length

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """Generate balanced prompt improvement with reasoning."""
        result = self.improver(original_idea=original_idea, context=context)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(result.improved_prompt)

        return result

    @property
    def name(self) -> str:
        return "moderate"

    def _truncate_at_sentence(self, text: str) -> str:
        """Truncate at last complete sentence within limit."""
        truncated = text[:self._max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        if last_period > self._max_length * 0.7:
            return truncated[:last_period + 1]
        elif last_newline > self._max_length * 0.7:
            return truncated[:last_newline]
        else:
            return truncated
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_strategies/test_moderate_strategy.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add eval/src/strategies/moderate_strategy.py tests/test_strategies/test_moderate_strategy.py
git commit -m "feat: add ModerateStrategy with ChainOfThought"
```

---

## Task 7: Implement ComplexStrategy with FewShot

**Files:**
- Create: `eval/src/strategies/complex_strategy.py`
- Test: `tests/test_strategies/test_complex_strategy.py`

**Step 1: Write failing test**

```python
# tests/test_strategies/test_complex_strategy.py
from eval.src.strategies.complex_strategy import ComplexStrategy

def test_complex_strategy_has_name():
    strategy = ComplexStrategy(trainset_path="datasets/exports/unified-fewshot-pool.json", k=3)
    assert strategy.name == "complex"

def test_complex_strategy_uses_fewshot():
    strategy = ComplexStrategy(trainset_path="datasets/exports/unified-fewshot-pool.json", k=3)
    result = strategy.improve("diseña un sistema completo", "")
    # Complex strategy allows longer outputs
    assert len(result.improved_prompt) > 0
    assert hasattr(result, 'role')
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_strategies/test_complex_strategy.py -v
```
Expected: FAIL with "ComplexStrategy not defined"

**Step 3: Implement ComplexStrategy**

```python
# eval/src/strategies/complex_strategy.py
from eval.src.dspy_prompt_improver_fewshot import create_fewshot_improver
from .base import PromptImproverStrategy


class ComplexStrategy(PromptImproverStrategy):
    """Full few-shot strategy for complex inputs requiring high quality."""

    def __init__(self, trainset_path: str, k: int = 3):
        """
        Initialize complex strategy with few-shot learning.

        Args:
            trainset_path: Path to few-shot training dataset
            k: Number of neighbors for KNNFewShot
        """
        self._trainset_path = trainset_path
        self._k = k
        self._improver = None
        self._name = "complex"

    def improve(self, original_idea: str, context: str):
        """Generate high-quality prompt improvement with few-shot examples."""
        if self._improver is None:
            # Lazy initialization of few-shot improver
            self._improver = create_fewshot_improver(
                trainset_path=self._trainset_path,
                k=self._k
            )

        return self._improver(original_idea=original_idea, context=context)

    @property
    def name(self) -> str:
        return self._name
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_strategies/test_complex_strategy.py -v
```
Expected: PASS (may take 10-30s due to few-shot compilation)

**Step 5: Commit**

```bash
git add eval/src/strategies/complex_strategy.py tests/test_strategies/test_complex_strategy.py
git commit -m "feat: add ComplexStrategy with few-shot learning"
```

---

## Task 8: Create StrategySelector

**Files:**
- Modify: `eval/src/strategies/__init__.py`
- Test: `tests/test_strategies/test_selector.py`

**Step 1: Write failing test for StrategySelector**

```python
# tests/test_strategies/test_selector.py
from eval.src.strategies import StrategySelector
from eval.src.complexity_analyzer import ComplexityLevel
from eval.src.strategies.simple_strategy import SimpleStrategy

def test_selector_returns_simple_strategy():
    selector = StrategySelector(
        simple_strategy=SimpleStrategy(),
        moderate_strategy=None,  # Not needed for this test
        complex_strategy=None
    )
    strategy = selector.get_strategy(ComplexityLevel.SIMPLE)
    assert strategy.name == "simple"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_strategies/test_selector.py -v
```
Expected: FAIL with "StrategySelector not defined"

**Step 3: Implement StrategySelector**

```python
# eval/src/strategies/__init__.py
from .base import PromptImproverStrategy
from .simple_strategy import SimpleStrategy
from .moderate_strategy import ModerateStrategy
from .complex_strategy import ComplexStrategy
from eval.src.complexity_analyzer import ComplexityLevel


class StrategySelector:
    """Selects appropriate strategy based on complexity level."""

    def __init__(
        self,
        simple_strategy: PromptImproverStrategy,
        moderate_strategy: PromptImproverStrategy,
        complex_strategy: PromptImproverStrategy
    ):
        """
        Initialize strategy selector.

        Args:
            simple_strategy: Strategy for SIMPLE complexity
            moderate_strategy: Strategy for MODERATE complexity
            complex_strategy: Strategy for COMPLEX complexity
        """
        self._strategies = {
            ComplexityLevel.SIMPLE: simple_strategy,
            ComplexityLevel.MODERATE: moderate_strategy,
            ComplexityLevel.COMPLEX: complex_strategy,
        }

    def get_strategy(self, complexity: ComplexityLevel) -> PromptImproverStrategy:
        """
        Get strategy for given complexity level.

        Args:
            complexity: The complexity level

        Returns:
            Appropriate PromptImproverStrategy instance

        Raises:
            ValueError: If no strategy registered for complexity level
        """
        strategy = self._strategies.get(complexity)
        if strategy is None:
            raise ValueError(f"No strategy registered for complexity level: {complexity}")
        return strategy


__all__ = [
    'StrategySelector',
    'PromptImproverStrategy',
    'SimpleStrategy',
    'ModerateStrategy',
    'ComplexStrategy',
]
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_strategies/test_selector.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add eval/src/strategies/__init__.py tests/test_strategies/test_selector.py
git commit -m "feat: add StrategySelector for complexity-based routing"
```

---

## Task 9: Update API Endpoint to Use Strategy Pattern

**Files:**
- Modify: `api/prompt_improver_api.py`

**Step 1: Add imports at top of file**

```python
# api/prompt_improver_api.py (after existing imports)
from eval.src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from eval.src.strategies import StrategySelector
from eval.src.strategies.simple_strategy import SimpleStrategy
from eval.src.strategies.moderate_strategy import ModerateStrategy
from eval.src.strategies.complex_strategy import ComplexStrategy
```

**Step 2: Add factory function for StrategySelector**

```python
# api/prompt_improver_api.py (after get_fewshot_improver function)

# Strategy selector factory (lazy loading)
_strategy_selector = None

def get_strategy_selector(settings: Settings) -> StrategySelector:
    """Get or initialize StrategySelector with all strategies."""
    global _strategy_selector

    if _strategy_selector is None:
        # Initialize strategies
        _strategy_selector = StrategySelector(
            simple_strategy=SimpleStrategy(max_length=800),
            moderate_strategy=ModerateStrategy(max_length=2000),
            complex_strategy=ComplexStrategy(
                trainset_path=settings.DSPY_FEWSHOT_TRAINSET_PATH,
                k=settings.DSPY_FEWSHOT_K
            )
        )
        logger.info("StrategySelector initialized with Simple/Moderate/Complex strategies")

    return _strategy_selector
```

**Step 3: Replace the improve_prompt function's routing logic**

```python
# api/prompt_improver_api.py (modify the improve_prompt function)
@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    Uses Strategy Pattern with complexity-based routing.

    POST /api/v1/improve-prompt
    {
        "idea": "Design ADR process",
        "context": "Software architecture team"
    }
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400, detail="Idea must be at least 5 characters"
        )

    # Get settings
    settings = container.get(Settings)

    # NEW: Analyze complexity and select strategy
    analyzer = ComplexityAnalyzer()
    complexity = analyzer.analyze(request.idea, request.context)

    selector = get_strategy_selector(settings)
    strategy = selector.get_strategy(complexity)

    logger.info(
        f"Input complexity: {complexity.value} -> using {strategy.name} strategy "
        f"(input_length={len(request.idea)}, context_length={len(request.context)})"
    )

    # Start timer
    start_time = time.time()

    # Improve prompt using selected strategy
    try:
        result = strategy.improve(original_idea=request.idea, context=request.context)

        # ... rest of the function remains the same (metrics, response building, etc) ...

        # Build response (modify backend field to use strategy name)
        response = ImprovePromptResponse(
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails,
            reasoning=getattr(result, "reasoning", None),
            confidence=getattr(result, "confidence", None),
            backend=strategy.name,  # Now uses strategy name: "simple", "moderate", or "complex"
        )

        # ... rest of function unchanged ...
```

**Step 4: Run API tests**

```bash
# Start backend if not running
make dev

# Test simple input
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "hola mundo", "context": ""}' \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Backend: {d['backend']}\"); print(f\"Length: {len(d['improved_prompt'])}\")"
```
Expected: Backend: simple, Length: < 800

**Step 5: Run full test suite**

```bash
pytest tests/test_strategies/ -v
pytest tests/test_complexity_analyzer.py -v
```
Expected: All PASS

**Step 6: Commit**

```bash
git add api/prompt_improver_api.py
git commit -m "feat: integrate Strategy Pattern into API endpoint"
```

---

## Task 10: Add Integration Tests

**Files:**
- Create: `tests/test_integration/test_strategy_routing.py`

**Step 1: Write integration test**

```python
# tests/test_integration/test_strategy_routing.py
import pytest
from eval.src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from eval.src.strategies import StrategySelector
from eval.src.strategies.simple_strategy import SimpleStrategy
from eval.src.strategies.moderate_strategy import ModerateStrategy
from eval.src.strategies.complex_strategy import ComplexStrategy

def test_end_to_end_simple_routing():
    """Test that simple inputs use SimpleStrategy."""
    analyzer = ComplexityAnalyzer()
    selector = StrategySelector(
        simple_strategy=SimpleStrategy(),
        moderate_strategy=ModerateStrategy(),
        complex_strategy=ComplexStrategy(
            trainset_path="datasets/exports/unified-fewshot-pool.json",
            k=3
        )
    )

    # Simple input
    complexity = analyzer.analyze("hola mundo", "")
    assert complexity == ComplexityLevel.SIMPLE

    strategy = selector.get_strategy(complexity)
    result = strategy.improve("hola mundo", "")

    assert strategy.name == "simple"
    assert len(result.improved_prompt) <= 800

def test_end_to_end_complex_routing():
    """Test that complex inputs use ComplexStrategy."""
    analyzer = ComplexityAnalyzer()
    selector = StrategySelector(
        simple_strategy=SimpleStrategy(),
        moderate_strategy=ModerateStrategy(),
        complex_strategy=ComplexStrategy(
            trainset_path="datasets/exports/unified-fewshot-pool.json",
            k=3
        )
    )

    # Complex input
    complex_input = "diseña un sistema completo de arquitectura hexagonal para una aplicación de gestión de prompts que incluya dominio, infraestructura, adaptadores y repositorios con ejemplos concretos de implementación"
    complexity = analyzer.analyze(complex_input, "")
    assert complexity == ComplexityLevel.COMPLEX

    strategy = selector.get_strategy(complexity)
    assert strategy.name == "complex"
```

**Step 2: Run integration tests**

```bash
pytest tests/test_integration/test_strategy_routing.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration/
git commit -m "test: add integration tests for strategy routing"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `docs/architecture/strategy-pattern.md`

**Step 1: Update CLAUDE.md with new architecture**

```markdown
# DSPy Prompt Improver - Raycast Extension

...

## Architecture

The system uses a **Strategy Pattern** for prompt improvement based on input complexity:

```
Input → ComplexityAnalyzer → StrategySelector → SpecificStrategy
                                        ↓
                            ┌───────────┼───────────┐
                            ↓           ↓           ↓
                        Simple    Moderate     Complex
                        Strategy   Strategy    Strategy
```

### Complexity Levels

- **SIMPLE** (< 50 chars, no technical terms): Zero-shot, 800 char limit
- **MODERATE** (50-150 chars or some technical terms): ChainOfThought, 2000 char limit
- **COMPLEX** (> 150 chars or multiple technical terms): Few-shot with KNN, unlimited

### Key Files

| Path | Purpose |
|------|---------|
| `eval/src/complexity_analyzer.py` | Multi-dimensional complexity classification |
| `eval/src/strategies/` | Strategy Pattern implementations |
| `api/prompt_improver_api.py` | API endpoint with strategy routing |
```

**Step 2: Create detailed architecture doc**

```markdown
# Strategy Pattern Architecture

## Overview

The PromptImprover uses the Strategy Pattern to select the appropriate improvement strategy based on input complexity.

## Components

### ComplexityAnalyzer

Analyzes input across 4 dimensions:
1. **Length** (40%): Character count of input + context
2. **Technical Terms** (30%): Detection of domain-specific keywords
3. **Structure** (20%): Sentence/clause complexity
4. **Context** (10%): Whether additional context was provided

### Strategies

#### SimpleStrategy
- **Backend:** `dspy.Predict` (no ChainOfThought)
- **Max Length:** 800 characters
- **Use Case:** Trivial inputs like "hola mundo"
- **Performance:** Fastest (~1-2s)

#### ModerateStrategy
- **Backend:** `dspy.ChainOfThought`
- **Max Length:** 2000 characters
- **Use Case:** Standard prompts with moderate detail
- **Performance:** Medium (~2-5s)

#### ComplexStrategy
- **Backend:** KNNFewShot with k=3
- **Max Length:** Unlimited
- **Use Case:** Detailed technical specifications
- **Performance:** Slower (~10-30s on first call)

## Adding New Strategies

```python
# 1. Create new strategy class
class CustomStrategy(PromptImproverStrategy):
    def improve(self, original_idea: str, context: str):
        # Your implementation
        pass

    @property
    def name(self) -> str:
        return "custom"

# 2. Register in StrategySelector
selector = StrategySelector(
    simple_strategy=SimpleStrategy(),
    moderate_strategy=ModerateStrategy(),
    complex_strategy=ComplexStrategy(...),
    custom_strategy=CustomStrategy()  # NEW
)
```
```

**Step 3: Commit documentation**

```bash
git add CLAUDE.md docs/architecture/strategy-pattern.md
git commit -m "docs: document Strategy Pattern architecture"
```

---

## Task 12: Final Verification and Cleanup

**Files:**
- Run all tests
- Check type hints
- Verify imports

**Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: All PASS

**Step 2: Type check (if using mypy)**

```bash
mypy eval/src/strategies/ eval/src/complexity_analyzer.py
```
Expected: No errors (or acceptable warnings)

**Step 3: Verify imports**

```bash
python3 -c "
from eval.src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from eval.src.strategies import StrategySelector
from eval.src.strategies.simple_strategy import SimpleStrategy
from eval.src.strategies.moderate_strategy import ModerateStrategy
from eval.src.strategies.complex_strategy import ComplexStrategy
print('✓ All imports successful')
"
```
Expected: ✓ All imports successful

**Step 4: Test API endpoint**

```bash
# Ensure backend is running
make health

# Test all three strategies
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "test", "context": ""}' | python3 -c "import sys,json; print(json.load(sys.stdin)['backend'])"

curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "crea un framework para diseño de software", "context": ""}' | python3 -c "import sys,json; print(json.load(sys.stdin)['backend'])"
```
Expected: "simple" then "moderate" or "complex"

**Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete Strategy Pattern implementation for prompt improvement

- Add ComplexityAnalyzer with multi-dimensional scoring
- Implement 3 strategies: Simple, Moderate, Complex
- Update API to use strategy-based routing
- Add comprehensive tests and documentation

Fixes issue where simple inputs produced 2000+ word outputs.
Now routes to appropriate strategy based on input complexity."
```

---

## Summary

This plan implements a complete Strategy Pattern architecture for prompt improvement:

**What was built:**
1. `ComplexityAnalyzer` - Multi-dimensional input classification
2. `PromptImproverStrategy` interface - Base strategy pattern
3. `SimpleStrategy` - Ultra-concise zero-shot (800 char limit)
4. `ModerateStrategy` - Balanced ChainOfThought (2000 char limit)
5. `ComplexStrategy` - Full few-shot learning
6. `StrategySelector` - Routes to appropriate strategy
7. API integration - Minimal changes to existing endpoint
8. Comprehensive tests - Unit + integration
9. Documentation - Architecture and usage

**Estimated time:** 6-8 hours (2-3 days as predicted)

**Files created:** 12 new files
**Files modified:** 2 existing files
**Lines of code:** ~800 LOC

**Next Steps:**
- Monitor production metrics for strategy distribution
- Tune ComplexityAnalyzer thresholds based on real data
- Consider adding more strategies if needed (e.g., UltraComplex for very long inputs)
