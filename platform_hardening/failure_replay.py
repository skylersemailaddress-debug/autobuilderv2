from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _hash_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def append_failure_corpus(
    target_repo: str | Path,
    lane_id: str,
    validation_status: str,
    failure_classification: list[dict[str, object]],
    runtime_report: dict[str, object],
) -> dict[str, object]:
    target = Path(target_repo).resolve()
    autobuilder = target / ".autobuilder"
    autobuilder.mkdir(parents=True, exist_ok=True)
    corpus_path = autobuilder / "failure_corpus.jsonl"

    entry = {
        "lane_id": lane_id,
        "validation_status": validation_status,
        "runtime_status": runtime_report.get("runtime_status", "unknown"),
        "failure_classification": failure_classification,
    }
    entry["entry_signature_sha256"] = _hash_json(entry)

    with corpus_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")

    return {
        "corpus_path": str(corpus_path),
        "entry_signature_sha256": entry["entry_signature_sha256"],
    }


def emit_replay_harness(
    target_repo: str | Path,
    lane_id: str,
    determinism: dict[str, object],
    validation_status: str,
    runtime_report: dict[str, object],
) -> dict[str, object]:
    target = Path(target_repo).resolve()
    autobuilder = target / ".autobuilder"
    autobuilder.mkdir(parents=True, exist_ok=True)

    replay_payload = {
        "lane_id": lane_id,
        "replay_version": "v1",
        "determinism": {
            "verified": determinism.get("verified", False),
            "build_signature_sha256": determinism.get("build_signature_sha256", ""),
            "proof_signature_sha256": determinism.get("proof_signature_sha256", ""),
        },
        "validation_status": validation_status,
        "runtime_status": runtime_report.get("runtime_status", "unknown"),
        "replay_instructions": [
            "python cli/autobuilder.py build --spec <spec> --target <target> --json",
            "python cli/autobuilder.py validate-app --target <target> --repair --json",
            "python cli/autobuilder.py proof-app --target <target> --repair --json",
        ],
    }
    replay_payload["replay_signature_sha256"] = _hash_json(replay_payload)

    path = autobuilder / "replay_harness.json"
    path.write_text(json.dumps(replay_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "replay_harness_path": str(path),
        "replay_signature_sha256": replay_payload["replay_signature_sha256"],
    }
