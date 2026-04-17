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


# ---------------------------------------------------------------------------
# Generated security structure scaffolds
# ---------------------------------------------------------------------------

AUTH_GENERATED_SCAFFOLD: dict[str, object] = {
    "scaffold_version": "v2",
    "maturity": "bounded_prototype",
    "description": "Generated authentication and authorization code scaffold",
    "generated_files": {
        "backend/api/auth.py": {
            "purpose": "JWT token issuance and validation middleware",
            "endpoints": [
                "POST /auth/token — issue access + refresh tokens",
                "POST /auth/token/refresh — rotate refresh token",
                "POST /auth/logout — invalidate session",
                "GET /auth/me — return current user claims",
            ],
            "security_controls": [
                "JWT HS256/RS256 signing required",
                "refresh_token_rotation enabled",
                "token_expiry: access=15m, refresh=7d",
                "rate_limiting on /auth/token",
                "mfa_hook invocation point present",
            ],
        },
        "backend/api/permissions.py": {
            "purpose": "RBAC permission guard decorator and dependency",
            "patterns": [
                "require_role(role: str) → FastAPI dependency",
                "require_permission(permission: str) → decorator",
                "deny_by_default: True",
            ],
        },
        "backend/api/admin.py": {
            "purpose": "Admin-only surfaces with role guards",
            "role_guard": "require_role('admin') | require_role('owner')",
            "endpoints": [
                "GET /admin/users",
                "POST /admin/users/{id}/role",
                "DELETE /admin/users/{id}",
                "GET /admin/audit-log",
            ],
        },
    },
    "validation_checks": [
        "jwt_signing_key_not_hardcoded",
        "all_routes_have_auth_guard",
        "admin_endpoints_role_guarded",
        "refresh_token_rotation_present",
        "mfa_hook_invocation_present",
    ],
}

RBAC_GENERATED_SCAFFOLD: dict[str, object] = {
    "scaffold_version": "v2",
    "maturity": "bounded_prototype",
    "description": "Generated RBAC role/permission table and enforcement scaffold",
    "role_definitions": {
        "owner": {"permissions": ["*"], "inherits": None},
        "admin": {"permissions": ["users:*", "billing:*", "audit:read", "settings:*"], "inherits": "member"},
        "billing_admin": {"permissions": ["billing:*", "subscriptions:*"], "inherits": "member"},
        "member": {"permissions": ["workspace:read", "workspace:write", "profile:*"], "inherits": "viewer"},
        "viewer": {"permissions": ["workspace:read", "profile:read"], "inherits": None},
    },
    "permission_matrix_contract": {
        "format": "role → list[scope:action]",
        "wildcard_supported": True,
        "deny_by_default": True,
        "check_function": "check_permission(user_roles, required_permission) → bool",
    },
    "generated_files": {
        "backend/api/rbac.py": {
            "purpose": "Role resolution and permission evaluation",
            "exports": ["check_permission", "get_user_roles", "require_role"],
        },
        "db/schema_rbac.sql": {
            "purpose": "RBAC tables: roles, permissions, role_assignments",
        },
    },
    "validation_checks": [
        "role_definitions_present",
        "deny_by_default_enforced",
        "permission_matrix_has_no_gaps",
        "rbac_check_function_wired",
    ],
}

SECRETS_GENERATED_SCAFFOLD: dict[str, object] = {
    "scaffold_version": "v2",
    "maturity": "bounded_prototype",
    "description": "Generated secrets and config posture scaffold",
    "generated_files": {
        ".env.example": {
            "purpose": "Non-secret environment variable template",
            "required_vars": [
                "APP_ENV=development",
                "APP_VERSION=0.1.0",
                "DATABASE_URL=postgresql://user:pass@localhost:5432/db",
                "JWT_SECRET_KEY=REPLACE_WITH_STRONG_SECRET",
                "ALLOWED_ORIGINS=http://localhost:3000",
                "STRIPE_PUBLISHABLE_KEY=pk_test_...",
            ],
            "forbidden": ["hardcoded secrets in source", "plain-text passwords in repo"],
        },
        "backend/api/config.py": {
            "purpose": "Pydantic BaseSettings config with environment loading",
            "security_controls": [
                "secrets loaded from env only",
                "strict=True on all secret fields",
                "no default values for secret fields",
                "production_mode disables debug",
            ],
        },
    },
    "rotation_policy": {
        "jwt_secret": "rotate every 90 days or on breach",
        "database_password": "rotate every 180 days or on breach",
        "api_keys": "rotate on staff offboarding or annually",
    },
    "validation_checks": [
        "no_hardcoded_secrets_in_source",
        "env_example_present",
        "config_uses_pydantic_settings",
        "production_debug_disabled",
        "jwt_secret_minimum_entropy",
    ],
}


def build_generated_security_scaffolds(lane_id: str) -> dict[str, object]:
    """Return full generated security scaffold definitions for a lane."""
    return {
        "lane_id": lane_id,
        "scaffold_version": "v2",
        "maturity": "bounded_prototype",
        "auth_scaffold": AUTH_GENERATED_SCAFFOLD,
        "rbac_scaffold": RBAC_GENERATED_SCAFFOLD,
        "secrets_scaffold": SECRETS_GENERATED_SCAFFOLD,
        "combined_validation_checks": sorted(set(
            AUTH_GENERATED_SCAFFOLD["validation_checks"]
            + RBAC_GENERATED_SCAFFOLD["validation_checks"]
            + SECRETS_GENERATED_SCAFFOLD["validation_checks"]
        )),
        "known_limitations": [
            "no live auth provider wiring; operator must inject credentials",
            "ABAC not fully implemented; RBAC is primary enforcement",
            "secrets rotation is policy-only; tooling not included",
        ],
    }

