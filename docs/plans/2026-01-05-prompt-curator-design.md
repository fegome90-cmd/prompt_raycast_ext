# Prompt Curator Wizard - Design Document

> **For Claude:** REQUIRED NEXT SKILL: Use superpowers:writing-plans to create implementation plan from this design.

**Goal:** Design an interactive CLI wizard for systematic extraction, validation, and curation of prompts from LangChain Hub, expanding the few-shot pool from 109 to ~150 examples.

**Architecture:** 4-phase pipeline (Fetch → Curate → Validate → Merge) with interactive terminal UI, quality scoring, remediation wizard, and audit trail.

**Tech Stack:** Python 3.14, asyncio, langchain-classic, DSPy KNNFewShot, pytest

---

## Overview

The Prompt Curator Wizard solves the problem of continuously expanding our DSPy few-shot learning pool with high-quality prompts from LangChain Hub. It provides:

1. **Automated Fetching**: Pull prompts from LangChain Hub by handle whitelist
2. **Format Conversion**: Convert LangChain templates to DSPy unified format
3. **Interactive Curation**: Terminal-based wizard for human review
4. **Quality Validation**: Automated 4D quality scoring (≥0.5 threshold)
5. **Safe Merging**: SHA256 deduplication with backup/recovery
6. **Audit Trail**: Complete metadata tracking of all operations

**Key Design Decisions:**
- **Manual curation required**: No automatic imports - human reviewer decides
- **Quality threshold dual validation**: PromptMetodizer (0.6) + ExampleValidator (0.5)
- **Remediation workflow**: Weak prompts can be fixed interactively
- **Backup before merge**: Never lose existing pool data

---

## Sección 1: Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE 4 FASES                                     │
└─────────────────────────────────────────────────────────────────────────────┘

FETCH (Auto)              CURATE (Wizard)           VALIDATE (Auto)          MERGE (Auto)
┌──────────────┐          ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
│ LangChain    │   ───▶   │ Terminal UI  │   ───▶   │ Example      │   ───▶  │ Unified Pool │
│ Hub API      │          │ Cards +      │          │ Validator    │         │ + SHA256     │
│              │          │ Decisions    │          │ (4D Score)   │         │ Dedup        │
└──────────────┘          └──────────────┘          └──────────────┘         └──────────────┘
      │                         │                         │                        │
      ▼                         ▼                         ▼                        ▼
  Raw LC                 Approved List            Validated List          Updated Pool
  Prompts               (human curated)          (scored ≥0.5)          (109 → ~150)
   (N)                       (M)                        (L)                 (109+L)
                                                             │
                                                             ▼
                                                    ┌──────────────────┐
                                                    │ API Recompile    │
                                                    │ KNNFewShot(k=3)  │
                                                    └──────────────────┘

User Controls:
- [a] Approve    → Moves to validation
- [r] Remediate  → Opens remediation wizard
- [x] Reject     → Discarded (logged)
- [s] Skip       → Review later
- [q] Quit       → Save progress, exit
```

---

## Sección 2: Componentes del Sistema

### 2.1 PromptCuratorWizard (Main CLI)

```python
class PromptCuratorWizard:
    """Interactive wizard for prompt curation from LangChain Hub."""

    def __init__(self, config_path: str = "scripts/langchain/config/langchain_whitelist.json"):
        self.fetcher = LangChainHubFetcher()
        self.converter = FormatConverter()
        self.validator = ExampleValidator(threshold=0.5)
        self.merger = merge_unified_pool()
        self.config = self._load_config(config_path)

    async def run(self, handles: List[str] = None):
        """Main wizard loop."""
        # PHASE 1: Fetch
        if not handles:
            handles = self.config['handles']

        print("🔍 Fetching prompts from LangChain Hub...")
        fetch_result = await self.fetcher.fetch_by_handles(handles)

        if fetch_result['errors']:
            print(f"⚠️  {len(fetch_result['errors'])} prompts failed to fetch")
            for err in fetch_result['errors']:
                print(f"   - {err['handle']}: {err['message']}")

        candidates = fetch_result['fetched']
        print(f"✓ Fetched {len(candidates)} prompts")

        # PHASE 2: Interactive Curation
        approved = []
        rejected = []

        for i, prompt in enumerate(candidates):
            self._show_prompt_card(i, len(candidates), prompt)

            decision = await self._get_decision()

            if decision == 'a':  # Approve
                approved.append(prompt)
                print("✓ Approved")
            elif decision == 'r':  # Remediate
                fixed = await self._remediate_wizard(prompt)
                approved.append(fixed)
                print("✓ Remediated and approved")
            elif decision == 'x':  # Reject
                rejected.append(prompt)
                print("✗ Rejected")
            elif decision == 's':  # Skip
                continue
            elif decision == 'q':  # Quit
                break

        # PHASE 3: Validate
        if not approved:
            print("No prompts approved. Exiting.")
            return

        print(f"\n🔬 Validating {len(approved)} approved prompts...")
        validation_result = self.validator.validate_batch(approved)

        print(f"✓ {len(validation_result['validated'])} passed validation")
        if validation_result['failed']:
            print(f"✗ {len(validation_result['failed'])} failed validation")

        # PHASE 4: Merge
        validated = validation_result['validated']
        if not validated:
            print("No prompts validated. Exiting.")
            return

        print(f"\n🔗 Merging {len(validated)} prompts into unified pool...")

        # Save to temp file first
        temp_path = "/tmp/langchain-validated.json"
        with open(temp_path, 'w') as f:
            json.dump(validated, f, indent=2)

        # Merge with backup
        merge_result = self.merger.merge_with_recovery(
            existing_path="datasets/exports/unified-fewshot-pool.json",
            new_path=temp_path
        )

        if merge_result['success']:
            print(f"✓ Pool updated: {merge_result['new_count']} examples")
        else:
            print(f"✗ Merge failed: {merge_result.get('error')}")
            if merge_result.get('restored_from_backup'):
                print("  Restored from backup")

        # PHASE 5: Update metadata
        self._update_metadata({
            'fetched': len(candidates),
            'approved': len(approved),
            'validated': len(validated),
            'merged': merge_result.get('new_count', 0) - 109,
            'rejected': len(rejected) + len(validation_result.get('failed', []))
        })

        print("\n✨ Wizard complete!")
