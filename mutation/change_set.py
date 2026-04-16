from dataclasses import dataclass


@dataclass
class ChangeSet:
    change_id: str
    action: str
    target: str
    risk_level: str
    requires_checkpoint: bool
    approved: bool
    applied: bool
