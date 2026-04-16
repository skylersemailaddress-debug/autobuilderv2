from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class RunEvent:
    timestamp: str
    event_type: str
    detail: Dict[str, Any]


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_event(event_type: str, detail: Dict[str, Any]) -> RunEvent:
    return RunEvent(timestamp=current_utc_timestamp(), event_type=event_type, detail=detail)


def event_to_dict(event: RunEvent) -> Dict[str, Any]:
    return asdict(event)
