from universal_capability.agent_runtime import execute_computer_use_plan, model_computer_use_task


def test_computer_use_task_modeling_is_deterministic() -> None:
    task = "Open app, fill form, and save result"
    first = model_computer_use_task(task, {"mode": "test"})
    second = model_computer_use_task(task, {"mode": "test"})

    assert first == second
    assert first["steps"][0]["action_type"] == "browser_navigate"
    assert any(step["action_type"] == "file_write" for step in first["steps"])
    assert first["bounded_execution_contract"]["desktop_control"] == "simulated_only"
    assert first["confidence_summary"]["model_confidence"] > 0


def test_computer_use_runtime_applies_approval_gating_and_audit() -> None:
    plan = model_computer_use_task("save admin changes", {})

    blocked = execute_computer_use_plan(plan, approvals={})
    assert blocked["overall_status"] == "blocked"
    assert any(item["status"] == "awaiting_approval" for item in blocked["audit_log"])
    assert blocked["execution_confidence"]["blocked"] is True

    approved = execute_computer_use_plan(plan, approvals={"file_write": True, "app_admin_action": True})
    assert approved["overall_status"] == "completed"
    assert all(item["status"] == "executed" for item in approved["audit_log"] if item["status"] != "skipped_due_to_gate")
    assert approved["replay_signature_sha256"]


def test_sensitive_block_halts_following_steps() -> None:
    plan = model_computer_use_task("save admin changes and fill form", {})
    result = execute_computer_use_plan(plan, approvals={})

    assert result["overall_status"] == "blocked"
    assert result["blocked_steps"]
    assert any(item["status"] == "skipped_due_to_gate" for item in result["audit_log"])
