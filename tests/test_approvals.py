from control_plane.approvals import ApprovalRequest, require_approval, transition_approval


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
    assert approval.history


def test_approval_transition_records_history_and_actor():
    approval = require_approval(
        "run_execution",
        "High-risk action",
        requested_by="autobuilder",
        action_scope=["Delete production resources safely"],
    )

    updated = transition_approval(
        approval,
        "approved",
        approver_identity="operator-1",
        decision_reason="Rollback path verified",
        actor="operator-1",
        metadata={"ticket": "CAB-42"},
    )

    assert updated.status == "approved"
    assert updated.approver_identity == "operator-1"
    assert updated.action_scope == ["Delete production resources safely"]
    assert updated.audit_metadata["ticket"] == "CAB-42"
    assert updated.history[-1]["status"] == "approved"
    assert updated.history[-1]["actor"] == "operator-1"


def test_approval_lifecycle_supports_escalation_and_denial_metadata():
    approval = require_approval(
        "self_extend_core",
        "Core extension touches trusted control surface",
        requested_by="autobuilder",
        action_scope=["first_class_commercial", "core_capability"],
        escalation_level="cab",
        audit_metadata={"ticket": "CAB-77", "requested_for": "self-extend"},
    )

    escalated = transition_approval(
        approval,
        "escalated",
        actor="governance-bot",
        decision_reason="Requires CAB review",
        metadata={"escalation_queue": "cab"},
    )
    denied = transition_approval(
        escalated,
        "denied",
        approver_identity="cab-chair",
        actor="cab-chair",
        decision_reason="Rollback plan insufficient",
        metadata={"decision_ticket": "CAB-77"},
    )

    assert denied.status == "denied"
    assert denied.approver_identity == "cab-chair"
    assert denied.action_scope == ["first_class_commercial", "core_capability"]
    assert denied.audit_metadata["decision_ticket"] == "CAB-77"
    assert denied.history[-2]["status"] == "escalated"
    assert denied.history[-1]["from_status"] == "escalated"
    assert denied.history[-1]["status"] == "denied"
    assert denied.history[-1]["approver_identity"] == "cab-chair"
    assert denied.resolved_at is not None
