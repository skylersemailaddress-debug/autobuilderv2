import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class Checkpoint:
    checkpoint_id: str
    stage: str
    created_at: str
    metadata: Dict


def create_checkpoint(stage: str, metadata: Dict) -> Checkpoint:
    return Checkpoint(
        checkpoint_id=f"{stage}-{uuid.uuid4().hex}",
        stage=stage,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
    )
