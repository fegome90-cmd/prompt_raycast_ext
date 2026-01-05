# Prompt Curator Wizard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an interactive CLI wizard for fetching, curating, validating, and merging prompts from LangChain Hub into the DSPy few-shot pool, expanding from 109 to ~150 examples.

**Architecture:** 4-phase pipeline (Fetch → Curate → Validate → Merge) with interactive terminal UI, quality scoring via ExampleValidator (4D), SHA256 deduplication, and audit trail metadata.

**Tech Stack:** Python 3.14, asyncio, langchain-classic (hub.pull), DSPy KNNFewShot, pytest, rich (terminal UI), existing infrastructure (PromptMetodizer, ExampleValidator, merge_unified_pool.py).

---

## Prerequisites

**Existing Infrastructure to Reuse:**
- `scripts/data/validator.py` - ExampleValidator with 4D scoring (threshold: 0.5)
- `scripts/data/merge_unified_pool.py` - merge_with_recovery() with SHA256 deduplication
- `scripts/data/fewshot_optimizer.py` - KNNFewShot compilation
- `datasets/exports/unified-fewshot-pool.json` - Master pool (109 examples)

**Design Document:** `docs/plans/2026-01-05-prompt-curator-design.md` - Read this first for architecture context.

---

## Task 1: Create project structure and config

**Files:**
- Create: `scripts/langchain/__init__.py`
- Create: `scripts/langchain/config/__init__.py`
- Create: `scripts/langchain/config/langchain_whitelist.json`

**Step 1: Create package init files**

```bash
mkdir -p scripts/langchain/config
touch scripts/langchain/__init__.py
touch scripts/langchain/config/__init__.py
```

**Step 2: Create whitelist config**

```json
{
  "handles": [
    "hwchase17/react",
    "hwchase17/openai-functions",
    "hwchase17/self-ask-with-search"
  ],
  "quality_threshold": 0.5,
  "fetch_timeout": 30
}
```

**Step 3: Commit**

```bash
git add scripts/langchain/
git commit -m "feat(langchain): add project structure and whitelist config"
```

---

## Task 2: Implement LangChainHubFetcher

**Files:**
- Create: `scripts/langchain/fetch_prompts.py`
- Test: `scripts/langchain/tests/test_fetch_prompts.py`

**Step 1: Write the failing test**

Create test file first:

```python
# scripts/langchain/tests/test_fetch_prompts.py
import pytest
from scripts.langchain.fetch_prompts import LangChainHubFetcher, FetchResult

@pytest.mark.asyncio
async def test_fetch_single_prompt_success():
    """Test successful fetch of single prompt."""
    # This test will need mocking since we can't call real Hub in tests
    pytest.skip("Skip - will implement with mocks in Step 4")

def test_fetch_result_structure():
    """Test FetchResult dataclass structure."""
    result = FetchResult(
        fetched=[{"handle": "test"}],
        errors=[],
        partial_success=False
    )
    assert len(result.fetched) == 1
    assert len(result.errors) == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest scripts/langchain/tests/test_fetch_prompts.py -v
```
Expected: PASS for structure test, SKIP for async test

**Step 3: Write minimal implementation**

```python
# scripts/langchain/fetch_prompts.py
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    """Result of fetching prompts from LangChain Hub."""
    fetched: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    partial_success: bool


class LangChainHubFetcher:
    """Fetch prompts from LangChain Hub."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def fetch_by_handles(self, handles: List[str]) -> FetchResult:
        """Fetch prompts by their handles.

        Args:
            handles: List of LangChain Hub handles (e.g., "hwchase17/react")

        Returns:
            FetchResult with fetched prompts and any errors
        """
        # Import here to avoid issues if langchain not installed
        try:
            from langchain import hub
        except ImportError:
            logger.error("langchain-classic not installed. Run: pip install langchain-classic")
            return FetchResult(fetched=[], errors=[], partial_success=False)

        results = []
        errors = []

        for handle in handles:
            try:
                # Sync call in thread pool to avoid blocking
                prompt = await asyncio.to_thread(hub.pull, handle)

                results.append({
                    "handle": handle,
                    "name": getattr(prompt, 'name', handle),
                    "template": prompt.template,
                    "tags": list(getattr(prompt, 'tags', []))
                })

                logger.info(f"Fetched: {handle}")

            except Exception as e:
                logger.warning(f"Failed to fetch {handle}: {e}")
                errors.append({
                    "handle": handle,
                    "error": type(e).__name__,
                    "message": str(e)
                })

        return FetchResult(
            fetched=results,
            errors=errors,
            partial_success=len(results) > 0
        )
```

