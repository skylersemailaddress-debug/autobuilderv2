from dataclasses import dataclass


@dataclass
class ControlDecision:
    action: str
    allowed: bool
    requires_pause: bool
    reason: str