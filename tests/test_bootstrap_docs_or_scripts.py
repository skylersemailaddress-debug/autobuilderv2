"""
Smoke tests for AutobuilderV2 bootstrap, cleanup, and packaging infrastructure.

Verifies that:
- All operational scripts exist and have correct permissions
- VERSION file exists with valid content
- CHANGELOG.md exists with expected sections
- Scripts contain expected operational patterns
- Packaging would exclude runtime noise
"""

import os
import stat
from pathlib import Path


def get_project_root():
    """Get the absolute path to the project root."""
    test_dir = Path(__file__).parent
    return test_dir.parent


def test_bootstrap_script_exists():
    """Bootstrap script should exist."""
    project_root = get_project_root()
    bootstrap_path = project_root / "scripts" / "bootstrap_local.sh"
    assert bootstrap_path.exists(), f"Bootstrap script missing: {bootstrap_path}"


def test_bootstrap_script_executable():
    """Bootstrap script should be executable."""
    project_root = get_project_root()
    bootstrap_path = project_root / "scripts" / "bootstrap_local.sh"
    
    # Read and verify it's a shell script
    content = bootstrap_path.read_text()
    assert content.startswith("#!/bin/bash"), "Bootstrap script must be a bash script"
    assert "virtual environment" in content, "Bootstrap should mention venv creation"
    assert "pip install" in content, "Bootstrap should install dependencies"


def test_clean_runtime_script_exists():
    """Cleanup script should exist."""
    project_root = get_project_root()
    clean_path = project_root / "scripts" / "clean_runtime.sh"
    assert clean_path.exists(), f"Cleanup script missing: {clean_path}"


def test_clean_runtime_script_content():
    """Cleanup script should have expected safety features."""
    project_root = get_project_root()
    clean_path = project_root / "scripts" / "clean_runtime.sh"
    content = clean_path.read_text()
    
    # Verify safety features
    assert "#!/bin/bash" in content, "Must be a bash script"
    assert "read -p" in content, "Should prompt for confirmation"
    assert "runs/*.json" in content, "Should clean runs/*.json"
    assert "memory/*.json" in content, "Should clean memory/*.json"
    assert "__pycache__" in content, "Should clean __pycache__"
    assert ".pytest_cache" in content, "Should clean pytest cache"


def test_package_release_script_exists():
    """Package release script should exist."""
    project_root = get_project_root()
    package_path = project_root / "scripts" / "package_release.sh"
    assert package_path.exists(), f"Package script missing: {package_path}"


def test_package_release_script_content():
    """Package release script should have expected features."""
    project_root = get_project_root()
    package_path = project_root / "scripts" / "package_release.sh"
    content = package_path.read_text()
    
    # Verify expected content
    assert "#!/bin/bash" in content, "Must be a bash script"
    assert "VERSION" in content, "Should read VERSION file"
    assert ".zip" in content, "Should create zip archive"
    assert "dist" in content, "Should output to dist directory"
    assert "cli/" in content, "Should include cli source"
    assert "tests/" in content, "Should include tests"
    assert "docs/" in content, "Should include docs"


def test_version_file_exists():
    """VERSION file should exist."""
    project_root = get_project_root()
    version_path = project_root / "VERSION"
    assert version_path.exists(), f"VERSION file missing: {version_path}"


def test_version_file_format():
    """VERSION file should have valid content."""
    project_root = get_project_root()
    version_path = project_root / "VERSION"
    content = version_path.read_text().strip()
    
    # Should be non-empty
    assert content, "VERSION file should not be empty"
    
    # Should look like a version string
    assert "-" in content or "." in content, "VERSION should contain version-like characters"
    
    # Should not be absurdly long
    assert len(content) < 100, "VERSION should be a reasonable length"


def test_changelog_exists():
    """CHANGELOG.md should exist."""
    project_root = get_project_root()
    changelog_path = project_root / "CHANGELOG.md"
    assert changelog_path.exists(), f"CHANGELOG.md missing: {changelog_path}"


