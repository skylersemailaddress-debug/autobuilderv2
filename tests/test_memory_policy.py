from memory.policy import MemoryRetrievalPolicy
from cli.run import perform_run
from memory.json_memory import JsonMemoryStore
from pathlib import Path


def test_memory_policy_limits_and_selects_relevant_items():
    policy = MemoryRetrievalPolicy(max_memories=2)
    memories = [
        {"key": "old_goal", "value": {"goal": "Build docs"}},
        {"key": "summary", "value": {"goal": "Build autonomous execution plan"}},
        {"key": "risk", "value": {"risk_level": "high", "goal": "Delete production"}},
    ]

    selected, summary = policy.select_memories("Build autonomous plan", memories)

    assert len(selected) == 2
    assert summary["max_memories"] == 2
    assert summary["candidate_count"] == 3
    assert summary["selected_count"] == 2
    assert len(summary["selected_memory_keys"]) == 2


def test_memory_policy_deterministic_ordering():
    policy = MemoryRetrievalPolicy(max_memories=3)
    memories = [
        {"key": "b", "value": {"goal": "build app"}},
        {"key": "a", "value": {"goal": "build app"}},
    ]

    selected, _ = policy.select_memories("build", memories)
    assert [item["key"] for item in selected] == ["a", "b"]


def test_memory_policy_influences_selected_memories_in_run_record():
    run_id = "memory_policy_integration_run"
    memory_file = Path(__file__).resolve().parents[1] / "memory" / f"{run_id}.json"
    store = JsonMemoryStore(str(memory_file))

    store.add_memory("m1", {"goal": "Build autonomous execution plan alpha"})
    store.add_memory("m2", {"goal": "Build autonomous execution plan beta"})
    store.add_memory("m3", {"goal": "Build autonomous execution plan gamma"})
    store.add_memory("m4", {"goal": "Build autonomous execution plan delta"})
    store.add_memory("summary", {"goal": "Build autonomous execution plan summary"})

    record, saved_path = perform_run(run_id, goal="Build autonomous execution plan")

    assert "memory_policy_summary" in record
    assert record["memory_policy_summary"]["max_memories"] == 3
    assert record["memory_policy_summary"]["selected_count"] <= 3
    assert "selected_memory_keys" in record
    assert len(record["selected_memory_keys"]) <= 3
    assert set(record["selected_memory_keys"]) == set(record["memory_context"].keys())

    Path(saved_path).unlink()
    if memory_file.exists():
        memory_file.unlink()
