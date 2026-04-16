from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class ApprovalRequest:
    approval_id: str
    action_type: str
    reason: str
    status: str = "pending"
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requested_by: str = "system"
    approver_identity: Optional[str] = None
    action_scope: List[str] = field(default_factory=list)
    escalation_level: str = "standard"
    decision_reason: Optional[str] = None
    audit_metadata: Dict = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)


def transition_approval(
    approval: ApprovalRequest,
    status: str,
    *,
    approver_identity: Optional[str] = None,
    decision_reason: Optional[str] = None,
    actor: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> ApprovalRequest:
    recorded_at = datetime.now(timezone.utc).isoformat()
    approval.status = status
    approval.approver_identity = approver_identity or approval.approver_identity
    approval.decision_reason = decision_reason or approval.decision_reason
    approval.history.append(
        {
            "status": status,
            "recorded_at": recorded_at,
            "actor": actor or approver_identity or approval.requested_by,
            "reason": decision_reason,
            "metadata": metadata or {},
        }
    )
    if metadata:
        approval.audit_metadata.update(metadata)
    return approval


def require_approval(
    action_type: str,
    reason: str,
    *,
    requested_by: str = "system",
    action_scope: Optional[List[str]] = None,
    escalation_level: str = "standard",
    audit_metadata: Optional[Dict] = None,
) -> ApprovalRequest:
    approval = ApprovalRequest(
        approval_id=f"approval-{uuid.uuid4().hex}",
        action_type=action_type,
        reason=reason,
        requested_by=requested_by,
        action_scope=list(action_scope or []),
        escalation_level=escalation_level,
        audit_metadata=dict(audit_metadata or {}),
    )
    approval.history.append(
        {
            "status": "pending",
            "recorded_at": approval.requested_at,
            "actor": requested_by,
            "reason": reason,
            "metadata": dict(audit_metadata or {}),
        }
    )
    return approval