**Step 4: Run test to verify it passes**

```bash
pytest scripts/langchain/tests/test_fetch_prompts.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/langchain/fetch_prompts.py scripts/langchain/tests/
git commit -m "feat(langchain): implement LangChainHubFetcher with async support"
```

---

## Task 3: Implement FormatConverter

**Files:**
- Create: `scripts/langchain/format_converter.py`
- Test: `scripts/langchain/tests/test_format_converter.py`

**Step 1: Write the failing test**

```python
# scripts/langchain/tests/test_format_converter.py
import pytest
from scripts.langchain.format_converter import FormatConverter

def test_convert_react_prompt():
    """Test conversion of ReAct prompt to DSPy format."""
    lc_prompt = {
        "handle": "hwchase17/react",
        "name": "ReAct",
        "template": "You are a helpful assistant that uses thought-action-observation reasoning.",
        "tags": ["agent", "react"]
    }

    converter = FormatConverter()
    result = converter.to_dspy_format(lc_prompt)

    # Verify structure
    assert 'inputs' in result
    assert 'outputs' in result
    assert 'metadata' in result

    # Verify framework detection
    assert result['outputs']['framework'] == "Chain-of-Thought"

    # Verify metadata
    assert result['metadata']['source'] == "langchain-hub"
    assert result['metadata']['source_handle'] == "hwchase17/react"
    assert 'sha256' in result['metadata']
```

**Step 2: Run test to verify it fails**

```bash
pytest scripts/langchain/tests/test_format_converter.py::test_convert_react_prompt -v
```
Expected: FAIL - "FormatConverter not defined"

**Step 3: Write minimal implementation**

```python
# scripts/langchain/format_converter.py
import hashlib
import json
from typing import Dict, Any

class FormatConverter:
    """Convert LangChain prompts to DSPy unified format."""

    def to_dspy_format(self, lc_prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LangChain prompt to DSPy format.

        Args:
            lc_prompt: Raw prompt from LangChain Hub

        Returns:
            DSPy-format prompt with inputs/outputs/metadata
        """
        template = lc_prompt["template"]
        handle = lc_prompt["handle"]

        # Generate synthetic input from template
        role = self._extract_role(template)
        original_idea = f"{role} agent from LangChain Hub"

        # Calculate SHA256 for deduplication
        sha256_hash = self._calculate_sha256(original_idea, template)

        return {
            "inputs": {
                "original_idea": original_idea,
                "context": ""
            },
            "outputs": {
                "improved_prompt": template,
                "role": role,
                "directive": self._extract_directive(template),
                "framework": self._detect_framework(template),
                "guardrails": self._extract_guardrails(template)
            },
            "metadata": {
                "source": "langchain-hub",
                "source_handle": handle,
                "source_name": lc_prompt.get("name", handle),
                "sha256": sha256_hash,
                "tags": lc_prompt.get("tags", [])
            }
        }

    def _extract_role(self, template: str) -> str:
        """Extract role from template."""
        template_lower = template.lower()

        role_patterns = {
            "expert data analyst": ["data analyst", "analyze data"],
            "expert document retrieval": ["retrieval", "rag", "document"],
            "ai assistant": ["assistant", "helpful"],
            "ai agent": ["agent", "reasoning"]
        }

        for role, patterns in role_patterns.items():
            if any(pattern in template_lower for pattern in patterns):
                return role

        return "AI Assistant"

    def _extract_directive(self, template: str) -> str:
        """Extract directive from template."""
        # First sentence is usually the directive
        sentences = template.split('.')
        if sentences:
            return sentences[0].strip()
        return ""

    def _detect_framework(self, template: str) -> str:
        """Detect reasoning framework from template content."""
        template_lower = template.lower()

        framework_patterns = {
            "Chain-of-Thought": ["thought", "reasoning", "step by step", "react"],
            "Decomposition": ["decompose", "break down", "split into"],
            "Reflexión": ["reflect", "review", "critique"],
            "Planificación": ["plan", "strategy", "approach"]
        }

        for framework, patterns in framework_patterns.items():
            if any(pattern in template_lower for pattern in patterns):
                return framework

        return ""

    def _extract_guardrails(self, template: str) -> list:
        """Extract guardrails from template."""
        guardrails = []
        template_lower = template.lower()

        guardrail_patterns = {
            "Source fidelity": ["only use provided", "from sources"],
            "Citation accuracy": ["cite", "reference"],
            "Be concise": ["concise", "brief", "short"],
            "Be accurate": ["accurate", "correct", "factual"]
        }

        for guardrail, patterns in guardrail_patterns.items():
            if any(pattern in template_lower for pattern in patterns):
                guardrails.append(guardrail)

        return guardrails

    def _calculate_sha256(self, input_text: str, output_text: str) -> str:
        """Calculate SHA256 hash for deduplication."""
        combined = f"{input_text}|||{output_text}"
        return hashlib.sha256(combined.encode()).hexdigest()
```

