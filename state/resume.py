from typing import Dict


def resume_run(record: Dict) -> Dict:
    return {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status"),
        "summary": record.get("summary"),
        "memory_keys": record.get("memory_keys", []),
        "last_state": record.get("state_history", [])[-1] if record.get("state_history") else None,
        "repair_count": record.get("repair_count", 0),
    }
