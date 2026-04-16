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

## Quick Start

### Local Bootstrap

Initialize a clean development environment (one-time setup):

```bash
scripts/bootstrap_local.sh
```

This creates a virtual environment, installs dependencies, and prints next steps.

### Canonical Commands

Run these commands once the environment is bootstrapped:

```bash
# Check if system is ready
python cli/autobuilder.py readiness --json

# Run proof-of-execution validation
python cli/autobuilder.py proof --json

# Start a mission (autonomous execution)
python cli/autobuilder.py mission "Your goal here" --json

# Inspect any run
python cli/autobuilder.py inspect <run_id> --json

# Run benchmark regression tests
python cli/autobuilder.py benchmark --json
```

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
