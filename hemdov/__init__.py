"""
HemDov - Domain Driven Architecture for DSPy Applications.

This package provides a clean, modular architecture for DSPy-based applications.
"""

from hemdov.infrastructure.config import settings, Settings
from hemdov.interfaces import container

__all__ = ["settings", "Settings", "container"]
