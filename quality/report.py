from typing import Dict, Optional

from quality.reliability import derive_run_reliability


def build_mission_quality_report(record: Dict, benchmark_summary: Optional[Dict] = None) -> Dict:
    summary = record.get("summary", {})
    selected_memory_keys = record.get("selected_memory_keys", [])
    memory_policy_summary = record.get("memory_policy_summary", {})
    restore_payload = record.get("restore_payload") or {}
    audit_record = record.get("audit_record") or {}
    approval_request = record.get("approval_request") or {}
    confidence = record.get("confidence", summary.get("confidence", 0.0))
    confidence_details = record.get("confidence_details", summary.get("confidence_details", {}))
    reliability_summary = (
        record.get("reliability_summary")
        or summary.get("reliability_summary")
        or derive_run_reliability(record)
    )
    approval_required = summary.get(
        "approval_required",
        record.get("policy", {}).get("approval_required", False),
    )
    awaiting_approval = record.get("awaiting_approval", False)
    mutation_risk = record.get("mutation_risk", summary.get("mutation_risk", "safe"))
    repair_count = record.get("repair_count", 0)

    return {
        "run_id": record.get("run_id"),
        "mission_status": record.get("status", summary.get("final_status")),
        "confidence": confidence,
        "repairs_used": repair_count,
        "mutation_risk": mutation_risk,
        "reliability_summary": reliability_summary,
        "confidence_derivation": {
            "score": confidence,
            "details": confidence_details,
        },
        "operator_summary": {
            "approval_required": approval_required,
            "awaiting_approval": awaiting_approval,
            "mutation_risk": mutation_risk,
            "repairs_used": repair_count,
        },
        "approval_usage": {
            "approval_required": approval_required,
            "awaiting_approval": awaiting_approval,
            "approval_state": approval_request.get("status", "not_required"),
            "approver_identity": approval_request.get("approver_identity"),
        },
        "rollback_readiness": {
            "restore_possible": restore_payload.get("restore_possible", False),
            "restore_checkpoint_id": restore_payload.get("checkpoint_id"),
            "restore_strategy": restore_payload.get("restore_plan", {}).get("strategy"),
        },
        "audit_summary": {
            "audit_id": audit_record.get("audit_id"),
            "approval_state": audit_record.get("approval_state"),
            "rollback_ready": audit_record.get("rollback_ready", False),
        },
        "benchmark_context": benchmark_summary,
        "selected_memories": {
            "keys": selected_memory_keys,
            "count": len(selected_memory_keys),
            "policy_summary": memory_policy_summary,
        },
    }