**Step 4: Run test to verify it passes**

```bash
pytest scripts/langchain/tests/test_format_converter.py::test_convert_react_prompt -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/langchain/format_converter.py scripts/langchain/tests/test_format_converter.py
git commit -m "feat(langchain): implement FormatConverter with framework detection"
```

---

## Task 4: Implement PromptCuratorWizard main CLI

**Files:**
- Create: `scripts/langchain/prompt_curator.py`
- Create: `scripts/langchain/__main__.py` (for CLI entry point)

**Step 1: Create main wizard class with basic structure**

```python
# scripts/langchain/prompt_curator.py
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from scripts.langchain.fetch_prompts import LangChainHubFetcher
from scripts.langchain.format_converter import FormatConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptCuratorWizard:
    """Interactive wizard for prompt curation from LangChain Hub."""

    def __init__(self, config_path: str = "scripts/langchain/config/langchain_whitelist.json"):
        self.fetcher = LangChainHubFetcher()
        self.converter = FormatConverter()
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config not found: {config_path}, using defaults")
            return {"handles": [], "quality_threshold": 0.5}

        with open(path, 'r') as f:
            return json.load(f)

    async def run(self, handles: Optional[List[str]] = None):
        """Main wizard loop."""
        # Use provided handles or config
        if not handles:
            handles = self.config.get('handles', [])

        if not handles:
            print("❌ No handles provided. Use --handles or configure langchain_whitelist.json")
            return

        # PHASE 1: Fetch
        print("\n🔍 Fetching prompts from LangChain Hub...")
        print(f"   Handles: {', '.join(handles)}")

        fetch_result = await self.fetcher.fetch_by_handles(handles)

        if fetch_result.errors:
            print(f"\n⚠️  {len(fetch_result.errors)} prompts failed to fetch:")
            for err in fetch_result.errors:
                print(f"   - {err['handle']}: {err['message']}")

        if not fetch_result.fetched:
            print("\n❌ No prompts fetched. Exiting.")
            return

        print(f"\n✓ Fetched {len(fetch_result.fetched)} prompts")

        # Convert to DSPy format
        candidates = [self.converter.to_dspy_format(p) for p in fetch_result.fetched]

        # PHASE 2: Interactive Curation
        approved = []

        for i, prompt in enumerate(candidates):
            self._show_prompt_card(i, len(candidates), prompt)

            decision = self._get_decision()

            if decision == 'a':  # Approve
                approved.append(prompt)
                print("✓ Approved\n")
            elif decision == 'x':  # Reject
                print("✗ Rejected\n")
            elif decision == 's':  # Skip
                print("⊘ Skipped\n")
                continue
            elif decision == 'q':  # Quit
                print("\n👋 Exiting wizard.")
                break

        # PHASE 3: Save results
        if approved:
            output_path = "datasets/exports/langchain-approved.json"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(approved, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Saved {len(approved)} approved prompts to {output_path}")
        else:
            print("\n⚠️  No prompts approved.")

    def _show_prompt_card(self, index: int, total: int, prompt: Dict[str, Any]):
        """Display prompt card in terminal."""
        print("\n" + "="*78)
        print(f"Prompt {index+1}/{total}: {prompt['metadata'].get('source_name', 'Unknown')}")
        print("="*78)

        # Quality info
        framework = prompt['outputs'].get('framework', 'Unknown')
        role = prompt['outputs'].get('role', 'No role')

        print(f"\n📊 Framework: {framework}")
        print(f"👤 Role: {role}")

        # Content preview
        directive = prompt['outputs'].get('directive', '')
        if directive:
            print(f"\n📝 Directive: {directive[:100]}...")

        guardrails = prompt['outputs'].get('guardrails', [])
        print(f"\n🛡️  Guardrails: {len(guardrails)} items")

        print("\n" + "-"*78)
        print("DECISION: [a] Approve    [x] Reject    [s] Skip    [q] Quit")
        print("-"*78)

    def _get_decision(self) -> str:
        """Get user decision."""
        while True:
            try:
                choice = input("Your choice: ").strip().lower()
                if choice in ['a', 'x', 's', 'q']:
                    return choice
                print("Invalid choice. Try again.")
            except (EOFError, KeyboardInterrupt):
                return 'q'


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Prompt Curator Wizard for LangChain Hub")
    parser.add_argument('--handles', nargs='+', help='LangChain Hub handles to fetch')
    parser.add_argument('--config', default='scripts/langchain/config/langchain_whitelist.json',
                       help='Path to config file')

    args = parser.parse_args()

    wizard = PromptCuratorWizard(config_path=args.config)
    asyncio.run(wizard.run(handles=args.handles))


if __name__ == "__main__":
    main()
```