```

### 2.2 Prompt Card Display

```python
def _show_prompt_card(self, index: int, total: int, prompt: dict):
    """Display prompt card in terminal."""
    clear_screen()

    # Header
    print("╔" + "═"*76 + "╗")
    print("║" + f" Prompt {index+1}/{total}: ".ljust(77) + "║")
    print("║" + f" {prompt['metadata'].get('source_handle', 'Unknown')}".ljust(77) + "║")
    print("╠" + "═"*76 + "╣")

    # Quality Metrics
    quality = prompt['metadata'].get('quality_score', 0)
    framework = prompt['outputs'].get('framework', 'Unknown')

    print("║ 📊 QUALITY METRICS".ljust(77) + "║")
    print("║" + "─"*76 + "║")
    print(f"║    Overall: {quality:.2f}/1.0".ljust(77) + "║")
    print(f"║    Framework: {framework}".ljust(77) + "║")

    # Content Preview
    print("╠" + "═"*76 + "╣")
    print("║ 📝 CONTENT PREVIEW".ljust(77) + "║")
    print("║" + "─"*76 + "║")

    role = prompt['outputs'].get('role', 'No role')
    print(f"║ Role: {role[:60]}".ljust(77) + "║")

    directive = prompt['outputs'].get('directive', '')
    print(f"║ Directive: {directive[:60]}...".ljust(77) + "║")

    guardrails = prompt['outputs'].get('guardrails', [])
    print(f"║ Guardrails: {len(guardrails)} items".ljust(77) + "║")

    # Decision Prompt
    print("╠" + "═"*76 + "╣")
    print("║ DECISION: ".ljust(77) + "║")
    print("║   [a] Approve    [r] Remediate    [x] Reject    [s] Skip    [q] Quit ║")
    print("╚" + "═"*76 + "╝")
```

### 2.3 Remediation Wizard

```python
async def _remediate_wizard(self, weak_prompt: dict) -> dict:
    """Interactive wizard for fixing weak prompts."""
    print("\n🔧 REMEDIATION WIZARD")
    print("="*70)

    # Step 1: Diagnose weaknesses
    weaknesses = self._diagnose_weaknesses(weak_prompt)

    print("\n📋 DIAGNOSED WEAKNESSES:")
    for weakness in weaknesses:
        print(f"  ❌ {weakness['category']}: {weakness['issue']}")
        print(f"     Fix: {weakness['suggestion']}")

    # Step 2: Offer fixes
    print("\n🔧 AVAILABLE FIXES:")
    print("  [1] Auto-fix with LLM (Recommended)")
    print("  [2] Manual edit")
    print("  [3] Cancel remediation")

    choice = input("\nSelect fix option [1-3]: ").strip()

    if choice == '1':
        # Auto-fix with RemediationAgent
        print("\n🤖 Applying LLM remediation...")
        remediated = await self._apply_llm_fix(weak_prompt, weaknesses)

        print("\n✓ REMEDIATED PROMPT:")
        self._show_remediated_preview(remediated)

        confirm = input("\nApply these changes? [y/N]: ").strip().lower()
        if confirm == 'y':
            return remediated
        else:
            return weak_prompt

    elif choice == '2':
        # Manual edit
        return self._manual_edit(weak_prompt)

    else:
        # Cancel
        return weak_prompt

