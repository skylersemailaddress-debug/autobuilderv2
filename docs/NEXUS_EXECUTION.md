# Nexus0.5 Execution Guide

This document explains how to operate AutobuilderV2 in Nexus0.5 mission mode and how to interpret run outcomes.

## Nexus mission mode

Nexus mission mode is enabled with:

```bash
python cli/run.py --nexus
```

In this mode, the run record includes Nexus-specific fields such as:

- `nexus_mode`
- `project_name`
- `approvals_enabled`
- `resumability_enabled`
- `memory_enabled`
- `contract_validation_enabled`

Nexus mode keeps the same core autonomous pipeline while persisting mission metadata for operator governance.

## Goal-driven runs

Runs are initiated with a goal string and executed through the autonomous path in cli/run.py.

- planning builds tasks from goal + memory + repo context
- execution produces task artifacts
- validation checks task completion
- repair may run when validation fails
- completion writes summary, contract checks, and resume payload

The run record in runs/<run_id>.json is the operator source of truth.

## Approvals and pause states

Approval is policy-driven. High-risk goal keywords trigger approval requirements, and the run pauses with:

- `status: awaiting_approval`
- `awaiting_approval: true`
- an `approval_request` object
- `control_state` explaining why pause occurred

When paused, execution does not continue until the approval state is changed.

## Resume flow

Resume command:

```bash
python cli/resume.py <run_id>
```

Resume behavior:

- if approval is pending, resume exits without continuing
- if approval is denied, resume exits with no continuation
- if approval is approved, resume continues from inferred next stage
- if run is already complete/failed, resume reports no action

The resumed record is saved back to runs/<run_id>.json.

## Benchmark usage

Benchmark cases are defined in benchmarks/cases.py:

- `simple_run`
- `repair_run`
- `approval_run`
- `nexus_run`

Run benchmarks from Python:

```python
from benchmarks.runner import run_benchmark_cases
from benchmarks.report import build_benchmark_report

results = run_benchmark_cases()
report = build_benchmark_report(results)
```

Each case result includes:

- `success`
- `final_status`
- `repair_count`
- `confidence`
- `event_count`
- `approval_required`

The report adds:

- `total_cases`
- `passed_cases`
- `failed_cases`
- `average_confidence`
- `cases`

## Inspection CLI usage

Inspect a saved run:

```bash
python cli/inspect.py <run_id>
python cli/inspect.py <run_id> --json
```

Inspection output includes:

- `run_id`
- `goal`
- `final_status`
- `confidence`
- `repair_count`
- `approval_required`
- `event_count`
- `summary`
- `failure_info` (when failures exist)

## Confidence, summaries, and artifacts

Key run-level fields:

- `confidence`: aggregate confidence score for run quality
- `summary`: compact operator view with policy, event, memory, and failure counts
- `artifacts`: task outputs and state transition records
- `contract_validation_results`: plan/task/summary contract evidence

Operator interpretation tips:

- high confidence + `final_status=complete` generally indicates healthy autonomous completion
- low confidence + failures indicates review and possible rerun are needed
- artifact and checkpoint counts should align with expected task depth and state transitions

## Failures and repair behavior

When validation fails, failure records are classified and stored under `failures`.

Common interpretation pattern:

- `failure_count > 0` with `repair_count >= 1` and final complete status means auto-repair recovered
- `status=failed` with critical failures means manual intervention is required
- repeated failures with low confidence indicate unstable task quality and should block Nexus-sensitive changes

Repair is bounded by retry policy, so not all failures are recoverable in one run.