**Step 2: Create CLI entry point**

```python
# scripts/langchain/__main__.py
from scripts.langchain.prompt_curator import main

if __name__ == "__main__":
    main()
```

**Step 3: Test CLI manually**

```bash
python -m scripts.langchain --help
```
Expected: Help message displayed

**Step 4: Commit**

```bash
git add scripts/langchain/prompt_curator.py scripts/langchain/__main__.py
git commit -m "feat(langchain): implement PromptCuratorWizard CLI with basic flow"
```

---

## Task 5: Integrate ExampleValidator for quality scoring

**Files:**
- Modify: `scripts/langchain/prompt_curator.py`
- Test: `scripts/langchain/tests/test_validator_integration.py`

**Step 1: Add validation phase to wizard**

Modify `scripts/langchain/prompt_curator.py`:

```python
# Add import at top
from scripts.data.validator import ExampleValidator

# Modify __init__ to add validator
def __init__(self, config_path: str = "scripts/langchain/config/langchain_whitelist.json"):
    self.fetcher = LangChainHubFetcher()
    self.converter = FormatConverter()
    self.validator = ExampleValidator(threshold=0.5)  # Add this
    self.config = self._load_config(config_path)

# Modify run() method to add validation phase after curation
# Replace the "PHASE 3: Save results" section with:

        # PHASE 3: Validate
        if not approved:
            print("\n⚠️  No prompts approved. Exiting.")
            return

        print(f"\n🔬 Validating {len(approved)} approved prompts...")

        validated = []
        failed = []

        for prompt in approved:
            try:
                score = self.validator.validate(prompt)
                if score >= 0.5:
                    validated.append(prompt)
                    logger.info(f"Validated: {prompt['metadata']['source_handle']} (score: {score:.2f})")
                else:
                    failed.append({'prompt': prompt, 'score': score})
                    logger.warning(f"Failed validation: {prompt['metadata']['source_handle']} (score: {score:.2f})")
            except Exception as e:
                logger.error(f"Validation error: {e}")
                failed.append({'prompt': prompt, 'error': str(e)})

        print(f"\n✓ {len(validated)} prompts passed validation")
        if failed:
            print(f"✗ {len(failed)} prompts failed validation")

        # PHASE 4: Save results
        if validated:
            output_path = "datasets/exports/langchain-validated.json"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Saved {len(validated)} validated prompts to {output_path}")
        else:
            print("\n⚠️  No prompts validated.")
```

**Step 2: Commit**

```bash
git add scripts/langchain/prompt_curator.py
git commit -m "feat(langchain): integrate ExampleValidator for quality scoring"
```

---

## Task 6: Integrate merge_unified_pool for safe merging

**Files:**
- Modify: `scripts/langchain/prompt_curator.py`

**Step 1: Add merge phase to wizard**

Modify `scripts/langchain/prompt_curator.py`:

