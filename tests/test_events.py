from observability.events import create_event


def test_create_event_has_expected_fields():
    event = create_event("run_started", {"run_id": "abc"})

    assert event.event_type == "run_started"
    assert event.detail == {"run_id": "abc"}
    assert event.timestamp.endswith("+00:00") or event.timestamp.endswith("Z")
