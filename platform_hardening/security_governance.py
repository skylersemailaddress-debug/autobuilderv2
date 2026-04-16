from __future__ import annotations


def build_security_governance_contract(lane_id: str) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "auth_support": {
            "authentication_model": "token_session_hybrid",
            "authorization_model": "policy_guard",
            "rbac_ready": True,
            "abac_ready": True,
            "session_integrity_required": True,
        },
        "secrets_and_config": {
            "secret_sources": ["environment", "managed_secret_store"],
            "plain_text_secret_forbidden": True,
            "required_config_markers": ["APP_ENV", "APP_VERSION", "DATABASE_URL"],
            "rotation_policy_required": True,
        },
        "audit_logging": {
            "audit_stream_enabled": True,
            "sensitive_actions_must_log": True,
            "event_schema": ["actor", "action", "scope", "outcome", "timestamp"],
        },
        "safe_generation_defaults": {
            "deny_by_default_permissions": True,
            "strict_input_validation": True,
            "production_debug_disabled": True,
        },
        "policy_hooks": {
            "sensitive_action_policy_hooks": [
                "before_destructive_action",
                "before_privilege_escalation",
                "before_external_billing_mutation",
            ],
            "approval_contract_points": [
                "requires_human_approval",
                "approval_context_payload",
                "approval_result_record",
            ],
            "governance_contract_points": [
                "run_governance_check",
                "record_governance_decision",
                "abort_on_policy_violation",
            ],
        },
    }
