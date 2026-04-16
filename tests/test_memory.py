from memory.store import MemoryStore


def test_memory_store_add_get_list():
    store = MemoryStore()

    assert store.list_keys() == []

    store.add_memory("goal", {"goal": "Build an autonomous execution plan"})
    assert store.get_memory("goal") == {"goal": "Build an autonomous execution plan"}
    assert store.list_keys() == ["goal"]
    assert store.get_memory("missing") is None
