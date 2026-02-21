"""
Quality Gates v0.1 + v0.2 (Starter Set)

Validates output quality across multiple dimensions:
- v0.1: Format (Gate 1) + Completeness (Gate 2) - HARD FAIL
- v0.2: Anti-trampa heuristics - WARN initially

Design principles:
- Single source of truth: templates.json (backend)
- Cheap O(1) string operations, no LLM calls
- WARN before FAIL (promote based on real data)
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ============================================================================
# Configuration
# ============================================================================

class GateSeverity(Enum):
    """Severity levels for gate failures"""
    SKIP = "SKIP"   # Gate not applicable for this template
    PASS = "PASS"   # Gate passed
    WARN = "WARN"   # Warning but allow output
    FAIL = "FAIL"   # Hard fail, block output


@dataclass
class GateThresholds:
    """Centralized threshold configuration for all gates"""
    # v0.2 Core thresholds
    A1_MAX_FILLER_COUNT: int = 2
    A1_CONTENT_DENSITY_THRESHOLD: float = 0.35
    A4_DUPLICATE_RATIO_THRESHOLD: float = 0.30
    A4_MIN_LINE_COUNT: int = 6

    # v0.2 JSON thresholds
    J1_MAX_EMPTY_RATIO: float = 0.30

    # v0.2 Procedure thresholds (relaxed for MVP)
    P1_MAX_EMPTY_STEP_RATIO: float = 0.30  # Increased from 0.20 to allow some generic steps
    P1_MIN_NON_TRIVIAL_TOKENS: int = 4     # Decreased from 6 to be more permissive

    # v0.2 Checklist thresholds
    C1_MAX_GENERIC_RATIO: float = 0.40     # Increased from 0.30
    C1_MIN_NON_TRIVIAL_TOKENS: int = 3     # Decreased from 4

    # v0.2 Example thresholds
    E1_MIN_CODE_LINES: int = 3             # Decreased from 6 for smaller code examples


@dataclass
class GateConfig:
    """Per-gate configuration with severity overrides"""
    gate_id: str
    default_severity: GateSeverity
    severity_overrides: dict[str, GateSeverity] = field(
        default_factory=dict
    )  # template_id -> severity

    def get_severity(self, template_id: str) -> GateSeverity:
        """Get severity for a specific template"""
        return self.severity_overrides.get(template_id, self.default_severity)


# Default configuration - v0.2 gates are WARN by default
GATE_CONFIG = {
    # v0.1 gates - always FAIL
    "v0.1_gate1_format": GateConfig("v0.1_gate1_format", GateSeverity.FAIL),
    "v0.1_gate2_completeness": GateConfig("v0.1_gate2_completeness", GateSeverity.FAIL),

    # v0.2 Core gates - WARN initially
    "A1_filler_detector": GateConfig("A1_filler_detector", GateSeverity.WARN),
    "A4_repetition_detector": GateConfig("A4_repetition_detector", GateSeverity.WARN),

    # v0.2 JSON gates - J1 is FAIL for json template
    "J1_empty_value_ratio": GateConfig(
        "J1_empty_value_ratio",
        GateSeverity.WARN,
        severity_overrides={"json": GateSeverity.FAIL}  # Hard FAIL for JSON
    ),

    # v0.2 Procedure gates - WARN initially
    "P1_real_step_content": GateConfig("P1_real_step_content", GateSeverity.WARN),

    # v0.2 Checklist gates - WARN initially
    "C1_bullet_specificity": GateConfig("C1_bullet_specificity", GateSeverity.WARN),

    # v0.2 Example gates - WARN initially
    "E1_non_trivial_code": GateConfig("E1_non_trivial_code", GateSeverity.WARN),
}

# Filler tokens for A1 gate
FILLER_TOKENS = [
    "tbd", "todo", "lorem", "placeholder", "insert", "fill",
    "n/a", "none", "etc", "stuff", "item", "thing", "whatever", "???"
]

# Action verbs for A5/P1 gates
ACTION_VERBS = [
    "validar", "verificar", "crear", "ejecutar", "medir", "comparar",
    "registrar", "revisar", "implementar", "configurar", "probar", "documentar",
    "check", "test", "validate", "verify", "create", "run", "measure"
]

# Technical terms for C1 gate
TECHNICAL_TERMS_PATTERN = re.compile(
    r'(api|endpoint|\.py|\.ts|\.js|http|sql|test|ci|cd|regex|validator|'
    r'config|file|class|def|function|assert|import|const|let|var)',
    re.IGNORECASE
)

# Code indicators for E1 gate
CODE_INDICATORS_PATTERN = re.compile(
    r'(def |class |function |const |let |var |import |SELECT|INSERT|assert|test)',
    re.IGNORECASE
)

# Stopwords for A2/P2 gates
STOPWORDS = {
    "el", "la", "de", "en", "y", "o", "que", "con", "para", "the",
    "a", "an", "of", "in", "and", "or", "to", "for", "with", "on"
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class GateResult:
    """Result of a single gate evaluation"""
    gate_id: str
    gate_version: str
    status: GateSeverity
    score: float | None = None  # Optional numeric score
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "gate_id": self.gate_id,
            "gate_version": self.gate_version,
            "status": self.status.value,
            "score": self.score,
            "details": self.details
        }


@dataclass
class GateReport:
    """Complete gate evaluation report"""
    template_id: str
    output_length: int
    v0_1_gates: dict[str, GateResult] = field(default_factory=dict)
    v0_2_gates: dict[str, GateResult] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def v0_1_pass(self) -> bool:
        """Check if all v0.1 gates passed"""
        return all(
            result.status == GateSeverity.PASS
            for result in self.v0_1_gates.values()
        )

    @property
    def v0_2_fail_count(self) -> int:
        """Count FAIL severity gates in v0.2"""
        return sum(
            1 for result in self.v0_2_gates.values()
            if result.status == GateSeverity.FAIL
        )

    @property
    def v0_2_warn_count(self) -> int:
        """Count WARN severity gates in v0.2"""
        return sum(
            1 for result in self.v0_2_gates.values()
            if result.status == GateSeverity.WARN
        )

    @property
    def overall_pass(self) -> bool:
        """Check if output passes all gates (v0.1 must PASS, v0.2 must not FAIL)"""
        return self.v0_1_pass and self.v0_2_fail_count == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "template_id": self.template_id,
            "output_length": self.output_length,
            "v0.1_gates": {
                k: v.to_dict() for k, v in self.v0_1_gates.items()
            },
            "v0.2_gates": {
                k: v.to_dict() for k, v in self.v0_2_gates.items()
            },
            "summary": {
                "v0.1_pass": self.v0_1_pass,
                "v0.2_fail_count": self.v0_2_fail_count,
                "v0.2_warn_count": self.v0_2_warn_count,
                "overall_pass": self.overall_pass,
                "overall_status": self._get_overall_status()
            }
        }

    def _get_overall_status(self) -> str:
        """Get human-readable overall status"""
        if not self.v0_1_pass:
            return "FAIL"  # v0.1 failed
        elif self.v0_2_fail_count > 0:
            return "FAIL"  # v0.2 hard failed
        elif self.v0_2_warn_count > 0:
            return "WARN"  # v0.2 warnings
        else:
            return "PASS"


# ============================================================================
# Template Specification
# ============================================================================

@dataclass
class TemplateSpec:
    """Template specification loaded from templates.json"""
    id: str
    name: str
    requires_json: bool
    markdown_sections: list[str]
    type: str  # "json", "procedure", "checklist", "example"
    required_keys: list[str] = field(default_factory=list)
    actionable: bool = False
    coverage_keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, template_id: str, data: dict[str, Any]) -> "TemplateSpec":
        """Create from templates.json dict"""
        return cls(
            id=template_id,
            name=data.get("name", ""),
            requires_json=data.get("requires_json", False),
            markdown_sections=data.get("markdown_sections", []),
            type=data.get("type", "json"),
            required_keys=data.get("required_keys", []),
            actionable=data.get("actionable", False),
            coverage_keywords=data.get("coverage_keywords", [])
        )


# Default templates (fallback if templates.json not loaded)
DEFAULT_TEMPLATES: dict[str, dict[str, Any]] = {
    "json": {
        "id": "json",
        "name": "JSON Output",
        "requires_json": True,
        "markdown_sections": [],
        "type": "json",
        "required_keys": ["prompt", "role", "context"],
        "actionable": False,
        "coverage_keywords": []
    },
    "procedure_md": {
        "id": "procedure_md",
        "name": "Procedure (Markdown)",
        "requires_json": False,
        "markdown_sections": ["## Objetivo", "## Pasos", "## Criterios"],
        "type": "procedure",
        "required_keys": [],
        "actionable": True,
        "coverage_keywords": [
            "entrada", "input", "requisito", "precondición", "antes de", "necesitas"
        ]
    },
    "checklist_md": {
        "id": "checklist_md",
        "name": "Checklist (Markdown)",
        "requires_json": False,
        "markdown_sections": ["## Checklist"],
        "type": "checklist",
        "required_keys": [],
        "actionable": True,
        "coverage_keywords": ["validar", "verificar", "probar", "test", "casos", "edge", "límite"]
    },
    "example_md": {
        "id": "example_md",
        "name": "Example (Markdown)",
        "requires_json": False,
        "markdown_sections": [],
        "type": "example",
        "required_keys": [],
        "actionable": False,
        "coverage_keywords": []
    }
}


# ============================================================================
# v0.1 Gates (Format + Completeness) - HARD FAIL
# ============================================================================

def gate1_expected_format(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.1 Gate 1: Formato Esperado

    Checks if output matches expected format (JSON or markdown sections).
    """
    if template.requires_json:
        # JSON template: must parse as JSON
        try:
            parsed = json.loads(output)
            # Check if it's non-empty
            if not parsed or len(str(parsed)) == 0:
                return GateResult(
                    gate_id="v0.1_gate1_format",
                    gate_version="0.1",
                    status=GateSeverity.FAIL,
                    details={"reason": "JSON is empty or null"}
                )
            return GateResult(
                gate_id="v0.1_gate1_format",
                gate_version="0.1",
                status=GateSeverity.PASS,
                details={"format": "json", "parsed": True}
            )
        except json.JSONDecodeError as e:
            return GateResult(
                gate_id="v0.1_gate1_format",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Invalid JSON", "error": str(e)}
            )
    else:
        # Markdown template: must have required sections
        if not template.markdown_sections:
            return GateResult(
                gate_id="v0.1_gate1_format",
                gate_version="0.1",
                status=GateSeverity.PASS,  # No sections required
                details={"format": "markdown", "sections_required": False}
            )

        output_lower = output.lower()
        missing_sections = [
            section for section in template.markdown_sections
            if section.lower() not in output_lower
        ]

        if missing_sections:
            return GateResult(
                gate_id="v0.1_gate1_format",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={
                    "format": "markdown",
                    "missing_sections": missing_sections
                }
            )

        return GateResult(
            gate_id="v0.1_gate1_format",
            gate_version="0.1",
            status=GateSeverity.PASS,
            details={"format": "markdown", "all_sections_present": True}
        )


