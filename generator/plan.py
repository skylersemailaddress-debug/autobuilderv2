from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from generator.template_packs import first_class_validation_plan, generate_first_class_templates
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
    templates = generate_first_class_templates(ir)

    planned_repo_structure = [
        ".autobuilder/",
        "backend/",
        "backend/api/",
        "backend/tests/",
        "frontend/",
        "frontend/app/",
        "frontend/app/settings/",
        "frontend/app/admin/",
        "frontend/app/activity/",
        "frontend/components/",
        "frontend/public/",
        "frontend/tests/",
        "db/",
        "docs/",
        "release/",
        "release/deploy/",
        "release/runbook/",
        "release/proof/",
    ]
    planned_repo_structure = sorted(set(planned_repo_structure))

    stack_modules = [
        module
        for category in sorted(stack_entries)
        for module in stack_entries[category]["required_files_modules"]
    ]

    planned_modules = [template.path for template in templates]
    for module in stack_modules:
        if module not in planned_modules:
            planned_modules.append(module)
    if ".autobuilder/ir.json" not in planned_modules:
        planned_modules.append(".autobuilder/ir.json")
    if ".autobuilder/build_plan.json" not in planned_modules:
        planned_modules.append(".autobuilder/build_plan.json")
    if ".autobuilder/generation_summary.json" not in planned_modules:
        planned_modules.append(".autobuilder/generation_summary.json")
    planned_modules = sorted(set(planned_modules))

    planned_validation_surface: list[str] = []
    for item in ir.archetype["expected_validation_concerns"]:
        if item not in planned_validation_surface:
            planned_validation_surface.append(item)
    for category in sorted(stack_entries):
        for expectation in stack_entries[category]["validation_expectations"]:
            if expectation not in planned_validation_surface:
                planned_validation_surface.append(expectation)
    for check in first_class_validation_plan():
        if check not in planned_validation_surface:
            planned_validation_surface.append(check)
    planned_validation_surface = sorted(planned_validation_surface)

    templates_by_path = sorted(templates, key=lambda template: template.path)

    operations: list[BuildOperation] = [
        BuildOperation(op="create_dir", path=path.rstrip("/")) for path in planned_repo_structure
    ]
    write_operations: list[BuildOperation] = [
        BuildOperation(op="write_file", path=template.path, content=template.content)
        for template in templates_by_path
    ]
    write_operations.append(
        BuildOperation(
            op="write_file",
            path=".autobuilder/ir.json",
            content=json.dumps(ir.to_dict(), indent=2, sort_keys=True),
        )
    )
    write_operations.append(
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
                sort_keys=True,
            ),
        )
    )
    write_operations.append(
        BuildOperation(
            op="write_file",
            path=".autobuilder/generation_summary.json",
            content=json.dumps(
                {
                    "generated_files": sorted(planned_modules),
                    "validation_plan": sorted(planned_validation_surface),
                },
                indent=2,
                sort_keys=True,
            ),
        )
    )
    operations.extend(sorted(write_operations, key=lambda operation: operation.path))

    return BuildPlan(
        target_repo=str(target),
        archetype_chosen=ir.archetype,
        stack_chosen=stack_entries,
        planned_repo_structure=planned_repo_structure,
        planned_modules=planned_modules,
        planned_validation_surface=planned_validation_surface,
        operations=operations,
    )
