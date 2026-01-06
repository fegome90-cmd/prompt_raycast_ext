# Minimal Template System v0.1

**Date:** January 5, 2026
**Purpose:** MVP template system for quality gates
**Status:** Ready for implementation

---

## 1. Overview

**Principle:** Hardcoded templates with `mode` parameter selection. No database, no UI for template creation, no dynamic loading.

**Design decision:** Opción A from contra-audit - templates hardcoded in code with simple configuration.

---

## 2. Template Specification

### 2.1 Template Interface

```typescript
interface Template {
  id: string;
  name: string;
  requires_json: boolean;
  markdown_sections: string[];
  type: "json" | "procedure" | "checklist" | "example";
}
```

### 2.2 Available Templates

#### Template 1: JSON

```typescript
{
  id: "json",
  name: "JSON Output",
  requires_json: true,
  markdown_sections: [],
  type: "json"
}
```

**Purpose:** Structured data output (API responses, configs, data schemas)

**Quality Gate 1 (Format):**
```python
def gate1_json(output: str) -> bool:
    try:
        parsed = json.loads(output)
        return bool(parsed and len(str(parsed)) > 0)
    except:
        return False
```

**Quality Gate 2 (Completeness):**
```python
def gate2_json(output: str) -> bool:
    try:
        parsed = json.loads(output)
        # Must have at least 2 keys
        return isinstance(parsed, dict) and len(parsed) >= 2
    except:
        return False
```

---

#### Template 2: Procedure (Markdown)

```typescript
{
  id: "procedure_md",
  name: "Procedure (Markdown)",
  requires_json: false,
  markdown_sections: ["## Objetivo", "## Pasos", "## Criterios"],
  type: "procedure"
}
```

**Purpose:** Step-by-step procedures, tutorials, guides

**Quality Gate 1 (Format):**
```python
def gate1_procedure(output: str) -> bool:
    required = ["objetivo", "pasos", "criterios"]
    output_lower = output.lower()
    return all(section in output_lower for section in required)
```

**Quality Gate 2 (Completeness):**
```python
def gate2_procedure(output: str) -> bool:
    # Must have at least 2 numbered steps
    steps = len(re.findall(r'^\s*\d+\.\s+', output, re.MULTILINE))
    return steps >= 2
```

---

#### Template 3: Checklist (Markdown)

```typescript
{
  id: "checklist_md",
  name: "Checklist (Markdown)",
  requires_json: false,
  markdown_sections: ["## Checklist"],
  type: "checklist"
}
```

**Purpose:** Actionable checklists, verification lists

**Quality Gate 1 (Format):**
```python
def gate1_checklist(output: str) -> bool:
    return "checklist" in output.lower()
```

**Quality Gate 2 (Completeness):**
```python
def gate2_checklist(output: str) -> bool:
    # Must have at least 3 bullet points
    bullets = len(re.findall(r'^\s*-\s+', output, re.MULTILINE))
    return bullets >= 3
```

---

#### Template 4: Example (Markdown)

```typescript
{
  id: "example_md",
  name: "Example (Markdown)",
  requires_json: false,
  markdown_sections: [],
  type: "example"
}
```

**Purpose:** Code examples, snippets, demos

**Quality Gate 1 (Format):**
```python
def gate1_example(output: str) -> bool:
    return '```' in output  # Has code block
```

**Quality Gate 2 (Completeness):**
```python
def gate2_example(output: str) -> bool:
    # Must have code block + explanation
    has_code = '```' in output
    has_text = len(output.strip().replace('```', '')) > 50
    return has_code and has_text
```

---

## 3. Implementation

### 3.1 Backend-Only Template Definition (Single Source of Truth)

**CRITICAL:** Frontend does NOT define templates. Backend is single source of truth.

**File:** `api/templates.json`

```json
{
  "json": {
    "id": "json",
    "name": "JSON Output",
    "requires_json": true,
    "markdown_sections": [],
    "type": "json",
    "required_keys": ["prompt", "role", "context"],
    "actionable": false,
    "coverage_keywords": []
  },
  "procedure_md": {
    "id": "procedure_md",
    "name": "Procedure (Markdown)",
    "requires_json": false,
    "markdown_sections": ["## Objetivo", "## Pasos", "## Criterios"],
    "type": "procedure",
    "required_keys": [],
    "actionable": true,
    "coverage_keywords": ["entrada", "input", "requisito", "precondición", "antes de", "necesitas"]
  },
  "checklist_md": {
    "id": "checklist_md",
    "name": "Checklist (Markdown)",
    "requires_json": false,
    "markdown_sections": ["## Checklist"],
    "type": "checklist",
    "required_keys": [],
    "actionable": true,
    "coverage_keywords": ["validar", "verificar", "probar", "test", "casos", "edge", "límite"]
  },
  "example_md": {
    "id": "example_md",
    "name": "Example (Markdown)",
    "requires_json": false,
    "markdown_sections": [],
    "type": "example",
    "required_keys": [],
    "actionable": false,
    "coverage_keywords": []
  }
}
```

**New fields (v0.2):**
- `required_keys`: List of mandatory keys for JSON templates
- `actionable`: True if template requires action verbs (procedure, checklist)
- `coverage_keywords`: Domain-specific keywords that must appear in output

**Frontend (TypeScript) - NO duplication, only types:**

**File:** `dashboard/src/core/config/templates.ts`

```typescript
// Single source of truth: backend (api/templates.json)
// Frontend only sends template_id string

