from planner.task import Task
from debugger.repair import RepairEngine


def test_repair_engine_converts_incomplete_tasks():
    tasks = [
        Task(task_id="task-1", title="Analyze goal", status="complete", result={}),
        Task(task_id="task-2", title="Generate artifact", status="pending"),
    ]
    engine = RepairEngine()
    repaired = engine.repair_tasks(tasks)

    assert all(task.status == "complete" for task in repaired)
    repaired_task = next(task for task in repaired if task.task_id == "task-2")
    assert repaired_task.result is not None
    assert repaired_task.result.get("repaired") is True
