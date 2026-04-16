# AutobuilderV2

## What is AutobuilderV2?

AutobuilderV2 is a **stateful autonomous execution kernel** for goal-driven software work. It:

- **Plans** tasks from high-level goals with repository context injection
- **Executes** planned work autonomously with durable state recording
- **Validates** outcomes deterministically with bounded self-repair
- **Governs** using operator-controlled approval gates and policies
- **Inspects** via operator-readable run records and status APIs
- **Tracks** complete lineage and audit trails across runs

Perfect for autonomous workflows, CI/CD pipelines, local development, and enterprise governance scenarios requiring deterministic validation.

AutobuilderV2 now also includes a commercial app-planning spine for spec-driven application builds across a controlled set of first-class archetypes and stacks.

AutobuilderV2 now runs this lane through a plugin platform with deterministic plugin resolution for:

- archetypes
- stacks
- code generation backend
- generated-app validation
- repair policy
- packaging/proof targets

Platform hardening layers now also run through deterministic lane contracts:

- stack-specific failure classification and bounded repair policy resolution
- stack-specific runtime/startup verification and machine-readable runtime proof outputs
- reusable power-pack composition (domain/workflow/ui/validation/repair/deployment/asset/research)
- security and governance contracts (auth/authz, RBAC/ABAC-ready, secrets policy, audit, approvals)
- commerce/billing contracts (subscriptions, entitlements, webhooks, invoices/trials/plans)
- failure corpus logging and deterministic replay harness artifacts

## Quick Start

### Local Bootstrap

Initialize a clean development environment (one-time setup):

```bash
scripts/bootstrap_local.sh
```

This creates a virtual environment, installs dependencies, and prints next steps.

### Canonical Commands

Run these canonical commercial-lane commands once the environment is bootstrapped:

```bash
# Check if system is ready
python cli/autobuilder.py readiness --json

# Compile canonical specs into a target repository scaffold
python cli/autobuilder.py build --spec specs --target /tmp/my-app --json

# Canonical one-command commercial builder
python cli/autobuilder.py ship --spec specs --target /tmp/my-app --json

# Chat-first preview and guided build
python cli/autobuilder.py chat-build --prompt "Build a mobile app for school reminders" --target /tmp/my-app --json
python cli/autobuilder.py chat-build --prompt "Build a mobile app for school reminders" --target /tmp/my-app --approve --json

# Computer-use agent runtime modeling/execution
python cli/autobuilder.py agent-runtime --task "Open app, fill form, and save result" --json

# Safe self-extension in sandbox
python cli/autobuilder.py self-extend --lane first_class_commercial --needs custom_validator_for_geo --sandbox /tmp/autobuilder-sandbox --approve-core --json

# Validate generated app structure/surfaces and auto-repair common defects
python cli/autobuilder.py validate-app --target /tmp/my-app --repair --json

# Emit generated-app proof certification artifacts
python cli/autobuilder.py proof-app --target /tmp/my-app --repair --json
```

Operational autonomy commands (`mission`, `resume`, `inspect`, `benchmark`, `proof`) remain available but are secondary to the commercial ship lane above.

### Cleanup Runtime Artifacts

Remove all generated runs, memory, and cache (preserves source/tests/docs):

```bash
scripts/clean_runtime.sh
```

### Package for Distribution

Create a clean, distributable archive:

```bash
scripts/package_release.sh
```

Output archive is in `dist/` directory, ready to distribute or deploy.

## Current capabilities

- Planner: creates task plans from a goal and planning context
- Executor: runs planned tasks and records task output artifacts
- Validator: checks completion status and produces validation evidence
- Repair loop: retries failed validation with bounded repair attempts
- Memory: in-memory plus durable JSON memory for cross-run context
- Repo-targeted planning: repository context is inspected and fed into planning
- Approvals/policy: high-risk goals can pause in awaiting approval state
- Benchmarks: benchmark case runner and report utilities for regression checks
- Readiness evaluation: deterministic readiness checks and final readiness reports
- Inspection CLI: operator-readable run inspection output from saved records
- Nexus0.5 mission mode: enabled with mission-specific run metadata and controls
- Commercial planning: app archetype resolution and controlled stack selection for spec-driven builds
- Build generation: deterministic commercial starter app generation with machine-readable summaries and validation plan

## Commercial Build Support

Supported app archetypes:

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

First-class stack lanes in this tranche:

- web lane: `react_next` + `fastapi` + `postgres` + `docker_compose`
- mobile lane: `flutter_mobile` + `fastapi` + `postgres` + `docker_compose`
- game lane: `godot_game` + `fastapi` + `postgres` + `docker_compose`
- realtime/sensing lane: `react_next` + `fastapi` + `postgres` + `docker_compose`
- enterprise-agent/workflow lane: `react_next` + `fastapi` + `postgres` + `docker_compose`

Enterprise polish in this tranche means generated apps include:

- deterministic loading/empty/error response states
- shell navigation and status conventions
- settings/admin/activity operator surfaces
- backend readiness/version/health and admin/operator/audit placeholders
- proof/readiness and packaging bundle artifacts for handoff

Support tiers:

