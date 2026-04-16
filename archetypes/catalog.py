from __future__ import annotations

from dataclasses import asdict, dataclass


class ArchetypeResolutionError(ValueError):
    """Raised when an app type cannot be mapped to a supported archetype."""


@dataclass(frozen=True)
class AppArchetype:
    name: str
    expected_surfaces: list[str]
    expected_backend_shape: list[str]
    expected_runtime_concerns: list[str]
    expected_validation_concerns: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


ARCHETYPES: dict[str, AppArchetype] = {
    "internal_tool": AppArchetype(
        name="internal_tool",
        expected_surfaces=["web_admin", "operator_console"],
        expected_backend_shape=["crud_api", "authz_layer", "admin_workflows"],
        expected_runtime_concerns=["rbac", "audit_trails", "internal_sso"],
        expected_validation_concerns=["permission_matrix", "operator_workflows", "data_integrity"],
    ),
    "workspace_app": AppArchetype(
        name="workspace_app",
        expected_surfaces=["web_workspace", "settings"],
        expected_backend_shape=["multi_user_api", "collaboration_state", "background_jobs"],
        expected_runtime_concerns=["tenancy", "session_state", "async_jobs"],
        expected_validation_concerns=["workspace_isolation", "collaboration_flows", "job_retries"],
    ),
    "saas_web_app": AppArchetype(
        name="saas_web_app",
        expected_surfaces=["marketing_site", "authenticated_web_app", "billing_settings"],
        expected_backend_shape=["tenant_api", "authn_authz", "subscription_services"],
        expected_runtime_concerns=["multi_tenancy", "billing_events", "operational_observability"],
        expected_validation_concerns=["signup_to_activation", "tenant_boundaries", "subscription_state"],
    ),
    "api_service": AppArchetype(
        name="api_service",
        expected_surfaces=["http_api", "developer_docs"],
        expected_backend_shape=["service_endpoints", "domain_services", "integration_adapters"],
        expected_runtime_concerns=["api_stability", "rate_limits", "service_observability"],
        expected_validation_concerns=["contract_tests", "latency_budgets", "error_handling"],
    ),
    "workflow_system": AppArchetype(
        name="workflow_system",
        expected_surfaces=["workflow_designer", "execution_monitor", "ops_controls"],
        expected_backend_shape=["orchestration_engine", "state_store", "worker_runtime"],
        expected_runtime_concerns=["durable_state", "retries", "queue_health"],
        expected_validation_concerns=["workflow_replay", "failure_recovery", "state_transitions"],
    ),
    "copilot_chat_app": AppArchetype(
        name="copilot_chat_app",
        expected_surfaces=["chat_surface", "conversation_history", "admin_controls"],
        expected_backend_shape=["chat_api", "tool_router", "memory_services"],
        expected_runtime_concerns=["conversation_state", "tool_safety", "response_observability"],
        expected_validation_concerns=["tool_invocation", "conversation_continuity", "policy_controls"],
    ),
    "mobile_app": AppArchetype(
        name="mobile_app",
        expected_surfaces=["mobile_navigation", "native_ui", "offline_state"],
        expected_backend_shape=["mobile_api", "session_services", "sync_services"],
        expected_runtime_concerns=["device_state", "session_resilience", "background_sync"],
        expected_validation_concerns=["navigation_state", "offline_recovery", "session_consistency"],
    ),
    "game_app": AppArchetype(
        name="game_app",
        expected_surfaces=["scenes", "hud_ui", "input_surface"],
        expected_backend_shape=["game_state_services", "asset_services", "event_services"],
        expected_runtime_concerns=["update_loops", "input_latency", "event_consistency"],
        expected_validation_concerns=["scene_transitions", "entity_updates", "asset_integrity"],
    ),
    "realtime_system": AppArchetype(
        name="realtime_system",
        expected_surfaces=["live_dashboard", "channel_controls", "event_streams"],
        expected_backend_shape=["realtime_api", "channel_router", "event_processors"],
        expected_runtime_concerns=["channel_uptime", "event_ordering", "session_presence"],
        expected_validation_concerns=["channel_delivery", "event_replay", "presence_accuracy"],
    ),
}


def resolve_archetype(app_type: str) -> AppArchetype:
    try:
        return ARCHETYPES[app_type]
    except KeyError as exc:
        supported = ", ".join(sorted(ARCHETYPES))
        raise ArchetypeResolutionError(
            f"Unsupported app_type '{app_type}'. Supported archetypes: {supported}"
        ) from exc