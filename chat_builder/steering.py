from __future__ import annotations

from chat_builder.models import ParsedIntent, SteeringDecision


def _prioritize_questions(intent: ParsedIntent) -> list[str]:
    ranked = list(intent.missing_info)
    high_priority: list[str] = []

    for item in ranked:
        text = item.lower()
        if "compliance" in text or "credentials" in text:
            high_priority.append(item)

    for item in ranked:
        if item not in high_priority:
            high_priority.append(item)

    if "billing" in intent.requested_features and all("billing" not in q.lower() for q in high_priority):
        high_priority.append("Confirm billing authority and support workflow for payment disputes.")
    if "realtime" in intent.requested_features and all("throughput" not in q.lower() for q in high_priority):
        high_priority.append("What event throughput target should the realtime workflow assume?")

    return high_priority[:3]


def build_steering_decision(intent: ParsedIntent) -> SteeringDecision:
    warnings = list(intent.risky_requests)
    if intent.unsupported_requests:
        warnings.extend(intent.unsupported_requests)

    tradeoffs = [
        "Using first-class stacks makes builds reliable but limits custom stack choices.",
        "Safe defaults speed progress now and can be refined in later iterations.",
    ]

    critical_questions = _prioritize_questions(intent)
    if not critical_questions and intent.app_type == "saas_web_app":
        critical_questions = ["Should I include billing placeholders in version one?"]

    next_steps = [
        "Review the plan preview.",
        "Approve the preview to start deterministic build and proof.",
    ]

    features = ", ".join(intent.requested_features[:5]) if intent.requested_features else "core workflow"
    simple_summary = (
        f"I mapped your request to {intent.app_type} on {intent.lane_id} with supported stacks and focus on: {features}."
    )

    if intent.unsupported_requests:
        next_steps = [
            "Remove unsupported engine/stack requests.",
            "Keep lane-compatible requirements and regenerate preview.",
        ]

    return SteeringDecision(
        simple_summary=simple_summary,
        critical_questions=critical_questions,
        tradeoffs=tradeoffs,
        warnings=warnings,
        next_steps=next_steps,
    )
