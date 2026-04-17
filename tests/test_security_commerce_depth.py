"""
Tests for deeper generated security and commerce scaffolds.
"""
from platform_hardening.security_governance import (
    build_generated_security_scaffolds,
    build_security_governance_contract,
    AUTH_GENERATED_SCAFFOLD,
    RBAC_GENERATED_SCAFFOLD,
    SECRETS_GENERATED_SCAFFOLD,
)
from platform_hardening.commerce import (
    build_generated_commerce_scaffolds,
    build_commerce_pack_contract,
    COMMERCE_GENERATED_SCAFFOLD,
    ADMIN_OPERATIONS_SCAFFOLD,
)


# ---------------------------------------------------------------------------
# Security scaffolds
# ---------------------------------------------------------------------------

def test_security_scaffolds_structure():
    result = build_generated_security_scaffolds("first_class_commercial")
    assert result["lane_id"] == "first_class_commercial"
    assert result["maturity"] == "bounded_prototype"
    assert "auth_scaffold" in result
    assert "rbac_scaffold" in result
    assert "secrets_scaffold" in result


def test_auth_scaffold_has_endpoints():
    scaffold = AUTH_GENERATED_SCAFFOLD
    auth_file = scaffold["generated_files"]["backend/api/auth.py"]
    assert "endpoints" in auth_file
    assert any("token" in ep.lower() for ep in auth_file["endpoints"])
    assert "security_controls" in auth_file
    assert any("rotation" in ctrl for ctrl in auth_file["security_controls"])


def test_rbac_scaffold_deny_by_default():
    scaffold = RBAC_GENERATED_SCAFFOLD
    assert scaffold["permission_matrix_contract"]["deny_by_default"] is True


def test_rbac_scaffold_has_standard_roles():
    scaffold = RBAC_GENERATED_SCAFFOLD
    roles = scaffold["role_definitions"]
    assert "owner" in roles
    assert "admin" in roles
    assert "viewer" in roles
    assert "member" in roles


def test_rbac_scaffold_owner_has_all_permissions():
    scaffold = RBAC_GENERATED_SCAFFOLD
    assert scaffold["role_definitions"]["owner"]["permissions"] == ["*"]


def test_secrets_scaffold_no_plaintext():
    scaffold = SECRETS_GENERATED_SCAFFOLD
    env_example = scaffold["generated_files"][".env.example"]
    assert "plain-text passwords in repo" in (env_example.get("forbidden") or [])


def test_secrets_scaffold_rotation_policy():
    scaffold = SECRETS_GENERATED_SCAFFOLD
    assert "rotation_policy" in scaffold
    assert "jwt_secret" in scaffold["rotation_policy"]


def test_combined_validation_checks_present():
    result = build_generated_security_scaffolds("first_class_enterprise_agent")
    checks = result["combined_validation_checks"]
    assert len(checks) >= 8
    assert "jwt_signing_key_not_hardcoded" in checks
    assert "deny_by_default_enforced" in checks
    assert "no_hardcoded_secrets_in_source" in checks


def test_security_scaffolds_known_limitations_honest():
    result = build_generated_security_scaffolds("first_class_realtime")
    lims = result["known_limitations"]
    combined = " ".join(lims)
    assert "operator" in combined.lower()


# ---------------------------------------------------------------------------
# Commerce scaffolds
# ---------------------------------------------------------------------------

def test_commerce_scaffolds_structure():
    result = build_generated_commerce_scaffolds("first_class_commercial")
    assert result["lane_id"] == "first_class_commercial"
    assert result["maturity"] == "bounded_prototype"
    assert "commerce_scaffold" in result
    assert "admin_operations_scaffold" in result


def test_billing_scaffold_has_webhook_verification():
    scaffold = COMMERCE_GENERATED_SCAFFOLD
    billing = scaffold["generated_files"]["backend/api/billing.py"]
    assert any("webhook" in ctrl.lower() for ctrl in billing["security_controls"])


def test_billing_scaffold_idempotency():
    scaffold = COMMERCE_GENERATED_SCAFFOLD
    billing = scaffold["generated_files"]["backend/api/billing.py"]
    assert any("idempotency" in ctrl.lower() for ctrl in billing["security_controls"])


def test_entitlements_scaffold_check_function():
    scaffold = COMMERCE_GENERATED_SCAFFOLD
    ent = scaffold["generated_files"]["backend/api/entitlements.py"]
    exports = ent["exports"]
    assert any("check_entitlement" in e for e in exports)
    assert any("record_usage" in e for e in exports)


def test_admin_billing_role_guarded():
    scaffold = COMMERCE_GENERATED_SCAFFOLD
    admin_billing = scaffold["generated_files"]["backend/api/admin_billing.py"]
    assert "role_guard" in admin_billing
    assert "billing_admin" in admin_billing["role_guard"]


def test_admin_operations_user_management():
    scaffold = ADMIN_OPERATIONS_SCAFFOLD
    user_mgmt = scaffold["admin_surfaces"]["user_management"]
    endpoints = user_mgmt["endpoints"]
    assert any("/admin/users" in ep for ep in endpoints)
    # Ensure no hard-delete — only soft delete
    assert not any("hard_delete" in ep.lower() for ep in endpoints)


def test_admin_operations_audit_log():
    scaffold = ADMIN_OPERATIONS_SCAFFOLD
    audit = scaffold["admin_surfaces"]["audit_log_surface"]
    assert any("audit" in ep for ep in audit["endpoints"])


def test_combined_commerce_validation_checks():
    result = build_generated_commerce_scaffolds("first_class_commercial")
    checks = result["combined_validation_checks"]
    assert "webhook_signature_verification_present" in checks
    assert "entitlement_check_function_wired" in checks
    assert "audit_log_endpoint_present" in checks
