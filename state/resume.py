from typing import Dict


def resume_run(record: Dict) -> Dict:
    approval_request = record.get("approval_request") or {}
    restore_payload = record.get("restore_payload") or {}
    return {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status"),
        "summary": record.get("summary"),
        "memory_keys": record.get("memory_keys", []),
        "last_state": record.get("state_history", [])[-1] if record.get("state_history") else None,
        "repair_count": record.get("repair_count", 0),
        "approval_state": approval_request.get("status", "not_required"),
        "rollback_ready": bool(restore_payload.get("restore_possible")),
        "restore_checkpoint_id": restore_payload.get("checkpoint_id"),
    }