- `first_class`: implemented and validated in this tranche
- `future`: registry placeholder only, not generated or validated yet

Plugin architecture scope in this tranche:

- production plugin lanes: `first_class_commercial`, `first_class_mobile`, `first_class_game`, `first_class_realtime`, `first_class_enterprise_agent`
- plugin registry resolves compatible plugin combinations deterministically per spec
- unsupported or incompatible plugin combinations fail cleanly before generation

Not yet supported in this tranche:

- additional frontend/backend/database/deployment stacks
- non-first-class stack combinations
- non-Python backend lanes
- production cloud IaC deployment generation

## Canonical interface

Use the top-level Autobuilder CLI as the canonical interface:

```bash
python cli/autobuilder.py --help
```

Supported commands:

- `mission`
- `resume`
- `inspect`
- `benchmark`
- `readiness`
- `proof`
- `build`
- `validate-app`
- `proof-app`
- `ship`
- `chat-build`
- `agent-runtime`
- `self-extend`

## Chat-First Builder UX

AutobuilderV2 now includes a thin, conversation-centered operator surface through `chat-build`:

- one main conversation surface: your plain-language prompt
- plan summary: lane, stack, defaults, questions, and tradeoffs
- build progress: preview, approval, build/proof milestones
- final outputs/proof: readiness/proof/package summaries from ship flow

Preview-first flow:

1. Describe app in plain English
2. Autobuilder infers lane + safe defaults
3. Autobuilder asks only critical missing questions
4. Autobuilder returns a structured spec preview
5. Approve with `--approve` to run build/proof
6. Review final readiness and proof outputs

Safety and explainability in chat flow:

- clear unsupported feature messages
- simple tradeoff explanations
- deterministic default inference (no silent assumption drift)
- next-step guidance in every response

## Universal Capability Layer

AutobuilderV2 now includes bounded universal capability systems for controlled autonomous growth:

- computer-use agent runtime: browser/file/form/app interaction abstractions with audit logs, approval gating, and replay signatures
- multimodal/world-state foundations: text/doc/media/sensor/event references and normalized action-output schema
- self-extension/meta-builder: detect capability gaps, synthesize candidate tools in sandbox, validate, and safely register
- tool factory: deterministic generation of validators/connectors/helpers/domain utilities
- safe governance: tiered registration decisions, quarantine on failure, and rollback for active generated capabilities
- universal failure intelligence: failure corpus and replay artifacts for self-generated capabilities

Commercial guardrails remain intact:

- core build/ship determinism is unchanged
- first-class lane compatibility gates remain enforced
- self-generated capabilities require validation and can be quarantined/rolled back

Canonical commercial lane command order:

1. `readiness`
2. `build`
3. `validate-app`
4. `proof-app`
5. `ship`

Build command options:

- `--spec <path>`: canonical spec bundle directory (default: `specs`)
- `--target <path>`: target repository path for scaffold output

## What build now generates

For each first-class lane, build mode now generates a real starter application into the `--target` repository:

- Web lane (`react_next` + `fastapi` + `postgres` + `docker_compose`) includes:

- Frontend React/Next enterprise shell with:
	- coherent shell layout with navigation and header conventions
	- deterministic loading, empty, error, and success state rendering
	- command/input surface polish and response-state region
	- operator-ready route placeholders under `/settings`, `/admin`, and `/activity`
	- status/notification convention markers used by generated validation
- Backend FastAPI enterprise surface with:
	- structured config and startup logging placeholder
	- structured response envelopes for health, readiness, version, and execute routes
	- admin/operator/audit route placeholders under `/api/admin`, `/api/operator`, `/api/audit`
	- clearer readiness payload shape and version metadata
- Postgres-oriented runtime env scaffolding
- Docker Compose local deployment scaffold
- Root README with run instructions
- Deterministic backend endpoint tests and frontend shell checks
- Proof/readiness artifacts:
	- `docs/ENTERPRISE_POLISH.md`
	- `docs/READINESS.md`
	- `docs/PROOF_OF_RUN.md`
	- `.autobuilder/proof_report.json`
	- `.autobuilder/readiness_report.json`
- Packaging/deployment handoff assets:
	- `docs/DEPLOYMENT.md`
	- `docs/STARTUP_VALIDATION.md`
	- `release/README.md`
	- `release/deploy/DEPLOYMENT_NOTES.md`
	- `release/runbook/OPERATOR_RUNBOOK.md`
	- `release/proof/PROOF_BUNDLE.md`
	- `.autobuilder/package_artifact_summary.json`
	- `.autobuilder/proof_readiness_bundle.json`

Lane-specific first-class additions:

- Mobile lane (`flutter_mobile`): Flutter scaffold with `pubspec.yaml`, `lib/main.dart`, navigation/state/API client modules, and lane validation markers.
- Game lane (`godot_game`): Godot scaffold with `project.godot`, `scenes/*`, `scripts/*`, input mapping, and prototype main-loop validation markers.
- Realtime lane (`react_next` realtime profile): stream subscription/polling scaffold, sensor connectors, alert/action paths, and world-state update placeholders.
- Enterprise-agent lane (`react_next` workflow profile): multi-role routing, approvals, memory/state scaffolds, reporting/briefing outputs, and operator workflow surfaces.

