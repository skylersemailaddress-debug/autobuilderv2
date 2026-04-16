from dataclasses import dataclass
from typing import Optional


@dataclass
class ChangeSet:
    change_id: str
    action: str
    target: str
    risk_level: str
    requires_checkpoint: bool
    approved: bool
    applied: bool
    action_class: str = "creation"
    target_type: str = "logical_goal"
    destructive_potential: str = "low"
    environment_sensitivity: str = "standard"
    irreversible_operation: bool = False
    rollback_strategy: Optional[str] = None
