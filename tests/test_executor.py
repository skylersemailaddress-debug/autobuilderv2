from planner.task import Task
from execution.executor import Executor


def test_executor_marks_tasks_complete():
    tasks = [
        Task(task_id="task-1", title="Analyze goal"),
        Task(task_id="task-2", title="Generate artifact"),
    ]
    executor = Executor()

    completed_tasks = executor.run_tasks(tasks)

    assert all(task.status == "complete" for task in completed_tasks)
    assert all(task.result is not None for task in completed_tasks)
    assert completed_tasks[0].result["task_id"] == "task-1"
    assert completed_tasks[1].result["task_id"] == "task-2"