Current lane status:

- `first_class_commercial`: first-class production web lane
- `first_class_mobile`: first-class bounded mobile lane
- `first_class_game`: first-class bounded game prototype lane
- `first_class_realtime`: first-class bounded realtime/sensing lane
- `first_class_enterprise_agent`: first-class bounded enterprise-agent/workflow lane

Build JSON output includes:

- `files_created_summary` (deterministic file list and count)
- `validation_plan` (deterministic validation checklist)
- `generated_app_validation` (enterprise UX/backend/proof readiness checks)
- `build_status`, `validation_status`, `proof_status`
- `repaired_issues` and `unrepaired_blockers`
- `repair_report` and `proof_artifacts`
- `packaging_summary`, `deployment_readiness_summary`, `proof_summary`
- stack-specific runtime verification and hardening contract artifact paths in `proof_artifacts`
- `plan` and `execution` details

Ship JSON output includes:

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

Generated-app validation mode checks:

- required repo structure
- frontend shell essentials
- backend endpoint essentials
- env/config essentials
- docker/deployment essentials
- proof/readiness artifact presence
- enterprise polish surface presence

Generated-app proof artifacts:

- `.autobuilder/proof_report.json`
- `.autobuilder/readiness_report.json`
- `.autobuilder/validation_summary.json`
- `.autobuilder/determinism_signature.json`
- `.autobuilder/package_artifact_summary.json`
- `.autobuilder/proof_readiness_bundle.json`

## Packaging and Deployment Workflow

For a commercial handoff package in one command:

```bash
python cli/autobuilder.py ship --spec specs --target /tmp/my-app --json
```

Deployment assumptions in this tranche:

- local deployment model: Docker Compose
- frontend startup: Next.js service on `3000`
- backend startup: FastAPI/Uvicorn service on `8000`
- database startup: Postgres 16 on `5432`

Handoff packaging bundle is emitted under:

- `release/`
- `.autobuilder/package_artifact_summary.json`
- `.autobuilder/proof_readiness_bundle.json`

## Using a generated app

After generating an app:

```bash
python cli/autobuilder.py build --spec specs --target /tmp/my-app --json
cd /tmp/my-app
docker compose up
```

## Canonical Ship Mode

One command for the commercial flow (specs in -> app generated -> validated -> repaired if needed -> proof emitted):

```bash
python cli/autobuilder.py ship --spec specs --target /tmp/my-app --json
```

Example high-quality spec bundle:

```bash
python cli/autobuilder.py ship --spec specs/examples/commercial_workspace --target /tmp/commercial-app --json
```

Then open:

- Frontend: `http://localhost:3000`
- API health: `http://localhost:8000/health`

## One clear operator path

Start a mission:

```bash
python cli/autobuilder.py mission "Build an autonomous execution plan" --json
```

Run pauses needing approval can be resumed with:

```bash
python cli/autobuilder.py resume <run_id> --approve --json
```

Inspect any run:

```bash
python cli/autobuilder.py inspect <run_id> --json
```

Run benchmark harness:

```bash
python cli/autobuilder.py benchmark --json
```

Generate readiness report:

```bash
python cli/autobuilder.py readiness --with-benchmarks --json
```

Run end-to-end proof workflow:

```bash
python cli/autobuilder.py proof --json
```

## Direct module CLIs (advanced)

Run default autonomous flow:

```bash
python cli/run.py
```

Run in Nexus mission mode:

```bash
python cli/run.py --nexus
```

Both commands print `run_id`, `status`, and `saved_path` for the persisted record in runs/.

## One-button Nexus mission workflow

Start a mission:

```bash
python cli/mission.py "Build an autonomous execution plan" --json
```

If approval is required, the mission result includes `resume_hint` and stays in `awaiting_approval` state.

Inspect a mission run:

```bash
python cli/inspect.py <run_id>
python cli/inspect.py <run_id> --json
```

Resume a mission after approval:

```bash
python cli/mission.py --resume <run_id> --approve --json
```

## How to inspect and resume

Inspect a saved run:

```bash
python cli/inspect.py <run_id>
python cli/inspect.py <run_id> --json
```

Resume a saved run:

```bash
python cli/resume.py <run_id>
```

If a run is paused for approval, update the saved record approval status to `approved` (or `denied`) before resuming.

## Benchmark harness (Python API)

Execute benchmark cases and build a summary report from Python:

```python
from benchmarks.runner import run_benchmark_cases
from benchmarks.report import build_benchmark_report

results = run_benchmark_cases()
report = build_benchmark_report(results)
```

The built-in benchmark cases are in benchmarks/cases.py and cover simple runs, repair behavior, approval pauses, and Nexus mode.

## Operator docs

- docs/NEXUS_EXECUTION.md: Nexus mission-mode behavior and interpretation guide
- docs/OPERATOR_WORKFLOW.md: step-by-step operator workflow
- docs/SPEC_COMPILER.md: canonical spec bundle, IR contract, build mode behavior and limitations
