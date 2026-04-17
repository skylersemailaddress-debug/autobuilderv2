from chat_builder.compiler import parse_conversation_intent, synthesize_spec_bundle


def test_conversation_to_spec_synthesis_is_deterministic() -> None:
    prompt = "Build a mobile app called Field Buddy for team tasks with alerts and history"
    intent = parse_conversation_intent(prompt)
    spec = synthesize_spec_bundle(intent)

    assert intent.app_type == "mobile_app"
    assert intent.lane_id == "first_class_mobile"
    assert intent.stack["frontend"] == "flutter_mobile"
    assert spec.product["name"] == "Field Buddy"
    assert spec.stack["frontend"] == "flutter_mobile"
    assert spec.stack["backend"] == "fastapi"


def test_missing_info_and_default_inference() -> None:
    prompt = "make app"
    intent = parse_conversation_intent(prompt)

    assert intent.lane_id == "first_class_commercial"
    assert intent.app_type == "saas_web_app"
    assert len(intent.missing_info) >= 1
    assert any("default" in item.lower() for item in intent.inferred_defaults)


def test_unsupported_request_is_detected_clearly() -> None:
    prompt = "Build a unity game with kubernetes"
    intent = parse_conversation_intent(prompt)

    assert intent.app_type == "game_app"
    assert intent.unsupported_requests
    assert any("unsupported" in item.lower() for item in intent.unsupported_requests)


def test_auth_and_roles_tokens_propagate_into_spec_architecture() -> None:
    prompt = "Build an internal tool with auth, RBAC, roles for admin and auditor"
    intent = parse_conversation_intent(prompt)
    spec = synthesize_spec_bundle(intent)

    routes = {route["path"] for route in spec.architecture["api_routes"]}
    role_names = {item["name"] for item in spec.architecture["auth_roles"]}
    runtime_services = {service["name"] for service in spec.architecture["runtime_services"]}

    assert "auth" in intent.requested_features
    assert "rbac" in intent.requested_features
    assert "roles" in intent.requested_features
    assert "/api/auth/session" in routes
    assert {"admin", "auditor"}.issubset(role_names)
    assert "security_service" in runtime_services
    assert spec.architecture["decision_map"]["runtime"]["auth_mode"] in {"session_auth", "federated_auth_scaffold", "token_auth"}


def test_billing_and_payments_tokens_propagate_into_spec_architecture() -> None:
    prompt = "Build a SaaS app with billing, payments, and Stripe subscriptions"
    intent = parse_conversation_intent(prompt)
    spec = synthesize_spec_bundle(intent)

    routes = {route["path"] for route in spec.architecture["api_routes"]}
    runtime_services = {service["name"] for service in spec.architecture["runtime_services"]}
    role_names = {item["name"] for item in spec.architecture["auth_roles"]}

    assert "billing" in intent.requested_features
    assert "payments" in intent.requested_features
    assert "/api/plans" in routes
    assert "/api/billing/webhooks" in routes
    assert "billing_service" in runtime_services
    assert "billing_admin" in role_names
    assert "billing_reconciliation" in {job["name"] for job in spec.architecture["background_jobs"]}


def test_realtime_intent_maps_into_decision_map_and_routes() -> None:
    prompt = "Build a realtime control app with telemetry streams, memory, and operator console"
    intent = parse_conversation_intent(prompt)
    spec = synthesize_spec_bundle(intent)

    routes = {route["path"] for route in spec.architecture["api_routes"]}
    runtime_services = {service["name"] for service in spec.architecture["runtime_services"]}

    assert "realtime" in intent.requested_features
    assert "/api/realtime/events" in routes
    assert "event_router" in runtime_services
    assert "memory_state" in runtime_services
    assert spec.architecture["decision_map"]["workflow"]["focus"]