def gate2_min_completeness(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.1 Gate 2: Completitud Mínima

    Checks if output meets minimum completeness requirements based on template type.
    """
    if template.type == "json":
        # JSON: must have at least 2 keys
        try:
            parsed = json.loads(output)
            key_count: int | str  # Initialize before conditional
            if isinstance(parsed, dict):
                key_count = len(parsed)
                if key_count < 2:
                    return GateResult(
                        gate_id="v0.1_gate2_completeness",
                        gate_version="0.1",
                        status=GateSeverity.FAIL,
                        details={"reason": "JSON has <2 keys", "key_count": key_count}
                    )
            else:
                key_count = "N/A"
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.PASS,
                details={"key_count": key_count}
            )
        except json.JSONDecodeError:
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Invalid JSON"}
            )

    elif template.type == "procedure":
        # Procedure: must have >=2 numbered steps
        steps = len(re.findall(r'^\s*\d+\.\s+', output, re.MULTILINE))
        if steps < 2:
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Procedure has <2 steps", "step_count": steps}
            )
        return GateResult(
            gate_id="v0.1_gate2_completeness",
            gate_version="0.1",
            status=GateSeverity.PASS,
            details={"step_count": steps}
        )

    elif template.type == "checklist":
        # Checklist: must have >=3 bullets
        bullets = len(re.findall(r'^\s*[-*]\s+', output, re.MULTILINE))
        if bullets < 3:
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Checklist has <3 bullets", "bullet_count": bullets}
            )
        return GateResult(
            gate_id="v0.1_gate2_completeness",
            gate_version="0.1",
            status=GateSeverity.PASS,
            details={"bullet_count": bullets}
        )

    elif template.type == "example":
        # Example: must have code block
        if '```' not in output:
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Example has no code block"}
            )
        return GateResult(
            gate_id="v0.1_gate2_completeness",
            gate_version="0.1",
            status=GateSeverity.PASS,
            details={"has_code_block": True}
        )

    else:
        # Fallback: check minimum length
        if len(output.strip()) < 100:
            return GateResult(
                gate_id="v0.1_gate2_completeness",
                gate_version="0.1",
                status=GateSeverity.FAIL,
                details={"reason": "Output too short", "length": len(output.strip())}
            )
        return GateResult(
            gate_id="v0.1_gate2_completeness",
            gate_version="0.1",
            status=GateSeverity.PASS,
            details={"length": len(output.strip())}
        )


# ============================================================================
# v0.2 Gates (Starter Set) - WARN initially
# ============================================================================

def gate_a1_filler_detector(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate A1: Placeholder / Filler Detector

    Detects "TBD", "lorem", "insert here", "TODO", "N/A" as main content.
    """
    output_lower = output.lower()
    filler_count = sum(1 for token in FILLER_TOKENS if token in output_lower)

    # Calculate content density (alphanumeric ratio)
    alnum_chars = len(re.findall(r'[a-z0-9]', output_lower))
    content_density = alnum_chars / len(output) if output else 0

    # FAIL if: 2+ fillers OR 1 filler with low content density
    fail = (
        filler_count >= thresholds.A1_MAX_FILLER_COUNT or
        (filler_count == 1 and content_density < thresholds.A1_CONTENT_DENSITY_THRESHOLD)
    )

    return GateResult(
        gate_id="A1_filler_detector",
        gate_version="0.2",
        status=GateSeverity.FAIL if fail else GateSeverity.PASS,
        score=1.0 - (filler_count / max(1, len(output_lower.split()))),
        details={
            "filler_count": filler_count,
            "content_density": round(content_density, 3),
            "fillers_found": [t for t in FILLER_TOKENS if t in output_lower]
        }
    )


def gate_a4_repetition_detector(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate A4: Repetition / Tautology

    Detects "- Item - Item - Item" or repeated steps.
    """
    lines = [line.strip().lower() for line in output.split('\n') if line.strip()]

    if len(lines) < thresholds.A4_MIN_LINE_COUNT:
        return GateResult(
            gate_id="A4_repetition_detector",
            gate_version="0.2",
            status=GateSeverity.SKIP,  # Too few lines to check
            details={"reason": "Not enough lines", "line_count": len(lines)}
        )

    # Remove punctuation and normalize
    normalized = [re.sub(r'[^\w\s]', '', line) for line in lines]

    # Count duplicates
    unique = set(normalized)
    duplicate_ratio = 1 - (len(unique) / len(normalized)) if normalized else 0

    fail = duplicate_ratio > thresholds.A4_DUPLICATE_RATIO_THRESHOLD

    return GateResult(
        gate_id="A4_repetition_detector",
        gate_version="0.2",
        status=GateSeverity.FAIL if fail else GateSeverity.PASS,
        score=1.0 - duplicate_ratio,
        details={
            "duplicate_ratio": round(duplicate_ratio, 3),
            "line_count": len(lines),
            "unique_lines": len(unique)
        }
    )


def gate_j1_empty_value_ratio(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate J1: Empty-Value Ratio

    Detects valid JSON but with empty values.
    """
    if not template.requires_json:
        return GateResult(
            gate_id="J1_empty_value_ratio",
            gate_version="0.2",
            status=GateSeverity.SKIP,
            details={"reason": "Not a JSON template"}
        )

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return GateResult(
            gate_id="J1_empty_value_ratio",
            gate_version="0.2",
            status=GateSeverity.FAIL,
            details={"error": "invalid_json"}
        )

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
    empty_ratio = empty / total if total > 0 else 1.0

    # Check required keys
    missing_required = []
    if isinstance(data, dict):
        for key in template.required_keys:
            if key not in data or not data[key]:
                missing_required.append(key)

    fail = empty_ratio > thresholds.J1_MAX_EMPTY_RATIO or len(missing_required) > 0

    return GateResult(
        gate_id="J1_empty_value_ratio",
        gate_version="0.2",
        status=GateSeverity.FAIL if fail else GateSeverity.PASS,
        score=1.0 - empty_ratio,
        details={
            "empty_ratio": round(empty_ratio, 3),
            "empty_count": empty,
            "total_count": total,
            "missing_required": missing_required
        }
    )


def gate_p1_real_step_content(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate P1: Real Step Content

    Detects numbered steps but empty/generic ("1. TBD").
    """
    if template.type != "procedure":
        return GateResult(
            gate_id="P1_real_step_content",
            gate_version="0.2",
            status=GateSeverity.SKIP,
            details={"reason": "Not a procedure template"}
        )

    # Extract numbered steps
    steps = re.findall(r'^\s*\d+\.\s+(.+)$', output, re.MULTILINE)

    if not steps:
        return GateResult(
            gate_id="P1_real_step_content",
            gate_version="0.2",
            status=GateSeverity.FAIL,
            details={"reason": "No numbered steps found"}
        )

    # Check each step for non-trivial content
    empty_steps = 0

    for step in steps:
        step_lower = step.lower()
        # Count non-trivial tokens (length >= 4)
        words = re.findall(r'\b[a-z]{4,}\b', step_lower)
        # Check for action verbs
        has_verb = any(verb in step_lower for verb in ACTION_VERBS)

        if len(words) < thresholds.P1_MIN_NON_TRIVIAL_TOKENS or not has_verb:
            empty_steps += 1

    empty_ratio = empty_steps / len(steps)
    fail = empty_ratio > thresholds.P1_MAX_EMPTY_STEP_RATIO

    return GateResult(
        gate_id="P1_real_step_content",
        gate_version="0.2",
        status=GateSeverity.FAIL if fail else GateSeverity.PASS,
        score=1.0 - empty_ratio,
        details={
            "empty_ratio": round(empty_ratio, 3),
            "empty_steps": empty_steps,
            "step_count": len(steps)
        }
    )


def gate_c1_bullet_specificity(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate C1: Bullet Specificity

    Detects generic bullets ("Item", "Check", "Do it").
    """
    if template.type != "checklist":
        return GateResult(
            gate_id="C1_bullet_specificity",
            gate_version="0.2",
            status=GateSeverity.SKIP,
            details={"reason": "Not a checklist template"}
        )

    # Extract bullets
    bullets = re.findall(r'^\s*[-*]\s+(.+)$', output, re.MULTILINE)

    if not bullets:
        return GateResult(
            gate_id="C1_bullet_specificity",
            gate_version="0.2",
            status=GateSeverity.FAIL,
            details={"reason": "No bullets found"}
        )

    generic_bullets = 0

    for bullet in bullets:
        # Check for non-trivial content
        words = re.findall(r'\b[a-z]{4,}\b', bullet.lower())
        # Check for concrete object (colon-separated OR technical term)
        has_structure = ':' in bullet or TECHNICAL_TERMS_PATTERN.search(bullet)

        if len(words) < thresholds.C1_MIN_NON_TRIVIAL_TOKENS or not has_structure:
            generic_bullets += 1

    generic_ratio = generic_bullets / len(bullets)
    fail = generic_ratio > thresholds.C1_MAX_GENERIC_RATIO

    return GateResult(
        gate_id="C1_bullet_specificity",
        gate_version="0.2",
        status=GateSeverity.FAIL if fail else GateSeverity.PASS,
        score=1.0 - generic_ratio,
        details={
            "generic_ratio": round(generic_ratio, 3),
            "generic_bullets": generic_bullets,
            "bullet_count": len(bullets)
        }
    )


def gate_e1_non_trivial_code(
    output: str, template: TemplateSpec, thresholds: GateThresholds
) -> GateResult:
    """
    v0.2 Gate E1: Code Fence + Non-Trivial Code

    Detects code blocks that are empty or just comments.
    """
    if template.type != "example":
        return GateResult(
            gate_id="E1_non_trivial_code",
            gate_version="0.2",
            status=GateSeverity.SKIP,
            details={"reason": "Not an example template"}
        )

    # Extract code blocks
    code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', output, re.DOTALL)

    if not code_blocks:
        return GateResult(
            gate_id="E1_non_trivial_code",
            gate_version="0.2",
            status=GateSeverity.FAIL,
            details={"reason": "No code blocks found"}
        )

    total_code_lines = 0  # Track total across all blocks
    for block in code_blocks:
        lines = [
            line for line in block.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        total_code_lines += len(lines)

        # Check for minimum non-comment lines
        if len(lines) < thresholds.E1_MIN_CODE_LINES:
            return GateResult(
                gate_id="E1_non_trivial_code",
                gate_version="0.2",
                status=GateSeverity.FAIL,
                details={
                    "reason": "Code block too short",
                    "code_lines": len(lines)
                }
            )

        # Check for code-like constructs
        if not CODE_INDICATORS_PATTERN.search(block):
            return GateResult(
                gate_id="E1_non_trivial_code",
                gate_version="0.2",
                status=GateSeverity.FAIL,
                details={"reason": "No code constructs found"}
            )

    return GateResult(
        gate_id="E1_non_trivial_code",
        gate_version="0.2",
        status=GateSeverity.PASS,
        score=1.0,  # Code is good
        details={
            "code_blocks": len(code_blocks),
            "code_lines": total_code_lines
        }
    )


# ============================================================================
# Main Evaluation Function
# ============================================================================

def evaluate_output(
    output_text: str,
    template_id: str,
    template_spec: dict[str, Any] | None = None,
    thresholds: GateThresholds | None = None
) -> GateReport:
    """
    Evaluate output against v0.1 + v0.2 gates.

    Args:
        output_text: The output to evaluate
        template_id: Template identifier (json, procedure_md, checklist_md, example_md)
        template_spec: Optional template dict from templates.json
        thresholds: Optional threshold overrides

    Returns:
        GateReport with complete evaluation results
    """
    if thresholds is None:
        thresholds = GateThresholds()

    # Load template spec
    if template_spec:
        template = TemplateSpec.from_dict(template_id, template_spec)
    else:
        template = TemplateSpec.from_dict(template_id, DEFAULT_TEMPLATES.get(template_id, {}))

    # Initialize report
    report = GateReport(
        template_id=template_id,
        output_length=len(output_text)
    )

    # ============================================================================
    # Phase 1: v0.1 Gates (Format + Completeness) - HARD FAIL
    # ============================================================================

    report.v0_1_gates["gate1_format"] = gate1_expected_format(
        output_text, template, thresholds
    )
    report.v0_1_gates["gate2_completeness"] = gate2_min_completeness(
        output_text, template, thresholds
    )

    # Early exit if v0.1 fails
    if not report.v0_1_pass:
        return report

    # ============================================================================
    # Phase 2: v0.2 Gates (Starter Set) - WARN initially
    # ============================================================================

    # Core gates
    report.v0_2_gates["A1_filler"] = gate_a1_filler_detector(
        output_text, template, thresholds
    )
    report.v0_2_gates["A4_repetition"] = gate_a4_repetition_detector(
        output_text, template, thresholds
    )

    # JSON gates
    if template.requires_json:
        report.v0_2_gates["J1_empty"] = gate_j1_empty_value_ratio(output_text, template, thresholds)

    # Procedure gates
    if template.type == "procedure":
        report.v0_2_gates["P1_steps"] = gate_p1_real_step_content(
            output_text, template, thresholds
        )

    # Checklist gates
    if template.type == "checklist":
        report.v0_2_gates["C1_specific"] = gate_c1_bullet_specificity(
            output_text, template, thresholds
        )

    # Example gates
    if template.type == "example":
        report.v0_2_gates["E1_code"] = gate_e1_non_trivial_code(output_text, template, thresholds)

    # Apply severity overrides from GATE_CONFIG
    for gate_id, gate_result in report.v0_2_gates.items():
        if gate_id in GATE_CONFIG:
            config = GATE_CONFIG[gate_id]
            configured_severity = config.get_severity(template_id)

            # Override status based on configuration
            if gate_result.status != GateSeverity.SKIP:
                is_warn = configured_severity == GateSeverity.WARN
                is_fail = configured_severity == GateSeverity.FAIL
                if is_warn and gate_result.status == GateSeverity.FAIL:
                    gate_result.status = GateSeverity.WARN
                elif is_fail and gate_result.status != GateSeverity.PASS:
                    gate_result.status = GateSeverity.FAIL

    # Populate summary
    report.summary = {
        "v0.1_pass": report.v0_1_pass,
        "v0.2_fail_count": report.v0_2_fail_count,
        "v0.2_warn_count": report.v0_2_warn_count,
        "overall_pass": report.overall_pass
    }

    return report


# ============================================================================
# Helper Functions
# ============================================================================

def get_template_summary(report: GateReport) -> str:
    """
    Get human-readable summary of gate failures.

    Returns a single line describing the main issue.
    """
    if not report.v0_1_pass:
        # v0.1 failed - check which gate
        for gate_id, result in report.v0_1_gates.items():
            if result.status == GateSeverity.FAIL:
                if gate_id == "v0.1_gate1_format":
                    return "Formato inválido"
                elif gate_id == "v0.1_gate2_completeness":
                    return "Contenido incompleto"
        return "Error de formato"

    # v0.2 warnings/failures
    if report.v0_2_fail_count > 0:
        for gate_id, result in report.v0_2_gates.items():
            if result.status == GateSeverity.FAIL:
                if gate_id == "A1_filler":
                    return "Contiene placeholders (TODO, TBD, etc.)"
                elif gate_id == "A4_repetition":
                    return "Contenido repetitivo"
                elif gate_id == "J1_empty":
                    return "Valores vacíos en JSON"
                elif gate_id == "P1_steps":
                    return "Pasos genéricos o vacíos"
                elif gate_id == "C1_specific":
                    return "Bullets demasiado genéricos"
                elif gate_id == "E1_code":
                    return "Código insuficiente"

    if report.v0_2_warn_count > 0:
        for gate_id, result in report.v0_2_gates.items():
            if result.status == GateSeverity.WARN:
                if gate_id == "A1_filler":
                    return "Posibles placeholders detectados"
                elif gate_id == "A4_repetition":
                    return "Algo de repetición detectada"
                elif gate_id == "J1_empty":
                    return "Algunos valores vacíos"
                elif gate_id == "P1_steps":
                    return "Algunos pasos podrían ser más específicos"
                elif gate_id == "C1_specific":
                    return "Algunos bullets podrían ser más específicos"
                elif gate_id == "E1_code":
                    return "Código podría ser más robusto"

    return "Output válido"
