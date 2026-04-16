from dataclasses import dataclass
from typing import Optional


@dataclass
class FailureRecord:
    failure_id: str
    failure_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    task_id: Optional[str] = None
    recoverable: bool = True