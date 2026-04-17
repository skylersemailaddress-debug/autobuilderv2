from __future__ import annotations

"""Enterprise readiness artifacts.

Emits structured, truthful enterprise-readiness documentation including
deployment expectations, supportability contracts, operational runbooks,
known limitations, and escalation boundaries.
"""

# ---------------------------------------------------------------------------
# Deployment expectations
# ---------------------------------------------------------------------------

DEPLOYMENT_EXPECTATIONS: dict[str, object] = {
    "deployment_contract_version": "v1",
    "supported_deployment_targets": ["docker_compose", "kubernetes", "cloud_run", "bare_server"],
    "infrastructure_as_code_scaffold": True,
    "environment_tiers": ["development", "staging", "production"],
    "required_environment_variables": [
        "APP_ENV",
        "APP_VERSION",
        "DATABASE_URL",
        "SECRET_KEY",
    ],
    "health_check_endpoints_required": True,
    "readiness_probe_contract": "/health/ready",
    "liveness_probe_contract": "/health/live",
    "graceful_shutdown_required": True,
    "zero_downtime_deploy_strategy": "rolling_update_placeholder",
    "known_limitations": [
        "IaC templates are scaffolds; operator must configure provider-specific details",
        "zero-downtime strategies require operator-managed load balancer config",
    ],
}

# ---------------------------------------------------------------------------
# Supportability contract
# ---------------------------------------------------------------------------

SUPPORTABILITY_CONTRACT: dict[str, object] = {
    "supportability_version": "v1",
    "log_format": "structured_json",
    "log_levels": ["debug", "info", "warning", "error", "critical"],
    "metrics_contract": {
        "instrumentation_scaffold": True,
        "supported_exporters": ["prometheus_placeholder", "opentelemetry_placeholder"],
        "key_metrics": ["request_latency_p99", "error_rate", "active_sessions", "job_queue_depth"],
    },
    "tracing_contract": {
        "distributed_tracing_scaffold": True,
        "trace_id_propagation_required": True,
        "opentelemetry_placeholder": True,
    },
    "alerting_contract": {
        "alerts_scaffold": ["high_error_rate", "latency_spike", "health_check_failure"],
        "pagerduty_integration_placeholder": True,
    },
    "runbook_coverage": [
        "deployment_runbook",
        "rollback_runbook",
        "incident_triage_runbook",
        "scaling_runbook",
        "secret_rotation_runbook",
    ],
    "known_limitations": [
        "metrics exporters require operator-supplied observability backend",
        "alerting thresholds must be tuned by operator",
    ],
}

# ---------------------------------------------------------------------------
# Operational runbook scaffolds
# ---------------------------------------------------------------------------

OPERATIONAL_RUNBOOKS: dict[str, dict[str, object]] = {
    "deployment_runbook": {
        "runbook_id": "deployment_runbook",
        "title": "Standard Deployment Runbook",
        "steps": [
            "verify_environment_variables_set",
            "run_pre_deploy_health_check",
            "create_deployment_checkpoint",
            "execute_rolling_update",
            "validate_readiness_probe",
            "confirm_deployment_success",
            "record_deployment_audit_event",
        ],
        "rollback_trigger": "readiness_probe_failure_after_3_retries",
        "escalation_on_failure": "escalation_boundary_l2",
    },
    "rollback_runbook": {
        "runbook_id": "rollback_runbook",
        "title": "Rollback Runbook",
        "steps": [
            "confirm_rollback_authorization",
            "restore_from_checkpoint",
            "verify_previous_version_health",
            "notify_stakeholders",
            "record_rollback_audit_event",
        ],
        "rollback_trigger": "operator_initiated_or_automated_health_failure",
        "escalation_on_failure": "escalation_boundary_l3",
    },
    "secret_rotation_runbook": {
        "runbook_id": "secret_rotation_runbook",
        "title": "Secret Rotation Runbook",
        "steps": [
            "generate_new_secret",
            "update_secret_store",
            "rolling_restart_services",
            "verify_auth_flows_post_rotation",
            "revoke_old_secret",
            "record_rotation_audit_event",
        ],
        "rollback_trigger": "auth_failure_post_rotation",
        "escalation_on_failure": "escalation_boundary_l2",
    },
    "incident_triage_runbook": {
        "runbook_id": "incident_triage_runbook",
        "title": "Incident Triage Runbook",
        "steps": [
            "detect_alert_or_report",
            "classify_severity",
            "assign_incident_owner",
            "gather_logs_and_traces",
            "identify_root_cause",
            "apply_mitigation",
            "validate_recovery",
            "write_postmortem_placeholder",
        ],
        "rollback_trigger": "mitigation_ineffective_after_15_minutes",
        "escalation_on_failure": "escalation_boundary_l3",
    },
}

