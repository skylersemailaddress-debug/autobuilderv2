from __future__ import annotations

from self_extend.trust_registry import TrustRegistry


_registry = TrustRegistry()


def register_extension(name: str, provenance: str) -> None:
    _registry.register(name, "quarantined", provenance)


def promote_extension(name: str) -> None:
    _registry.promote(name)


def quarantine_extension(name: str) -> None:
    _registry.quarantine(name)


def rollback_extension(name: str) -> None:
    _registry.rollback(name)


def get_status(name: str):
    return _registry.get(name)
