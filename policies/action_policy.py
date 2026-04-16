from typing import List

from mutation.safety import MutationSafetyPolicy, SAFE


class ActionPolicy:
    def classify_action(self, goal: str, tasks: List[dict]) -> dict:
        task_titles = " ".join(str(task.get("title", "")) for task in tasks)
        decision = MutationSafetyPolicy().evaluate(goal, task_titles or goal)
        if decision.risk_level == SAFE:
            risk_level = "low"
        elif decision.risk_level == "caution":
            risk_level = "medium"
        else:
            risk_level = "high"
        return {
            "risk_level": risk_level,
            "approval_required": decision.approval_required,
            "action_class": decision.action_class,
            "target_type": decision.target_type,
            "checkpoint_required": decision.checkpoint_required,
            "destructive_potential": decision.destructive_potential,
            "environment_sensitivity": decision.environment_sensitivity,
            "irreversible_operation": decision.irreversible_operation,
            "restore_strategy": decision.restore_strategy,
        }
