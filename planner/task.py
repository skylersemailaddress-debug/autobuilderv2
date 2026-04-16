from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    task_id: str
    title: str
    status: str = "pending"
    result: Optional[dict] = None
