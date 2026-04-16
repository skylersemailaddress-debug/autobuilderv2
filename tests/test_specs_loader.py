from pathlib import Path

import pytest

from specs.loader import SpecValidationError, load_spec_bundle


REQUIRED_FILES = {
    "product.yaml": '{"name": "Sample App", "app_type": "web_app"}\n',
    "architecture.yaml": '{"entities": [], "workflows": [], "api_routes": [], "runtime_services": [], "permissions": []}\n',
    "ui.yaml": '{"pages": []}\n',
    "acceptance.yaml": '{"criteria": ["works"]}\n',
    "stack.yaml": '{"deployment_target": "container"}\n',
}


def _write_bundle(root: Path) -> None:
    for file_name, content in REQUIRED_FILES.items():
        (root / file_name).write_text(content, encoding="utf-8")


def test_load_spec_bundle_success_from_canonical_specs():
    project_root = Path(__file__).resolve().parents[1]
    bundle = load_spec_bundle(project_root / "specs")

    assert bundle.app_identity == "Autobuilder Demo App"
    assert bundle.app_type == "web_app"
    assert bundle.deployment_target == "container"
    assert len(bundle.acceptance_criteria) >= 1


def test_load_spec_bundle_fails_when_required_file_missing(tmp_path: Path):
    _write_bundle(tmp_path)
    (tmp_path / "ui.yaml").unlink()

    with pytest.raises(SpecValidationError, match="Missing required spec files"):
        load_spec_bundle(tmp_path)
