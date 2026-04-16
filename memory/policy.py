import json
from datetime import datetime
from typing import Dict, List, Tuple


class MemoryRetrievalPolicy:
    def __init__(self, max_memories: int = 3):
        self.max_memories = max_memories

    def _relevance_score(self, query: str, key: str, value: Dict) -> int:
        query_tokens = [token for token in query.lower().split() if token]
        haystack = f"{key} {json.dumps(value, sort_keys=True).lower()}"
        return sum(1 for token in query_tokens if token in haystack)

    def _recency_score(self, value: Dict, key: str) -> int:
        created_at = value.get("created_at") if isinstance(value, dict) else None
        if isinstance(created_at, str):
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                return int(dt.timestamp())
            except ValueError:
                return 0
        if key == "summary":
            return 1
        return 0

    def select_memories(self, query: str, memories: List[Dict]) -> Tuple[List[Dict], Dict]:
        scored = []
        for item in memories:
            key = item.get("key", "")
            value = item.get("value", {})
            relevance = self._relevance_score(query, key, value)
            recency = self._recency_score(value, key)
            scored.append({
                "key": key,
                "value": value,
                "relevance": relevance,
                "recency": recency,
            })

        scored.sort(key=lambda item: (-item["relevance"], -item["recency"], item["key"]))
        selected = scored[: self.max_memories]

        return selected, {
            "max_memories": self.max_memories,
            "candidate_count": len(memories),
            "selected_count": len(selected),
            "selection_strategy": "relevance_then_recency_then_key",
            "selected_memory_keys": [item["key"] for item in selected],
        }
