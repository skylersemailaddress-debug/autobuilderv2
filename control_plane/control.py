from dataclasses import dataclass
from typing import Dict


@dataclass
class ControlDecision:
    action: str
    allowed: bool
    requires_pause: bool
    reason: str
    policy_snapshot: Dict | None = None