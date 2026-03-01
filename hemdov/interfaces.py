"""
HemDov Dependency Injection Container

Simple container for managing dependencies like Settings.
"""

from asyncio import iscoroutinefunction
from collections.abc import Callable
from typing import Any, TypeVar

from hemdov.infrastructure.config import settings

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: dict[type, Any] = {}
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}
        self._cleanup_hooks: list[Callable] = []

    def register(self, interface: type[T], implementation: T) -> None:
        """Register a service implementation."""
        self._services[interface] = implementation

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register factory function for lazy initialization."""
        self._factories[interface] = factory

    def get(self, interface: type[T]) -> T:
        """Get service, instantiating from factory if needed."""
        # Check services
        if interface in self._services:
            return self._services[interface]

        # Check singletons
        if interface in self._singletons:
            return self._singletons[interface]

        # Check factories - lazy initialization
        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance
            del self._factories[interface]  # Remove after use
            return instance

        # Create default Settings
        if interface is settings.__class__:
            if interface not in self._singletons:
                self._singletons[interface] = settings
            return self._singletons[interface]

        raise ValueError(f"No service registered for {interface}")

    def add_cleanup_hook(self, hook: Callable) -> None:
        """Register a cleanup hook for shutdown."""
        self._cleanup_hooks.append(hook)

    async def shutdown(self):
        """Cleanup resources on application shutdown."""
        for hook in reversed(self._cleanup_hooks):
            if iscoroutinefunction(hook):
                await hook()
            else:
                hook()


# Global container instance
container = Container()

# Register default services
container.register(settings.__class__, settings)
