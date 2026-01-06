"""
HemDov Dependency Injection Container

Simple container for managing dependencies like Settings.
"""

from typing import Callable, Dict, List, Type, TypeVar, Any
from asyncio import iscoroutinefunction
from hemdov.infrastructure.config import settings

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._cleanup_hooks: List[Callable] = []

    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a service implementation."""
        self._services[interface] = implementation

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register factory function for lazy initialization."""
        self._factories[interface] = factory

    def get(self, interface: Type[T]) -> T:
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
