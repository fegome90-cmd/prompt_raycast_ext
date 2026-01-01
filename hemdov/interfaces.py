"""
HemDov Dependency Injection Container

Simple container for managing dependencies like Settings.
"""

from typing import Dict, Type, TypeVar, Any
from hemdov.infrastructure.config import settings

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type[T], implementation: T):
        """Register a service implementation."""
        self._services[interface] = implementation

    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        # Check if we have a registered service
        if interface in self._services:
            return self._services[interface]

        # Check for singleton instances
        if interface in self._singletons:
            return self._singletons[interface]

        # Create default instances for known types
        if interface is settings.__class__:
            if settings.__class__ not in self._singletons:
                self._singletons[settings.__class__] = settings
            return self._singletons[settings.__class__]

        raise ValueError(f"No service registered for {interface}")


# Global container instance
container = Container()

# Register default services
container.register(settings.__class__, settings)
