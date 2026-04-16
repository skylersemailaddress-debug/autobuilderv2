import uuid
from typing import Dict, Iterable, List

from benchmarks.cases import BENCHMARK_CASES, BenchmarkCase
from cli.resume import resume_saved_run
from cli.run import perform_run
from state.json_store import JsonRunStore


def _case_passed(case: BenchmarkCase, result: Dict) -> bool:
    expected = case.expected_outcome
    if "final_status" in expected and result["final_status"] != expected["final_status"]:
        return False
    if "approval_required" in expected and result["approval_required"] != expected["approval_required"]:
        return False
    if "minimum_repair_count" in expected and result["repair_count"] < expected["minimum_repair_count"]:
        return False
    if "nexus_mode" in expected and result["nexus_mode"] != expected["nexus_mode"]:
        return False
    if "repo_mode" in expected and result["repo_mode"] != expected["repo_mode"]:
        return False
    if "resumed" in expected and result["resumed"] != expected["resumed"]:
        return False
    return True


def run_benchmark_cases(cases: Iterable[BenchmarkCase] = BENCHMARK_CASES) -> List[Dict]:
    results: List[Dict] = []
    store = JsonRunStore()
    for case in cases:
        run_id = f"benchmark_{case.name}_{uuid.uuid4().hex[:12]}"
        record, _ = perform_run(
            run_id=run_id,
            goal=case.goal,
            nexus_mode_enabled=case.nexus_mode_enabled,
        )

        resumed = False
        if case.requires_resume and record.get("awaiting_approval"):
            if case.auto_approve_on_resume:
                approval_request = record.get("approval_request")
                if approval_request:
                    approval_request["status"] = "approved"
                    record["approval_request"] = approval_request
                    store.save(run_id, record)
            resumed_record, _ = resume_saved_run(run_id)
            if resumed_record is not None:
                record = resumed_record
                resumed = True

        summary = record.get("summary", {})
        final_status = record.get("status", summary.get("final_status"))
        approval_required = summary.get(
            "approval_required",
            record.get("policy", {}).get("approval_required", False),
        )
        result = {
            "case": case.name,
            "run_id": run_id,
            "success": False,
            "final_status": final_status,
            "repair_count": record.get("repair_count", 0),
            "confidence": record.get("confidence", 0.0),
            "event_count": len(record.get("events", [])),
            "approval_required": approval_required,
            "nexus_mode": record.get("nexus_mode", False),
            "repo_mode": summary.get("repo_mode", bool(record.get("repo_context"))),
            "resumed": resumed,
            "expected_resumable": case.requires_resume,
            "failure_reason": None,
        }
        result["success"] = _case_passed(case, result)
        if not result["success"]:
            result["failure_reason"] = f"expected={case.expected_outcome}, got={{{'final_status': result['final_status'], 'approval_required': result['approval_required'], 'repair_count': result['repair_count'], 'nexus_mode': result['nexus_mode'], 'repo_mode': result['repo_mode'], 'resumed': result['resumed']}}}"
        results.append(result)

    return results
