import json
from pathlib import Path

import pytest

from platform_hardening.capability_maturity import (
    CapabilityContractError,
    evaluate_capability_family,
    enforce_lane_contract,
)
from cli.autobuilder import run_build_workflow


def test_lane_maturity_contract_enforces_frontend_stack() -> None:
    contract = enforce_lane_contract(
        "mobile_app",
        {
            "frontend": "flutter_mobile",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    )
    assert contract.lane_id == "first_class_mobile"
    assert contract.maturity == "first_class"

    with pytest.raises(CapabilityContractError, match="only supports frontend stack"):
        enforce_lane_contract(
            "mobile_app",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        )


def test_capability_family_reports_unsupported_requests() -> None:
    contract = evaluate_capability_family(
        "chat-first",
        requested=["conversation_to_spec", "auto_ship_without_preview"],
    )
    assert contract["accepted"] is False
    assert "auto_ship_without_preview" in contract["unsupported_requested"]


def test_build_workflow_exposes_lane_maturity_contract(tmp_path: Path) -> None:
    spec_root = tmp_path / "mobile_specs"
    spec_root.mkdir()

    files = {
        "product.yaml": {"name": "Mobile Contract", "app_type": "mobile_app"},
        "architecture.yaml": {
            "entities": [{"name": "User"}],
            "workflows": [{"name": "Flow"}],
            "api_routes": [{"path": "/health"}],
            "runtime_services": [{"name": "api"}],
            "permissions": [{"role": "user"}],
        },
        "ui.yaml": {"pages": [{"name": "Home", "route": "/"}]},
        "acceptance.yaml": {"criteria": ["works"]},
        "stack.yaml": {
            "frontend": "flutter_mobile",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
            "deployment_target": "container",
        },
    }
    for name, payload in files.items():
        (spec_root / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")

    result = run_build_workflow(str(spec_root), str(tmp_path / "out"))
    assert result["lane_maturity_contract"]["lane_id"] == "first_class_mobile"
    assert result["lane_maturity_contract"]["maturity"] == "first_class"


def test_build_workflow_rejects_unsupported_lane_stack_pair(tmp_path: Path) -> None:
    spec_root = tmp_path / "bad_mobile_specs"
    spec_root.mkdir()
    files = {
        "product.yaml": {"name": "Bad Mobile Contract", "app_type": "mobile_app"},
        "architecture.yaml": {
            "entities": [{"name": "User"}],
            "workflows": [{"name": "Flow"}],
            "api_routes": [{"path": "/health"}],
            "runtime_services": [{"name": "api"}],
            "permissions": [{"role": "user"}],
        },
        "ui.yaml": {"pages": [{"name": "Home", "route": "/"}]},
        "acceptance.yaml": {"criteria": ["works"]},
        "stack.yaml": {
            "frontend": "react_next",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
            "deployment_target": "container",
        },
    }
    for name, payload in files.items():
        (spec_root / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(CapabilityContractError, match="only supports frontend stack"):
        run_build_workflow(str(spec_root), str(tmp_path / "out_bad"))
