from typing import Dict, List


def build_artifact_lineage(run_id: str, artifacts: List[Dict], checkpoints: List[Dict]) -> Dict:
    checkpoint_ids = [checkpoint.get("checkpoint_id") for checkpoint in checkpoints if checkpoint.get("checkpoint_id")]
    lineage_items = []

    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id") or artifact.get("state")
        content = artifact.get("content") if isinstance(artifact.get("content"), dict) else {}
        task_id = content.get("task_id") or artifact.get("task_id") or artifact.get("artifact_id")
        lineage_items.append(
            {
                "artifact_id": artifact_id,
                "task_id": task_id,
                "checkpoint_ids": checkpoint_ids,
            }
        )

    return {
        "run_id": run_id,
        "artifact_ids": [item.get("artifact_id") for item in lineage_items],
        "lineage": lineage_items,
    }


def summarize_artifact_lineage(run_id: str, artifacts: List[Dict], checkpoints: List[Dict]) -> Dict:
    lineage = build_artifact_lineage(run_id, artifacts, checkpoints)
    return {
        "run_id": run_id,
        "artifact_lineage_count": len(lineage.get("lineage", [])),
        "artifact_ids": lineage.get("artifact_ids", []),
    }