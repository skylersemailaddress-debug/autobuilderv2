# Spec Compiler Foundations

This document defines the canonical spec bundle and the current build-mode compiler path in AutobuilderV2.

## Scope

AutobuilderV2 provides a deterministic compiler spine and commercial generation surface:

1. Load and validate canonical specs.
2. Resolve app archetype and stack selections.
3. Compile normalized specs into internal IR.
4. Prepare and execute a target-repo build plan.
5. Generate a real starter app scaffold for the first-class stack.
6. Enforce enterprise generated-app validation gates before build succeeds.
7. Attempt bounded generated-app repairs for common stack defects.
8. Emit proof certification artifacts for generated-app trust signals.
9. Emit packaging and deployment-readiness bundle artifacts for product handoff.
10. Emit stack-specific runtime verification, security/governance, commerce, pack composition, failure corpus, and replay harness artifacts.

The compiler/build lane is now plugin-driven with deterministic resolution across plugin categories:

- archetype plugins
- stack plugins
- generation backend plugins
- validation plugins
- repair policy plugins
- packaging target plugins
- runtime verification and repair-policy hardening modules
- platform power-pack composition modules
- security/governance contract modules
- commerce/billing contract modules

Current production lane is the `first_class_commercial` plugin set.

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
- `mobile_app`
- `game_app`
- `realtime_system`
- `enterprise_agent_system`

Lane support matrix:

- `first_class_commercial`: `react_next` + `fastapi` + `postgres` + `docker_compose` (`first_class`)
- `first_class_mobile`: `flutter_mobile` + `fastapi` + `postgres` + `docker_compose` (`first_class`)
- `first_class_game`: `godot_game` + `fastapi` + `postgres` + `docker_compose` (`bounded_prototype`)
- `first_class_realtime`: `react_next` + `fastapi` + `postgres` + `docker_compose` (`first_class`)
- `first_class_enterprise_agent`: `react_next` + `fastapi` + `postgres` + `docker_compose` (`first_class`)

Support category definitions:

- `first_class`: deterministic generation/validation/proof/ship.
- `bounded_prototype`: deterministic but intentionally scoped runtime envelope.
- `structural_only`: contracts/schema with bounded hooks.
- `future`: placeholder only.

## Command Safety Guarantees

JSON outputs for `mission`, `resume`, `inspect`, `build`, `ship`, `chat-build`, `agent-runtime`, and `self-extend` include `audit_record` and `safety_guarantee` metadata.

- `mission`: dangerous goals require approval, capture approval history, and emit restore payloads when checkpoints are required.
- `resume`: only continues after approved governance state and records resumed audit outcome.
- `inspect`: remains read-only while surfacing rollback and audit state.
- `build` and `ship`: preserve deterministic validation/proof semantics and expose rollback-ready proof metadata.
- `chat-build`: keeps preview-first gating before approved build execution.
- `agent-runtime`: keeps bounded execution with explicit approval-gated step handling.
- `self-extend`: keeps sandbox and quarantine controls around synthesized capabilities.

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

Canonical ship mode command:

```bash
python cli/autobuilder.py ship --spec <spec_dir> --target <repo_path> --json
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

Build output now generates:

- `.autobuilder/ir.json`
- `.autobuilder/build_plan.json`
- `.autobuilder/README.md`
- `.autobuilder/proof_report.json`
- `.autobuilder/readiness_report.json`
- `README.md` with startup and test instructions
- `frontend/*` React/Next enterprise shell including:
	- deterministic loading/empty/error state components
	- shell navigation/header and status notification conventions
	- operator-facing settings/admin/activity route placeholders
- `backend/*` FastAPI service and endpoint tests including:
	- structured response envelopes
	- admin/operator/audit placeholder routes
	- structured logging/config placeholders
- `db/schema.sql`
- `docker-compose.yml`
- `.env.example` and backend env example
- `docs/OPERATOR.md`
- `docs/ENTERPRISE_POLISH.md`
- `docs/READINESS.md`
- `docs/PROOF_OF_RUN.md`
- `docs/DEPLOYMENT.md`
- `docs/STARTUP_VALIDATION.md`
- `release/README.md`
- `release/deploy/DEPLOYMENT_NOTES.md`
- `release/runbook/OPERATOR_RUNBOOK.md`
- `release/proof/PROOF_BUNDLE.md`
- `.autobuilder/package_artifact_summary.json`
- `.autobuilder/proof_readiness_bundle.json`

Structured build plan output includes:

- `archetype_chosen`
- `stack_chosen`
- `planned_repo_structure`
- `planned_modules`
- `planned_validation_surface`

Structured build result output includes:

- `files_created_summary`
- `validation_plan`
- `generated_app_validation`
- `build_status`, `validation_status`, `proof_status`
- `repair_report`, `repaired_issues`, `unrepaired_blockers`
- `proof_artifacts`
- `packaging_summary`
- `deployment_readiness_summary`
- `proof_summary`
- `execution.operations_applied` with deterministic hashes
- `proof_artifacts.artifact_paths.runtime_verification`
- `proof_artifacts.artifact_paths.security_governance_contract`
- `proof_artifacts.artifact_paths.commerce_pack_contract`
- `proof_artifacts.artifact_paths.pack_composition`
- `proof_artifacts.artifact_paths.failure_corpus`
- `proof_artifacts.artifact_paths.replay_harness`

Structured ship result output includes:

- `build_status`
- `archetype`
- `stack`
- `files_generated`
- `validation_result`
- `repair_actions_taken`
- `proof_result`
- `readiness_result`
- `packaged_app_artifact_summary`
- `deployment_readiness_summary`
- `proof_summary`
- `final_target_path`

## Hardening Artifacts

Build/proof flow now emits deterministic hardening artifacts under `.autobuilder/`:

- `runtime_verification.json`
- `security_governance_contract.json`
- `commerce_pack_contract.json`
- `pack_composition.json`
- `failure_corpus.jsonl`
- `replay_harness.json`

## Template Packs

Internal template packs are used to build the app scaffold (no donor repository merge strategy):

- frontend shell templates
- frontend enterprise polish pack templates:
	- loading states
	- empty states
	- error states
	- shell navigation/header
	- status/notification conventions
	- settings/admin/activity surfaces
- API service templates
- backend enterprise placeholders:
	- response envelope helpers
	- admin/operator/audit route placeholders
	- logging placeholders
- runtime/config templates
- deployment templates

Template generation is implemented in `generator/template_packs.py` and consumed through `generator/plan.py`.

## Target Repo Mutation Foundation

`generator` layer includes:

- `prepare_build_plan`: deterministic list of scoped operations
- `apply_build_plan`: executes `create_dir`, `write_file`, `update_file`

Safety guarantees:

- all mutation paths are resolved under `--target`
- path traversal outside target is rejected
- each applied operation includes machine-readable status and hash
- generated app must pass enterprise validation checks before build returns success

## Generated-App Validation/Repair/Proof Commands

Validate generated app shape:

```bash
python cli/autobuilder.py validate-app --target <repo_path> --json
```

Validate and bounded-repair generated app:

```bash
python cli/autobuilder.py validate-app --target <repo_path> --repair --json
```

Emit generated-app proof artifacts and certification status:

```bash
python cli/autobuilder.py proof-app --target <repo_path> --repair --json
```

### Strict Failure Semantics

- incomplete spec bundles: fail
- deterministic repeat-build divergence: fail
- unrepairable generated-app validation blockers: fail
- missing or non-certified proof/readiness artifacts: fail

Proof artifacts written under `.autobuilder/`:

- `proof_report.json`
- `readiness_report.json`
- `validation_summary.json`
- `determinism_signature.json`
- `package_artifact_summary.json`
- `proof_readiness_bundle.json`

## Command Surface Contract

Top-level commands produce machine-readable JSON with:

- `status`: `ok` or `error`
- `command`: command identifier
- command-specific payload fields

Failure semantics are stable:

- `build`/`ship`/`chat-build`/`self-extend` return non-zero on deterministic contract errors
- `validate-app`/`proof-app` return non-zero when validation/proof requirements are not met
- `agent-runtime` returns `ok` with `completed` or `blocked` execution status depending on approval-gated steps

## Plugin Registry

`platform_plugins/registry.py` provides:

- automatic plugin registration/discovery
- plugin inventory listing by type
- deterministic plugin resolution for the same spec inputs
- clean failure when no compatible plugin combination exists

## Current Limitations

- Only the defined support-matrix lanes are generated.
- YAML fallback without `PyYAML` requires JSON-compatible YAML syntax.
- Generated starter is intentionally clean and minimal but deployable locally.
- First-class lanes are constrained to:
  - `react_next` + `fastapi` + `postgres` + `docker_compose`
  - `flutter_mobile` + `fastapi` + `postgres` + `docker_compose`
  - `godot_game` + `fastapi` + `postgres` + `docker_compose`
	- realtime/sensing profile on `react_next` + `fastapi` + `postgres` + `docker_compose`
	- enterprise-agent/workflow profile on `react_next` + `fastapi` + `postgres` + `docker_compose`
- Existing readiness/proof/benchmark/mission/repair flows remain deterministic and unchanged in contract.
