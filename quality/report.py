from typing import Dict, Optional


def build_mission_quality_report(record: Dict, benchmark_summary: Optional[Dict] = None) -> Dict:
    summary = record.get("summary", {})
    selected_memory_keys = record.get("selected_memory_keys", [])
    memory_policy_summary = record.get("memory_policy_summary", {})
    restore_payload = record.get("restore_payload") or {}
    audit_record = record.get("audit_record") or {}
    approval_request = record.get("approval_request") or {}

    return {
        "run_id": record.get("run_id"),
        "mission_status": record.get("status", summary.get("final_status")),
        "confidence": record.get("confidence", summary.get("confidence", 0.0)),
        "repairs_used": record.get("repair_count", 0),
        "mutation_risk": record.get("mutation_risk", summary.get("mutation_risk", "safe")),
        "approval_usage": {
            "approval_required": summary.get(
                "approval_required",
                record.get("policy", {}).get("approval_required", False),
            ),
            "awaiting_approval": record.get("awaiting_approval", False),
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
