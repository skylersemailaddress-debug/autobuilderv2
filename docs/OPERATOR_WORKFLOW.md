# Operator Workflow

This runbook describes day-to-day operation of AutobuilderV2 for Nexus0.5-oriented work.

## 1. Start a run

1. Choose execution mode.
2. Run standard mode for baseline autonomy:

```bash
python cli/run.py
```

3. Run Nexus mission mode when governance metadata is required:

```bash
python cli/run.py --nexus
```

4. Capture `run_id` and `saved_path` from command output.

## 2. Handle approval pauses

1. Detect pause by checking `status=awaiting_approval` or `awaiting_approval=true` in the saved run record.
2. Review `control_state.reason`, `policy`, and `approval_request` fields.
3. Set approval request status to one of:
   - `approved` to continue
   - `denied` to stop
4. Keep an audit note for why the approval decision was made.

## 3. Resume runs

1. Resume with:

```bash
python cli/resume.py <run_id>
```

2. Confirm expected behavior:
   - approved pause resumes execution
   - pending approval remains paused
   - denied approval does not continue
3. Re-open the saved JSON record and verify updated `status`, `events`, and `summary`.

## 4. Inspect runs

1. Quick operator output:

```bash
python cli/inspect.py <run_id>
```

2. Structured output for tooling:

```bash
python cli/inspect.py <run_id> --json
```

3. Review the core fields:
   - run identity: `run_id`, `goal`
   - outcome: `final_status`, `confidence`
   - stabilization: `repair_count`, `failure_info`
   - governance: `approval_required`
   - trace density: `event_count`, `summary`

## 5. Run benchmarks

1. Execute benchmark suite from Python:

```python
from benchmarks.runner import run_benchmark_cases
from benchmarks.report import build_benchmark_report

results = run_benchmark_cases()
report = build_benchmark_report(results)
```

2. Confirm all expected cases are present:
   - `simple_run`
   - `repair_run`
   - `approval_run`
   - `nexus_run`
3. Use report-level metrics (`passed_cases`, `failed_cases`, `average_confidence`) for regression tracking.

## 6. Evaluate readiness for Nexus0.5 work

Use this lightweight gate before Nexus-sensitive tasks:

1. Functional outcome:
   - target runs complete or intentionally pause for approval
2. Stability:
   - repairs are bounded and not escalating
   - confidence is acceptable for task criticality
3. Governance:
   - approval pathways behave as expected
   - pause/resume behavior is deterministic
4. Regression baseline:
   - benchmark report has no unexpected case failures
5. Operator visibility:
   - inspection output contains enough detail to explain run decisions and failure handling

If any gate fails, treat the run as non-ready and investigate before Nexus0.5 delivery work.