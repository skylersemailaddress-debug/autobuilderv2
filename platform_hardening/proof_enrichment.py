from __future__ import annotations

import json
from pathlib import Path

from platform_hardening.commerce import build_commerce_pack_contract
from platform_hardening.failure_replay import append_failure_corpus, emit_replay_harness
from platform_hardening.packs import get_pack_registry
from platform_hardening.repair_runtime import verify_runtime_startup
from platform_hardening.security_governance import build_security_governance_contract


def _write_json(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def enrich_proof_with_platform_hardening(
    *,
    lane_id: str,
    target_repo: str | Path,
    determinism: dict[str, object],
    validation_report: dict[str, object],
    repair_report: dict[str, object],
    proof_artifacts: dict[str, object],
) -> dict[str, object]:
    target = Path(target_repo).resolve()
    autobuilder = target / ".autobuilder"

    runtime_report = verify_runtime_startup(lane_id=lane_id, target_repo=target)
    security_governance = build_security_governance_contract(lane_id)
    commerce_contract = build_commerce_pack_contract(lane_id)
    pack_profile = get_pack_registry().compose_lane_profile(lane_id)

    failure_corpus = append_failure_corpus(
        target_repo=target,
        lane_id=lane_id,
        validation_status=str(validation_report.get("validation_status", "failed")),
        failure_classification=list(repair_report.get("failure_classification", [])),
        runtime_report=runtime_report,
    )
    replay = emit_replay_harness(
        target_repo=target,
        lane_id=lane_id,
        determinism=determinism,
        validation_status=str(validation_report.get("validation_status", "failed")),
        runtime_report=runtime_report,
    )

    runtime_path = _write_json(autobuilder / "runtime_verification.json", runtime_report)
    security_path = _write_json(autobuilder / "security_governance_contract.json", security_governance)
    commerce_path = _write_json(autobuilder / "commerce_pack_contract.json", commerce_contract)
    packs_path = _write_json(autobuilder / "pack_composition.json", pack_profile)

    merged = dict(proof_artifacts)
    merged.setdefault("artifact_paths", {})
    merged["artifact_paths"]["runtime_verification"] = runtime_path
    merged["artifact_paths"]["security_governance_contract"] = security_path
    merged["artifact_paths"]["commerce_pack_contract"] = commerce_path
    merged["artifact_paths"]["pack_composition"] = packs_path
    merged["artifact_paths"]["failure_corpus"] = failure_corpus["corpus_path"]
    merged["artifact_paths"]["replay_harness"] = replay["replay_harness_path"]

    merged["runtime_verification"] = runtime_report
    merged["security_governance"] = security_governance
    merged["commerce_pack"] = commerce_contract
    merged["pack_profile"] = pack_profile
    merged["failure_corpus"] = failure_corpus
    merged["replay_harness"] = replay
    return merged
