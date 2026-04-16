import hashlib
import json
from pathlib import Path

import pytest

import cli.autobuilder as autobuilder_cli
from cli.autobuilder import run_build_workflow


def _hash_files(root: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\n")
        digest.update((root / rel).read_bytes())
        digest.update(b"\n")
    return digest.hexdigest()


def test_build_workflow_emits_file_summary_and_validation_plan(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"

    target = tmp_path / "starter"
    result = run_build_workflow(str(spec_root), str(target))

    assert result["status"] == "ok"
    assert result["files_created_summary"]["count"] > 0
    assert "frontend/app/page.tsx" in result["files_created_summary"]["paths"]
    assert "frontend/components/enterprise-shell.tsx" in result["files_created_summary"]["paths"]
    assert "frontend/components/enterprise-states.tsx" in result["files_created_summary"]["paths"]
    assert "frontend/app/settings/page.tsx" in result["files_created_summary"]["paths"]
    assert "backend/api/main.py" in result["files_created_summary"]["paths"]
    assert "backend/api/admin.py" in result["files_created_summary"]["paths"]
    assert "backend/api/operator.py" in result["files_created_summary"]["paths"]
    assert "backend/api/audit.py" in result["files_created_summary"]["paths"]
    assert "backend/api/responses.py" in result["files_created_summary"]["paths"]
    assert "docs/ENTERPRISE_POLISH.md" in result["files_created_summary"]["paths"]
    assert ".autobuilder/proof_report.json" in result["files_created_summary"]["paths"]
    assert "backend_pytest_endpoints" in result["validation_plan"]
    assert "enterprise_ui_state_surfaces_present" in result["validation_plan"]
    assert result["generated_app_validation"]["all_passed"] is True
    assert result["generated_app_validation"]["failed_count"] == 0
    assert result["determinism"]["verified"] is True
    assert result["determinism"]["repeat_build_match_required"] is True
    assert len(result["execution"]["output_hash"]) == 64
    assert result["execution"]["output_files"]


def test_build_generation_is_deterministic(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"

    target_a = tmp_path / "starter_a"
    target_b = tmp_path / "starter_b"

    result_a = run_build_workflow(str(spec_root), str(target_a))
    result_b = run_build_workflow(str(spec_root), str(target_b))

    files_a = result_a["files_created_summary"]["paths"]
    files_b = result_b["files_created_summary"]["paths"]

    assert files_a == files_b
    assert result_a["validation_plan"] == result_b["validation_plan"]

    hash_a = _hash_files(target_a, files_a)
    hash_b = _hash_files(target_b, files_b)
    assert hash_a == hash_b

    summary_a = json.dumps(result_a["files_created_summary"], sort_keys=True)
    summary_b = json.dumps(result_b["files_created_summary"], sort_keys=True)
    assert summary_a == summary_b
    assert result_a["execution"]["output_hash"] == result_b["execution"]["output_hash"]
    assert result_a["determinism"]["build_signature_sha256"] == result_b["determinism"]["build_signature_sha256"]
    assert result_a["determinism"]["proof_signature_sha256"] == result_b["determinism"]["proof_signature_sha256"]


def test_build_workflow_fails_hard_when_repeat_build_diverges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_root = Path(__file__).resolve().parents[1]
    spec_root = project_root / "specs"

    original_apply = autobuilder_cli.apply_build_plan
    call_count = 0

    def _flaky_apply(plan):
        nonlocal call_count
        call_count += 1
        result = original_apply(plan)
        if call_count == 2:
            mutated = list(result.output_files)
            mutated[0] = {"path": mutated[0]["path"], "sha256": "0" * 64}
            combined = hashlib.sha256(
                "\n".join(f"{item['path']}:{item['sha256']}" for item in mutated).encode("utf-8")
            ).hexdigest()
            return type(result)(
                target_repo=result.target_repo,
                operations_applied=result.operations_applied,
                output_hash=combined,
                output_files=mutated,
            )
        return result

    monkeypatch.setattr(autobuilder_cli, "apply_build_plan", _flaky_apply)

    with pytest.raises(RuntimeError, match="Determinism verification failed"):
        run_build_workflow(str(spec_root), str(tmp_path / "starter"))