export type TemplateId = "json" | "procedure_md" | "checklist_md" | "example_md";

export interface TemplateMetadata {
  id: string;
  name: string;
  requires_json: boolean;
  markdown_sections: string[];
  type: "json" | "procedure" | "checklist" | "example";
}

// Fetch from backend (DO NOT hardcode)
export async function getTemplates(): Promise<Record<TemplateId, TemplateMetadata>> {
  const response = await fetch("http://localhost:8000/api/v1/templates");
  return response.json();
}
```

### 3.2 Backend (Python)

**File:** `api/quality_gates.py`

```python
import json
import re
from typing import Dict, Any

class Template:
    def __init__(self, template_id: str, config: Dict[str, Any]):
        self.id = template_id
        self.requires_json = config.get("requires_json", False)
        self.markdown_sections = config.get("markdown_sections", [])
        self.type = config.get("type", "json")

# Hardcoded templates
TEMPLATES = {
    "json": Template("json", {
        "requires_json": True,
        "markdown_sections": [],
        "type": "json"
    }),
    "procedure_md": Template("procedure_md", {
        "requires_json": False,
        "markdown_sections": ["## Objetivo", "## Pasos", "## Criterios"],
        "type": "procedure"
    }),
    "checklist_md": Template("checklist_md", {
        "requires_json": False,
        "markdown_sections": ["## Checklist"],
        "type": "checklist"
    }),
    "example_md": Template("example_md", {
        "requires_json": False,
        "markdown_sections": [],
        "type": "example"
    })
}

def gate1_expected_format(output: str, template: Template) -> bool:
    """Gate 1: Formato esperado"""
    if template.requires_json:
        try:
            parsed = json.loads(output)
            return bool(parsed and len(str(parsed)) > 0)
        except:
            return False
    else:
        if not template.markdown_sections:
            # No sections required (e.g., example template)
            return True
        output_lower = output.lower()
        return all(section.lower() in output_lower for section in template.markdown_sections)

def gate2_min_completeness(output: str, template: Template) -> bool:
    """Gate 2: Completitud mínima"""
    if template.type == "json":
        try:
            parsed = json.loads(output)
            return isinstance(parsed, dict) and len(parsed) >= 2
        except:
            return False
    elif template.type == "procedure":
        steps = len(re.findall(r'^\s*\d+\.\s+', output, re.MULTILINE))
        return steps >= 2
    elif template.type == "checklist":
        bullets = len(re.findall(r'^\s*-\s+', output, re.MULTILINE))
        return bullets >= 3
    elif template.type == "example":
        has_code = '```' in output
        has_text = len(output.strip().replace('```', '')) > 50
        return has_code and has_text
    else:
        # Fallback: longitud mínima
        return len(output.strip()) >= 100

def evaluate_quality_gates(output: str, template_id: str) -> Dict[str, bool]:
    """Evaluar ambos quality gates"""
    template = TEMPLATES.get(template_id, TEMPLATES["json"])
    return {
        "gate1_pass": gate1_expected_format(output, template),
        "gate2_pass": gate2_min_completeness(output, template),
        "both_pass": gate1_expected_format(output, template) and gate2_min_completeness(output, template)
    }
```

---

## 4. Advanced Gates v0.2 (Anti-Trampa Heuristics)

**Purpose:** Detect outputs that pass format checks but are semantically empty or "cheating" the system.

**Principle:** Cheap O(1) string operations, no additional LLM calls, WARN before FAIL.

**Integration Strategy:**
- v0.1 gates (format + completeness) = FAIL
- v0.2 gates (anti-trampa) = WARN initially, promote to FAIL with real data

---

### 4.1 Core Gates (Apply to All Templates)

#### Gate A1: Placeholder / Filler Detector

**Detects:** "TBD", "lorem", "insert here", "TODO", "N/A", etc. as main content.

```python
def gate_a1_filler_detector(output: str) -> Dict[str, Any]:
    """Detect placeholder/filler tokens"""
    filler_tokens = [
        "tbd", "todo", "lorem", "placeholder", "insert", "fill",
        "n/a", "none", "etc", "stuff", "item", "thing", "whatever", "???"
    ]

    output_lower = output.lower()
    filler_count = sum(1 for token in filler_tokens if token in output_lower)

    # Check if fillers are dominant
    words = output_lower.split()
    filler_ratio = filler_count / len(words) if words else 0

    # FAIL if: 2+ fillers OR 1 filler with low content density
    content_density = len(re.findall(r'[a-z]', output_lower)) / len(output) if output else 0

    fail = filler_count >= 2 or (filler_count == 1 and content_density < 0.35)

    return {
        "gate": "A1_filler_detector",
        "pass": not fail,
        "filler_count": filler_count,
        "content_density": round(content_density, 3),
        "severity": "FAIL"
    }