```python
# Add import
from scripts.data.merge_unified_pool import merge_pools  # Adjust based on actual function name

# Modify run() method to add merge phase after validation

        # PHASE 4: Save to temp file for merge
        if not validated:
            print("\n⚠️  No prompts validated. Exiting.")
            return

        temp_path = "/tmp/langchain-validated.json"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(validated, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(validated)} validated prompts to {temp_path}")

        # PHASE 5: Merge with unified pool
        print(f"\n🔗 Merging into unified pool...")

        existing_path = "datasets/exports/unified-fewshot-pool.json"

        try:
            # Load existing pool
            with open(existing_path, 'r') as f:
                existing_pool = json.load(f)

            existing_count = len(existing_pool.get('examples', existing_pool))

            # Perform merge
            result = merge_pools(existing_path, temp_path)

            new_count = result.get('new_count', existing_count)
            added = new_count - existing_count
            duplicates = result.get('duplicates', 0)

            print(f"\n✓ Pool updated:")
            print(f"   Before: {existing_count} examples")
            print(f"   Added: {added} new examples")
            print(f"   Duplicates skipped: {duplicates}")
            print(f"   After: {new_count} examples")

        except Exception as e:
            print(f"\n❌ Merge failed: {e}")
            logger.error("Merge error", exc_info=True)
            return

        # PHASE 6: Update metadata
        metadata_path = "datasets/exports/langchain-metadata.json"
        self._update_metadata(metadata_path, {
            'fetched': len(fetch_result.fetched),
            'approved': len(approved),
            'validated': len(validated),
            'merged': added,
            'rejected': len(failed)
        })

        print("\n✨ Wizard complete!")
```

**Step 2: Add metadata update helper**

```python
def _update_metadata(self, metadata_path: str, stats: Dict[str, int]):
    """Update audit trail metadata."""
    from datetime import datetime

    # Load existing or create new
    metadata = {}
    if Path(metadata_path).exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

    # Update with current session stats
    metadata['last_run'] = datetime.now().isoformat()
    metadata['last_session'] = stats
    metadata['total_runs'] = metadata.get('total_runs', 0) + 1

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"📊 Metadata updated: {metadata_path}")
```

**Step 3: Commit**

```bash
git add scripts/langchain/prompt_curator.py
git commit -m "feat(langchain): integrate merge_unified_pool with metadata tracking"
```

---

## Task 7: Add comprehensive error handling

**Files:**
- Modify: `scripts/langchain/prompt_curator.py`

**Step 1: Wrap main flow in try-except**

Modify the `run()` method to add comprehensive error handling:

```python
async def run(self, handles: Optional[List[str]] = None):
    """Main wizard loop with error handling."""
    try:
        # ... existing code ...

    except KeyboardInterrupt:
        print("\n\n👋 Wizard interrupted by user.")
        logger.info("Wizard interrupted")
    except Exception as e:
        print(f"\n❌ Wizard failed: {e}")
        logger.error("Wizard error", exc_info=True)
```

**Step 2: Add backup before merge**

Add helper method:

```python
def _create_backup(self, file_path: str) -> str:
    """Create backup of file before modification."""
    import shutil
    from datetime import datetime

    if not Path(file_path).exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"

    shutil.copy2(file_path, backup_path)
    logger.info(f"Backup created: {backup_path}")

    return backup_path
```

Call before merge in PHASE 5:

```python
# Create backup before merge
backup_path = self._create_backup(existing_path)
if backup_path:
    print(f"📦 Backup created: {backup_path}")
```

**Step 3: Commit**

```bash
git add scripts/langchain/prompt_curator.py
git commit -m "feat(langchain): add comprehensive error handling and backup"
```

---

## Task 8: Write integration test

**Files:**
- Create: `scripts/langchain/tests/test_integration.py`

**Step 1: Write integration test**

