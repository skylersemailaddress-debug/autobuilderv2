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
}


def resolve_archetype(app_type: str) -> AppArchetype:
    try:
        return ARCHETYPES[app_type]
    except KeyError as exc:
        supported = ", ".join(sorted(ARCHETYPES))
        raise ArchetypeResolutionError(
            f"Unsupported app_type '{app_type}'. Supported archetypes: {supported}"
        ) from exc