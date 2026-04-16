# AutobuilderV2

AutobuilderV2 is a stateful autonomous execution kernel for goal-driven software work. It plans tasks, executes work, validates outcomes, performs bounded repair, and records durable run state with operator controls for approvals, resume, and inspection.

## Current capabilities

- Planner: creates task plans from a goal and planning context
- Executor: runs planned tasks and records task output artifacts
- Validator: checks completion status and produces validation evidence
- Repair loop: retries failed validation with bounded repair attempts
- Memory: in-memory plus durable JSON memory for cross-run context
- Repo-targeted planning: repository context is inspected and fed into planning
- Approvals/policy: high-risk goals can pause in awaiting approval state
- Benchmarks: benchmark case runner and report utilities for regression checks
- Inspection CLI: operator-readable run inspection output from saved records
- Nexus0.5 mission mode: enabled with mission-specific run metadata and controls

## How to run

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

## Benchmark harness

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
