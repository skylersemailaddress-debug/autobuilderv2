from typing import Dict, Optional


def build_restore_payload(record: Dict, checkpoint_id: str) -> Dict:
    checkpoints = record.get("checkpoints", [])
    checkpoint = next(
        (item for item in checkpoints if item.get("checkpoint_id") == checkpoint_id),
        None,
    )

    if checkpoint is None:
        return {
            "run_id": record.get("run_id"),
            "checkpoint_id": checkpoint_id,
            "stage": None,
            "metadata": {},
            "restore_possible": False,
            "restore_plan": {},
            "restore_metadata": {},
            "rollback_reference": None,
            "failure_semantics": "checkpoint_missing",
            "restore_references": {},
        }

    restore_metadata = checkpoint.get("restore_metadata", {})
    restore_possible = restore_metadata.get("restorable", True)
    return {
        "run_id": record.get("run_id"),
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "stage": checkpoint.get("stage"),
        "metadata": checkpoint.get("metadata", {}),
        "restore_possible": restore_possible,
        "restore_plan": checkpoint.get(
            "restore_plan",
            {
                "strategy": checkpoint.get("restore_hint", {}).get("strategy", "checkpoint_restore"),
                "stage": checkpoint.get("stage"),
                "rollback_ready": True,
                "mutation_safety": checkpoint.get("mutation_safety", {}),
            },
        ),
        "restore_metadata": restore_metadata,
        "rollback_reference": checkpoint.get("rollback_reference"),
        "failure_semantics": checkpoint.get("failure_semantics", {"mode": "resume_from_checkpoint"}),
        "restore_references": {
            "checkpoint_id": checkpoint.get("checkpoint_id"),
            "rollback_reference": checkpoint.get("rollback_reference"),
            "manifest_version": checkpoint.get("manifest_version"),
        },
    }


def latest_restore_payload(record: Dict) -> Optional[Dict]:
    checkpoints = record.get("checkpoints", [])
    if not checkpoints:
        return None
    latest = checkpoints[-1]
    return build_restore_payload(record, latest.get("checkpoint_id", ""))
