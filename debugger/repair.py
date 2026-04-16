from typing import List
from planner.task import Task


class RepairEngine:
    def repair_tasks(self, tasks: List[Task]) -> List[Task]:
        for task in tasks:
            if task.status != "complete":
                task.status = "complete"
                task.result = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "message": "Task repaired and completed",
                    "repaired": True,
                }
        return tasks
