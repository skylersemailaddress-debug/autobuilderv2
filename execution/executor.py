from typing import List
from planner.task import Task


class Executor:
    def run_tasks(self, tasks: List[Task]) -> List[Task]:
        for task in tasks:
            task.status = "complete"
            task.result = {
                "task_id": task.task_id,
                "title": task.title,
                "message": f"{task.title} completed successfully",
            }
        return tasks
