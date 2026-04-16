import tempfile
from pathlib import Path
from memory.json_memory import JsonMemoryStore


def test_json_memory_search_memories():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JsonMemoryStore(str(Path(temp_dir) / "memory.json"))
        
        # Add some test data
        store.add_memory("goal1", {"goal": "Build an autonomous execution plan"})
        store.add_memory("goal2", {"goal": "Delete production database"})
        store.add_memory("summary", {"confidence": 0.8, "risk_level": "high"})
        
        # Test search
        results = store.search_memories("execution")
        assert len(results) == 1
        assert results[0]["key"] == "goal1"
        assert "execution" in results[0]["value"]["goal"]
        
        # Test search in key
        results = store.search_memories("goal")
        assert len(results) == 2  # goal1 and goal2
        
        # Test no matches
        results = store.search_memories("nonexistent")
        assert len(results) == 0
