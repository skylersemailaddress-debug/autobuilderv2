import tempfile
from pathlib import Path
from memory.json_memory import JsonMemoryStore


def test_json_memory_add_get_list():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JsonMemoryStore(str(Path(temp_dir) / "memory.json"))
        
        assert store.list_keys() == []
        
        store.add_memory("goal", {"goal": "Build an autonomous execution plan"})
        assert store.get_memory("goal") == {"goal": "Build an autonomous execution plan"}
        assert store.list_keys() == ["goal"]
        assert store.get_memory("missing") is None


def test_json_memory_persistence():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "memory.json"
        store1 = JsonMemoryStore(str(file_path))
        store1.add_memory("test", {"value": 42})
        
        # Create new instance to test persistence
        store2 = JsonMemoryStore(str(file_path))
        assert store2.get_memory("test") == {"value": 42}
        assert store2.list_keys() == ["test"]