```

---

#### Gate A2: Non-Trivial Token Count

**Detects:** Content with structure but no substance (titles + nothing).

```python
def gate_a2_non_trivial_tokens(output: str) -> Dict[str, Any]:
    """Detect meaningful content beyond structure"""
    stopwords = {"el", "la", "de", "en", "y", "o", "que", "con", "para", "the", "a", "an", "of", "in", "and", "or"}

    # Non-trivial = word length >= 4 and not in stopwords
    words = re.findall(r'\b[a-z]{4,}\b', output.lower())
    non_trivial = [w for w in words if w not in stopwords]

    # FAIL if less than 25 non-trivial tokens
    fail = len(non_trivial) < 25

    return {
        "gate": "A2_non_trivial_tokens",
        "pass": not fail,
        "non_trivial_count": len(non_trivial),
        "threshold": 25,
        "severity": "FAIL"
    }
```

---

#### Gate A3: Content Density

**Detects:** Outputs with high markup but low substance.

```python
def gate_a3_content_density(output: str) -> Dict[str, Any]:
    """Detect structure-heavy, content-light outputs"""
    if not output:
        return {"gate": "A3_content_density", "pass": False, "density": 0, "severity": "FAIL"}

    alnum_chars = len(re.findall(r'[a-z0-9]', output.lower()))
    total_chars = len(output)
    density = alnum_chars / total_chars if total_chars > 0 else 0

    # FAIL if density < 0.25 (too much markup, not enough content)
    fail = density < 0.25

    return {
        "gate": "A3_content_density",
        "pass": not fail,
        "density": round(density, 3),
        "threshold": 0.25,
        "severity": "FAIL"
    }
```

---

#### Gate A4: Repetition / Tautology

**Detects:** "- Item - Item - Item" or repeated steps.

```python
def gate_a4_repetition_detector(output: str) -> Dict[str, Any]:
    """Detect repetitive lines (tautologies)"""
    lines = [line.strip().lower() for line in output.split('\n') if line.strip()]

    # Remove punctuation and normalize
    normalized = [re.sub(r'[^\w\s]', '', line) for line in lines]

    # Count duplicates
    unique = set(normalized)
    duplicate_ratio = 1 - (len(unique) / len(normalized)) if normalized else 0

    # FAIL if >30% duplicates AND at least 6 lines
    fail = duplicate_ratio > 0.30 and len(lines) >= 6

    return {
        "gate": "A4_repetition_detector",
        "pass": not fail,
        "duplicate_ratio": round(duplicate_ratio, 3),
        "line_count": len(lines),
        "severity": "FAIL"
    }
```

---

#### Gate A5: Action Verb Presence

**Detects:** Checklist/procedure without operable verbs (nouns only).

```python
def gate_a5_action_verbs(output: str, template: Template) -> Dict[str, Any]:
    """Detect action verbs in actionable templates"""
    if not template.actionable:
        return {"gate": "A5_action_verbs", "pass": True, "skipped": True, "severity": "SKIP"}

    action_verbs = [
        "validar", "verificar", "crear", "ejecutar", "medir", "comparar",
        "registrar", "revisar", "implementar", "configurar", "probar", "documentar",
        "check", "test", "validate", "verify", "create", "run", "measure"
    ]

    # Extract bullets/steps (lines starting with -, *, 1., 2., etc.)
    lines = output.split('\n')
    actionable_lines = [
        line for line in lines
        if re.match(r'^\s*[-*]\s+', line) or re.match(r'^\s*\d+\.\s+', line)
    ]

    if not actionable_lines:
        return {"gate": "A5_action_verbs", "pass": False, "actionable_lines": 0, "severity": "FAIL"}

    # Check if lines start with action verbs or imperatives
    verb_start_count = 0
    for line in actionable_lines:
        line_lower = line.lower()
        # Check for action verbs OR Spanish imperative (-ar, -er, -ir)
        if any(verb in line_lower for verb in action_verbs):
            verb_start_count += 1
        elif re.search(r'\b(ar|er|ir)\s+', line_lower):
            verb_start_count += 1

    verb_ratio = verb_start_count / len(actionable_lines)
    fail = verb_ratio < 0.50  # Less than 50% have action verbs

    return {
        "gate": "A5_action_verbs",
        "pass": not fail,
        "verb_ratio": round(verb_ratio, 3),
        "actionable_lines": len(actionable_lines),
        "severity": "FAIL"
    }
