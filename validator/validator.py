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
        incomplete_tasks = []
        failed_task_details = []
        
        for task in tasks:
            status = None
            task_id = None
            result = None
            
            if hasattr(task, "status"):
                status = task.status
                task_id = task.task_id
                result = task.result
            elif isinstance(task, dict):
                status = task.get("status")
                task_id = task.get("task_id")
                result = task.get("result")

            if status != "complete":
                failed_tasks.append(task_id or "unknown")
                incomplete_tasks.append(task_id or "unknown")
                failed_task_details.append({
                    "task_id": task_id,
                    "status": status,
                    "result": result
                })

        if not failed_tasks:
            return True, {"status": "pass"}

        # Enhanced evidence for classification
        evidence = {
            "status": "fail",
            "failed_tasks": failed_tasks,
            "incomplete_tasks": incomplete_tasks,
            "failed_task_details": failed_task_details,
            "total_tasks": len(tasks),
            "failed_count": len(failed_tasks),
            "reason": f"{len(failed_tasks)} tasks are not complete",
            "evidence_type": "validation_result"
        }
        
        return False, evidence
