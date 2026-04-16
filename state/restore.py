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
        }

    return {
        "run_id": record.get("run_id"),
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "stage": checkpoint.get("stage"),
        "metadata": checkpoint.get("metadata", {}),
        "restore_possible": True,
    }


def latest_restore_payload(record: Dict) -> Optional[Dict]:
    checkpoints = record.get("checkpoints", [])
    if not checkpoints:
        return None
    latest = checkpoints[-1]
    return build_restore_payload(record, latest.get("checkpoint_id", ""))
