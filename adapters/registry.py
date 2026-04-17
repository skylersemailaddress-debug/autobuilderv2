"""
Adapter registry: capability-aware, validated, registry-managed.
"""
from __future__ import annotations

from typing import Any, Optional
from adapters.base import AdapterBase, AdapterMetadata, AdapterKind


class AdapterRegistry:
    """Registry for all adapter kinds with capability-aware resolution."""

    def __init__(self) -> None:
        self._adapters: dict[str, AdapterBase] = {}

    def register(self, adapter: AdapterBase) -> None:
        validation = adapter.validate()
        if not validation.get("valid"):
            raise ValueError(
                f"Adapter {adapter.metadata.adapter_id} failed validation: {validation['issues']}"
            )
        self._adapters[adapter.metadata.adapter_id] = adapter

    def get(self, adapter_id: str) -> Optional[AdapterBase]:
        return self._adapters.get(adapter_id)

    def list_by_kind(self, kind: AdapterKind) -> list[AdapterBase]:
        return [a for a in self._adapters.values() if a.metadata.adapter_kind == kind]

    def list_by_lane(self, lane_id: str) -> list[AdapterBase]:
        return [a for a in self._adapters.values() if lane_id in a.metadata.lane_ids]

    def list_by_capability(self, capability: str) -> list[AdapterBase]:
        return [a for a in self._adapters.values() if capability in a.metadata.capabilities]

    def resolve_for_lane(
        self,
        lane_id: str,
        required_capabilities: Optional[list[str]] = None,
    ) -> list[AdapterBase]:
        """Return validated adapters for a lane with optional capability filter."""
        candidates = self.list_by_lane(lane_id)
        if required_capabilities:
            candidates = [
                a for a in candidates
                if all(cap in a.metadata.capabilities for cap in required_capabilities)
            ]
        return [a for a in candidates if a.metadata.validated]

    def catalog(self) -> dict[str, Any]:
        return {
            "adapter_count": len(self._adapters),
            "kinds": sorted({a.metadata.adapter_kind for a in self._adapters.values()}),
            "adapters": [
                {
                    "adapter_id": a.metadata.adapter_id,
                    "kind": a.metadata.adapter_kind,
                    "maturity": a.metadata.maturity,
                    "validated": a.metadata.validated,
                    "lanes": a.metadata.lane_ids,
                    "capabilities": a.metadata.capabilities,
                }
                for a in sorted(self._adapters.values(), key=lambda x: x.metadata.adapter_id)
            ],
        }


# ---------------------------------------------------------------------------
# Built-in adapter definitions
# ---------------------------------------------------------------------------

from adapters.base import BaseAdapter


def _make(
    adapter_id: str,
    kind: AdapterKind,
    lanes: list[str],
    capabilities: list[str],
    maturity: str = "bounded_prototype",
    description: str = "",
    validated: bool = True,
) -> BaseAdapter:
    return BaseAdapter(
        AdapterMetadata(
            adapter_id=adapter_id,
            adapter_kind=kind,
            lane_ids=lanes,
            capabilities=capabilities,
            maturity=maturity,
            description=description,
            validated=validated,
        )
    )


ALL_LANES = [
    "first_class_commercial",
    "first_class_mobile",
    "first_class_game",
    "first_class_realtime",
    "first_class_enterprise_agent",
]

BUILTIN_ADAPTERS: list[BaseAdapter] = [
    # Runtime adapters
    _make("fastapi_runtime_adapter", "runtime", ALL_LANES, ["http_api", "async_support", "openapi"], "first_class", "FastAPI ASGI runtime"),
    _make("nextjs_runtime_adapter", "runtime", ["first_class_commercial", "first_class_enterprise_agent"], ["ssr_rendering", "static_export", "api_routes"], "first_class", "Next.js SSR runtime"),
    _make("flutter_runtime_adapter", "runtime", ["first_class_mobile"], ["cross_platform_mobile", "offline_mode", "platform_channels"], "first_class", "Flutter mobile runtime"),
    _make("godot_runtime_adapter", "runtime", ["first_class_game"], ["game_loop", "scene_management", "physics_2d_3d"], "first_class", "Godot game runtime"),
    _make("websocket_runtime_adapter", "runtime", ["first_class_realtime"], ["realtime_channels", "event_streaming", "pub_sub"], "first_class", "WebSocket realtime runtime"),
    # Framework adapters
    _make("postgres_framework_adapter", "framework", ALL_LANES, ["relational_db", "migrations", "connection_pooling"], "first_class", "PostgreSQL data framework"),
    _make("docker_compose_framework_adapter", "framework", ALL_LANES, ["container_orchestration", "local_dev", "env_config"], "first_class", "Docker Compose deployment"),
    # External system connectors
    _make("stripe_connector", "enterprise_connector", ["first_class_commercial", "first_class_enterprise_agent"], ["billing", "subscriptions", "webhooks", "payment_intents"], "bounded_prototype", "Stripe billing connector"),
    _make("sendgrid_connector", "enterprise_connector", ALL_LANES, ["transactional_email", "templates", "delivery_tracking"], "bounded_prototype", "SendGrid email connector"),
    _make("s3_connector", "enterprise_connector", ALL_LANES, ["object_storage", "presigned_urls", "lifecycle_policies"], "bounded_prototype", "AWS S3 storage connector"),
    _make("openai_connector", "enterprise_connector", ["first_class_commercial", "first_class_enterprise_agent"], ["llm_inference", "embeddings", "function_calling"], "bounded_prototype", "OpenAI API connector"),
    # Tool/action adapters
    _make("webhook_tool_adapter", "tool_action", ALL_LANES, ["outbound_webhooks", "event_dispatch", "retry_logic"], "bounded_prototype", "Generic webhook dispatcher"),
    _make("approval_gate_adapter", "tool_action", ALL_LANES, ["approval_gates", "human_in_the_loop", "escalation"], "first_class", "Approval gate action adapter"),
    # Media/sensor adapters
    _make("image_document_adapter", "media_sensor", ALL_LANES, ["image_reference", "document_reference", "media_normalization"], "structural_only", "Image/document media adapter"),
    _make("audio_adapter", "media_sensor", ["first_class_mobile", "first_class_enterprise_agent"], ["audio_reference", "transcription_contract"], "structural_only", "Audio media adapter"),
    _make("sensor_event_adapter", "media_sensor", ["first_class_realtime"], ["sensor_ingestion", "event_stream_normalization", "world_state_updates"], "structural_only", "Sensor/event stream adapter"),
    # Enterprise connectors
    _make("ldap_sso_connector", "enterprise_connector", ["first_class_enterprise_agent", "first_class_commercial"], ["sso", "ldap_auth", "enterprise_identity"], "bounded_prototype", "Enterprise LDAP/SSO connector"),
    _make("audit_log_connector", "enterprise_connector", ALL_LANES, ["immutable_audit_log", "compliance_stream", "pii_redaction"], "first_class", "Audit log enterprise connector"),
]


GLOBAL_ADAPTER_REGISTRY = AdapterRegistry()


def _bootstrap_registry() -> None:
    for adapter in BUILTIN_ADAPTERS:
        try:
            GLOBAL_ADAPTER_REGISTRY.register(adapter)
        except ValueError:
            pass  # Skip invalid during bootstrap


_bootstrap_registry()


def get_adapter_registry() -> AdapterRegistry:
    return GLOBAL_ADAPTER_REGISTRY
