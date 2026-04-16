from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FailureRecord:
    failure_id: str
    failure_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    task_id: Optional[str] = None
    recoverable: bool = True
    replayable: bool = True
    replay_case: Optional[Dict[str, object]] = None
    benchmark_case: Optional[Dict[str, object]] = None