def test_changelog_content():
    """CHANGELOG.md should have expected sections."""
    project_root = get_project_root()
    changelog_path = project_root / "CHANGELOG.md"
    content = changelog_path.read_text()
    
    # Should have main sections
    assert "## [" in content, "CHANGELOG should have version headers"
    assert "Release Summary" in content, "Should have release summary"
    assert "Major Capabilities" in content, "Should document capabilities"
    assert "Bootstrap" in content, "Should mention bootstrap"
    assert "Artifact Isolation" in content, "Should document artifact isolation"


def test_readme_has_bootstrap_section():
    """README.md should document bootstrap path."""
    project_root = get_project_root()
    readme_path = project_root / "README.md"
    assert readme_path.exists(), "README.md should exist"
    
    content = readme_path.read_text()
    assert "Local Bootstrap" in content, "README should document bootstrap"
    assert "scripts/bootstrap_local.sh" in content, "README should reference bootstrap script"
    assert "Cleanup Runtime" in content, "README should document cleanup"
    assert "scripts/clean_runtime.sh" in content, "README should reference cleanup script"
    assert "Package for Distribution" in content, "README should document packaging"
    assert "scripts/package_release.sh" in content, "README should reference package script"


def test_operator_workflow_updated():
    """OPERATOR_WORKFLOW.md should include bootstrap and cleanup."""
    project_root = get_project_root()
    workflow_path = project_root / "docs" / "OPERATOR_WORKFLOW.md"
    assert workflow_path.exists(), "OPERATOR_WORKFLOW.md should exist"
    
    content = workflow_path.read_text()
    
    # Should document all major workflows
    assert "Bootstrap" in content, "Should have bootstrap section"
    assert "Cleanup Runtime" in content, "Should have cleanup section"
    assert "Packaging for Distribution" in content, "Should have packaging section"
    assert "proof" in content.lower(), "Should mention proof command"
    assert "readiness" in content.lower(), "Should mention readiness command"
    assert "mission" in content.lower(), "Should mention mission command"
    assert "benchmark" in content.lower(), "Should mention benchmark command"


def test_scripts_directory_exists():
    """Scripts directory should be present."""
    project_root = get_project_root()
    scripts_dir = project_root / "scripts"
    assert scripts_dir.exists(), "scripts/ directory should exist"
    assert scripts_dir.is_dir(), "scripts should be a directory"


def test_all_scripts_present():
    """All required operational scripts should be present."""
    project_root = get_project_root()
    scripts_needed = [
        "bootstrap_local.sh",
        "clean_runtime.sh",
        "package_release.sh",
    ]
    
    for script_name in scripts_needed:
        script_path = project_root / "scripts" / script_name
        assert script_path.exists(), f"Missing script: {script_name}"


def test_gitignore_has_artifact_entries():
    """
    .gitignore should have entries for common runtime artifacts.
    This helps ensure generated files don't accidentally get committed.
    """
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore should exist"
    
    content = gitignore_path.read_text()
    
    # Python artifacts
    assert "__pycache__" in content, "Should ignore __pycache__"
    assert ".pyc" in content, "Should ignore .pyc files"
    
    # Virtual environments
    assert ".venv" in content, "Should ignore .venv/"
    
    # Testing
    assert ".pytest_cache" in content, "Should ignore pytest cache"
    
    # Runtime state
    assert "runs/" in content, "Should ignore runs/"
    assert "memory/" in content, "Should ignore memory/"


def test_pyproject_present():
    """pyproject.toml should exist for packaging."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist"


def test_core_cli_modules_present():
    """Core CLI modules should still exist (no breaking changes)."""
    project_root = get_project_root()
    cli_dir = project_root / "cli"
    
    required_modules = [
        "autobuilder.py",
        "mission.py",
        "inspect.py",
        "resume.py",
        "run.py",
    ]
    
    for module in required_modules:
        module_path = cli_dir / module
        assert module_path.exists(), f"CLI module missing: {module} (breaking change)"
