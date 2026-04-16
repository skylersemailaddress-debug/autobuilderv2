# Spec Compiler Foundations

This document defines the canonical spec bundle and the current build-mode compiler path in AutobuilderV2.

## Scope

This tranche adds a deterministic compiler spine and commercial planning surface:

1. Load and validate canonical specs.
2. Resolve app archetype and stack selections.
3. Compile normalized specs into internal IR.
4. Prepare and execute a target-repo build plan.

It does not add full framework-specific code generation yet.

## Canonical Spec Bundle

Build mode expects a directory containing these files:

- `product.yaml`
- `architecture.yaml`
- `ui.yaml`
- `acceptance.yaml`
- `stack.yaml`

Required keys by file:

- `product.yaml`: `name`, `app_type`
- `architecture.yaml`: `entities`, `workflows`, `api_routes`, `runtime_services`, `permissions`
- `ui.yaml`: `pages`
- `acceptance.yaml`: `criteria`
- `stack.yaml`: `frontend`, `backend`, `database`, `deployment`, `deployment_target`

Supported `app_type` values:

- `internal_tool`
- `workspace_app`
- `saas_web_app`
- `api_service`
- `workflow_system`
- `copilot_chat_app`

First-class supported stack selections in this tranche:

- frontend: `react_next`
- backend: `fastapi`
- database: `postgres`
- deployment: `docker_compose`

Registry placeholders may exist for future expansion, but only the first-class stack above is in scope for deterministic planning in this tranche.

Current parser behavior:

- Reads YAML via `PyYAML` when installed.
- Falls back to JSON-compatible YAML parsing if `PyYAML` is unavailable.
- Fails deterministically with a `SpecValidationError` on missing files, missing keys, wrong top-level types, or invalid field types.

## IR Purpose

The internal IR is a stable app-shape contract between spec parsing and generation. It currently captures:

- app identity
- app type
- archetype resolution
- entities
- workflows
- pages/surfaces
- API routes
- runtime services
- permissions
- stack selection and resolved stack registry entries
- deployment target
- acceptance criteria

Compiler entrypoint:

- `ir/compiler.py::compile_specs_to_ir`

## Build Mode

Command:

```bash
python cli/autobuilder.py build --spec <spec_dir> --target <repo_path> --json
```

Minimum behavior:

1. load specs
2. validate required sections
3. resolve app archetype from `app_type`
4. resolve stack selections through the stack registry
5. compile IR
6. prepare build plan
7. execute target repo mutations
8. emit machine-readable summary JSON

Build output currently scaffolds:

- `.autobuilder/ir.json`
- `.autobuilder/build_plan.json`
- `app/README.md`
- `api/README.md`
- `db/README.md`
- `validation/README.md`
- `README.md` create or append metadata

Structured build plan output includes:

- `archetype_chosen`
- `stack_chosen`
- `planned_repo_structure`
- `planned_modules`
- `planned_validation_surface`

## Target Repo Mutation Foundation

`generator` layer includes:

- `prepare_build_plan`: deterministic list of scoped operations
- `apply_build_plan`: executes `create_dir`, `write_file`, `update_file`

Safety guarantees:

- all mutation paths are resolved under `--target`
- path traversal outside target is rejected
- each applied operation includes machine-readable status and hash

## Support Tiers

- `first_class`: deterministic planning and build-plan support exists now
- `future`: placeholder registry entry only

## Current Limitations

- No full universal code generation templates yet.
- YAML fallback without `PyYAML` requires JSON-compatible YAML syntax.
- Build scaffold is intentionally minimal and deterministic.
- Only the `react_next` + `fastapi` + `postgres` + `docker_compose` stack is first-class in this tranche.
- Existing readiness/proof/benchmark/mission/repair flows are unchanged.
