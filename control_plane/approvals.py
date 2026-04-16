from dataclasses import dataclass
import uuid


@dataclass
class ApprovalRequest:
    approval_id: str
    action_type: str
    reason: str
    status: str = "pending"


def require_approval(action_type: str, reason: str) -> ApprovalRequest:
    return ApprovalRequest(
        approval_id=f"approval-{uuid.uuid4().hex}",
        action_type=action_type,
        reason=reason,
    )
