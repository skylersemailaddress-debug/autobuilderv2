from typing import List, Optional, Dict
from .task import Task


class Planner:
    def create_plan(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """Create a plan with optional context from memory."""
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
        }
        
        if context:
            insights = context.get("memory_insights", [])
            plan_metadata["memory_insights"] = insights
            
            # Add memory-informed notes to tasks
            if insights:
                for task in tasks:
                    task.result = {
                        "memory_context": f"Planning with {len(insights)} memory insights",
                        "insights": insights[:2],  # Include first 2 insights in task metadata
                    }
        
        return {
            "tasks": tasks,
            "metadata": plan_metadata,
        }

