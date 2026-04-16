from typing import List, Optional, Dict
from .task import Task


class Planner:
    def create_plan(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """Create a plan with optional context from memory and repository metadata."""
        repo_context = context.get("repo_context") if context else None
        repo_mode = bool(repo_context)

        tasks = [
            Task(task_id="task-1", title=f"Analyze goal: {goal}"),
            Task(task_id="task-2", title="Generate artifact"),
            Task(task_id="task-3", title="Validate output"),
        ]
        
        plan_metadata = {
            "goal": goal,
            "task_count": len(tasks),
            "memory_used": context is not None,
            "memory_insights": [],
            "repo_mode": repo_mode,
            "repo_signals": {},
        }

        if repo_context:
            if repo_context.get("framework_hints"):
                plan_metadata["repo_signals"]["framework_hints"] = repo_context["framework_hints"]
            if repo_context.get("config_files"):
                plan_metadata["repo_signals"]["config_files"] = repo_context["config_files"]
            if repo_context.get("test_folders"):
                plan_metadata["repo_signals"]["test_folders"] = repo_context["test_folders"]

        if context:
            insights = context.get("memory_insights", [])
            plan_metadata["memory_insights"] = insights

            # Add memory-informed notes to tasks
            if insights:
                for task in tasks:
                    task.result = {
                        "memory_context": f"Planning with {len(insights)} memory insights",
                        "insights": insights[:2],
                    }

        if repo_context:
            # Adjust task metadata to reflect repository structure.
            detected = repo_context.get("framework_hints", [])
            config_files = repo_context.get("config_files", [])
            test_folders = repo_context.get("test_folders", [])

            tasks[0].title = f"Analyze repository structure for {goal}"
            tasks[0].result = {
                "repo_mode": True,
                "framework_hints": detected,
                "config_files": config_files,
                "test_folders": test_folders,
            }
            tasks[1].title = "Generate artifact aligned with existing codebase"
            tasks[1].result = {
                "repo_mode": True,
                "target_frameworks": detected,
                "repository_signals": repo_context,
            }
            tasks[2].title = "Validate artifact against repository test structure"
            tasks[2].result = {
                "repo_mode": True,
                "test_folders": test_folders,
            }

        return {
            "tasks": tasks,
            "metadata": plan_metadata,
        }

