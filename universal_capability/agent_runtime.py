from __future__ import annotations

import hashlib
import json


SENSITIVE_ACTION_TYPES = {
    "file_write",
    "file_delete",
    "form_submit_payment",
    "app_admin_action",
}


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def model_computer_use_task(task: str, world_state: dict[str, object] | None = None) -> dict[str, object]:
    text = task.lower().strip()
    steps: list[dict[str, object]] = []

    steps.append(
        {
            "step_id": "step_01",
            "action_type": "browser_navigate",
            "target": "https://example.local/workspace",
            "sensitive": False,
            "reason": "Open the app surface for task context.",
        }
    )

    if "upload" in text or "document" in text:
        steps.append(
            {
                "step_id": "step_02",
                "action_type": "file_read",
                "target": "./input/document.txt",
                "sensitive": False,
                "reason": "Read a local file for form/app interaction.",
            }
        )

    if "fill" in text or "form" in text:
        steps.append(
            {
                "step_id": "step_03",
                "action_type": "form_fill",
                "target": "form#main",
                "sensitive": False,
                "reason": "Fill required fields in controlled abstraction.",
            }
        )

    if "save" in text or "write" in text:
        steps.append(
            {
                "step_id": "step_04",
                "action_type": "file_write",
                "target": "./output/result.json",
                "sensitive": True,
                "reason": "Persist generated output file.",
            }
        )

    if "approve" in text or "admin" in text:
        steps.append(
            {
                "step_id": "step_05",
                "action_type": "app_admin_action",
                "target": "admin/approval",
                "sensitive": True,
                "reason": "Sensitive admin action requires explicit approval.",
            }
        )

    if len(steps) == 1:
        steps.append(
            {
                "step_id": "step_02",
                "action_type": "app_interaction",
                "target": "workspace/primary_action",
                "sensitive": False,
                "reason": "Default app interaction step for bounded execution.",
            }
        )

    approval_requirements = sorted(
        {
            step["action_type"]
            for step in steps
            if bool(step.get("sensitive", False)) or step.get("action_type") in SENSITIVE_ACTION_TYPES
        }
    )

    plan = {
        "task_model_version": "v2",
        "task": task,
        "task_category": "computer_use",
        "expected_outputs": ["audit_log", "replay_payload", "status"],
        "approval_requirements": approval_requirements,
        "world_state": world_state or {},
        "steps": steps,
    }
    plan["plan_signature_sha256"] = _hash_payload(plan)
    return plan


def execute_computer_use_plan(
    plan: dict[str, object],
    *,
    approvals: dict[str, bool] | None = None,
) -> dict[str, object]:
    approvals = approvals or {}
    steps = plan.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("plan.steps must be a list")

    audit_log: list[dict[str, object]] = []
    blocked = False
    blocked_steps: list[str] = []
    completed_steps: list[str] = []

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("step_id", f"step_{index:02d}"))
        action_type = str(step.get("action_type", "unknown"))
        sensitive = bool(step.get("sensitive", False)) or action_type in SENSITIVE_ACTION_TYPES

        approved = True
        if sensitive:
            approved = approvals.get(step_id, approvals.get(action_type, False))

        status = "executed" if approved else "awaiting_approval"
        if sensitive and not approved:
            blocked = True
            blocked_steps.append(step_id)
        else:
            completed_steps.append(step_id)

        audit_log.append(
            {
                "step_id": step_id,
                "action_type": action_type,
                "target": step.get("target", ""),
                "sensitive": sensitive,
                "approved": bool(approved),
                "status": status,
                "gate": "approval_required" if sensitive else "none",
                "blocked_reason": ("missing approval" if sensitive and not approved else ""),
                "replay_token": f"replay::{step_id}",
            }
        )

    result = {
        "runtime_contract_version": "v2",
        "task": plan.get("task", ""),
        "overall_status": "blocked" if blocked else "completed",
        "completed_steps": completed_steps,
        "blocked_steps": blocked_steps,
        "approval_requirements": list(plan.get("approval_requirements", [])),
        "audit_log": audit_log,
        "approval_required": any(item["sensitive"] for item in audit_log),
    }

    replay_payload = {
        "plan_signature_sha256": plan.get("plan_signature_sha256", ""),
        "audit_log": audit_log,
        "overall_status": result["overall_status"],
    }
    result["replay_payload"] = replay_payload
    result["replay_signature_sha256"] = _hash_payload(replay_payload)
    return result
