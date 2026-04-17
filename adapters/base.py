"""
Universal adapter base protocols.
Adapters bridge runtimes, frameworks, external systems, tools/actions,
media/sensor/event sources, and enterprise connectors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable


AdapterKind = str  # "runtime" | "framework" | "external_system" | "tool_action" | "media_sensor" | "enterprise_connector"
AdapterMaturity = str  # "first_class" | "bounded_prototype" | "structural_only"


@dataclass(frozen=True)
class AdapterMetadata:
    adapter_id: str
    adapter_kind: AdapterKind
    lane_ids: list[str]
    capabilities: list[str]
    maturity: AdapterMaturity
    version: str = "1.0.0"
    description: str = ""
    validated: bool = False
    validation_notes: list[str] = field(default_factory=list)
    compatibility_constraints: dict[str, list[str]] = field(default_factory=dict)


@runtime_checkable
class AdapterBase(Protocol):
    """Protocol all adapters must conform to."""

    @property
    def metadata(self) -> AdapterMetadata: ...

    def adapt(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def validate(self) -> dict[str, Any]: ...


class BaseAdapter:
    """Concrete base class providing default adapter behaviour."""

    def __init__(self, metadata: AdapterMetadata) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> AdapterMetadata:
        return self._metadata

    def adapt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "adapted",
            "adapter_id": self._metadata.adapter_id,
            "adapter_kind": self._metadata.adapter_kind,
            "payload": payload,
        }

    def validate(self) -> dict[str, Any]:
        issues = []
        if not self._metadata.adapter_id:
            issues.append("adapter_id is required")
        if not self._metadata.adapter_kind:
            issues.append("adapter_kind is required")
        if not self._metadata.lane_ids:
            issues.append("at least one lane_id is required")
        if not self._metadata.capabilities:
            issues.append("at least one capability is required")
        return {
            "adapter_id": self._metadata.adapter_id,
            "valid": len(issues) == 0,
            "maturity": self._metadata.maturity,
            "validated": self._metadata.validated,
            "issues": issues,
        }
