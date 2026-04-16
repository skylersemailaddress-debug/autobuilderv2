from pathlib import Path

from cli.autobuilder import run_proof_workflow


def test_end_to_end_proof_workflow_runs():
    proof = run_proof_workflow()

    assert proof["proof_status"] == "ok"
    assert proof["mission_started"] is True
    assert proof["approval_pause_detected"] is True
    assert proof["inspect_reachable"] is True
    assert proof["resume_path_exists"] is True
    assert proof["resume_completed"] is True
    assert proof["benchmark_executed"] is True
    assert proof["readiness_generated"] is True

    project_root = Path(__file__).resolve().parents[1]
    for run_id_key in ("low_risk_run_id", "approval_run_id", "resumed_run_id"):
        run_id = proof["artifacts"][run_id_key]
        run_file = project_root / "runs" / f"{run_id}.json"
        mission_file = project_root / "runs" / f"{run_id}.mission.json"
        if run_file.exists():
            run_file.unlink()
        if mission_file.exists():
            mission_file.unlink()
