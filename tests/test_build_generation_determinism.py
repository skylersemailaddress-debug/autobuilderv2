import hashlib
import json
from pathlib import Path

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
    assert "backend/api/main.py" in result["files_created_summary"]["paths"]
    assert "backend_pytest_endpoints" in result["validation_plan"]


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
