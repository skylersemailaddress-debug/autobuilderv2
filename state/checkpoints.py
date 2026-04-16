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


def create_checkpoint(
    stage: str,
    metadata: Dict,
    *,
    mutation_safety: Optional[Dict] = None,
    rollback_reference: Optional[str] = None,
) -> Checkpoint:
    checkpoint_id = f"{stage}-{uuid.uuid4().hex}"
    return Checkpoint(
        checkpoint_id=checkpoint_id,
        stage=stage,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
        manifest_version="v2",
        rollback_reference=rollback_reference or f"rollback:{checkpoint_id}",
        restore_hint={
            "strategy": "checkpoint_restore",
            "stage": stage,
            "metadata_keys": sorted(metadata.keys()),
        },
        mutation_safety=dict(mutation_safety or {}),
    )
