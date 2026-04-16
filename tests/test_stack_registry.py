import pytest

from stack_registry.registry import StackRegistryResolutionError, resolve_stack_bundle


def test_resolve_stack_bundle_returns_first_class_entries():
    bundle = resolve_stack_bundle(
        {
            "frontend": "react_next",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        }
    )

    assert bundle["frontend"].support_tier == "first_class"
    assert bundle["backend"].required_files_modules
    assert "container_startup" in bundle["deployment"].validation_expectations


def test_resolve_stack_bundle_rejects_unknown_selection():
    with pytest.raises(StackRegistryResolutionError, match="Unsupported frontend stack"):
        resolve_stack_bundle(
            {
                "frontend": "unknown_ui",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            }
        )