import os
from pathlib import Path
from planner.repo_context import inspect_repo_context


def test_inspect_repo_context_detects_top_level_folders_and_configs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = \"autobuilder\"\n")
    (tmp_path / "package.json").write_text('{"name": "autobuilder"}')

    context = inspect_repo_context(tmp_path)

    assert context["repo_mode"] is True
    assert "src" in context["top_level_folders"]
    assert "tests" in context["top_level_folders"]
    assert "pyproject.toml" in context["config_files"]
    assert "package.json" in context["config_files"]
    assert "tests" in context["test_folders"]
    assert "python" in context["framework_hints"]
    assert "node" in context["framework_hints"]


def test_inspect_repo_context_detects_framework_hints_in_files(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "requirements.txt").write_text("flask\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")

    context = inspect_repo_context(tmp_path)

    assert "requirements.txt" in context["config_files"]
    assert "Dockerfile" in context["config_files"]
    assert "flask" in context["framework_hints"]
    assert "python" in context["framework_hints"]
    assert "tests" not in context["test_folders"]
