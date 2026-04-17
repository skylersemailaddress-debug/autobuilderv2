from __future__ import annotations

# ---------------------------------------------------------------------------
# Auth / AuthZ pack definitions
# ---------------------------------------------------------------------------

AUTH_PACK: dict[str, object] = {
    "pack_id": "auth_authz_pack",
    "authentication_model": "token_session_hybrid",
    "supported_flows": ["oauth2_pkce", "api_key", "session_cookie"],
    "jwt_signing_required": True,
    "refresh_token_rotation": True,
    "mfa_ready": True,
}

RBAC_PACK: dict[str, object] = {
    "pack_id": "rbac_pack",
    "model": "role_based_access_control",
    "role_hierarchy_supported": True,
    "roles_scaffold": ["owner", "admin", "member", "viewer", "billing_admin"],
    "permission_matrix_required": True,
    "deny_by_default": True,
}

ABAC_PACK: dict[str, object] = {
    "pack_id": "abac_pack",
    "model": "attribute_based_access_control",
    "attribute_types": ["user_attribute", "resource_attribute", "environment_attribute"],
    "policy_engine_placeholder": True,
    "composable_with_rbac": True,
}

SECRETS_POLICY: dict[str, object] = {
    "secret_sources": ["environment", "managed_secret_store"],
    "plain_text_secret_forbidden": True,
    "required_config_markers": ["APP_ENV", "APP_VERSION", "DATABASE_URL"],
    "rotation_policy_required": True,
    "encryption_at_rest_required": True,
    "encryption_in_transit_required": True,
}

AUDIT_DEFAULTS: dict[str, object] = {
    "audit_stream_enabled": True,
    "sensitive_actions_must_log": True,
    "event_schema": ["actor", "action", "scope", "outcome", "timestamp", "request_id"],
    "immutable_log_required": True,
    "retention_policy_placeholder": True,
    "pii_redaction_required": True,
}

SAFE_GENERATION_DEFAULTS: dict[str, object] = {
    "deny_by_default_permissions": True,
    "strict_input_validation": True,
    "output_encoding_required": True,
    "production_debug_disabled": True,
    "dependency_pinning_required": True,
    "csp_headers_scaffold": True,
    "cors_strictness": "explicit_allowlist_only",
}


def build_auth_authz_pack(lane_id: str) -> dict[str, object]:
    """Return composed auth/authz pack for a lane."""
    return {
        "lane_id": lane_id,
        "pack_contract_version": "v1",
        "auth_pack": AUTH_PACK,
        "rbac_pack": RBAC_PACK,
        "abac_pack": ABAC_PACK,
    }


def build_security_governance_contract(lane_id: str) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "contract_version": "v2",
        "auth_support": {
            "authentication_model": AUTH_PACK["authentication_model"],
            "authorization_model": "policy_guard",
            "rbac_ready": True,
            "abac_ready": True,
            "session_integrity_required": True,
            "mfa_ready": AUTH_PACK["mfa_ready"],
            "supported_flows": AUTH_PACK["supported_flows"],
        },
        "rbac_abac": {
            "rbac": RBAC_PACK,
            "abac": ABAC_PACK,
        },
        "secrets_and_config": SECRETS_POLICY,
        "audit_logging": AUDIT_DEFAULTS,
        "safe_generation_defaults": SAFE_GENERATION_DEFAULTS,
        "policy_hooks": {
            "sensitive_action_policy_hooks": [
                "before_destructive_action",
                "before_privilege_escalation",
                "before_external_billing_mutation",
                "before_pii_export",
                "before_admin_role_grant",
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
        "security_maturity": "bounded_prototype",
        "known_limitations": [
            "auth implementation requires operator-supplied provider credentials",
            "ABAC policy engine is scaffold/placeholder; full evaluation engine not included",
            "audit retention enforcement deferred to operator infrastructure",
        ],
    }
