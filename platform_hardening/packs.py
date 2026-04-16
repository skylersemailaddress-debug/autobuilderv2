from __future__ import annotations

from dataclasses import asdict, dataclass


PackType = str


@dataclass(frozen=True)
class PackDefinition:
    pack_id: str
    pack_type: PackType
    lane_id: str
    version: str
    capabilities: list[str]
    metadata: dict[str, object]
    priority: int = 100

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PackRegistry:
    def __init__(self) -> None:
        self._packs: dict[str, PackDefinition] = {}

    def register(self, pack: PackDefinition) -> None:
        self._packs[pack.pack_id] = pack

    def list_packs(self, lane_id: str | None = None, pack_type: str | None = None) -> list[PackDefinition]:
        items = list(self._packs.values())
        if lane_id is not None:
            items = [item for item in items if item.lane_id == lane_id]
        if pack_type is not None:
            items = [item for item in items if item.pack_type == pack_type]
        return sorted(items, key=lambda item: (item.pack_type, item.priority, item.pack_id))

    def compose_lane_profile(self, lane_id: str) -> dict[str, object]:
        packs = self.list_packs(lane_id=lane_id)
        return {
            "lane_id": lane_id,
            "pack_count": len(packs),
            "pack_types": sorted({pack.pack_type for pack in packs}),
            "packs": [pack.to_dict() for pack in packs],
        }


GLOBAL_PACK_REGISTRY = PackRegistry()


def register_pack(pack: PackDefinition) -> PackDefinition:
    GLOBAL_PACK_REGISTRY.register(pack)
    return pack


def get_pack_registry() -> PackRegistry:
    return GLOBAL_PACK_REGISTRY


def _register_base_packs() -> None:
    lane_config = {
        "first_class_commercial": {
            "domain": ["saas_core", "workspace_ops", "api_service"],
            "workflow": ["approval_flow", "audit_flow", "retry_flow"],
            "ui": ["enterprise_shell", "admin_surface", "activity_surface"],
            "validation": ["web_structure", "proof_bundle", "packaging_bundle"],
            "repair": ["web_repair_policy", "bounded_repair"],
            "deployment": ["docker_local", "cloud_ready_contract"],
            "asset": ["ui_assets", "config_assets"],
            "research": ["integration_notes", "future_lane_hooks"],
            "security": ["authn_model", "audit_contract", "safe_defaults"],
            "governance": ["approval_hooks", "sensitive_action_policy"],
            "commerce": ["subscriptions", "entitlements", "webhook_events"],
        },
        "first_class_mobile": {
            "domain": ["mobile_workspace", "offline_sync"],
            "workflow": ["mobile_navigation", "sync_retry_flow"],
            "ui": ["flutter_shell", "settings_surface"],
            "validation": ["mobile_structure", "mobile_markers", "proof_bundle"],
            "repair": ["mobile_repair_policy", "bounded_repair"],
            "deployment": ["docker_backend_mobile_client", "cloud_ready_contract"],
            "asset": ["mobile_ui_assets", "icon_placeholders"],
            "research": ["device_matrix_hook", "flutter_perf_hook"],
            "security": ["authn_model", "mobile_token_rules", "safe_defaults"],
            "governance": ["approval_hooks", "sensitive_action_policy"],
            "commerce": ["subscriptions", "entitlements", "trial_plan"],
        },
        "first_class_game": {
            "domain": ["gameplay_core", "session_state"],
            "workflow": ["input_loop", "physics_loop", "session_retry"],
            "ui": ["hud_shell", "scene_navigation"],
            "validation": ["game_structure", "game_markers", "proof_bundle"],
            "repair": ["game_repair_policy", "bounded_repair"],
            "deployment": ["docker_backend_game_client", "cloud_ready_contract"],
            "asset": ["scene_assets", "audio_placeholders"],
            "research": ["frame_time_hook", "content_pipeline_hook"],
            "security": ["authn_model", "session_rules", "safe_defaults"],
            "governance": ["approval_hooks", "sensitive_action_policy"],
            "commerce": ["subscriptions", "entitlements", "plan_catalog"],
        },
        "first_class_realtime": {
            "domain": ["realtime_ops", "sensor_ingestion", "state_projection"],
            "workflow": ["event_ingestion", "alert_dispatch", "action_pipeline"],
            "ui": ["live_dashboard", "alert_surface"],
            "validation": ["realtime_structure", "realtime_markers", "realtime_packaging"],
            "repair": ["realtime_repair_policy", "bounded_repair"],
            "deployment": ["docker_local", "stream_connector_contract"],
            "asset": ["dashboard_assets", "connector_placeholders"],
            "research": ["sensor_latency_hook", "stream_reliability_hook"],
            "security": ["authn_model", "stream_access_policy", "safe_defaults"],
            "governance": ["approval_hooks", "sensitive_action_policy"],
            "commerce": ["subscriptions", "entitlements", "usage_billing"],
        },
        "first_class_enterprise_agent": {
            "domain": ["enterprise_workflows", "agent_orchestration", "corporate_ops"],
            "workflow": ["multi_role_routing", "approval_chain", "briefing_generation"],
            "ui": ["operator_console", "workflow_board", "briefing_surface"],
            "validation": ["enterprise_structure", "enterprise_markers", "enterprise_packaging"],
            "repair": ["enterprise_repair_policy", "bounded_repair"],
            "deployment": ["docker_local", "enterprise_runtime_contract"],
            "asset": ["report_templates", "workflow_assets"],
            "research": ["routing_quality_hook", "approval_latency_hook"],
            "security": ["authn_model", "rbac_abac_controls", "safe_defaults"],
            "governance": ["approval_hooks", "governance_contract_points"],
            "commerce": ["subscriptions", "entitlements", "enterprise_plan_catalog"],
        },
    }

    for lane_id, packs_by_type in lane_config.items():
        for idx, (pack_type, capabilities) in enumerate(sorted(packs_by_type.items())):
            register_pack(
                PackDefinition(
                    pack_id=f"{lane_id}.{pack_type}.v1",
                    pack_type=pack_type,
                    lane_id=lane_id,
                    version="1.0.0",
                    capabilities=sorted(capabilities),
                    metadata={
                        "deterministic": True,
                        "enabled": True,
                    },
                    priority=idx + 1,
                )
            )


_register_base_packs()