```

---

### 4.2 JSON-Specific Gates

#### Gate J1: Empty-Value Ratio

**Detects:** Valid JSON but empty values.

```python
def gate_j1_empty_value_ratio(output: str, template: Template) -> Dict[str, Any]:
    """Detect JSON with empty/trivial values"""
    if not template.requires_json:
        return {"gate": "J1_empty_value_ratio", "pass": True, "skipped": True, "severity": "SKIP"}

    try:
        data = json.loads(output)
    except:
        return {"gate": "J1_empty_value_ratio", "pass": False, "error": "invalid_json", "severity": "FAIL"}

    # Recursively count leaf values
    def count_leaves(obj, empty_count=0, total_count=0):
        if isinstance(obj, dict):
            for v in obj.values():
                empty_count, total_count = count_leaves(v, empty_count, total_count)
        elif isinstance(obj, list):
            for item in obj:
                empty_count, total_count = count_leaves(item, empty_count, total_count)
        else:
            total_count += 1
            # Empty = "", null, [], {}
            if obj in ["", None] or obj == [] or obj == {}:
                empty_count += 1
        return empty_count, total_count

    empty, total = count_leaves(data)
    empty_ratio = empty / total if total > 0 else 0

    # FAIL if >30% empty OR any required key is empty
    required_keys = template.required_keys or []
    missing_required = []
    if isinstance(data, dict):
        for key in required_keys:
            if key not in data or not data[key]:
                missing_required.append(key)

    fail = empty_ratio > 0.30 or len(missing_required) > 0

    return {
        "gate": "J1_empty_value_ratio",
        "pass": not fail,
        "empty_ratio": round(empty_ratio, 3),
        "missing_required": missing_required,
        "severity": "FAIL"
    }
```

---

#### Gate J2: Minimal Information Per Field

**Detects:** Trivial strings ("ok", "yes", "item").

```python
def gate_j2_minimal_info_per_field(output: str, template: Template) -> Dict[str, Any]:
    """Detect trivial string values in JSON"""
    if not template.requires_json:
        return {"gate": "J2_minimal_info", "pass": True, "skipped": True, "severity": "SKIP"}

    try:
        data = json.loads(output)
    except:
        return {"gate": "J2_minimal_info", "pass": False, "error": "invalid_json", "severity": "FAIL"}

    trivial_strings = {"ok", "yes", "no", "item", "value", "test", "data", "foo", "bar", "thing"}

    def count_string_values(obj, trivial_count=0, total_strings=0):
        if isinstance(obj, dict):
            for v in obj.values():
                trivial_count, total_strings = count_string_values(v, trivial_count, total_strings)
        elif isinstance(obj, list):
            for item in obj:
                trivial_count, total_strings = count_string_values(item, trivial_count, total_strings)
        elif isinstance(obj, str):
            total_strings += 1
            if obj.strip().lower() in trivial_strings:
                trivial_count += 1
            elif len(obj.strip()) < 8 or len(obj.strip().split()) < 2:
                # Too short or single-word (unless it looks like an identifier)
                if not re.match(r'^[a-z_][a-z0-9_]*$', obj.strip()):
                    trivial_count += 1
        return trivial_count, total_strings

    trivial, total = count_string_values(data)
    trivial_ratio = trivial / total if total > 0 else 0

    # FAIL if >25% trivial strings
    fail = trivial_ratio > 0.25

    return {
        "gate": "J2_minimal_info_per_field",
        "pass": not fail,
        "trivial_ratio": round(trivial_ratio, 3),
        "severity": "FAIL"
    }
```

---

#### Gate J3: Required Keys Presence

**Detects:** Parseable JSON that avoids the contract.

```python
def gate_j3_required_keys(output: str, template: Template) -> Dict[str, Any]:
    """Enforce required keys in JSON"""
    if not template.requires_json:
        return {"gate": "J3_required_keys", "pass": True, "skipped": True, "severity": "SKIP"}

    try:
        data = json.loads(output)
    except:
        return {"gate": "J3_required_keys", "pass": False, "error": "invalid_json", "severity": "FAIL"}

    required_keys = template.required_keys or []

    if not isinstance(data, dict):
        return {
            "gate": "J3_required_keys",
            "pass": False,
            "error": "not_a_dict",
            "severity": "FAIL"
        }

    missing = [k for k in required_keys if k not in data]
    fail = len(missing) > 0

    return {
        "gate": "J3_required_keys",
        "pass": not fail,
        "missing_keys": missing,
        "severity": "FAIL"
    }
