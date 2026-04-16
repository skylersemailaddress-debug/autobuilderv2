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
    archetype_chosen: dict[str, object]
    stack_chosen: dict[str, object]
    planned_repo_structure: list[str]
    planned_modules: list[str]
    planned_validation_surface: list[str]
    operations: list[BuildOperation]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_repo": self.target_repo,
            "archetype_chosen": self.archetype_chosen,
            "stack_chosen": self.stack_chosen,
            "planned_repo_structure": self.planned_repo_structure,
            "planned_modules": self.planned_modules,
            "planned_validation_surface": self.planned_validation_surface,
            "operations": [op.__dict__ for op in self.operations],
        }


def prepare_build_plan(ir: AppIR, target_repo: str | Path) -> BuildPlan:
    target = Path(target_repo).resolve()
    stack_entries = ir.stack_entries
    planned_repo_structure = [
        ".autobuilder/",
        "app/",
        "api/",
        "db/",
        "validation/",
    ]
    planned_modules = [
        "app/README.md",
        ".autobuilder/ir.json",
        ".autobuilder/build_plan.json",
        "api/README.md",
        "db/README.md",
        "validation/README.md",
    ]
    planned_modules.extend(
        module
        for entry in stack_entries.values()
        for module in entry["required_files_modules"]
        if module not in planned_modules
    )
    planned_validation_surface = []
    planned_validation_surface.extend(ir.archetype["expected_validation_concerns"])
    for entry in stack_entries.values():
        for expectation in entry["validation_expectations"]:
            if expectation not in planned_validation_surface:
                planned_validation_surface.append(expectation)

    operations: list[BuildOperation] = [
        BuildOperation(op="create_dir", path=".autobuilder"),
        BuildOperation(op="create_dir", path="app"),
        BuildOperation(op="create_dir", path="api"),
        BuildOperation(op="create_dir", path="db"),
        BuildOperation(op="create_dir", path="validation"),
        BuildOperation(
            op="write_file",
            path="app/README.md",
            content=(
                f"# {ir.app_identity}\n\n"
                "Generated scaffold from AutobuilderV2 spec compiler build mode.\n"
                f"App type: {ir.app_type}\n"
                f"Archetype: {ir.archetype['name']}\n"
                f"Deployment target: {ir.deployment_target}\n"
            ),
        ),
        BuildOperation(
            op="write_file",
            path="api/README.md",
            content=(
                "# API Modules\n\n"
                f"Backend stack: {ir.stack_selection['backend']}\n"
                f"Expected backend shape: {', '.join(ir.archetype['expected_backend_shape'])}\n"
            ),
        ),
        BuildOperation(
            op="write_file",
            path="db/README.md",
            content=(
                "# Database Modules\n\n"
                f"Database stack: {ir.stack_selection['database']}\n"
                "Schema and migration modules will be generated in later tranches.\n"
            ),
        ),
        BuildOperation(
            op="write_file",
            path="validation/README.md",
            content=(
                "# Validation Surface\n\n"
                + "\n".join(f"- {item}" for item in planned_validation_surface)
                + "\n"
            ),
        ),
        BuildOperation(
            op="write_file",
            path=".autobuilder/ir.json",
            content=json.dumps(ir.to_dict(), indent=2),
        ),
        BuildOperation(
            op="write_file",
            path=".autobuilder/build_plan.json",
            content=json.dumps(
                {
                    "archetype_chosen": ir.archetype,
                    "stack_chosen": stack_entries,
                    "planned_repo_structure": planned_repo_structure,
                    "planned_modules": planned_modules,
                    "planned_validation_surface": planned_validation_surface,
                },
                indent=2,
            ),
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
                    f"- archetype: {ir.archetype['name']}\n"
                    f"- frontend: {ir.stack_selection['frontend']}\n"
                    f"- backend: {ir.stack_selection['backend']}\n"
                    f"- database: {ir.stack_selection['database']}\n"
                    f"- deployment: {ir.stack_selection['deployment']}\n"
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
                    f"Archetype: {ir.archetype['name']}\n"
                ),
            )
        )

    return BuildPlan(
        target_repo=str(target),
        archetype_chosen=ir.archetype,
        stack_chosen=stack_entries,
        planned_repo_structure=planned_repo_structure,
        planned_modules=planned_modules,
        planned_validation_surface=planned_validation_surface,
        operations=operations,
    )
