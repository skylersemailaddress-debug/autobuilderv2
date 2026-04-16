class Validator:
    def validate(self, items):
        tasks = []
        if isinstance(items, dict):
            if "tasks" in items:
                tasks = items["tasks"]
            elif "artifacts" in items:
                tasks = items["artifacts"]
        elif isinstance(items, list):
            tasks = items

        failed_tasks = []
        for task in tasks:
            status = None
            task_id = None
            if hasattr(task, "status"):
                status = task.status
            elif isinstance(task, dict):
                status = task.get("status")

            if hasattr(task, "task_id"):
                task_id = task.task_id
            elif isinstance(task, dict):
                task_id = task.get("task_id")

            if status != "complete":
                failed_tasks.append(task_id or "unknown")

        if not failed_tasks:
            return True, {"status": "pass"}

        return False, {
            "status": "fail",
            "failed_tasks": failed_tasks,
            "reason": "Some tasks are not complete",
        }
