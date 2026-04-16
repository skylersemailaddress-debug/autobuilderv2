from typing import List
from .task import Task


class Planner:
    def create_plan(self, goal: str) -> List[Task]:
        return [
            Task(task_id="task-1", title=f"Analyze goal: {goal}"),
            Task(task_id="task-2", title="Generate artifact"),
            Task(task_id="task-3", title="Validate output"),
        ]
