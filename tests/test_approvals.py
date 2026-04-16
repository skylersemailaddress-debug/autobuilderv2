from control_plane.approvals import ApprovalRequest, require_approval


def test_approval_request_fields():
    approval = ApprovalRequest(
        approval_id="approval-123",
        action_type="run_execution",
        reason="High-risk action",
        status="pending",
    )

    assert approval.approval_id == "approval-123"
    assert approval.action_type == "run_execution"
    assert approval.reason == "High-risk action"
    assert approval.status == "pending"


def test_require_approval_helper():
    approval = require_approval("run_execution", "High-risk action")

    assert isinstance(approval, ApprovalRequest)
    assert approval.action_type == "run_execution"
    assert approval.reason == "High-risk action"
    assert approval.status == "pending"
    assert approval.approval_id.startswith("approval-")