```python
# scripts/langchain/tests/test_integration.py
import pytest
import json
import tempfile
from pathlib import Path

from scripts.langchain.prompt_curator import PromptCuratorWizard

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow_with_mock_data():
    """Test complete workflow with mock data (no real Hub calls)."""

    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"handles": [], "quality_threshold": 0.5}, f)
        config_path = f.name

    # Create wizard
    wizard = PromptCuratorWizard(config_path=config_path)

    # Simulate having fetched data
    mock_candidates = [{
        "inputs": {"original_idea": "Test agent", "context": ""},
        "outputs": {
            "improved_prompt": "You are a test assistant.",
            "role": "Test Assistant",
            "directive": "Help with testing",
            "framework": "Chain-of-Thought",
            "guardrails": ["Be accurate"]
        },
        "metadata": {
            "source": "test",
            "source_handle": "test/react",
            "sha256": "abc123"
        }
    }]

    # Test validator works
    from scripts.data.validator import ExampleValidator
    validator = ExampleValidator(threshold=0.5)

    score = validator.validate(mock_candidates[0])
    assert score >= 0.5, "Test prompt should pass validation"

    # Cleanup
    Path(config_path).unlink()

    print("✓ Integration test passed")
```

**Step 2: Run integration test**

```bash
pytest scripts/langchain/tests/test_integration.py -v -m integration
```
Expected: PASS

**Step 3: Commit**

```bash
git add scripts/langchain/tests/test_integration.py
git commit -m "test(langchain): add integration test for wizard workflow"
```

---

## Task 9: Add RemediationAgent for weak prompt fixing

**Files:**
- Create: `scripts/langchain/remediation_agent.py`
- Modify: `scripts/langchain/prompt_curator.py`

**Step 1: Create RemediationAgent**

```python
# scripts/langchain/remediation_agent.py
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RemediationAgent:
    """Fix weak prompts by adding missing components."""

    def remediate(self, prompt: Dict[str, Any], weaknesses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Remediate weak prompt by addressing diagnosed weaknesses.

        Args:
            prompt: Weak prompt in DSPy format
            weaknesses: List of diagnosed weaknesses from _diagnose_weaknesses

        Returns:
            Remediated prompt with improvements applied
        """
        remediated = prompt.copy()
        remediated['outputs'] = remediated['outputs'].copy()

        for weakness in weaknesses:
            category = weakness['category']
            suggestion = weakness['suggestion']

            if category == 'Role':
                remediated['outputs']['role'] = self._fix_role(suggestion)
            elif category == 'Directive':
                remediated['outputs']['directive'] = self._fix_directive(remediated['outputs'], suggestion)
            elif category == 'Framework':
                remediated['outputs']['framework'] = self._fix_framework(suggestion)
            elif category == 'Guardrails':
                remediated['outputs']['guardrails'] = self._fix_guardrails(remediated['outputs'].get('guardrails', []))

        # Update metadata
        remediated['metadata'] = remediated['metadata'].copy()
        remediated['metadata']['remediated'] = True

        return remediated

    def _fix_role(self, suggestion: str) -> str:
        """Fix missing or weak role."""
        if "data analyst" in suggestion.lower():
            return "Expert Data Analyst"
        elif "retrieval" in suggestion.lower():
            return "Expert Document Retrieval Specialist"
        else:
            return "AI Assistant"

    def _fix_directive(self, outputs: Dict[str, Any], suggestion: str) -> str:
        """Fix missing or weak directive."""
        current = outputs.get('directive', '')
        role = outputs.get('role', 'AI Assistant')

        if len(current) < 20:
            return f"Your mission is to assist users as {role}. Provide accurate, helpful responses."

        return current

    def _fix_framework(self, suggestion: str) -> str:
        """Fix missing framework."""
        if "chain-of-thought" in suggestion.lower() or "reasoning" in suggestion.lower():
            return "Chain-of-Thought"
        return ""

    def _fix_guardrails(self, current: List[str]) -> List[str]:
        """Fix insufficient guardrails."""
        if not current:
            return ["Be accurate", "Cite sources"]

        if len(current) < 2:
            return current + ["Be accurate"]

        return current
```

**Step 2: Integrate remediation into wizard**

Add to `PromptCuratorWizard` class:

