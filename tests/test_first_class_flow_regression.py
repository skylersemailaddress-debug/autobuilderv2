from __future__ import annotations

from pathlib import Path

from cli.autobuilder import run_build_workflow, run_ship_workflow


def test_first_class_build_and_ship_still_emit_proof_and_determinism(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"
    target = tmp_path / "regression_target"

    build_result = run_build_workflow(str(spec_root), str(target))
    assert build_result["status"] == "ok"
    assert build_result["build_status"] == "ok"
    assert build_result["determinism"]["verified"] is True
    assert build_result["proof_artifacts"]["proof_status"].startswith("certified")

    execution = build_result["execution"]
    assert "output_hash" in execution
    assert "output_files" in execution
    assert "lifecycle_regeneration_decisions" in execution

    artifacts = build_result["proof_artifacts"]["artifact_paths"]
    assert Path(artifacts["proof_bundle"]).exists()
    assert Path(artifacts["security_governance_contract"]).exists()
    assert Path(artifacts["commerce_pack_contract"]).exists()
    assert Path(artifacts["lifecycle_contract"]).exists()

    ship_result = run_ship_workflow(str(spec_root), str(target))
    assert ship_result["status"] == "ok"
    assert ship_result["build_status"] == "ok"
    assert ship_result["proof_result"]["status"].startswith("certified")
