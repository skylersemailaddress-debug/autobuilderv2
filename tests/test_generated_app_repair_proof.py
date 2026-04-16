import json
from pathlib import Path

from cli.autobuilder import run_build_workflow, run_generated_app_proof_workflow, run_generated_app_validation_workflow


def test_generated_app_validation_workflow_repairs_common_defects(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"
    target = tmp_path / "generated_app"

    run_build_workflow(str(spec_root), str(target))

    (target / "docs" / "READINESS.md").unlink()
    (target / "backend" / "api" / "admin.py").unlink()
    (target / "frontend" / "components" / "enterprise-states.tsx").unlink()

    result = run_generated_app_validation_workflow(str(target), repair=True)

    assert result["status"] == "ok"
    assert result["validation_status"] == "passed"
    assert result["repaired_issues"]
    assert result["unrepaired_blockers"] == []


def test_generated_app_proof_workflow_emits_certification_artifacts(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"
    target = tmp_path / "generated_app"

    run_build_workflow(str(spec_root), str(target))

    proof = run_generated_app_proof_workflow(str(target), repair=True)

    assert proof["status"] == "ok"
    assert str(proof["proof_status"]).startswith("certified")

    artifact_paths = proof["proof_artifacts"]["artifact_paths"]
    for key in ("proof_report", "readiness_report", "validation_summary", "determinism_signature"):
        artifact_path = Path(artifact_paths[key])
        assert artifact_path.exists()
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