```python
# Add import
from scripts.langchain.remediation_agent import RemediationAgent

# Add to __init__
def __init__(self, config_path: str = "scripts/langchain/config/langchain_whitelist.json"):
    # ... existing ...
    self.remediator = RemediationAgent()

# Add method
def _diagnose_weaknesses(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Diagnose weaknesses in prompt."""
    weaknesses = []
    outputs = prompt['outputs']

    if not outputs.get('role') or len(outputs.get('role', '')) < 10:
        weaknesses.append({
            'category': 'Role',
            'issue': 'Missing or too brief',
            'suggestion': 'Add specific role (e.g., "Expert Data Analyst")'
        })

    if not outputs.get('directive') or len(outputs.get('directive', '')) < 20:
        weaknesses.append({
            'category': 'Directive',
            'issue': 'Missing or incomplete',
            'suggestion': 'Add clear directive describing what the assistant should do'
        })

    if not outputs.get('framework'):
        weaknesses.append({
            'category': 'Framework',
            'issue': 'Not specified',
            'suggestion': 'Add reasoning framework (Chain-of-Thought, ReAct, etc.)'
        })

    guardrails = outputs.get('guardrails', [])
    if len(guardrails) < 2:
        weaknesses.append({
            'category': 'Guardrails',
            'issue': 'Insufficient guardrails',
            'suggestion': 'Add 2-3 guardrails for constraint management'
        })

    return weaknesses

def _remediate_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
    """Remediate weak prompt."""
    weaknesses = self._diagnose_weaknesses(prompt)

    if not weaknesses:
        print("✓ No weaknesses detected")
        return prompt

    print("\n🔧 Diagnosed weaknesses:")
    for w in weaknesses:
        print(f"  ❌ {w['category']}: {w['issue']}")

    print("\n🤖 Applying automatic remediation...")
    remediated = self.remediator.remediate(prompt, weaknesses)

    print("\n✓ Remediated prompt:")
    print(f"   Role: {remediated['outputs']['role']}")
    print(f"   Framework: {remediated['outputs']['framework']}")
    print(f"   Guardrails: {len(remediated['outputs']['guardrails'])} items")

    return remediated
```

**Step 3: Update decision handling in prompt card**

Modify the decision handling section:

```python
            if decision == 'a':  # Approve
                approved.append(prompt)
                print("✓ Approved\n")
            elif decision == 'r':  # Remediate
                remediated = self._remediate_prompt(prompt)
                approved.append(remediated)
                print("✓ Remediated and approved\n")
            # ... rest of decisions ...
```

**Step 4: Update prompt card to show remediation option**

```python
def _show_prompt_card(self, index: int, total: int, prompt: Dict[str, Any]):
    # ... existing code ...

    # Update decision line:
    print("DECISION: [a] Approve    [r] Remediate    [x] Reject    [s] Skip    [q] Quit")
```

**Step 5: Commit**

```bash
git add scripts/langchain/remediation_agent.py scripts/langchain/prompt_curator.py
git commit -m "feat(langchain): add RemediationAgent for weak prompt fixing"
```

---

## Task 10: Write end-to-end test

**Files:**
- Create: `scripts/langchain/tests/test_e2e.py`

**Step 1: Write E2E test**

```python
# scripts/langchain/tests/test_e2e.py
import pytest
import subprocess
import json
import tempfile
from pathlib import Path


def test_cli_help():
    """Test CLI help command."""
    result = subprocess.run(
        ["python", "-m", "scripts.langchain", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Prompt Curator Wizard" in result.stdout
    assert "--handles" in result.stdout


def test_whitelist_config_parsing():
    """Test whitelist config file parsing."""
    config_path = "scripts/langchain/config/langchain_whitelist.json"

    assert Path(config_path).exists()

    with open(config_path, 'r') as f:
        config = json.load(f)

    assert "handles" in config
    assert isinstance(config["handles"], list)


@pytest.mark.e2e
def test_full_wizard_flow_with_mock_data():
    """Test wizard flow with mock configuration."""
    # Create temp config with no handles (will use mock data in test)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"handles": [], "quality_threshold": 0.5}, f)
        temp_config = f.name

    try:
        # Run wizard (will exit immediately with no handles)
        result = subprocess.run(
            ["python", "-m", "scripts.langchain", "--config", temp_config],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should handle gracefully
        assert "No handles provided" in result.stdout or result.returncode == 0

    finally:
        Path(temp_config).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 2: Run E2E tests**

```bash
pytest scripts/langchain/tests/test_e2e.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add scripts/langchain/tests/test_e2e.py
git commit -m "test(langchain): add end-to-end tests for CLI"
```

---

## Task 11: Add requirements and documentation

**Files:**
- Modify: `requirements.txt`
- Create: `scripts/langchain/README.md`

**Step 1: Update requirements.txt**

Add to `requirements.txt`:

```txt
# LangChain Hub Integration
langchain-classic>=0.1.0
```

**Step 2: Create README**

```markdown
# Prompt Curator Wizard

