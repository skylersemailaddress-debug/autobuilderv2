from dataclasses import dataclass
import hashlib
import json
from typing import Dict, Iterable, Optional


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


def _stable_hash(payload: Dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def classify_replayability(record: FailureRecord) -> Dict[str, object]:
    replay_payload = {
        "failure_id": record.failure_id,
        "failure_type": record.failure_type,
        "severity": record.severity,
        "recoverable": record.recoverable,
        "replay_case": record.replay_case or {},
        "benchmark_case": record.benchmark_case or {},
    }
    return {
        "failure_id": record.failure_id,
        "failure_type": record.failure_type,
        "replayable": bool(record.replayable),
        "replay_signature_sha256": _stable_hash(replay_payload),
        "replay_case": record.replay_case or {},
        "benchmark_case": record.benchmark_case or {},
        "classification": (
            "replayable_high_priority"
            if record.replayable and record.severity in {"high", "critical"}
            else "replayable"
            if record.replayable
            else "non_replayable"
        ),
    }


def summarize_failure_intelligence(records: Iterable[FailureRecord]) -> Dict[str, object]:
    replayable = [classify_replayability(record) for record in records]
    benchmark_cases = [item["benchmark_case"] for item in replayable if item.get("benchmark_case")]
    high_priority = [item for item in replayable if item["classification"] == "replayable_high_priority"]
    return {
        "failure_count": len(replayable),
        "replayable_count": sum(1 for item in replayable if item.get("replayable")),
        "high_priority_replay_count": len(high_priority),
        "replay_cases": replayable,
        "benchmark_cases": benchmark_cases,
    }