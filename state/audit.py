from datetime import datetime, timezone
from typing import Dict, Optional
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_audit_record(
    command: str,
    *,
    outcome: str,
    run_id: Optional[str] = None,
    risk_level: str = "safe",
    approval_state: str = "not_required",
    checkpoint_ids: Optional[list[str]] = None,
    rollback_ready: bool = False,
    restore_checkpoint_id: Optional[str] = None,
    actor: str = "system",
    details: Optional[Dict] = None,
) -> Dict:
    return {
        "audit_id": f"audit-{uuid.uuid4().hex}",
        "command": command,
        "run_id": run_id,
        "recorded_at": utc_now(),
        "actor": actor,
        "outcome": outcome,
        "risk_level": risk_level,
        "approval_state": approval_state,
        "checkpoint_ids": list(checkpoint_ids or []),
        "rollback_ready": rollback_ready,
        "restore_checkpoint_id": restore_checkpoint_id,
        "details": details or {},
    }


def append_audit_event(
    audit_trail: Optional[list[Dict]],
    event_type: str,
    *,
    actor: str = "system",
    details: Optional[Dict] = None,
) -> list[Dict]:
    trail = list(audit_trail or [])
    trail.append(
        {
            "event_id": f"audit-event-{uuid.uuid4().hex}",
            "event_type": event_type,
            "recorded_at": utc_now(),
            "actor": actor,
            "details": details or {},
        }
    )
    return trail