# ---------------------------------------------------------------------------
# Known limitations registry
# ---------------------------------------------------------------------------

KNOWN_LIMITATIONS_REGISTRY: list[dict[str, object]] = [
    {
        "id": "auth_provider_credentials",
        "category": "security",
        "description": "Authentication provider credentials must be supplied by operator; no embedded defaults.",
        "mitigation": "Operator provides credentials via environment/secret store per deployment guide.",
        "severity": "blocker_without_operator_action",
    },
    {
        "id": "payment_provider_credentials",
        "category": "commerce",
        "description": "Payment provider (e.g. Stripe) credentials not included; billing scaffold only.",
        "mitigation": "Operator integrates payment provider via billing webhook scaffold.",
        "severity": "blocker_without_operator_action",
    },
    {
        "id": "agent_scope_bounded",
        "category": "agent_runtime",
        "description": "Agent runtime is bounded prototype; unbounded desktop/OS control not supported.",
        "mitigation": "Use bounded task model and approval gates per agent-runtime contract.",
        "severity": "design_boundary",
    },
    {
        "id": "multimodal_structural_only",
        "category": "multimodal",
        "description": "Multimodal/world-state support is schema-contract groundwork only; no live execution.",
        "mitigation": "Operator supplies live sensor/stream integration post-generation.",
        "severity": "capability_boundary",
    },
    {
        "id": "lifecycle_ci_integration",
        "category": "lifecycle",
        "description": "Lifecycle/regeneration tooling requires operator CI/CD integration to execute.",
        "mitigation": "Use lifecycle contract scaffolds as input to operator CI pipeline.",
        "severity": "integration_required",
    },
]

# ---------------------------------------------------------------------------
# Escalation boundary model
# ---------------------------------------------------------------------------

ESCALATION_BOUNDARIES: dict[str, dict[str, object]] = {
    "escalation_boundary_l1": {
        "level": "L1",
        "description": "Operator self-service resolution — use runbooks, logs, and checkpoints.",
        "trigger_conditions": ["non-critical alert", "expected transient error"],
        "resolution_owner": "operator",
    },
    "escalation_boundary_l2": {
        "level": "L2",
        "description": "Senior operator or platform team involvement — consult platform generated runbooks.",
        "trigger_conditions": ["deployment failure", "auth degradation", "secret rotation failure"],
        "resolution_owner": "platform_team",
    },
    "escalation_boundary_l3": {
        "level": "L3",
        "description": "Escalate to platform vendor or external support — incident outside operator scope.",
        "trigger_conditions": ["data loss risk", "widespread outage", "security incident"],
        "resolution_owner": "vendor_or_external_support",
    },
}


def build_enterprise_readiness_artifact(lane_id: str) -> dict[str, object]:
    """Build a full enterprise readiness artifact for a lane."""
    return {
        "lane_id": lane_id,
        "enterprise_readiness_version": "v1",
        "deployment_expectations": DEPLOYMENT_EXPECTATIONS,
        "supportability_contract": SUPPORTABILITY_CONTRACT,
        "operational_runbooks": OPERATIONAL_RUNBOOKS,
        "known_limitations": KNOWN_LIMITATIONS_REGISTRY,
        "escalation_boundaries": ESCALATION_BOUNDARIES,
        "runbook_ids": list(OPERATIONAL_RUNBOOKS.keys()),
        "limitations_count": len(KNOWN_LIMITATIONS_REGISTRY),
        "maturity": "bounded_prototype",
    }
