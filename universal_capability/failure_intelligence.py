from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _signature(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def append_capability_failure(
    *,
    target_root: str | Path,
    capability_id: str,
    stage: str,
    error_message: str,
    replay_inputs: dict[str, object],
) -> dict[str, object]:
    root = Path(target_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    corpus_path = root / "capability_failure_corpus.jsonl"

    entry = {
        "capability_id": capability_id,
        "stage": stage,
        "error_message": error_message,
        "replay_inputs": replay_inputs,
    }
    entry["entry_signature_sha256"] = _signature(entry)

    with corpus_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")

    return {
        "corpus_path": str(corpus_path),
        "entry_signature_sha256": entry["entry_signature_sha256"],
    }


def emit_capability_replay_case(
    *,
    target_root: str | Path,
    capability_id: str,
    replay_inputs: dict[str, object],
) -> dict[str, object]:
    root = Path(target_root).resolve()
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "capability_id": capability_id,
        "replay_version": "v1",
        "replay_inputs": replay_inputs,
        "replay_steps": [
            "load candidate capability",
            "run deterministic validation",
            "compare output signatures",
            "assert pass/fail expectations",
        ],
    }
    payload["replay_signature_sha256"] = _signature(payload)

    path = root / f"replay_case_{capability_id.replace(':', '_')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "replay_case_path": str(path),
        "replay_signature_sha256": payload["replay_signature_sha256"],
    }


def summarize_capability_confidence(*, target_root: str | Path) -> dict[str, object]:
    root = Path(target_root).resolve()
    corpus_path = root / "capability_failure_corpus.jsonl"
    if not corpus_path.exists():
        return {"confidence": "unknown", "failure_count": 0, "trend": "no_data"}

    failures = corpus_path.read_text(encoding="utf-8").splitlines()
    failure_count = len([line for line in failures if line.strip()])
    confidence = "high" if failure_count == 0 else ("medium" if failure_count < 3 else "low")
    trend = "improving" if failure_count < 3 else "unstable"
    return {
        "confidence": confidence,
        "failure_count": failure_count,
        "trend": trend,
    }
