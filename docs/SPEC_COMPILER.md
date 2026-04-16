# Spec Compiler Foundations

This document defines the canonical spec bundle and the current build-mode compiler path in AutobuilderV2.

## Scope

This tranche adds a deterministic compiler spine:

1. Load and validate canonical specs.
2. Compile normalized specs into internal IR.
3. Prepare and execute a target-repo build plan.

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
- `stack.yaml`: `deployment_target`

Current parser behavior:

- Reads YAML via `PyYAML` when installed.
- Falls back to JSON-compatible YAML parsing if `PyYAML` is unavailable.
- Fails deterministically with a `SpecValidationError` on missing files, missing keys, wrong top-level types, or invalid field types.

## IR Purpose

The internal IR is a stable app-shape contract between spec parsing and generation. It currently captures:

- app identity
- app type
- entities
- workflows
- pages/surfaces
- API routes
- runtime services
- permissions
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
3. compile IR
4. prepare build plan
5. execute target repo mutations
6. emit machine-readable summary JSON

Build output currently scaffolds:

- `.autobuilder/ir.json`
- `app/README.md`
- `README.md` create or append metadata

## Target Repo Mutation Foundation

`generator` layer includes:

- `prepare_build_plan`: deterministic list of scoped operations
- `apply_build_plan`: executes `create_dir`, `write_file`, `update_file`

Safety guarantees:

- all mutation paths are resolved under `--target`
- path traversal outside target is rejected
- each applied operation includes machine-readable status and hash

## Current Limitations

- No full universal code generation templates yet.
- YAML fallback without `PyYAML` requires JSON-compatible YAML syntax.
- Build scaffold is intentionally minimal and deterministic.
- Existing readiness/proof/benchmark/mission/repair flows are unchanged.
