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
