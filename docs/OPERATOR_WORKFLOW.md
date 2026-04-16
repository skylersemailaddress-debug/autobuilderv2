# AutobuilderV2 Operator Workflow

Complete runbook for operating AutobuilderV2 locally and in enterprise contexts.

## 0. Bootstrap (First-Time Setup)

Initialize a clean local development environment:

```bash
scripts/bootstrap_local.sh
```

This:
- Creates a Python virtual environment (.venv/)
- Installs all project dependencies
- Prints canonical next commands
- Safe to run repeatedly (idempotent)

After bootstrap, the environment is ready for all operational workflows below.

## 1. Canonical Top-Level Operations

Use the top-level CLI for all standard operations:

```bash
python cli/autobuilder.py --help
```

Available commands for the commercial lane: `readiness`, `build`, `validate-app`, `proof-app`, `ship`

Secondary operational autonomy commands remain available (`mission`, `resume`, `inspect`, `benchmark`, `proof`) but are not required for the commercial ship lane.

Supported commercial lane scope:

- app archetypes: `internal_tool`, `workspace_app`, `saas_web_app`, `api_service`, `workflow_system`, `copilot_chat_app`, `mobile_app`, `game_app`, `realtime_system`, `enterprise_agent_system`
- first-class lane stacks:
  - web: `react_next` + `fastapi` + `postgres` + `docker_compose`
  - mobile: `flutter_mobile` + `fastapi` + `postgres` + `docker_compose`
  - game: `godot_game` + `fastapi` + `postgres` + `docker_compose`
  - realtime/sensing: `react_next` + `fastapi` + `postgres` + `docker_compose`
  - enterprise-agent/workflow: `react_next` + `fastapi` + `postgres` + `docker_compose`

Not yet supported in this tranche:

- future/non-first-class stack entries
- additional languages or deployment lanes
- cloud-specific production deployment manifests

### 1a. Check System Readiness

Before starting missions, verify the system is ready:

```bash
python cli/autobuilder.py readiness --json
```

This runs deterministic checks on:
- Core autonomy capability
- Validation and repair behavior
- Approval and governance mechanisms
- Inspection and tracing
- Benchmark baseline stability
- Overall system state

Exit code 0 = ready. Non-zero = investigate before proceeding.

### 1b. Build Generated App

Compile canonical specs into a deterministic generated app target:

```bash
python cli/autobuilder.py build --spec specs --target /tmp/my-app --json
```

### 1c. Validate and Repair Generated App

Validate generated app essentials and auto-repair common defects:

```bash
python cli/autobuilder.py validate-app --target /tmp/my-app --repair --json
```

### 1d. Emit Generated-App Proof

Emit proof/readiness artifacts and certification summary:

```bash
python cli/autobuilder.py proof-app --target /tmp/my-app --repair --json
```

### 1e. Ship (One Command)

One-command flow for specs in -> polished generated app out:

```bash
python cli/autobuilder.py ship --spec specs --target /tmp/my-app --json
```

### 1f. Run Proof of Execution (Core System)

Validate that the system executes correctly end-to-end:

```bash
python cli/autobuilder.py proof --json
```

This runs the complete proof workflow:
- Plans and executes a simple goal
- Validates all expected outcomes
- Returns complete proof transcript
- Safe to run repeatedly

Use `proof` as a deterministic validation gate in CI/CD or before mission work.

### 1g. Start a Mission

Execute a goal autonomously with governance:

```bash
python cli/autobuilder.py mission "Your goal here" --json
```

Captures from output:
- `run_id`: unique run identifier for inspection/resume
- `saved_path`: location of persisted run record (JSON)
- `mission_result`: final outcome and confidence
- `awaiting_approval`: true if mission paused for approval

### 1h. Inspect a Run

View operator-friendly details of any run:

```bash
python cli/autobuilder.py inspect <run_id> --json
```

Check:
- `final_status`: completed, awaiting_approval, failed
- `confidence`: outcome confidence (0-100%)
- `repair_count`: how many times system repaired itself
- `events`: full execution trace
- `approval_request`: governance decision context if paused

### 1i. Resume After Approval

Continue a paused mission:

```bash
python cli/autobuilder.py resume <run_id> --approve --json
```

Use `--approve` to allow continuation or omit to check status only.

Behavior:
- Mission in `awaiting_approval` resumes if approved
- pending/denied approvals do not continue
- Execution picks up from checkpoint

### 1j. Run Benchmarks

Regression test the system against known cases:

```bash
python cli/autobuilder.py benchmark --json
```

Executes all benchmark cases:
- `simple_low_risk_mission`
- `repair_required_mission`
- `approval_required_dangerous_mission`
- `repo_targeted_mission`
- `nexus_mission_mode_run`
- `interrupted_resumable_mission`

Output includes:
- Per-case pass/fail
- Confidence metrics
- Performance metrics
- Regression summary

### 1k. Compile Spec Bundle Into Target Repo Scaffold (Details)

`build` remains available as a stepwise command if `ship` is not used.

## 2. Cleanup Runtime Artifacts

Safely remove all generated state and cache:

```bash
scripts/clean_runtime.sh
```