```

---

### 4.3 Procedure-Specific Gates

#### Gate P1: Real Step Content

**Detects:** Numbered steps but empty/generic ("1. TBD").

```python
def gate_p1_real_step_content(output: str, template: Template) -> Dict[str, Any]:
    """Detect numbered steps with real content"""
    if template.type != "procedure":
        return {"gate": "P1_real_step_content", "pass": True, "skipped": True, "severity": "SKIP"}

    # Extract numbered steps
    steps = re.findall(r'^\s*\d+\.\s+(.+)$', output, re.MULTILINE)

    if not steps:
        return {"gate": "P1_real_step_content", "pass": False, "step_count": 0, "severity": "FAIL"}

    # Check each step for non-trivial content
    action_verbs = ["validar", "verificar", "crear", "ejecutar", "medir", "comparar", "configurar", "probar"]
    empty_steps = 0

    for step in steps:
        step_lower = step.lower()
        # Count non-trivial tokens
        words = re.findall(r'\b[a-z]{4,}\b', step_lower)
        # Check for action verbs
        has_verb = any(verb in step_lower for verb in action_verbs)

        if len(words) < 6 or not has_verb:
            empty_steps += 1

    empty_ratio = empty_steps / len(steps)
    fail = empty_ratio > 0.20  # More than 20% empty steps

    return {
        "gate": "P1_real_step_content",
        "pass": not fail,
        "empty_ratio": round(empty_ratio, 3),
        "step_count": len(steps),
        "severity": "FAIL"
    }
```

---

#### Gate P2: Step Uniqueness

**Detects:** Repeated steps with minimal word changes.

```python
def gate_p2_step_uniqueness(output: str, template: Template) -> Dict[str, Any]:
    """Detect duplicate/similar steps using Jaccard similarity"""
    if template.type != "procedure":
        return {"gate": "P2_step_uniqueness", "pass": True, "skipped": True, "severity": "SKIP"}

    steps = re.findall(r'^\s*\d+\.\s+(.+)$', output, re.MULTILINE)

    if len(steps) < 2:
        return {"gate": "P2_step_uniqueness", "pass": True, "step_count": len(steps), "severity": "SKIP"}

    stopwords = {"el", "la", "de", "en", "y", "o", "que", "con", "para", "the", "a", "an", "of"}

    def tokenize(step):
        words = re.findall(r'\b[a-z]+\b', step.lower())
        return set(w for w in words if w not in stopwords)

    def jaccard_similarity(set1, set2):
        if not set1 or not set2:
            return 0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0

    # Check all pairs
    similar_pairs = 0
    for i in range(len(steps)):
        for j in range(i + 1, len(steps)):
            tokens1 = tokenize(steps[i])
            tokens2 = tokenize(steps[j])
            similarity = jaccard_similarity(tokens1, tokens2)
            if similarity > 0.85:  # 85% similar = duplicate
                similar_pairs += 1

    fail = similar_pairs > 0

    return {
        "gate": "P2_step_uniqueness",
        "pass": not fail,
        "similar_pairs": similar_pairs,
        "step_count": len(steps),
        "severity": "WARN"  # WARN initially, can promote to FAIL
    }
```

---

#### Gate P3: Preconditions / Inputs Mentioned

**Detects:** Procedure without mentioning inputs or prerequisites.

```python
def gate_p3_preconditions_mentioned(output: str, template: Template) -> Dict[str, Any]:
    """Detect mentions of inputs/prerequisites"""
    if template.type != "procedure":
        return {"gate": "P3_preconditions", "pass": True, "skipped": True, "severity": "SKIP"}

    coverage_keywords = template.coverage_keywords or [
        "entrada", "input", "requisito", "precondición", "antes de", "necesitas",
        "require", "before", "need", "input", "prerequisite"
    ]

    output_lower = output.lower()
    found_keywords = [kw for kw in coverage_keywords if kw in output_lower]

    # FAIL if no coverage keywords found (when template expects them)
    fail = len(found_keywords) == 0 and len(template.coverage_keywords or []) > 0

    return {
        "gate": "P3_preconditions",
        "pass": not fail,
        "found_keywords": found_keywords,
        "severity": "FAIL"
    }
