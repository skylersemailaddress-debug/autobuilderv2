from __future__ import annotations

from mutation.classifier import classify_mutation
from mutation.preflight import preflight_check
from mutation.postwrite_verify import verify_postwrite
from policies.engine import PolicyEngine
from control_plane.approval_engine import ApprovalEngine

_policy = PolicyEngine()
_approval = ApprovalEngine()


def execute_mutation(target_path: str, action: str, context: dict) -> bool:
    classification = classify_mutation(target_path, context)

    policy_result = _policy.evaluate(action, context)
    if policy_result["decision"] == "deny":
        raise RuntimeError("Policy denied mutation")

    approval = _approval.evaluate(action, context.get("actor", "system"), context)
    if not approval.get("approved"):
        raise RuntimeError("Mutation not approved")

    preflight = preflight_check(action, context)
    if not preflight.get("approved"):
        raise RuntimeError("Preflight check failed")

    # simulate mutation success
    success = True

    verify_postwrite(success)
    return success
