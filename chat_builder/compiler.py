from __future__ import annotations

import re
from pathlib import Path

from chat_builder.models import ParsedIntent, SynthesizedSpecBundle


UNSUPPORTED_KEYWORDS = {
    "unity": "Unity engine is currently unsupported. Use the bounded Godot lane for prototype game builds.",
    "unreal": "Unreal engine is currently unsupported. Use the bounded Godot lane for prototype game builds.",
    "react native": "React Native is currently unsupported. Use the bounded Flutter mobile lane.",
    "swiftui": "SwiftUI-only native lane is currently unsupported. Use the bounded Flutter mobile lane.",
    "kubernetes": "Kubernetes deployment manifests are currently unsupported. Use Docker Compose lane outputs.",
}

RISKY_KEYWORDS = {
    "medical": "Medical-regulated workflows require external compliance review.",
    "finance": "Financial workflows may require stricter audit and policy controls.",
    "children": "Apps for children need extra content and privacy safety review.",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _infer_lane(prompt: str) -> tuple[str, str, dict[str, str], list[str]]:
    text = _normalize(prompt)
    defaults: list[str] = []

    if any(word in text for word in ["flutter", "mobile", "android", "ios"]):
        return (
            "first_class_mobile",
            "mobile_app",
            {
                "frontend": "flutter_mobile",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
            defaults,
        )
    if any(word in text for word in ["godot", "game", "graphics", "prototype gameplay"]):
        return (
            "first_class_game",
            "game_app",
            {
                "frontend": "godot_game",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
            defaults,
        )
    if any(word in text for word in ["realtime", "sensor", "stream", "live", "telemetry"]):
        return (
            "first_class_realtime",
            "realtime_system",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
            defaults,
        )
    if any(word in text for word in ["workflow", "enterprise agent", "campaign", "office", "corporate operating"]):
        return (
            "first_class_enterprise_agent",
            "enterprise_agent_system",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
            defaults,
        )

    defaults.append("No lane phrase found; defaulted to commercial web lane.")
    return (
        "first_class_commercial",
        "saas_web_app",
        {
            "frontend": "react_next",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
        defaults,
    )


def _infer_name(prompt: str) -> tuple[str, list[str]]:
    defaults: list[str] = []
    match = re.search(
        r"(?:called|named)\s+([A-Za-z0-9 _-]{3,40}?)(?:\s+(?:for|with|that|which)\b|$)",
        prompt,
        flags=re.IGNORECASE,
    )
    if match:
        name = re.sub(r"\s+", " ", match.group(1)).strip()
        return name.title(), defaults

    # Deterministic fallback using first few words.
    words = [word for word in re.findall(r"[A-Za-z0-9]+", prompt) if len(word) > 2][:3]
    if words:
        return (" ".join(words)).title() + " App", defaults

    defaults.append("No explicit app name provided; using Starter App.")
    return "Starter App", defaults


def parse_conversation_intent(prompt: str) -> ParsedIntent:
    lane_id, app_type, stack, lane_defaults = _infer_lane(prompt)
    app_name, name_defaults = _infer_name(prompt)
    normalized = _normalize(prompt)

    unsupported = [message for token, message in UNSUPPORTED_KEYWORDS.items() if token in normalized]
    risky = [message for token, message in RISKY_KEYWORDS.items() if token in normalized]

    requested_features = sorted(
        {
            feature
            for feature in [
                "approvals" if "approval" in normalized else "",
                "notifications" if "alert" in normalized or "notification" in normalized else "",
                "analytics" if "report" in normalized or "analytics" in normalized else "",
                "memory" if "memory" in normalized or "history" in normalized else "",
                "realtime" if "stream" in normalized or "realtime" in normalized else "",
                "billing" if "billing" in normalized or "subscription" in normalized else "",
            ]
            if feature
        }
    )

    core_outcome = "Help users complete a clear workflow from input to outcome"
    if "for" in normalized:
        after_for = normalized.split("for", 1)[1].strip()
        if after_for:
            core_outcome = after_for[:120]

    missing: list[str] = []
    if "user" not in normalized and "team" not in normalized and "customer" not in normalized:
        missing.append("Who is the main user?")
    if "must" not in normalized and "need" not in normalized and "should" not in normalized:
        missing.append("What is the single most important outcome?")
    if not requested_features:
        missing.append("Which one feature matters most for version one?")

    inferred_defaults = lane_defaults + name_defaults
    if not requested_features:
        inferred_defaults.append("No feature list provided; defaulting to auth, health, and basic workflow scaffolds.")

    return ParsedIntent(
        prompt=prompt,
        app_name=app_name,
        app_type=app_type,
        lane_id=lane_id,
        stack=stack,
        core_outcome=core_outcome,
        requested_features=requested_features,
        unsupported_requests=unsupported,
        risky_requests=risky,
        inferred_defaults=inferred_defaults,
        missing_info=missing,
    )


def synthesize_spec_bundle(intent: ParsedIntent) -> SynthesizedSpecBundle:
    lane_focus = {
        "first_class_mobile": ["mobile_navigation", "api_sync", "state_model", "env_config"],
        "first_class_game": ["scene_structure", "input_model", "main_loop", "export_expectations"],
        "first_class_realtime": ["event_streams", "sensor_connectors", "alert_paths", "world_state_updates"],
        "first_class_enterprise_agent": ["multi_role_workflows", "approvals", "memory_state", "task_routing", "briefings"],
        "first_class_commercial": ["workspace_shell", "api_workflows", "proof_readiness"],
    }

    architecture_workflows = [{"name": feature} for feature in lane_focus[intent.lane_id]]
    if not architecture_workflows:
        architecture_workflows = [{"name": "core_flow"}]

    acceptance_points = [
        "Build completes deterministically",
        "Validation and proof pass",
        "Generated scaffold reflects lane expectations",
    ]
    if intent.requested_features:
        acceptance_points.append("Includes requested feature placeholders: " + ", ".join(intent.requested_features))

    product = {
        "name": intent.app_name,
        "app_type": intent.app_type,
        "application_domains": _domains_for_app_type(intent.app_type),
    }
    architecture = {
        "entities": [{"name": "WorkspaceItem"}, {"name": "UserProfile"}],
        "workflows": architecture_workflows,
        "api_routes": [{"path": "/health"}, {"path": "/api/workspace/execute"}],
        "runtime_services": [{"name": "api"}, {"name": "worker"}],
        "permissions": [{"role": "operator"}, {"role": "admin"}],
    }
    ui = {
        "pages": [{"name": "Home", "route": "/"}, {"name": "Settings", "route": "/settings"}],
    }
    acceptance = {"criteria": acceptance_points}
    stack = {
        "frontend": intent.stack["frontend"],
        "backend": intent.stack["backend"],
        "database": intent.stack["database"],
        "deployment": intent.stack["deployment"],
        "deployment_target": "container",
    }

    explanations = [
        f"I matched your app to lane {intent.lane_id} because of the request wording.",
        "I kept the stack inside supported first-class combinations to avoid fragile builds.",
        "I used safe defaults where details were missing so you can preview before building.",
    ]
    return SynthesizedSpecBundle(
        product=product,
        architecture=architecture,
        ui=ui,
        acceptance=acceptance,
        stack=stack,
        explanations=explanations,
    )


def write_spec_bundle(spec: SynthesizedSpecBundle, spec_root: Path) -> Path:
    spec_root.mkdir(parents=True, exist_ok=True)
    files = {
        "product.yaml": spec.product,
        "architecture.yaml": spec.architecture,
        "ui.yaml": spec.ui,
        "acceptance.yaml": spec.acceptance,
        "stack.yaml": spec.stack,
    }
    for name, payload in files.items():
        (spec_root / name).write_text(json_dumps(payload), encoding="utf-8")
    return spec_root


def json_dumps(payload: dict[str, object]) -> str:
    import json

    return json.dumps(payload, sort_keys=True) + "\n"


def _domains_for_app_type(app_type: str) -> list[str]:
    if app_type == "mobile_app":
        return ["mobile_apps"]
    if app_type == "game_app":
        return ["games"]
    if app_type == "realtime_system":
        return ["realtime_systems"]
    if app_type == "enterprise_agent_system":
        return ["enterprise_systems"]
    return ["web_apps"]
