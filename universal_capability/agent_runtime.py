from __future__ import annotations

import hashlib
import json
import re


SENSITIVE_ACTION_TYPES = {
    "file_write",
    "file_delete",
    "form_submit_payment",
    "app_admin_action",
}


ACTION_CLASSIFIERS: list[tuple[str, str, bool]] = [
    (r"\b(upload|document|attachment)\b", "file_read", False),
    (r"\b(fill|form|input|enter)\b", "form_fill", False),
    (r"\b(save|write|export|download)\b", "file_write", True),
    (r"\b(approve|admin|privileged|grant)\b", "app_admin_action", True),
    (r"\b(payment|charge|billing)\b", "form_submit_payment", True),
]


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _step_template(
    *,
    step_id: str,
    action_type: str,
    target: str,
    sensitive: bool,
    reason: str,
    confidence: float,
) -> dict[str, object]:
    step = {
        "step_id": step_id,
        "action_type": action_type,
        "target": target,
        "sensitive": sensitive,
        "reason": reason,
        "preconditions": ["bounded_operator_environment"],
        "expected_effect": "no-op" if action_type == "browser_navigate" else "bounded_state_change",
        "approval_scope": "operator_explicit" if sensitive else "none",
        "step_confidence": max(0.0, min(1.0, round(confidence, 4))),
    }
    step["step_signature_sha256"] = _hash_payload(step)
    return step


def model_computer_use_task(task: str, world_state: dict[str, object] | None = None) -> dict[str, object]:
    text = task.lower().strip()
    steps: list[dict[str, object]] = []

    steps.append(_step_template(
        step_id="step_01",
        action_type="browser_navigate",
        target="https://example.local/workspace",
        sensitive=False,
        reason="Open the app surface for task context.",
        confidence=0.98,
    ))

    next_step = 2
    for pattern, action_type, sensitive in ACTION_CLASSIFIERS:
        if re.search(pattern, text):
            target = {
                "file_read": "./input/document.txt",
                "form_fill": "form#main",
                "file_write": "./output/result.json",
                "app_admin_action": "admin/approval",
                "form_submit_payment": "billing/checkout",
            }.get(action_type, "workspace/unknown")
            reason = {
                "file_read": "Read local input document for bounded task context.",
                "form_fill": "Populate required fields via deterministic plan step.",
                "file_write": "Persist output artifact under explicit operator-governed path.",
                "app_admin_action": "Perform privileged action only with explicit approval.",
                "form_submit_payment": "Payment-affecting action is approval-gated and bounded.",
            }.get(action_type, "Execute bounded action.")
            steps.append(_step_template(
                step_id=f"step_{next_step:02d}",
                action_type=action_type,
                target=target,
                sensitive=sensitive,
                reason=reason,
                confidence=0.9 if not sensitive else 0.82,
            ))
            next_step += 1

    if len(steps) == 1:
        steps.append(_step_template(
            step_id="step_02",
            action_type="app_interaction",
            target="workspace/primary_action",
            sensitive=False,
            reason="Default app interaction step for bounded execution.",
            confidence=0.86,
        ))

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
        "bounded_execution_contract": {
            "desktop_control": "simulated_only",
            "browser_control": "schema_level_only",
            "side_effects": "approval_gated_and_declared",
        },
        "confidence_summary": {
            "model_confidence": round(sum(float(step.get("step_confidence", 0.0)) for step in steps) / len(steps), 4),
            "step_count": len(steps),
            "sensitive_step_count": sum(1 for step in steps if bool(step.get("sensitive", False))),
        },
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
    skipped_steps: list[str] = []

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("step_id", f"step_{index:02d}"))
        action_type = str(step.get("action_type", "unknown"))
        sensitive = bool(step.get("sensitive", False)) or action_type in SENSITIVE_ACTION_TYPES

        if blocked:
            skipped_steps.append(step_id)
            audit_log.append(
                {
                    "step_id": step_id,
                    "action_type": action_type,
                    "target": step.get("target", ""),
                    "sensitive": sensitive,
                    "approved": False,
                    "status": "skipped_due_to_gate",
                    "gate": "halted_after_block",
                    "blocked_reason": "prior_sensitive_step_missing_approval",
                    "replay_token": f"replay::{step_id}",
                    "step_signature_sha256": step.get("step_signature_sha256", ""),
                }
            )
            continue

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
                "sequence": index,
                "action_type": action_type,
                "target": step.get("target", ""),
                "sensitive": sensitive,
                "approved": bool(approved),
                "status": status,
                "gate": "approval_required" if sensitive else "none",
                "blocked_reason": ("missing approval" if sensitive and not approved else ""),
                "replay_token": f"replay::{step_id}",
                "step_signature_sha256": step.get("step_signature_sha256", ""),
            }
        )

    result = {
        "runtime_contract_version": "v2",
        "task": plan.get("task", ""),
        "overall_status": "blocked" if blocked else "completed",
        "completed_steps": completed_steps,
        "blocked_steps": blocked_steps,
        "skipped_steps": skipped_steps,
        "approval_requirements": list(plan.get("approval_requirements", [])),
        "audit_log": audit_log,
        "approval_required": any(item["sensitive"] for item in audit_log),
        "execution_confidence": {
            "plan_confidence": (plan.get("confidence_summary") or {}).get("model_confidence", 0.0),
            "completed_ratio": round(len(completed_steps) / len(steps), 4) if steps else 0.0,
            "blocked": blocked,
        },
    }

    replay_payload = {
        "plan_signature_sha256": plan.get("plan_signature_sha256", ""),
        "audit_log": audit_log,
        "overall_status": result["overall_status"],
        "completed_steps": completed_steps,
        "blocked_steps": blocked_steps,
        "skipped_steps": skipped_steps,
    }
    result["replay_payload"] = replay_payload
    result["replay_signature_sha256"] = _hash_payload(replay_payload)
    return result
