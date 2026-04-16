from pathlib import Path

from cli.autobuilder import run_build_workflow


def test_build_emits_packaging_and_proof_bundle_reports(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    result = run_build_workflow(str(project_root / "specs"), str(tmp_path / "packaged_app"))

    assert result["status"] == "ok"
    assert result["packaging_summary"]["packaging_status"] == "ready"
    assert result["deployment_readiness_summary"]["status"] == "ready"
    assert result["proof_summary"]["bundle_status"] == "complete"


def test_build_generates_deployment_docs_and_env_files(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    target = tmp_path / "packaged_app"
    run_build_workflow(str(project_root / "specs"), str(target))

    assert (target / "docs" / "DEPLOYMENT.md").exists()
    assert (target / "docs" / "STARTUP_VALIDATION.md").exists()
    assert (target / "release" / "deploy" / "DEPLOYMENT_NOTES.md").exists()
    assert (target / "release" / "runbook" / "OPERATOR_RUNBOOK.md").exists()
    assert (target / ".env.example").exists()
    assert (target / "backend" / ".env.example").exists()


def test_build_proof_bundle_is_complete(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    target = tmp_path / "packaged_app"
    run_build_workflow(str(project_root / "specs"), str(target))

    assert (target / ".autobuilder" / "proof_report.json").exists()
    assert (target / ".autobuilder" / "readiness_report.json").exists()
    assert (target / ".autobuilder" / "validation_summary.json").exists()
    assert (target / ".autobuilder" / "determinism_signature.json").exists()
    assert (target / ".autobuilder" / "package_artifact_summary.json").exists()
    assert (target / ".autobuilder" / "proof_readiness_bundle.json").exists()
