from pathlib import Path

from chat_builder.project_memory import ChatProjectMemoryStore


def test_project_memory_persists_session_and_decisions(tmp_path: Path) -> None:
    store = ChatProjectMemoryStore(tmp_path)
    session_id = store.derive_session_id("Build a mobile app")
    project_id = store.derive_project_id("/tmp/app")

    snapshot = store.load_or_create(session_id, project_id)
    snapshot.conversation_turns.append({"user": "hello", "assistant_summary": "ok"})
    snapshot.decisions.append({"lane_id": "first_class_mobile"})
    snapshot.accepted_defaults.append("default lane assumptions")

    path = store.save(snapshot)
    loaded = store.load_or_create(session_id, project_id)

    assert Path(path).exists()
    assert loaded.conversation_turns[0]["user"] == "hello"
    assert loaded.decisions[0]["lane_id"] == "first_class_mobile"
    assert "default lane assumptions" in loaded.accepted_defaults
