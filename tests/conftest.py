"""pytest automagics"""

from __future__ import annotations

import logging
from typing import Any, Literal

from libadvian.logging import init_logging
from cloudcoil.resources import Resource

init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class FakeCache[T: Resource]:
    """In-memory stand-in for an informer snapshot."""

    def __init__(self, objects: dict[str, T] | None = None) -> None:
        self._objects = objects or {}

    def get(self, name: str, namespace: str | None = None) -> T | None:
        _ = namespace
        return self._objects.get(name)

    def list(self, namespace: str | None = None, *, all_namespaces: bool = False) -> list[T]:
        _ = namespace, all_namespaces
        return list(self._objects.values())


class FakeContext:
    """Narrow test double for Context status and cache operations."""

    def __init__(self, caches: dict[type[Resource], FakeCache[Resource]] | None = None) -> None:
        self._caches = caches or {}
        self.status: dict[str, Any] = {}
        self.conditions: list[tuple[str, bool | Literal["Unknown"], str, str]] = []

    def cached[U: Resource](self, resource: type[U]) -> FakeCache[U]:
        cache = self._caches.get(resource)
        if cache is None:
            return FakeCache[U]()
        return cache  # type: ignore[return-value]

    def set_status(self, **changes: object) -> None:
        self.status.update(changes)

    def condition(self, name: str, status: bool | Literal["Unknown"], *, reason: str, message: str = "") -> None:
        self.conditions.append((name, status, reason, message))
