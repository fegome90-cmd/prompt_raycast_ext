from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Domain(str, Enum):
    """Domain categories for legacy prompts"""

    SOFTDEV = "softdev"  # Software Development & Architecture
    SECURITY = "security"  # Security & Infrastructure
    PRODUCTIVITY = "productivity"  # Productivity & Workflow Automation
    AIML = "aiml"  # AI/ML Engineering & Memory Systems
    OTHER = "other"  # Uncategorized


class FileMetadata(BaseModel):
    """Metadata extracted from legacy prompt files"""

    version: Optional[str] = None
    date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class File(BaseModel):
    """Represents a legacy prompt file with metadata"""

    path: str
    domain: Domain
    category: str  # e.g., "codemachine-agent", "sprint-prompt"
    size_tokens: int
    metadata: FileMetadata = Field(default_factory=FileMetadata)


class Component(BaseModel):
    """Extracted component from a legacy prompt"""

    source_file: str
    domain: Domain
    role: str
    directive: str
    framework: str  # "Chain-of-Thought", "Tree-of-Thoughts", etc.
    guardrails: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)  # Confidence score 0-1


class FileManifest(BaseModel):
    """Manifest of all scanned files"""

    files: list[File] = Field(default_factory=list)
    total_scanned: int = 0

    @staticmethod
    def _initial_domain_counts() -> dict[Domain, int]:
        """Initialize all domain counts to 0"""
        return {domain: 0 for domain in Domain}

    total_by_domain: dict[Domain, int] = Field(
        default_factory=lambda: {domain: 0 for domain in Domain}
    )


class ComponentCatalog(BaseModel):
    """Catalog of extracted components"""

    components: list[Component] = Field(default_factory=list)
    total_components: int = 0
    avg_confidence: float = 0.0
