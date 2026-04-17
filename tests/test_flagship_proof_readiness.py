"""
Tests for flagship-proof readiness layer: readiness checks, bundles,
operator runbooks, truth audits, launch evidence.
"""
from pathlib import Path
from readiness.flagship_proof import (
    run_flagship_readiness_checks,
    build_operator_runbook,
    build_truth_audit,
    build_launch_evidence,
    build_flagship_readiness_bundle,
    emit_flagship_bundle_to_disk,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_mission_result(status="complete", confidence=0.85, approval=False):
    return {
        "run_id": "test-flagship-001",
        "goal": "Build a flagship SaaS app",
        "final_status": status,
        "approval_required": approval,
        "awaiting_approval": approval,
        "confidence": confidence,
        "repair_count": 0,
        "capability_requirements": [{"family": "security"}, {"family": "commerce"}],
        "mission_plan": {
            "schema_version": "v2",
            "pause_resume_semantics": {"supports_interruption_recovery": True},
            "state": status,
        },
        "quality_report": {"confidence": confidence},
        "artifact_lineage_summary": {"artifact_ids": []},
        "mutation_risk": "safe",
        "operator_summary": {"next_action": "review quality report"},
    }


# ---------------------------------------------------------------------------
# Readiness checks
# ---------------------------------------------------------------------------

def test_flagship_readiness_checks_run():
    result = run_flagship_readiness_checks(str(REPO_ROOT))
    assert "checks" in result
    assert result["total_checks"] >= 15
    assert isinstance(result["readiness_score"], float)


def test_flagship_readiness_core_checks_pass():
    result = run_flagship_readiness_checks(str(REPO_ROOT))
    check_map = {c["name"]: c["passed"] for c in result["checks"]}
    assert check_map.get("mission_runner_present") is True
    assert check_map.get("executor_present") is True
    assert check_map.get("benchmark_harness_present") is True
    assert check_map.get("mutation_safety_present") is True
    assert check_map.get("mutation_provenance_present") is True
    assert check_map.get("adapter_registry_present") is True
    assert check_map.get("flagship_proof_present") is True


def test_readiness_score_high_when_all_pass():
    result = run_flagship_readiness_checks(str(REPO_ROOT))
    assert result["readiness_score"] >= 0.85


# ---------------------------------------------------------------------------
# Operator runbook
# ---------------------------------------------------------------------------

def test_operator_runbook_structure():
    mission_result = _make_mission_result()
    runbook = build_operator_runbook("Build a SaaS app", mission_result)
    assert "runbook_version" in runbook
    assert isinstance(runbook["operator_steps"], list)
    assert len(runbook["operator_steps"]) >= 5
    assert "approval_workflow" in runbook
    assert "restore_workflow" in runbook
    assert "known_limitations" in runbook


def test_operator_runbook_limitations_honest():
    mission_result = _make_mission_result()
    runbook = build_operator_runbook("goal", mission_result)
    combined = " ".join(runbook["known_limitations"])
    assert "bounded" in combined or "structural" in combined or "operator" in combined


def test_operator_runbook_approval_detected():
    mission_result = _make_mission_result(status="awaiting_approval", approval=True)
    runbook = build_operator_runbook("Delete production db", mission_result)
    assert runbook["approval_workflow"]["required"] is True


# ---------------------------------------------------------------------------
# Truth audit
# ---------------------------------------------------------------------------

def test_truth_audit_runs():
    audit = build_truth_audit(str(REPO_ROOT))
    assert "checks" in audit
    assert audit["total_checks"] >= 3
    assert isinstance(audit["truth_score"], float)


def test_truth_audit_security_maturity_honest():
    audit = build_truth_audit(str(REPO_ROOT))
    check_map = {c["check"]: c["passed"] for c in audit["checks"]}
    assert check_map.get("security_maturity_honest", True) is True
    assert check_map.get("commerce_maturity_honest", True) is True
    assert check_map.get("multimodal_maturity_honest", True) is True


# ---------------------------------------------------------------------------
# Launch evidence
# ---------------------------------------------------------------------------

def test_launch_evidence_structure():
    mission_result = _make_mission_result()
    readiness = run_flagship_readiness_checks(str(REPO_ROOT))
    evidence = build_launch_evidence(mission_result, readiness)
    assert "launch_ready" in evidence
    assert "readiness_score" in evidence
    assert "evidence_items" in evidence
    assert isinstance(evidence["evidence_items"], list)


def test_launch_evidence_low_confidence_not_ready():
    mission_result = _make_mission_result(confidence=0.3)
    readiness = {"all_passed": True, "readiness_score": 1.0}
    evidence = build_launch_evidence(mission_result, readiness)
    assert evidence["launch_ready"] is False
    assert "mission_confidence_threshold" in evidence["blocking_issues"]


def test_launch_evidence_high_confidence_ready():
    mission_result = _make_mission_result(confidence=0.9)
    readiness = {"all_passed": True, "readiness_score": 1.0}
    evidence = build_launch_evidence(mission_result, readiness)
    assert evidence["launch_ready"] is True
    assert evidence["blocking_issues"] == []


# ---------------------------------------------------------------------------
# Full bundle
# ---------------------------------------------------------------------------

def test_flagship_bundle_structure():
    mission_result = _make_mission_result()
    bundle = build_flagship_readiness_bundle(mission_result, str(REPO_ROOT))
    assert bundle.bundle_id.startswith("flagship-")
    assert len(bundle.bundle_signature) > 0
    assert bundle.readiness_checks["total_checks"] >= 15
    assert bundle.truth_audit["total_checks"] >= 3
    assert "launch_ready" in bundle.launch_evidence


def test_flagship_bundle_has_operator_runbook():
    mission_result = _make_mission_result()
    bundle = build_flagship_readiness_bundle(mission_result, str(REPO_ROOT))
    assert "operator_steps" in bundle.operator_runbook
    assert len(bundle.operator_runbook["operator_steps"]) >= 5


def test_flagship_bundle_to_dict():
    mission_result = _make_mission_result()
    bundle = build_flagship_readiness_bundle(mission_result, str(REPO_ROOT))
    d = bundle.to_dict()
    assert "bundle_id" in d
    assert "launch_evidence" in d
    assert "truth_audit" in d
    assert "operator_runbook" in d


def test_flagship_bundle_emit_to_disk(tmp_path):
    mission_result = _make_mission_result()
    bundle = build_flagship_readiness_bundle(mission_result, str(REPO_ROOT))
    result = emit_flagship_bundle_to_disk(bundle, str(tmp_path))
    assert Path(result["bundle_path"]).exists()
    assert result["readiness_score"] >= 0.0
