from pathlib import Path
import tomllib


def test_project_contract_sections_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    payload = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert "build-system" in payload
    assert "project" in payload

    project = payload["project"]
    assert project["name"] == "autobuilderv2"
    assert project["requires-python"] == ">=3.12"
    assert "dependencies" in project
    assert "scripts" in project
    assert project["scripts"]["autobuilder"] == "cli.autobuilder:main"

    tool = payload["tool"]
    assert "pytest" in tool
    assert "ruff" in tool
    assert "mypy" in tool
