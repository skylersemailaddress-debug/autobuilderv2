from typing import Dict, Optional


def build_mission_quality_report(record: Dict, benchmark_summary: Optional[Dict] = None) -> Dict:
    summary = record.get("summary", {})
    selected_memory_keys = record.get("selected_memory_keys", [])
    memory_policy_summary = record.get("memory_policy_summary", {})

    return {
        "run_id": record.get("run_id"),
        "mission_status": record.get("status", summary.get("final_status")),
        "confidence": record.get("confidence", summary.get("confidence", 0.0)),
        "repairs_used": record.get("repair_count", 0),
        "mutation_risk": record.get("mutation_risk", summary.get("mutation_risk", "safe")),
        "approval_usage": {
            "approval_required": summary.get(
                "approval_required",
                record.get("policy", {}).get("approval_required", False),
            ),
            "awaiting_approval": record.get("awaiting_approval", False),
        },
        "benchmark_context": benchmark_summary,
        "selected_memories": {
            "keys": selected_memory_keys,
            "count": len(selected_memory_keys),
            "policy_summary": memory_policy_summary,
        },
    }
