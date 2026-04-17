"""
Tests for the universal adapter architecture:
registry management, capability-aware resolution, validation.
"""
import pytest
from adapters.registry import (
    get_adapter_registry,
    BUILTIN_ADAPTERS,
    GLOBAL_ADAPTER_REGISTRY,
)
from adapters.base import AdapterMetadata, BaseAdapter, AdapterBase


# ---------------------------------------------------------------------------
# Registry basics
# ---------------------------------------------------------------------------

def test_registry_populated():
    registry = get_adapter_registry()
    catalog = registry.catalog()
    assert catalog["adapter_count"] > 0
    assert len(catalog["adapters"]) > 0


def test_registry_has_all_kinds():
    registry = get_adapter_registry()
    catalog = registry.catalog()
    kinds = set(catalog["kinds"])
    assert "runtime" in kinds
    assert "framework" in kinds
    assert "enterprise_connector" in kinds
    assert "tool_action" in kinds
    assert "media_sensor" in kinds


def test_registry_all_adapters_validated():
    registry = get_adapter_registry()
    for adapter in BUILTIN_ADAPTERS:
        result = adapter.validate()
        assert result["valid"], f"Adapter {adapter.metadata.adapter_id} failed: {result['issues']}"


# ---------------------------------------------------------------------------
# Adapter resolution by lane
# ---------------------------------------------------------------------------

def test_resolve_for_realtime_lane():
    registry = get_adapter_registry()
    adapters = registry.resolve_for_lane("first_class_realtime")
    assert len(adapters) > 0
    ids = [a.metadata.adapter_id for a in adapters]
    assert "websocket_runtime_adapter" in ids


def test_resolve_for_mobile_lane():
    registry = get_adapter_registry()
    adapters = registry.resolve_for_lane("first_class_mobile")
    assert len(adapters) > 0
    ids = [a.metadata.adapter_id for a in adapters]
    assert "flutter_runtime_adapter" in ids


def test_resolve_for_game_lane():
    registry = get_adapter_registry()
    adapters = registry.resolve_for_lane("first_class_game")
    ids = [a.metadata.adapter_id for a in adapters]
    assert "godot_runtime_adapter" in ids


def test_resolve_for_enterprise_lane():
    registry = get_adapter_registry()
    adapters = registry.resolve_for_lane("first_class_enterprise_agent")
    ids = [a.metadata.adapter_id for a in adapters]
    assert any("agent" in i or "enterprise" in i or "openai" in i for i in ids)


# ---------------------------------------------------------------------------
# Capability-aware resolution
# ---------------------------------------------------------------------------

def test_resolve_by_capability_billing():
    registry = get_adapter_registry()
    adapters = registry.list_by_capability("billing")
    assert len(adapters) > 0
    ids = [a.metadata.adapter_id for a in adapters]
    assert "stripe_connector" in ids


def test_resolve_by_capability_sensor():
    registry = get_adapter_registry()
    adapters = registry.list_by_capability("sensor_ingestion")
    assert len(adapters) > 0
    ids = [a.metadata.adapter_id for a in adapters]
    assert "sensor_event_adapter" in ids


def test_resolve_by_capability_approval_gate():
    registry = get_adapter_registry()
    adapters = registry.list_by_capability("approval_gates")
    assert len(adapters) > 0


def test_resolve_by_kind_runtime():
    registry = get_adapter_registry()
    runtimes = registry.list_by_kind("runtime")
    assert len(runtimes) >= 4
    ids = [a.metadata.adapter_id for a in runtimes]
    assert "fastapi_runtime_adapter" in ids
    assert "nextjs_runtime_adapter" in ids


# ---------------------------------------------------------------------------
# Adapter adapt() behavior
# ---------------------------------------------------------------------------

def test_adapter_adapt_returns_adapted():
    registry = get_adapter_registry()
    adapter = registry.get("fastapi_runtime_adapter")
    assert adapter is not None
    result = adapter.adapt({"test": "payload"})
    assert result["status"] == "adapted"
    assert result["adapter_id"] == "fastapi_runtime_adapter"
    assert result["payload"] == {"test": "payload"}


# ---------------------------------------------------------------------------
# Registry registration validation
# ---------------------------------------------------------------------------

def test_invalid_adapter_rejected():
    from adapters.registry import AdapterRegistry
    registry = AdapterRegistry()
    bad = BaseAdapter(AdapterMetadata(
        adapter_id="",  # invalid
        adapter_kind="runtime",
        lane_ids=[],
        capabilities=[],
        maturity="first_class",
    ))
    with pytest.raises(ValueError):
        registry.register(bad)


def test_catalog_structure():
    registry = get_adapter_registry()
    catalog = registry.catalog()
    assert "adapter_count" in catalog
    assert "kinds" in catalog
    assert "adapters" in catalog
    for entry in catalog["adapters"]:
        assert "adapter_id" in entry
        assert "kind" in entry
        assert "maturity" in entry
        assert "validated" in entry
