from dataclasses import dataclass
from typing import Optional


SAFE = "safe"
CAUTION = "caution"
DANGEROUS = "dangerous"


@dataclass(frozen=True)
class MutationSafetyDecision:
    action: str
    target: str
    action_class: str
    target_type: str
    risk_level: str
    checkpoint_required: bool
    approval_required: bool
    destructive_potential: str
    environment_sensitivity: str
    irreversible_operation: bool
    restore_strategy: str


class MutationSafetyPolicy:
    def _action_class(self, action: str, target: Optional[str]) -> str:
        combined = f"{(action or '').lower()} {(target or '').lower()}"
        if any(keyword in combined for keyword in ["delete", "destroy", "remove"]):
            return "destructive"
        if any(keyword in combined for keyword in ["migrate", "rename"]):
            return "structural"
        if any(keyword in combined for keyword in ["update", "modify", "write", "edit"]):
            return "mutation"
        return "creation"

    def _target_type(self, target: Optional[str]) -> str:
        target_lower = (target or "").lower()
        if "production" in target_lower:
            return "production_resource"
        if "database" in target_lower:
            return "database"
        if any(keyword in target_lower for keyword in ["file", "repo", "repository"]):
            return "filesystem"
        return "logical_goal"

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
        action_class = self._action_class(action, target)
        target_type = self._target_type(target)
        destructive_potential = "high" if risk_level == DANGEROUS else "medium" if risk_level == CAUTION else "low"
        environment_sensitivity = "production" if "production" in (target or "").lower() else "standard"
        irreversible_operation = action_class in {"destructive", "structural"} and risk_level == DANGEROUS
        return MutationSafetyDecision(
            action=action,
            target=target or "",
            action_class=action_class,
            target_type=target_type,
            risk_level=risk_level,
            checkpoint_required=self.requires_checkpoint(action, target),
            approval_required=risk_level == DANGEROUS,
            destructive_potential=destructive_potential,
            environment_sensitivity=environment_sensitivity,
            irreversible_operation=irreversible_operation,
            restore_strategy="checkpoint_restore" if self.requires_checkpoint(action, target) else "not_required",
        )
