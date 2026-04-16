from __future__ import annotations

from chat_builder.models import ParsedIntent, SteeringDecision


def build_steering_decision(intent: ParsedIntent) -> SteeringDecision:
    warnings = list(intent.risky_requests)
    if intent.unsupported_requests:
        warnings.extend(intent.unsupported_requests)

    tradeoffs = [
        "Using first-class stacks makes builds reliable but limits custom stack choices.",
        "Safe defaults speed progress now and can be refined in later iterations.",
    ]

    critical_questions = intent.missing_info[:2]
    if not critical_questions and intent.app_type == "saas_web_app":
        critical_questions = ["Should I include billing placeholders in version one?"]

    next_steps = [
        "Review the plan preview.",
        "Approve the preview to start deterministic build and proof.",
    ]

    simple_summary = (
        f"I understood your idea as a {intent.app_type} on lane {intent.lane_id} with a safe supported stack."
    )

    return SteeringDecision(
        simple_summary=simple_summary,
        critical_questions=critical_questions,
        tradeoffs=tradeoffs,
        warnings=warnings,
        next_steps=next_steps,
    )
