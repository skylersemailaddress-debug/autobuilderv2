from dataclasses import dataclass, field
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
    lane_id: str = "unspecified"
    stack_id: str = "unspecified"
    failure_mode: str = "continue"
    policy_basis: list[str] = field(default_factory=list)


class MutationSafetyPolicy:
    def _action_class(self, action: str, target: Optional[str]) -> str:
        combined = f"{(action or '').lower()} {(target or '').lower()}"
        if any(keyword in combined for keyword in ["delete", "destroy", "remove", "drop", "truncate", "purge"]):
            return "destructive"
        if any(keyword in combined for keyword in ["migrate", "rename", "replace", "refactor"]):
            return "structural"
        if any(keyword in combined for keyword in ["update", "modify", "write", "edit", "patch", "apply", "extend"]):
            return "mutation"
        if any(keyword in combined for keyword in ["validate", "inspect", "proof", "audit", "read", "check"]):
            return "validation"
        return "creation"

    def _target_type(self, target: Optional[str]) -> str:
        target_lower = (target or "").lower()
        if "production" in target_lower:
            return "production_resource"
        if any(keyword in target_lower for keyword in ["control_plane", "approval", "governance", "audit", "state/"]):
            return "governance_state"
        if "database" in target_lower:
            return "database"
        if "sandbox" in target_lower:
            return "sandbox"
        if any(keyword in target_lower for keyword in ["spec", "mission.yml", "stack.yml", "features.yml"]):
            return "spec_bundle"
        if any(keyword in target_lower for keyword in ["file", "repo", "repository"]):
            return "filesystem"
        if "/" in target_lower or "." in target_lower:
            return "filesystem"
        return "logical_goal"

    def classify(self, action: str, target: Optional[str] = None) -> str:
        return self.evaluate(action, target).risk_level

    def requires_checkpoint(self, action: str, target: Optional[str] = None) -> bool:
        return self.evaluate(action, target).checkpoint_required

    def evaluate(
        self,
        action: str,
        target: Optional[str] = None,
        *,
        lane_id: Optional[str] = None,
        stack_id: Optional[str] = None,
        target_type: Optional[str] = None,
        irreversible_operation: Optional[bool] = None,
    ) -> MutationSafetyDecision:
        action_class = self._action_class(action, target)
        resolved_target_type = target_type or self._target_type(target)
        action_lower = (action or "").lower()
        target_lower = (target or "").lower()
        policy_basis: list[str] = []

        if resolved_target_type in {"production_resource", "database", "governance_state"}:
            policy_basis.append(f"sensitive_target:{resolved_target_type}")
        if action_class in {"destructive", "structural"}:
            policy_basis.append(f"action_class:{action_class}")
        if lane_id:
            policy_basis.append(f"lane:{lane_id}")
        if stack_id:
            policy_basis.append(f"stack:{stack_id}")

        environment_sensitivity = "standard"
        if resolved_target_type == "production_resource":
            environment_sensitivity = "production"
        elif resolved_target_type == "governance_state":
            environment_sensitivity = "governance"
        elif resolved_target_type == "sandbox":
            environment_sensitivity = "sandbox"
        elif lane_id in {"first_class_enterprise_agent", "first_class_realtime"}:
            environment_sensitivity = "elevated"
            policy_basis.append("lane_requires_elevated_controls")

        resolved_irreversible = bool(irreversible_operation)
        if irreversible_operation is None:
            resolved_irreversible = action_class in {"destructive", "structural"} and resolved_target_type in {
                "filesystem",
                "database",
                "governance_state",
                "production_resource",
            }

        if action_class == "validation":
            risk_level = SAFE
        elif action_class == "creation" and resolved_target_type not in {"production_resource", "database", "governance_state"}:
            risk_level = SAFE
        elif resolved_irreversible or resolved_target_type in {"production_resource", "governance_state"} and action_class in {"mutation", "structural", "destructive"}:
            risk_level = DANGEROUS
        elif action_class in {"mutation", "structural"} or resolved_target_type in {"filesystem", "spec_bundle", "database"}:
            risk_level = CAUTION
        elif any(keyword in f"{action_lower} {target_lower}" for keyword in ["production", "delete", "destroy", "migrate", "rename"]):
            risk_level = DANGEROUS
        else:
            risk_level = SAFE

        destructive_potential = "low"
        if resolved_irreversible or action_class == "destructive" or resolved_target_type in {"database", "production_resource"}:
            destructive_potential = "high"
        elif action_class in {"mutation", "structural"} or resolved_target_type in {"filesystem", "governance_state", "spec_bundle"}:
            destructive_potential = "medium"

        checkpoint_required = risk_level == DANGEROUS or (
            risk_level == CAUTION and action_class in {"structural", "mutation"} and resolved_target_type in {"governance_state", "database"}
        )
        approval_required = risk_level == DANGEROUS or (
            resolved_irreversible and environment_sensitivity in {"production", "governance", "elevated"}
        )
        restore_strategy = "checkpoint_restore" if checkpoint_required else "journal_only" if risk_level == CAUTION else "not_required"
        failure_mode = "halt_before_mutation" if approval_required else "restore_from_checkpoint" if checkpoint_required else "continue"

        return MutationSafetyDecision(
            action=action,
            target=target or "",
            action_class=action_class,
            target_type=resolved_target_type,
            risk_level=risk_level,
            checkpoint_required=checkpoint_required,
            approval_required=approval_required,
            destructive_potential=destructive_potential,
            environment_sensitivity=environment_sensitivity,
            irreversible_operation=resolved_irreversible,
            restore_strategy=restore_strategy,
            lane_id=lane_id or "unspecified",
            stack_id=stack_id or "unspecified",
            failure_mode=failure_mode,
            policy_basis=policy_basis,
        )