```

---

### 4.4 Checklist-Specific Gates

#### Gate C1: Bullet Specificity

**Detects:** Generic bullets ("Item", "Check", "Do it").

```python
def gate_c1_bullet_specificity(output: str, template: Template) -> Dict[str, Any]:
    """Detect specific vs generic checklist items"""
    if template.type != "checklist":
        return {"gate": "C1_bullet_specificity", "pass": True, "skipped": True, "severity": "SKIP"}

    # Extract bullets
    bullets = re.findall(r'^\s*[-*]\s+(.+)$', output, re.MULTILINE)

    if not bullets:
        return {"gate": "C1_bullet_specificity", "pass": False, "bullet_count": 0, "severity": "FAIL"}

    generic_bullets = 0
    technical_terms = re.compile(
        r'(api|endpoint|\.py|\.ts|\.js|http|sql|test|ci|cd|regex|validator|'
        r'config|file|class|def|function|assert|import|const|let|var)',
        re.IGNORECASE
    )

    for bullet in bullets:
        # Check for non-trivial content
        words = re.findall(r'\b[a-z]{4,}\b', bullet.lower())
        # Check for concrete object (colon-separated OR technical term)
        has_structure = ':' in bullet or technical_terms.search(bullet)

        if len(words) < 4 or not has_structure:
            generic_bullets += 1

    generic_ratio = generic_bullets / len(bullets)
    fail = generic_ratio > 0.30  # More than 30% generic

    return {
        "gate": "C1_bullet_specificity",
        "pass": not fail,
        "generic_ratio": round(generic_ratio, 3),
        "bullet_count": len(bullets),
        "severity": "FAIL"
    }
```

---

#### Gate C2: Coverage Minimum

**Detects:** Checklist that avoids key aspects.

```python
def gate_c2_coverage_minimum(output: str, template: Template) -> Dict[str, Any]:
    """Check domain-specific coverage keywords"""
    if template.type != "checklist":
        return {"gate": "C2_coverage_minimum", "pass": True, "skipped": True, "severity": "SKIP"}

    coverage_keywords = template.coverage_keywords or []

    if not coverage_keywords:
        return {"gate": "C2_coverage_minimum", "pass": True, "skipped": True, "severity": "SKIP"}

    output_lower = output.lower()
    found_keywords = [kw for kw in coverage_keywords if kw in output_lower]

    # FAIL if missing 2+ coverage keywords
    fail = len(found_keywords) < len(coverage_keywords) - 1

    return {
        "gate": "C2_coverage_minimum",
        "pass": not fail,
        "found_keywords": found_keywords,
        "missing_count": len(coverage_keywords) - len(found_keywords),
        "severity": "FAIL"
    }
```

---

### 4.5 Example-Specific Gates

#### Gate E1: Code Fence + Non-Trivial Code

**Detects:** Code blocks that are empty or just comments.

```python
def gate_e1_non_trivial_code(output: str, template: Template) -> Dict[str, Any]:
    """Detect actual code in code blocks"""
    if template.type != "example":
        return {"gate": "E1_non_trivial_code", "pass": True, "skipped": True, "severity": "SKIP"}

    # Extract code blocks
    code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', output, re.DOTALL)

    if not code_blocks:
        return {"gate": "E1_non_trivial_code", "pass": False, "code_blocks": 0, "severity": "FAIL"}

    for block in code_blocks:
        lines = [l for l in block.split('\n') if l.strip() and not l.strip().startswith('#')]

        # Check for at least 6 non-comment lines
        if len(lines) < 6:
            return {"gate": "E1_non_trivial_code", "pass": False, "code_lines": len(lines), "severity": "FAIL"}

        # Check for code-like constructs
        code_indicators = re.compile(
            r'(def |class |function |const |let |var |import |SELECT|INSERT|assert|test)',
            re.IGNORECASE
        )

        if not code_indicators.search(block):
            return {"gate": "E1_non_trivial_code", "pass": False, "has_code_constructs": False, "severity": "FAIL"}

    return {
        "gate": "E1_non_trivial_code",
        "pass": True,
        "code_blocks": len(code_blocks),
        "severity": "FAIL"
    }
```

---

#### Gate E2: Code/Explanation Linkage

**Detects:** Code without explanation or vice versa.

```python
def gate_e2_code_explanation_linkage(output: str, template: Template) -> Dict[str, Any]:
    """Detect linkage between code and explanation"""
    if template.type != "example":
        return {"gate": "E2_code_explanation_linkage", "pass": True, "skipped": True, "severity": "SKIP"}

    # Extract function/class names from code
    code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', output, re.DOTALL)

    if not code_blocks:
        return {"gate": "E2_code_explanation_linkage", "pass": True, "skipped": True, "severity": "SKIP"}

    # Find function/class names
    code_names = set()
    for block in code_blocks:
        names = re.findall(r'\b(def|class|function|const)\s+(\w+)', block, re.IGNORECASE)
        code_names.update(n[1] for n in names)

    # Extract explanation text (outside code blocks)
    explanation = re.sub(r'```.*?```', '', output, flags=re.DOTALL)

    # Check if explanation references code
    found_references = 0
    for name in code_names:
        if name in explanation:
            found_references += 1

    # FAIL if no linkage between code and explanation
    fail = len(code_names) > 0 and found_references == 0

    return {
        "gate": "E2_code_explanation_linkage",
        "pass": not fail,
        "code_names": list(code_names),
        "found_references": found_references,
        "severity": "WARN"  # WARN initially
    }
