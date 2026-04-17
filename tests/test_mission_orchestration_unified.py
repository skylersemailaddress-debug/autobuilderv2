"""
Tests for unified mission orchestration: capability routing, machine-readable
plan/state, operator summary, pause/resume semantics, interruption recovery.
"""
from pathlib import Path

from cli.mission import (
    _build_machine_readable_mission_plan,
    _derive_capability_requirements,
    _build_operator_summary,
    _plan_change_set,
    run_mission,
)
from mutation.change_set import ChangeSet


def _cleanup(result):
    for key in ("saved_path", "mission_result_path"):
        v = result.get(key)
        if v:
            p = Path(v)
            if p.exists():
                p.unlink()


# ---------------------------------------------------------------------------
# Capability requirement derivation
# ---------------------------------------------------------------------------

def test_derive_capability_requirements_auth():
    reqs = _derive_capability_requirements("Build a dashboard with auth and rbac")
    families = [r["family"] for r in reqs]
    assert "security" in families


def test_derive_capability_requirements_commerce():
    reqs = _derive_capability_requirements("Add billing and subscription payment checkout")
    families = [r["family"] for r in reqs]
    assert "commerce" in families


def test_derive_capability_requirements_realtime():
    reqs = _derive_capability_requirements("Build realtime event streaming sensor app")
    families = [r["family"] for r in reqs]
    assert "realtime" in families


def test_derive_capability_requirements_multiple():
    reqs = _derive_capability_requirements("Build mobile app with auth and billing")
    families = [r["family"] for r in reqs]
    assert len(families) >= 2
    assert "mobile" in families or "security" in families


def test_derive_capability_requirements_default():
    reqs = _derive_capability_requirements("Do something generic")
    assert len(reqs) >= 1
    assert reqs[0]["family"] == "domain"


def test_derive_capability_requirements_all_have_route():
    reqs = _derive_capability_requirements("Build enterprise agent with auth, billing, realtime monitoring")
    for req in reqs:
        assert "acquisition_route" in req
        assert req["acquisition_route"] in (
            "use_existing", "compose_existing", "generate_pack",
            "generate_adapter", "generate_contract", "generate_tool", "generate_validator",
        )


# ---------------------------------------------------------------------------
# Machine-readable mission plan
# ---------------------------------------------------------------------------

def test_machine_readable_mission_plan_structure():
    change_set = _plan_change_set("Build an app")
    reqs = _derive_capability_requirements("Build an app")
    plan = _build_machine_readable_mission_plan("test-run-001", "Build an app", change_set, reqs)

    assert plan["schema_version"] == "v2"
    assert plan["run_id"] == "test-run-001"
    assert plan["goal"] == "Build an app"
    assert isinstance(plan["capability_requirements"], list)
    assert "change_envelope" in plan
    assert "pause_resume_semantics" in plan
    assert plan["pause_resume_semantics"]["supports_interruption_recovery"] is True
    assert plan["pause_resume_semantics"]["supports_approval_gate"] is True


def test_machine_readable_plan_state_transitions():
    change_set = _plan_change_set("Build an app")
    reqs = _derive_capability_requirements("Build an app")

    plan_planned = _build_machine_readable_mission_plan("r1", "goal", change_set, reqs, state="planned")
    assert plan_planned["state"] == "planned"

    plan_executing = _build_machine_readable_mission_plan("r1", "goal", change_set, reqs, state="executing")
    assert plan_executing["state"] == "executing"


def test_machine_readable_plan_dangerous_approval():
    change_set = _plan_change_set("Delete production database")
    reqs = _derive_capability_requirements("Delete production database")
    plan = _build_machine_readable_mission_plan("r2", "Delete production database", change_set, reqs)
    assert plan["change_envelope"]["approval_required"] is True


# ---------------------------------------------------------------------------
# Operator summary
# ---------------------------------------------------------------------------

def test_operator_summary_structure():
    record = {
        "status": "complete",
        "confidence": 0.9,
        "repair_count": 0,
        "capability_requirements": [{"family": "security"}, {"family": "commerce"}],
        "mission_plan": {"state": "complete"},
        "awaiting_approval": False,
        "checkpoint_required": False,
        "restore_available": False,
        "run_id": "test-op-sum-001",
    }
    summary = _build_operator_summary(record)
    assert summary["status"] == "complete"
    assert summary["mission_state"] == "complete"
    assert "interruption_recovery_supported" in summary
    assert summary["interruption_recovery_supported"] is True
    assert "security" in summary["capability_families_used"]
    assert "next_action" in summary


def test_operator_summary_approval_required():
    record = {
        "status": "awaiting_approval",
        "confidence": 0.5,
        "repair_count": 0,
        "capability_requirements": [],
        "mission_plan": {"state": "paused_approval"},
        "awaiting_approval": True,
        "checkpoint_required": True,
        "restore_available": False,
        "run_id": "test-op-sum-002",
    }
    summary = _build_operator_summary(record)
    assert summary["approval_required"] is True
    assert summary["next_action"] == "approve and resume"


# ---------------------------------------------------------------------------
# Full run_mission integration
# ---------------------------------------------------------------------------

def test_run_mission_emits_capability_requirements():
    result = run_mission("Build an auth and billing dashboard")
    assert "capability_requirements" in result
    assert isinstance(result["capability_requirements"], list)
    assert len(result["capability_requirements"]) >= 1
    _cleanup(result)


def test_run_mission_emits_machine_readable_plan():
    result = run_mission("Build a realtime sensor monitoring app")
    assert "mission_plan" in result
    plan = result["mission_plan"]
    assert "schema_version" in plan
    assert "pause_resume_semantics" in plan
    assert plan["pause_resume_semantics"]["supports_interruption_recovery"] is True
    _cleanup(result)


def test_run_mission_emits_operator_summary():
    result = run_mission("Build an enterprise admin reporting dashboard")
    assert "operator_summary" in result
    summary = result["operator_summary"]
    assert "status" in summary
    assert "mission_state" in summary
    assert "next_action" in summary
    _cleanup(result)


def test_run_mission_dangerous_sets_approval():
    result = run_mission("Delete production resources safely")
    assert result["approval_required"] is True
    _cleanup(result)


def test_run_mission_interruption_recovery_semantics():
    result = run_mission("Delete production database")
    plan = result.get("mission_plan", {})
    ps = plan.get("pause_resume_semantics", {})
    assert ps.get("supports_interruption_recovery") is True
    assert ps.get("supports_pause") is True
    assert ps.get("supports_resume") is True
    _cleanup(result)