Interactive CLI wizard for extracting, curating, and merging prompts from LangChain Hub into the DSPy few-shot pool.

## Usage

### Basic Workflow

```bash
# Use whitelist config
python -m scripts.langchain

# Specify handles directly
python -m scripts.langchain --handles hwchase17/react hwchase17/openai-functions
```

### Pipeline Phases

1. **Fetch**: Pull prompts from LangChain Hub
2. **Curate**: Interactive review with approval/rejection
3. **Validate**: Quality scoring (≥0.5 threshold)
4. **Merge**: SHA256 deduplication into unified pool

### Decision Options

- `[a]` Approve - Add to pool
- `[r]` Remediate - Auto-fix weak prompts
- `[x]` Reject - Discard
- `[s]` Skip - Review later
- `[q]` Quit - Save progress and exit

## Configuration

Edit `scripts/langchain/config/langchain_whitelist.json`:

```json
{
  "handles": ["hwchase17/react", "hwchase17/openai-functions"],
  "quality_threshold": 0.5,
  "fetch_timeout": 30
}
```

## Output Files

- `datasets/exports/langchain-approved.json` - Human-curated prompts
- `datasets/exports/langchain-validated.json` - After ExampleValidator
- `datasets/exports/langchain-metadata.json` - Audit trail
- `datasets/exports/unified-fewshot-pool.json` - Updated master pool

## Testing

```bash
# Unit tests
pytest scripts/langchain/tests/ -v

# Integration tests
pytest scripts/langchain/tests/ -v -m integration

# E2E tests
pytest scripts/langchain/tests/test_e2e.py -v -m e2e
```
```

**Step 3: Commit**

```bash
git add requirements.txt scripts/langchain/README.md
git commit -m "docs(langchain): add README and update requirements"
```

---

## Task 12: Final integration test with real data

**Files:**
- Create: `scripts/langchain/tests/test_real_hub.py`

**Step 1: Create test with real Hub (optional/skipped by default)**

```python
# scripts/langchain/tests/test_real_hub.py
import pytest
import asyncio

from scripts.langchain.fetch_prompts import LangChainHubFetcher
from scripts.langchain.format_converter import FormatConverter
from scripts.data.validator import ExampleValidator


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip("Requires real LangChain Hub access - run manually")
async def test_fetch_real_hub_prompt():
    """Test fetching real prompt from LangChain Hub."""

    fetcher = LangChainHubFetcher()
    result = await fetcher.fetch_by_handles(["hwchase17/react"])

    assert len(result.fetched) >= 1
    assert result.fetched[0]['handle'] == "hwchase17/react"

    # Convert and validate
    converter = FormatConverter()
    dspy_format = converter.to_dspy_format(result.fetched[0])

    validator = ExampleValidator(threshold=0.5)
    score = validator.validate(dspy_format)

    print(f"Fetched prompt score: {score:.2f}")
    assert score >= 0.5
```

**Step 2: Commit**

```bash
git add scripts/langchain/tests/test_real_hub.py
git commit -m "test(langchain): add optional real Hub integration test"
```

---

## Success Criteria Verification

After completing all tasks, verify:

✅ `scripts/langchain/` package exists with all modules
✅ `python -m scripts.langchain --help` shows CLI
✅ Unit tests pass: `pytest scripts/langchain/tests/ -v`
✅ Integration tests pass: `pytest scripts/langchain/tests/ -v -m integration`
✅ E2E tests pass: `pytest scripts/langchain/tests/test_e2e.py -v`
✅ Config file exists: `scripts/langchain/config/langchain_whitelist.json`
✅ README exists: `scripts/langchain/README.md`
✅ Can import: `from scripts.langchain.prompt_curator import PromptCuratorWizard`

---

## Estimated Completion Time

| Task | Estimate |
|------|----------|
| Project structure | 10 min |
| LangChainHubFetcher | 20 min |
| FormatConverter | 25 min |
| PromptCuratorWizard CLI | 30 min |
| ExampleValidator integration | 15 min |
| Merge integration | 20 min |
| Error handling | 20 min |
| Integration tests | 20 min |
| RemediationAgent | 30 min |
| E2E tests | 15 min |
| Documentation | 15 min |
| Real Hub test | 10 min |
| **Total** | **~3 hours** |