```

---

### 4.6 Integration: Complete Gate Evaluation

**File:** `api/quality_gates.py`

```python
def evaluate_all_gates(output: str, template_id: str) -> Dict[str, Any]:
    """Evaluate v0.1 (format) + v0.2 (anti-trampa) gates"""
    template = TEMPLATES.get(template_id, TEMPLATES["json"])

    results = {
        "output_length": len(output),
        "template_id": template_id,
        "v0.1_gates": {},
        "v0.2_gates": {},
        "summary": {}
    }

    # v0.1: Format + Completeness (FAIL)
    results["v0.1_gates"]["gate1_format"] = gate1_expected_format(output, template)
    results["v0.1_gates"]["gate2_completeness"] = gate2_min_completeness(output, template)

    # v0.2: Anti-Trampa (WARN initially)
    results["v0.2_gates"]["A1_filler"] = gate_a1_filler_detector(output)
    results["v0.2_gates"]["A2_tokens"] = gate_a2_non_trivial_tokens(output)
    results["v0.2_gates"]["A3_density"] = gate_a3_content_density(output)
    results["v0.2_gates"]["A4_repetition"] = gate_a4_repetition_detector(output)
    results["v0.2_gates"]["A5_verbs"] = gate_a5_action_verbs(output, template)

    # Template-specific gates
    if template.requires_json:
        results["v0.2_gates"]["J1_empty"] = gate_j1_empty_value_ratio(output, template)
        results["v0.2_gates"]["J2_trivial"] = gate_j2_minimal_info_per_field(output, template)
        results["v0.2_gates"]["J3_keys"] = gate_j3_required_keys(output, template)

    if template.type == "procedure":
        results["v0.2_gates"]["P1_steps"] = gate_p1_real_step_content(output, template)
        results["v0.2_gates"]["P2_unique"] = gate_p2_step_uniqueness(output, template)
        results["v0.2_gates"]["P3_precond"] = gate_p3_preconditions_mentioned(output, template)

    if template.type == "checklist":
        results["v0.2_gates"]["C1_specific"] = gate_c1_bullet_specificity(output, template)
        results["v0.2_gates"]["C2_coverage"] = gate_c2_coverage_minimum(output, template)

    if template.type == "example":
        results["v0.2_gates"]["E1_code"] = gate_e1_non_trivial_code(output, template)
        results["v0.2_gates"]["E2_linkage"] = gate_e2_code_explanation_linkage(output, template)

    # Summary
    v01_pass = (
        results["v0.1_gates"]["gate1_format"]["pass"] and
        results["v0.1_gates"]["gate2_completeness"]["pass"]
    )

    v02_fail_count = sum(
        1 for gate in results["v0.2_gates"].values()
        if gate.get("severity") == "FAIL" and not gate.get("pass", True)
    )
    v02_warn_count = sum(
        1 for gate in results["v0.2_gates"].values()
        if gate.get("severity") == "WARN" and not gate.get("pass", True)
    )

    results["summary"] = {
        "v0.1_pass": v01_pass,
        "v0.2_fail_count": v02_fail_count,
        "v0.2_warn_count": v02_warn_count,
        "overall_pass": v01_pass and v02_fail_count == 0
    }

    return results
```

---

## 5. Test Suite (12 Cases)

### 5.1 Test Cases

| # | Template | Input | Expected Gate 1 | Expected Gate 2 | Expected Both |
|---|----------|-------|-----------------|-----------------|---------------|
| 1 | json | `{"name": "test", "value": 123}` | PASS | PASS | PASS |
| 2 | json | `invalid json` | FAIL | FAIL | FAIL |
| 3 | json | `{"key": "value"}` | PASS | FAIL | FAIL (only 1 key) |
| 4 | procedure_md | `## Objetivo\n\nTest\n\n## Pasos\n\n1. Step 1\n\n2. Step 2` | PASS | PASS | PASS |
| 5 | procedure_md | `Steps:\n\n1. Step 1` | FAIL | PASS | FAIL (no Objetivo section) |
| 6 | procedure_md | `## Objetivo\n\n## Pasos\n\nOnly one step` | PASS | FAIL | FAIL (only 1 step) |
| 7 | checklist_md | `## Checklist\n\n- Item 1\n\n- Item 2\n\n- Item 3` | PASS | PASS | PASS |
| 8 | checklist_md | `Items:\n\n- Item 1` | FAIL | PASS | FAIL (no Checklist section) |
| 9 | checklist_md | `## Checklist\n\n- Only one item` | PASS | FAIL | FAIL (only 1 bullet) |
| 10 | example_md | `Example:\n\n\`\`\`python\nprint("hello")\n\`\`\`\n\nThis prints hello.` | PASS | PASS | PASS |
| 11 | example_md | `Just some text` | FAIL | FAIL | FAIL (no code block) |
| 12 | example_md | `\`\`\`python\nprint("hi")\n\`\`\`` | PASS | FAIL | FAIL (no explanation) |

