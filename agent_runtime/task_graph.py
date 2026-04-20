from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TaskNode:
    task_id: str
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)


class TaskGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, TaskNode] = {}

    def add_task(self, task_id: str, dependencies: List[str] | None = None) -> TaskNode:
        node = TaskNode(task_id=task_id, dependencies=dependencies or [])
        self.nodes[task_id] = node
        return node

    def ready_tasks(self) -> List[str]:
        ready: List[str] = []
        for task_id, node in self.nodes.items():
            if node.status != "pending":
                continue
            if all(self.nodes[d].status == "completed" for d in node.dependencies if d in self.nodes):
                ready.append(task_id)
        return ready
