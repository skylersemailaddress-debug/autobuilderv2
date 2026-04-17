import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class Checkpoint:
    checkpoint_id: str
    stage: str
    created_at: str
    metadata: Dict
    manifest_version: str
    rollback_reference: str
    restore_hint: Dict
    mutation_safety: Dict
    manifest: Dict
    restore_plan: Dict
    restore_metadata: Dict
    failure_semantics: Dict
    command: str
    actor: str


def create_checkpoint(
    stage: str,
    metadata: Dict,
    *,
    mutation_safety: Optional[Dict] = None,
    rollback_reference: Optional[str] = None,
    command: str = "system",
    actor: str = "system",
    restore_plan: Optional[Dict] = None,
    failure_semantics: Optional[Dict] = None,
) -> Checkpoint:
    checkpoint_id = f"{stage}-{uuid.uuid4().hex}"
    created_at = datetime.now(timezone.utc).isoformat()
    rollback_ref = rollback_reference or f"rollback:{checkpoint_id}"
    resolved_mutation_safety = dict(mutation_safety or {})
    checkpoint_restore_plan = {
        "strategy": "checkpoint_restore",
        "stage": stage,
        "preconditions": ["checkpoint_manifest_available"],
        "steps": [
            "load_checkpoint_manifest",
            "load_restore_metadata",
            "replay_safe_state",
            "verify_post_restore_contracts",
        ],
        "dangerous_mutation_guard": bool(resolved_mutation_safety.get("irreversible_operation", False)),
    }
    checkpoint_restore_plan.update(restore_plan or {})
    resolved_failure_semantics = {
        "on_restore_failure": "halt_and_escalate",
        "on_irreversible_mutation": (
            "block_without_approval"
            if resolved_mutation_safety.get("irreversible_operation", False)
            else "checkpoint_restore"
        ),
    }
    resolved_failure_semantics.update(failure_semantics or {})
    return Checkpoint(
        checkpoint_id=checkpoint_id,
        stage=stage,
        created_at=created_at,
        metadata=metadata,
        manifest_version="v3",
        rollback_reference=rollback_ref,
        restore_hint={
            "strategy": checkpoint_restore_plan["strategy"],
            "stage": stage,
            "metadata_keys": sorted(metadata.keys()),
            "command": command,
        },
        mutation_safety=resolved_mutation_safety,
        manifest={
            "checkpoint_id": checkpoint_id,
            "stage": stage,
            "created_at": created_at,
            "metadata_keys": sorted(metadata.keys()),
            "command": command,
            "actor": actor,
        },
        restore_plan=checkpoint_restore_plan,
        restore_metadata={
            "durable": True,
            "rollback_reference": rollback_ref,
            "restorable": not bool(resolved_mutation_safety.get("irreversible_operation", False)),
            "mutation_risk": resolved_mutation_safety.get("risk_level", "safe"),
        },
        failure_semantics=resolved_failure_semantics,
        command=command,
        actor=actor,
    )