def _diagnose_weaknesses(self, prompt: dict) -> List[dict]:
    """Diagnose weaknesses in prompt."""
    weaknesses = []
    outputs = prompt['outputs']

    # Check role
    if not outputs.get('role') or len(outputs['role']) < 10:
        weaknesses.append({
            'category': 'Role',
            'issue': 'Missing or too brief',
            'suggestion': 'Add specific role (e.g., "Expert Data Analyst")'
        })

    # Check directive
    if not outputs.get('directive') or len(outputs['directive']) < 20:
        weaknesses.append({
            'category': 'Directive',
            'issue': 'Missing or incomplete',
            'suggestion': 'Add clear directive describing what the assistant should do'
        })

    # Check framework
    if not outputs.get('framework'):
        weaknesses.append({
            'category': 'Framework',
            'issue': 'Not specified',
            'suggestion': 'Add reasoning framework (Chain-of-Thought, ReAct, etc.)'
        })

    # Check guardrails
    guardrails = outputs.get('guardrails', [])
    if len(guardrails) < 2:
        weaknesses.append({
            'category': 'Guardrails',
            'issue': 'Insufficient guardrails',
            'suggestion': 'Add 2-3 guardrails for constraint management'
        })

    return weaknesses
```

---

## Sección 3: Flujo de Datos

```
1. FETCH PHASE
   LangChain Hub API → Raw LC Prompts → PromptMetodizer → DSPy Format → candidates.json

2. CURATE PHASE
   candidates.json → PromptCuratorWizard (loop) → User Decisions → approved.json

3. VALIDATE PHASE
   approved.json → ExampleValidator (4D scoring) → validated.json (score ≥ 0.5)

4. MERGE PHASE
   validated.json + unified-fewshot-pool.json → SHA256 deduplication → unified-pool-updated.json

5. RECOMPILE PHASE
   unified-pool-updated.json → KNNFewShot.compile(k=3) → fewshot-compiled.json

6. API UPDATE
   API restart → Load updated pool → KNNFewShot uses new examples
```

---

## Sección 4: Manejo de Errores

### Error Recovery Strategy

1. **Fetch Errors**: Log and continue - partial success is OK
2. **Conversion Errors**: Fallback to minimal format
3. **Validation Errors**: Log failure reason, continue with valid prompts
4. **Merge Errors**: Automatic backup restore before any operation

### Example Error Handling

```python
class merge_unified_pool:
    def merge_with_recovery(self, existing_path: str, new_path: str) -> MergeResult:
        # 1. Create backup
        backup_path = self._create_backup(existing_path)

        try:
            # 2-5. Merge process
            merged = self._merge_and_validate(existing_path, new_path)

            # 6. Atomic save
            temp_path = existing_path.replace('.json', '-tmp.json')
            self._save_pool(merged, temp_path)
            shutil.move(temp_path, existing_path)

            return MergeResult(success=True, new_count=len(merged['examples']))

        except Exception as e:
            # Restore from backup
            shutil.copy(backup_path, existing_path)
            return MergeResult(success=False, error=str(e), restored_from_backup=True)
```

---

## Sección 5: Testing Strategy

### Unit Tests
- `test_fetch_prompts.py`: LangChainHubFetcher with mocked hub.pull()
- `test_format_converter.py`: FormatConverter conversion logic
- `test_validator.py`: ExampleValidator 4D scoring

### Integration Tests
- `test_integration.py`: Full workflow with real Hub prompts

### E2E Tests
- `test_e2e.py`: CLI commands (fetch, interactive, validate, merge)

---

## Sección 6: Estructura de Archivos

```
scripts/langchain/
├── __init__.py
├── fetch_prompts.py              # LangChainHubFetcher
├── format_converter.py           # FormatConverter
├── prompt_curator.py             # PromptCuratorWizard (CLI)
├── remediation_agent.py          # RemediationAgent
├── config/
│   └── langchain_whitelist.json  # Handles to fetch
└── tests/
    ├── test_fetch_prompts.py
    ├── test_format_converter.py
    ├── test_validator.py
    ├── test_integration.py
    └── fixtures.py

datasets/exports/
├── unified-fewshot-pool.json         # Master pool (109)
├── langchain-candidates.json         # Fetched
├── langchain-approved.json           # Curated
├── langchain-validated.json          # Validated
└── langchain-metadata.json           # Audit trail
```

---

## Success Criteria

✅ LangChain Hub prompts added to pool (20-40 new examples)
✅ All prompts pass ExampleValidator (score ≥ 0.5)
✅ No duplicates after merge (SHA256 deduplication)
✅ DSPy KNNFewShot loads updated pool successfully
✅ Manual review step maintained (no automatic imports)
✅ Remediation wizard fixes weak prompts
✅ Complete audit trail in langchain-metadata.json

---

## Estimated Effort

| Task | Hours |
|------|-------|
| PromptCuratorWizard | 2h |
| RemediationAgent | 1.5h |
| CLI interface | 1h |
| Error handling | 1h |
| Testing | 1.5h |
| Documentation | 0.5h |
| **Total** | **7.5h** |
