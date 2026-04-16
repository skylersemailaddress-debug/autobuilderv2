from pathlib import Path

from cli.autobuilder import run_build_workflow
from platform_hardening.commerce import build_commerce_pack_contract
from platform_hardening.security_governance import build_security_governance_contract


def test_security_and_governance_contract_structure() -> None:
    contract = build_security_governance_contract("first_class_commercial")

    assert contract["auth_support"]["rbac_ready"] is True
    assert contract["auth_support"]["abac_ready"] is True
    assert contract["secrets_and_config"]["plain_text_secret_forbidden"] is True
    assert "sensitive_action_policy_hooks" in contract["policy_hooks"]


def test_commerce_pack_contract_structure() -> None:
    contract = build_commerce_pack_contract("first_class_commercial")

    assert "free" in contract["subscription_models"]
    assert "enterprise" in contract["subscription_models"]
    assert contract["billing_webhooks"]["signature_verification_required"] is True
    assert "admin/billing/invoices" in contract["admin_billing_surfaces"]


def test_build_workflow_emits_security_commerce_and_runtime_artifacts(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    target = tmp_path / "hardened_output"

    result = run_build_workflow(str(project_root / "specs"), str(target))
    artifacts = result["proof_artifacts"]["artifact_paths"]

    assert Path(artifacts["runtime_verification"]).exists()
    assert Path(artifacts["security_governance_contract"]).exists()
    assert Path(artifacts["commerce_pack_contract"]).exists()
    assert Path(artifacts["pack_composition"]).exists()
    assert Path(artifacts["failure_corpus"]).exists()
    assert Path(artifacts["replay_harness"]).exists()