Removes:
- `runs/*.json` (run records)
- `memory/*.json` (memory artifacts)
- `__pycache__/` (Python cache)
- `*.pyc` (compiled Python)
- `.pytest_cache/` (test cache)

Preserves:
- Source code
- Tests
- Documentation
- Configuration

Safe to run repeatedly. Prompts for confirmation.

## 3. Packaging for Distribution

Create a clean, distributable archive:

```bash
scripts/package_release.sh
```

Creates a versioned zip in `dist/` containing:
- All source code
- Tests
- Documentation
- Scripts and bootstraps
- Configuration files

Excludes:
- Runtime artifacts (runs/, memory/)
- Virtual environment
- Python cache
- Generated noise

Use for:
- Distribution to other machines
- Version releases
- Archival and backup
- CI/CD staging

## 4. Advanced: Direct Module CLIs

For advanced workflows, use module-level CLIs directly:

### 4a. Standard Autonomous Execution

```bash
python cli/run.py
```

Prints `run_id`, `status`, `saved_path` for the persisted record.

### 4b. Nexus Mission Mode

Governance-oriented execution with mission metadata:

```bash
python cli/run.py --nexus
```

Includes approval controls, mission-level policies, and governance decoration.

### 4c. Mission API

Direct mission execution:

```bash
python cli/mission.py "Build something" --json
```

Resume a mission:

```bash
python cli/mission.py --resume <run_id> --approve --json
```

### 4d. Inspection API

Plain-text operator report:

```bash
python cli/inspect.py <run_id>
```

Structured JSON output for tooling:

```bash
python cli/inspect.py <run_id> --json
```

### 4e. Resume API

Manually update approval status and resume:

```bash
python cli/resume.py <run_id>
```

First, manually edit the saved run record to set approval status to `approved` or `denied`.

## 5. Day-to-Day Operations Checklist

### Before Mission Work

```bash
# 1. Bootstrap if first time
scripts/bootstrap_local.sh

# 2. Clean old artifacts
scripts/clean_runtime.sh

# 3. Verify readiness
python cli/autobuilder.py readiness --json

# 4. Run proof
python cli/autobuilder.py proof --json

# 5. Check benchmarks
python cli/autobuilder.py benchmark --json
```

### Running Missions

```bash
# Start mission
python cli/autobuilder.py mission "Your goal" --json

# Capture run_id from output

# Inspect status
python cli/autobuilder.py inspect <run_id> --json

# If awaiting_approval: review, decide, then resume
python cli/autobuilder.py resume <run_id> --approve --json
```

### Release/Deployment

```bash
# Clean up any runtime artifacts
scripts/clean_runtime.sh

# Run final validation
python cli/autobuilder.py proof --json
python cli/autobuilder.py benchmark --json

# Package for distribution
scripts/package_release.sh

# Archive or deploy dist/*.zip
```

## 6. Troubleshooting

### System Is Not Ready

Check readiness output and validate:
- Planner can create task plans
- Executor can run tasks
- Validator can assess outcomes
- Repair logic bounded correctly
- Approval/resume pathways work
- All benchmark cases pass

### Mission Fails Unexpectedly

```bash
# Inspect the full run record
python cli/autobuilder.py inspect <run_id> --json

# Review:
# - events: full trace of decisions
# - failure_info: technical failure details
# - repair_count: bounds on repair loops
# - confidence: outcome confidence

# Re-run proof to narrow issue
python cli/autobuilder.py proof --json
```

### Permission or State Corruption

```bash
# Clean all runtime state
scripts/clean_runtime.sh

# Re-bootstrap
scripts/bootstrap_local.sh

# Re-validate
python cli/autobuilder.py proof --json
```

### Archiving / Release Readiness

1. Clean artifacts: `scripts/clean_runtime.sh`
2. Final validation: `python cli/autobuilder.py proof --json`
3. Package: `scripts/package_release.sh`
4. Mark version in docs if needed
5. Commit to version control

## 7. Interpreting Output

### Run Status

- `completed`: Mission finished successfully
- `awaiting_approval`: Paused awaiting operator approval decision
- `failed`: Mission failed validation beyond repair limits
- `interrupted`: Operator interrupted the mission

### Confidence Metric

- 90-100%: Very high confidence in outcome
- 70-89%: Good confidence, ready for most work
- 50-69%: Moderate confidence, recommend inspection
- <50%: Low confidence, investigate before proceeding

### Repair Count

- 0: No self-repair needed (ideal)
- 1-2: Minor issues repaired (normal)
- 3+: Significant repair loops (investigate)
- Beyond 5: Potential system issue, stop and diagnose

## 8. Enterprise Notes

- **Governance**: Use approval gates for high-risk goals
- **Audit**: All runs saved as JSON records in runs/ for compliance
- **Isolation**: Memory and state completely local by default
- **Portability**: Scripts and bootstrap ensure consistent behavior across machines
- **Distribution**: Use `scripts/package_release.sh` for clean deployment packages
- **CI/CD**: Use `python cli/autobuilder.py readiness --json` and `python cli/autobuilder.py proof --json` as validation gates