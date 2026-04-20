from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict


@dataclass
class DecisionRecord:
    action: str
    approved: bool
    reason: str
    actor: str
    timestamp: str


class DecisionLog:
    def __init__(self) -> None:
        self._records: list[DecisionRecord] = []

    def record(self, action: str, approved: bool, reason: str, actor: str) -> Dict[str, Any]:
        rec = DecisionRecord(
            action=action,
            approved=approved,
            reason=reason,
            actor=actor,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._records.append(rec)
        return asdict(rec)

    def all(self) -> list[Dict[str, Any]]:
        return [asdict(r) for r in self._records]
