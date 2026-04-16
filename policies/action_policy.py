from typing import List


class ActionPolicy:
    def classify_action(self, goal: str, tasks: List[dict]) -> dict:
        high_risk_keywords = ["delete", "destroy", "production", "migrate"]
        
        if any(keyword in goal.lower() for keyword in high_risk_keywords):
            return {
                "risk_level": "high",
                "approval_required": True,
            }
        else:
            return {
                "risk_level": "low",
                "approval_required": False,
            }
