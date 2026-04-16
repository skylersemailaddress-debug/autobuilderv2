from typing import Dict


def build_run_summary(record: Dict) -> Dict:
    tasks = record.get("tasks", [])
    events = record.get("events", [])
    completed_tasks = sum(1 for task in tasks if task.get("status") == "complete")

    return {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status"),
        "repair_used": record.get("repair_used", False),
        "repair_count": record.get("repair_count", 0),
        "total_tasks": len(tasks),
        "completed_tasks": completed_tasks,
        "event_count": len(events),
    }
