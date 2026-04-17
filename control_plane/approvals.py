from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


PENDING = "pending"
APPROVED = "approved"
DENIED = "denied"
ESCALATED = "escalated"

VALID_APPROVAL_STATES = {PENDING, APPROVED, DENIED, ESCALATED}
TERMINAL_APPROVAL_STATES = {APPROVED, DENIED}


@dataclass
class ApprovalRequest:
    approval_id: str
    action_type: str
    reason: str
    status: str = PENDING
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requested_by: str = "system"
    approver_identity: Optional[str] = None
    action_scope: List[str] = field(default_factory=list)
    escalation_level: str = "standard"
    decision_reason: Optional[str] = None
    audit_metadata: Dict = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    updated_at: Optional[str] = None
    resolved_at: Optional[str] = None
    governance_version: str = "v2"


def _append_history(
    approval: ApprovalRequest,
    *,
    from_status: Optional[str],
    to_status: str,
    actor: str,
    reason: Optional[str],
    metadata: Optional[Dict],
    approver_identity: Optional[str],
) -> None:
    recorded_at = datetime.now(timezone.utc).isoformat()
    approval.history.append(
        {
            "from_status": from_status,
            "status": to_status,
            "recorded_at": recorded_at,
            "actor": actor,
            "reason": reason,
            "metadata": dict(metadata or {}),
            "approver_identity": approver_identity,
        }
    )
    approval.updated_at = recorded_at


def _validate_transition(current_status: str, next_status: str) -> None:
    if next_status not in VALID_APPROVAL_STATES:
        raise ValueError(f"Unsupported approval state: {next_status}")
    if current_status in TERMINAL_APPROVAL_STATES and current_status != next_status:
        raise ValueError(f"Cannot transition approval from terminal state {current_status} to {next_status}")


def transition_approval(
    approval: ApprovalRequest,
    status: str,
    *,
    approver_identity: Optional[str] = None,
    decision_reason: Optional[str] = None,
    actor: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> ApprovalRequest:
    _validate_transition(approval.status, status)
    recorded_actor = actor or approver_identity or approval.requested_by
    previous_status = approval.status
    approval.status = status
    approval.approver_identity = approver_identity or approval.approver_identity
    approval.decision_reason = decision_reason or approval.decision_reason
    _append_history(
        approval,
        from_status=previous_status,
        to_status=status,
        actor=recorded_actor,
        reason=decision_reason,
        metadata=metadata,
        approver_identity=approval.approver_identity,
    )
    if metadata:
        approval.audit_metadata.update(metadata)
    approval.audit_metadata.update(
        {
            "last_actor": recorded_actor,
            "last_status": status,
            "action_scope": list(approval.action_scope),
            "governance_version": approval.governance_version,
        }
    )
    if status in TERMINAL_APPROVAL_STATES:
        approval.resolved_at = approval.updated_at
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
    approval.audit_metadata.update(
        {
            "approval_id": approval.approval_id,
            "requested_by": requested_by,
            "action_scope": list(approval.action_scope),
            "escalation_level": escalation_level,
            "governance_version": approval.governance_version,
        }
    )
    approval.updated_at = approval.requested_at
    _append_history(
        approval,
        from_status=None,
        to_status=PENDING,
        actor=requested_by,
        reason=reason,
        metadata=audit_metadata,
        approver_identity=None,
    )
    return approval
