from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ir.model import AppIR


@dataclass(frozen=True)
class BuildOperation:
    op: str
    path: str
    content: str | None = None


@dataclass(frozen=True)
class BuildPlan:
    target_repo: str
    operations: list[BuildOperation]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_repo": self.target_repo,
            "operations": [op.__dict__ for op in self.operations],
        }


def prepare_build_plan(ir: AppIR, target_repo: str | Path) -> BuildPlan:
    target = Path(target_repo).resolve()
    operations: list[BuildOperation] = [
        BuildOperation(op="create_dir", path=".autobuilder"),
        BuildOperation(op="create_dir", path="app"),
        BuildOperation(
            op="write_file",
            path="app/README.md",
            content=(
                f"# {ir.app_identity}\n\n"
                "Generated scaffold from AutobuilderV2 spec compiler build mode.\n"
                f"App type: {ir.app_type}\n"
                f"Deployment target: {ir.deployment_target}\n"
            ),
        ),
        BuildOperation(
            op="write_file",
            path=".autobuilder/ir.json",
            content=json.dumps(ir.to_dict(), indent=2),
        ),
    ]

    root_readme = target / "README.md"
    if root_readme.exists():
        operations.append(
            BuildOperation(
                op="update_file",
                path="README.md",
                content=(
                    "\n\n## Autobuilder Build Metadata\n"
                    f"- app_identity: {ir.app_identity}\n"
                    f"- deployment_target: {ir.deployment_target}\n"
                ),
            )
        )
    else:
        operations.append(
            BuildOperation(
                op="write_file",
                path="README.md",
                content=(
                    f"# {ir.app_identity}\n\n"
                    "Scaffolded target repository prepared by AutobuilderV2 build mode.\n"
                ),
            )
        )

    return BuildPlan(target_repo=str(target), operations=operations)
