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


def test_packaging_includes_core_runtime_packages() -> None:
    project_root = Path(__file__).resolve().parents[1]
    payload = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    include_patterns = set(payload["tool"]["setuptools"]["packages"]["find"]["include"])
    required = {
        "archetypes*",
        "benchmarks*",
        "chat_builder*",
        "cli*",
        "control_plane*",
        "debugger*",
        "execution*",
        "generator*",
        "ir*",
        "memory*",
        "mutation*",
        "nexus*",
        "observability*",
        "orchestrator*",
        "platform_hardening*",
        "platform_plugins*",
        "planner*",
        "policies*",
        "quality*",
        "readiness*",
        "runs*",
        "specs*",
        "stack_registry*",
        "state*",
        "universal_capability*",
        "validator*",
    }
    assert required.issubset(include_patterns)


def test_packaging_patterns_cover_existing_package_directories() -> None:
    project_root = Path(__file__).resolve().parents[1]
    payload = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    include_patterns = set(payload["tool"]["setuptools"]["packages"]["find"]["include"])

    package_dirs = [
        path.name
        for path in project_root.iterdir()
        if path.is_dir()
        and (path / "__init__.py").exists()
        and path.name not in {"tests", "docs", "scripts", "output-app"}
    ]

    uncovered = [name for name in package_dirs if f"{name}*" not in include_patterns]
    assert not uncovered, f"Missing package include patterns for: {sorted(uncovered)}"