### 4.2 Test Execution

**Script:** `tests/test_quality_gates.py`

```python
import pytest
from api.quality_gates import evaluate_quality_gates

@pytest.mark.parametrize("template_id,output,expected_g1,expected_g2,expected_both", [
    ("json", '{"name": "test", "value": 123}', True, True, True),
    ("json", "invalid json", False, False, False),
    ("json", '{"key": "value"}', True, False, False),
    ("procedure_md", "## Objetivo\n\nTest\n\n## Pasos\n\n1. Step 1\n\n2. Step 2", True, True, True),
    ("procedure_md", "Steps:\n\n1. Step 1", False, True, False),
    ("procedure_md", "## Objetivo\n\n## Pasos\n\nOnly one step", True, False, False),
    ("checklist_md", "## Checklist\n\n- Item 1\n\n- Item 2\n\n- Item 3", True, True, True),
    ("checklist_md", "Items:\n\n- Item 1", False, True, False),
    ("checklist_md", "## Checklist\n\n- Only one item", True, False, False),
    ("example_md", "Example:\n\n\`\`\`python\nprint('hello')\n\`\`\`\n\nThis prints hello.", True, True, True),
    ("example_md", "Just some text", False, False, False),
    ("example_md", "\`\`\`python\nprint('hi')\n\`\`\`", True, False, False),
])
def test_quality_gates(template_id, output, expected_g1, expected_g2, expected_both):
    result = evaluate_quality_gates(output, template_id)
    assert result["gate1_pass"] == expected_g1
    assert result["gate2_pass"] == expected_g2
    assert result["both_pass"] == expected_both
```

**Run:** `pytest tests/test_quality_gates.py -v`

---

## 5. Integration with DSPy

### 5.1 Backend API Update

**File:** `api/prompt_improver_api.py`

```python
from pydantic import BaseModel
from api.quality_gates import evaluate_quality_gates

class ImprovePromptRequest(BaseModel):
    raw_input: str
    mode: str = "default"  # "fast", "default"
    template_id: str = "json"  # NEW: template selection

class ImprovePromptResponse(BaseModel):
    improved_prompt: str
    quality_gates: Dict[str, bool]  # NEW: gate results
    metadata: Dict[str, Any]

@app.post("/api/v1/improve-prompt")
async def improve_prompt(request: ImprovePromptRequest):
    # ... existing DSPy logic ...

    # Evaluate quality gates
    gate_results = evaluate_quality_gates(improved_prompt, request.template_id)

    return ImprovePromptResponse(
        improved_prompt=improved_prompt,
        quality_gates=gate_results,
        metadata={
            "template_id": request.template_id,
            "mode": request.mode,
            # ... existing metadata ...
        }
    )
```

### 5.2 Frontend Update

**File:** `dashboard/src/core/llm/improvePrompt.ts`

```typescript
interface ImprovePromptOptions {
  rawInput: string;
  mode?: string;
  templateId?: string;  // NEW
}

async function improvePrompt(options: ImprovePromptOptions): Promise<{
  improvedPrompt: string;
  qualityGates: { gate1_pass: boolean; gate2_pass: boolean; both_pass: boolean };
}> {
  const { rawInput, mode = "default", templateId = "json" } = options;

  const response = await fetch("http://localhost:8000/api/v1/improve-prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_input: rawInput,
      mode,
      template_id: templateId
    })
  });

  return response.json();
}
```

---

## 6. Migration Path

### Phase 1: Hardcoded Templates (v0.1)

- [ ] Implement 4 templates in code
- [ ] Add quality gates logic
- [ ] Update API with `template_id` parameter
- [ ] Test suite with 12 cases

### Phase 2: UI Template Selection (Later)

- [ ] Add dropdown in Raycast UI
- [ ] User can select template before improvement
- [ ] Display gate results in output

### Phase 3: Custom Templates (Future)

- [ ] Template editor UI
- [ ] Save/load custom templates
- [ ] Template validation

---

**v0.1 Specification - Ready for implementation**
