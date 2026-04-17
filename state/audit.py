from datetime import datetime, timezone
from typing import Dict, Optional
import uuid


COMMAND_SAFETY_GUARANTEES = {
    "mission": {
        "mutation_mode": "gated_execution",
        "approval_behavior": "pause_on_dangerous_mutations",
        "rollback_behavior": "checkpoint_restore_when_required",
    },
    "build": {
        "mutation_mode": "scaffold_generation",
        "approval_behavior": "no_operator_pause_for_local_targets",
        "rollback_behavior": "checkpoint_manifest_emitted",
    },
    "validate-app": {
        "mutation_mode": "read_only_unless_repair_enabled",
        "approval_behavior": "repair_respects_policy_classification",
        "rollback_behavior": "checkpoint_when_repair_touches_sensitive_state",
    },
    "proof-app": {
        "mutation_mode": "proof_emission_with_optional_repair",
        "approval_behavior": "repair_respects_policy_classification",
        "rollback_behavior": "checkpoint_before_repair_paths",
    },
    "ship": {
        "mutation_mode": "build_validate_proof_package",
        "approval_behavior": "future_tier_stacks_rejected_before_packaging",
        "rollback_behavior": "checkpoint_manifest_and_restore_plan_emitted",
    },
    "chat-build": {
        "mutation_mode": "preview_only",
        "approval_behavior": "no_approval_required",
        "rollback_behavior": "not_required",
    },
    "agent-runtime": {
        "mutation_mode": "task_execution_with_declared_approvals",
        "approval_behavior": "operator_approval_map_recorded",
        "rollback_behavior": "replay_reference_recorded",
    },
    "self-extend": {
        "mutation_mode": "sandbox_first_extension",
        "approval_behavior": "core_extension_requires_explicit_approval",
        "rollback_behavior": "checkpoint_manifest_emitted_for_extension_path",
    },
    "resume": {
        "mutation_mode": "resume_from_saved_state",
        "approval_behavior": "blocked_until_approval_granted",
        "rollback_behavior": "restore_reference_preserved",
    },
    "run": {
        "mutation_mode": "planned_execution",
        "approval_behavior": "pause_on_high_risk_actions",
        "rollback_behavior": "checkpoint_restore_when_required",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_command_safety_contract(command: str) -> Dict:
    return {
        "command": command,
        "contract_version": "v2",
        **COMMAND_SAFETY_GUARANTEES.get(
            command,
            {
                "mutation_mode": "unspecified",
                "approval_behavior": "unspecified",
                "rollback_behavior": "unspecified",
            },
        ),
    }


def build_audit_record(
    command: str,
    *,
    outcome: str,
    run_id: Optional[str] = None,
    action_type: Optional[str] = None,
    risk_level: str = "safe",
    approval_state: str = "not_required",
    approval_id: Optional[str] = None,
    checkpoint_ids: Optional[list[str]] = None,
    rollback_ready: bool = False,
    rollback_reference: Optional[str] = None,
    restore_checkpoint_id: Optional[str] = None,
    restore_reference: Optional[Dict] = None,
    actor: str = "system",
    failure_classification: str = "none",
    safety_contract: Optional[Dict] = None,
    details: Optional[Dict] = None,
) -> Dict:
    recorded_at = utc_now()
    return {
        "audit_version": "v2",
        "audit_id": f"audit-{uuid.uuid4().hex}",
        "command": command,
        "action_type": action_type or command,
        "run_id": run_id,
        "recorded_at": recorded_at,
        "when": recorded_at,
        "actor": actor,
        "who": {"actor": actor},
        "what": {"command": command, "action_type": action_type or command},
        "outcome": outcome,
        "risk_level": risk_level,
        "approval_state": approval_state,
        "approval_id": approval_id,
        "checkpoint_ids": list(checkpoint_ids or []),
        "rollback_ready": rollback_ready,
        "rollback_reference": rollback_reference,
        "restore_checkpoint_id": restore_checkpoint_id,
        "restore_reference": restore_reference or {},
        "failure_classification": failure_classification,
        "safety_contract": safety_contract or get_command_safety_contract(command),
        "details": details or {},
    }


def append_audit_event(
    audit_trail: Optional[list[Dict]],
    event_type: str,
    *,
    actor: str = "system",
    approval_state: Optional[str] = None,
    failure_classification: Optional[str] = None,
    details: Optional[Dict] = None,
) -> list[Dict]:
    trail = list(audit_trail or [])
    trail.append(
        {
            "event_id": f"audit-event-{uuid.uuid4().hex}",
            "event_type": event_type,
            "recorded_at": utc_now(),
            "actor": actor,
            "approval_state": approval_state,
            "failure_classification": failure_classification,
            "details": details or {},
        }
    )
    return trail
    return trail