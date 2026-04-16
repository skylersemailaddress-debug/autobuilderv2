from dataclasses import dataclass
from typing import Optional


SAFE = "safe"
CAUTION = "caution"
DANGEROUS = "dangerous"


@dataclass(frozen=True)
class MutationSafetyDecision:
    action: str
    target: str
    risk_level: str
    checkpoint_required: bool


class MutationSafetyPolicy:
    def classify(self, action: str, target: Optional[str] = None) -> str:
        action_lower = (action or "").lower()
        target_lower = (target or "").lower()
        combined = f"{action_lower} {target_lower}"

        dangerous_keywords = ["delete", "rename", "migrate", "production", "destroy"]
        caution_keywords = ["update", "modify", "write", "edit"]
        safe_keywords = ["create", "add", "new"]

        if any(keyword in combined for keyword in dangerous_keywords):
            return DANGEROUS
        if any(keyword in combined for keyword in caution_keywords):
            return CAUTION
        if any(keyword in combined for keyword in safe_keywords):
            return SAFE
        return SAFE

    def requires_checkpoint(self, action: str, target: Optional[str] = None) -> bool:
        return self.classify(action, target) == DANGEROUS

    def evaluate(self, action: str, target: Optional[str] = None) -> MutationSafetyDecision:
        risk_level = self.classify(action, target)
        return MutationSafetyDecision(
            action=action,
            target=target or "",
            risk_level=risk_level,
            checkpoint_required=self.requires_checkpoint(action, target),
        )
