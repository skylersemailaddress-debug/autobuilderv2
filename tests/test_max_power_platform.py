"""Tests for security & commerce contracts, cross-lane composition,
lifecycle/regeneration safety guardrails, and enterprise readiness artifacts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from platform_hardening.capability_maturity import (
    CAPABILITY_FAMILY_MATURITY,
    evaluate_capability_family,
)
from platform_hardening.commerce import (
    ADMIN_BILLING_SURFACES,
    BILLING_WEBHOOKS,
    ENTITLEMENT_MODEL,
    PLAN_CATALOG,
    build_commerce_pack_contract,
)
from platform_hardening.composition import (
    CompositionContractError,
    evaluate_composition_request,
    list_valid_composition_patterns,
    resolve_composition_contract,
)
from platform_hardening.enterprise_readiness import (
    ESCALATION_BOUNDARIES,
    KNOWN_LIMITATIONS_REGISTRY,
    OPERATIONAL_RUNBOOKS,
    build_enterprise_readiness_artifact,
)
from platform_hardening.lifecycle import (
    build_lifecycle_contract,
    build_migration_contract,
    build_capability_evolution_record,
    classify_file_regen_safety,
)
from platform_hardening.security_governance import (
    ABAC_PACK,
    RBAC_PACK,
    SAFE_GENERATION_DEFAULTS,
    build_auth_authz_pack,
    build_security_governance_contract,
)


# ---------------------------------------------------------------------------
# Security contract presence
# ---------------------------------------------------------------------------

class TestSecurityContractPresence:
    def test_contract_v2(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        assert c["contract_version"] == "v2"

    def test_rbac_and_abac_ready(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        assert c["auth_support"]["rbac_ready"] is True
        assert c["auth_support"]["abac_ready"] is True

    def test_rbac_pack_roles(self) -> None:
        assert "admin" in RBAC_PACK["roles_scaffold"]
        assert "viewer" in RBAC_PACK["roles_scaffold"]
        assert RBAC_PACK["deny_by_default"] is True

    def test_abac_composable_with_rbac(self) -> None:
        assert ABAC_PACK["composable_with_rbac"] is True

    def test_secrets_policy_forbids_plaintext(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        assert c["secrets_and_config"]["plain_text_secret_forbidden"] is True
        assert c["secrets_and_config"]["encryption_at_rest_required"] is True

    def test_audit_defaults_event_schema(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        schema = c["audit_logging"]["event_schema"]
        assert "actor" in schema
        assert "timestamp" in schema
        assert "request_id" in schema

    def test_safe_generation_defaults(self) -> None:
        assert SAFE_GENERATION_DEFAULTS["deny_by_default_permissions"] is True
        assert SAFE_GENERATION_DEFAULTS["csp_headers_scaffold"] is True
        assert SAFE_GENERATION_DEFAULTS["cors_strictness"] == "explicit_allowlist_only"

    def test_policy_hooks_include_pii_export(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        hooks = c["policy_hooks"]["sensitive_action_policy_hooks"]
        assert "before_pii_export" in hooks

    def test_known_limitations_present(self) -> None:
        c = build_security_governance_contract("first_class_commercial")
        assert len(c["known_limitations"]) > 0

    def test_auth_authz_pack_structure(self) -> None:
        pack = build_auth_authz_pack("first_class_commercial")
        assert pack["auth_pack"]["jwt_signing_required"] is True
        assert pack["rbac_pack"]["deny_by_default"] is True
        assert "abac_pack" in pack

    def test_security_capability_family_registered(self) -> None:
        assert "security" in CAPABILITY_FAMILY_MATURITY
        family = evaluate_capability_family("security", ["auth_authz_pack", "rbac_scaffold"])
        assert family["accepted"] is True
        assert family["maturity"] == "bounded_prototype"

    def test_security_family_rejects_unsupported(self) -> None:
        family = evaluate_capability_family("security", ["automated_penetration_testing"])
        assert family["accepted"] is False
        assert "automated_penetration_testing" in family["unsupported_requested"]


# ---------------------------------------------------------------------------
# Commerce contract presence
# ---------------------------------------------------------------------------

class TestCommerceContractPresence:
    def test_contract_v2(self) -> None:
        c = build_commerce_pack_contract("first_class_commercial")
        assert c["contract_version"] == "v2"

    def test_plan_catalog_includes_all_tiers(self) -> None:
        ids = [p["plan_id"] for p in PLAN_CATALOG]
        assert "free" in ids
        assert "trial" in ids
        assert "pro" in ids
        assert "enterprise" in ids

    def test_entitlement_model_supports_metered(self) -> None:
        assert ENTITLEMENT_MODEL["supports_metered"] is True
        assert ENTITLEMENT_MODEL["supports_tier_gates"] is True

    def test_billing_webhooks_complete(self) -> None:
        event_types = BILLING_WEBHOOKS["event_types"]
        assert "subscription.created" in event_types
        assert "invoice.paid" in event_types
        assert "payment_method.updated" in event_types
        assert BILLING_WEBHOOKS["signature_verification_required"] is True
        assert BILLING_WEBHOOKS["idempotency_required"] is True
        assert BILLING_WEBHOOKS["replay_protection"] is True

    def test_admin_billing_surfaces(self) -> None:
        assert "admin/billing/invoices" in ADMIN_BILLING_SURFACES
        assert "admin/billing/usage" in ADMIN_BILLING_SURFACES

    def test_known_limitations_present(self) -> None:
        c = build_commerce_pack_contract("first_class_commercial")
        assert len(c["known_limitations"]) > 0
        assert c["commerce_maturity"] == "bounded_prototype"

    def test_commerce_capability_family_registered(self) -> None:
        assert "commerce" in CAPABILITY_FAMILY_MATURITY
        family = evaluate_capability_family("commerce", ["plan_catalog", "billing_webhooks"])
        assert family["accepted"] is True

    def test_commerce_family_rejects_unsupported(self) -> None:
        family = evaluate_capability_family("commerce", ["live_payment_processing_without_operator_credentials"])
        assert family["accepted"] is False


# ---------------------------------------------------------------------------
# Cross-lane composition rules
# ---------------------------------------------------------------------------

class TestCrossLaneCompositionRules:
    def test_valid_patterns_registered(self) -> None:
        patterns = list_valid_composition_patterns()
        pattern_ids = [p["pattern_id"] for p in patterns]
        assert "app_plus_agent" in pattern_ids
        assert "app_plus_realtime" in pattern_ids
        assert "app_plus_mobile_companion" in pattern_ids
        assert "app_plus_payment_layer" in pattern_ids

    def test_app_plus_agent_accepted(self) -> None:
        result = evaluate_composition_request("first_class_commercial", "agent-runtime")
        assert result["accepted"] is True
        assert result["pattern"] is not None

    def test_app_plus_realtime_accepted(self) -> None:
        result = evaluate_composition_request("first_class_commercial", "first_class_realtime")
        assert result["accepted"] is True
        assert result["maturity"] == "first_class"

    def test_app_plus_mobile_companion_accepted(self) -> None:
        result = evaluate_composition_request("first_class_commercial", "first_class_mobile")
        assert result["accepted"] is True

    def test_app_plus_payment_layer_accepted(self) -> None:
        result = evaluate_composition_request("first_class_commercial", "commerce")
        assert result["accepted"] is True

    def test_unknown_pattern_rejected(self) -> None:
        result = evaluate_composition_request("first_class_commercial", "nonexistent_capability")
        assert result["accepted"] is False
        assert len(result["violations"]) > 0

    def test_unknown_primary_lane_rejected(self) -> None:
        result = evaluate_composition_request("unknown_lane", "agent-runtime")
        assert result["accepted"] is False

    def test_resolve_composition_contract_valid(self) -> None:
        contract = resolve_composition_contract("app_plus_agent")
        assert contract["primary_lane"] == "first_class_commercial"
        assert len(contract["composition_rules"]) > 0

    def test_resolve_composition_contract_invalid_raises(self) -> None:
        with pytest.raises(CompositionContractError):
            resolve_composition_contract("nonexistent_pattern")

    def test_composition_capability_family_registered(self) -> None:
        assert "cross-lane-composition" in CAPABILITY_FAMILY_MATURITY
        family = evaluate_capability_family("cross-lane-composition", ["app_plus_agent"])
        assert family["accepted"] is True

    def test_arbitrary_lane_mixing_rejected(self) -> None:
        family = evaluate_capability_family("cross-lane-composition",
                                            ["arbitrary_lane_mixing_without_contract"])
        assert family["accepted"] is False


# ---------------------------------------------------------------------------
# Lifecycle / regeneration safety guardrails
# ---------------------------------------------------------------------------

class TestLifecycleRegenerationSafety:
    def test_safe_overwrite_no_checkpoint(self) -> None:
        result = classify_file_regen_safety(
            "src/components/AutoGenerated.tsx",
            is_autogenerated=True,
            has_operator_modifications=False,
            is_production_critical=False,
        )
        assert result["regen_safety_level"] == "safe_overwrite"
        assert result["requires_checkpoint"] is False
        assert result["requires_approval"] is False

    def test_operator_modified_requires_merge(self) -> None:
        result = classify_file_regen_safety(
            "src/pages/Dashboard.tsx",
            is_autogenerated=True,
            has_operator_modifications=True,
            is_production_critical=False,
        )
        assert result["regen_safety_level"] == "merge_required"
        assert result["requires_checkpoint"] is True
        assert result["requires_approval"] is False

    def test_production_critical_requires_approval(self) -> None:
        result = classify_file_regen_safety(
            "db/migrations/001_init.sql",
            is_autogenerated=True,
            has_operator_modifications=False,
            is_production_critical=True,
        )
        assert result["regen_safety_level"] == "approval_required"
        assert result["requires_checkpoint"] is True
        assert result["requires_approval"] is True

    def test_migration_contract_with_schema_change(self) -> None:
        contract = build_migration_contract("1.0.0", "2.0.0", "first_class_commercial",
                                            changed_capabilities=["database_schema"])
        assert contract["requires_data_migration"] is True
        assert contract["pre_migration_checkpoint_required"] is True
        assert "apply_schema_migrations" in contract["migration_steps_scaffold"]
        assert contract["rollback_available"] is True

    def test_migration_contract_without_schema_change(self) -> None:
        contract = build_migration_contract("1.0.0", "1.1.0", "first_class_commercial",
                                            changed_capabilities=["ui_theme"])
        assert contract["requires_data_migration"] is False
        assert contract["pre_migration_checkpoint_required"] is False

    def test_capability_evolution_record_deterministic(self) -> None:
        r1 = build_capability_evolution_record(
            "first_class_commercial", "security",
            "structural_only", "bounded_prototype",
            promoted_capabilities=["auth_authz_pack"],
        )
        r2 = build_capability_evolution_record(
            "first_class_commercial", "security",
            "structural_only", "bounded_prototype",
            promoted_capabilities=["auth_authz_pack"],
        )
        assert r1["evolution_signature_sha256"] == r2["evolution_signature_sha256"]
        assert r1["net_direction"] == "promoted"

    def test_lifecycle_contract_structure(self) -> None:
        contract = build_lifecycle_contract("first_class_commercial")
        assert contract["lifecycle_contract_version"] == "v1"
        assert "initial_generation" in contract["supported_lifecycle_operations"]
        assert "silent_destructive_overwrite" in contract["blocked_lifecycle_operations"]
        assert contract["migration_contract_available"] is True
        assert len(contract["known_limitations"]) > 0

    def test_lifecycle_capability_family_registered(self) -> None:
        assert "lifecycle" in CAPABILITY_FAMILY_MATURITY
        family = evaluate_capability_family("lifecycle", ["regen_safety_classification", "migration_aware_updates"])
        assert family["accepted"] is True

    def test_lifecycle_family_rejects_unsupported(self) -> None:
        family = evaluate_capability_family("lifecycle", ["silent_destructive_overwrite"])
        assert family["accepted"] is False


# ---------------------------------------------------------------------------
# Enterprise readiness artifact completeness
# ---------------------------------------------------------------------------

class TestEnterpriseReadinessArtifact:
    def test_artifact_structure(self) -> None:
        artifact = build_enterprise_readiness_artifact("first_class_commercial")
        assert artifact["enterprise_readiness_version"] == "v1"
        assert "deployment_expectations" in artifact
        assert "supportability_contract" in artifact
        assert "operational_runbooks" in artifact
        assert "known_limitations" in artifact
        assert "escalation_boundaries" in artifact

    def test_all_runbooks_present(self) -> None:
        artifact = build_enterprise_readiness_artifact("first_class_commercial")
        runbook_ids = artifact["runbook_ids"]
        assert "deployment_runbook" in runbook_ids
        assert "rollback_runbook" in runbook_ids
        assert "secret_rotation_runbook" in runbook_ids
        assert "incident_triage_runbook" in runbook_ids

    def test_deployment_runbook_has_steps(self) -> None:
        rb = OPERATIONAL_RUNBOOKS["deployment_runbook"]
        assert len(rb["steps"]) >= 5
        assert "create_deployment_checkpoint" in rb["steps"]
        assert "record_deployment_audit_event" in rb["steps"]

    def test_known_limitations_coverage(self) -> None:
        ids = [lim["id"] for lim in KNOWN_LIMITATIONS_REGISTRY]
        assert "auth_provider_credentials" in ids
        assert "payment_provider_credentials" in ids
        assert "agent_scope_bounded" in ids
        assert "multimodal_structural_only" in ids
        assert "lifecycle_ci_integration" in ids

    def test_escalation_boundaries_all_levels(self) -> None:
        levels = {b["level"] for b in ESCALATION_BOUNDARIES.values()}
        assert "L1" in levels
        assert "L2" in levels
        assert "L3" in levels

    def test_supportability_metrics_contract(self) -> None:
        artifact = build_enterprise_readiness_artifact("first_class_commercial")
        metrics = artifact["supportability_contract"]["metrics_contract"]
        assert metrics["instrumentation_scaffold"] is True
        assert "request_latency_p99" in metrics["key_metrics"]

    def test_enterprise_readiness_capability_family_registered(self) -> None:
        assert "enterprise-readiness" in CAPABILITY_FAMILY_MATURITY
        family = evaluate_capability_family("enterprise-readiness",
                                            ["deployment_expectations", "operational_runbooks"])
        assert family["accepted"] is True

    def test_enterprise_readiness_family_rejects_unsupported(self) -> None:
        family = evaluate_capability_family("enterprise-readiness", ["automated_runbook_execution"])
        assert family["accepted"] is False

    def test_limitations_count(self) -> None:
        artifact = build_enterprise_readiness_artifact("first_class_commercial")
        assert artifact["limitations_count"] == len(KNOWN_LIMITATIONS_REGISTRY)
        assert artifact["limitations_count"] >= 5


# ---------------------------------------------------------------------------
# Build workflow exposes new artifacts
# ---------------------------------------------------------------------------

class TestBuildWorkflowNewArtifacts:
    def test_build_workflow_emits_lifecycle_and_enterprise_artifacts(self, tmp_path: Path) -> None:
        from cli.autobuilder import run_build_workflow

        project_root = Path(__file__).resolve().parents[1]
        target = tmp_path / "enterprise_output"

        result = run_build_workflow(str(project_root / "specs"), str(target))
        artifacts = result["proof_artifacts"]["artifact_paths"]

        assert Path(artifacts["lifecycle_contract"]).exists()
        assert Path(artifacts["enterprise_readiness"]).exists()

    def test_build_workflow_lifecycle_contract_valid(self, tmp_path: Path) -> None:
        import json
        from cli.autobuilder import run_build_workflow

        project_root = Path(__file__).resolve().parents[1]
        target = tmp_path / "lifecycle_output"

        result = run_build_workflow(str(project_root / "specs"), str(target))
        lc_path = result["proof_artifacts"]["artifact_paths"]["lifecycle_contract"]
        lc = json.loads(Path(lc_path).read_text())
        assert lc["lifecycle_contract_version"] == "v1"
        assert "initial_generation" in lc["supported_lifecycle_operations"]

    def test_build_workflow_enterprise_readiness_valid(self, tmp_path: Path) -> None:
        import json
        from cli.autobuilder import run_build_workflow

        project_root = Path(__file__).resolve().parents[1]
        target = tmp_path / "enterprise_output2"

        result = run_build_workflow(str(project_root / "specs"), str(target))
        er_path = result["proof_artifacts"]["artifact_paths"]["enterprise_readiness"]
        er = json.loads(Path(er_path).read_text())
        assert er["enterprise_readiness_version"] == "v1"
        assert len(er["runbook_ids"]) >= 4
