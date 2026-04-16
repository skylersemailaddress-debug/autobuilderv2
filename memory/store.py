from typing import Dict


class MemoryStore:
    def __init__(self):
        self._store: Dict[str, dict] = {}

    def add_memory(self, key: str, value: dict):
        self._store[key] = value

    def get_memory(self, key: str) -> dict | None:
        return self._store.get(key)

    def list_keys(self) -> list[str]:
        return list(self._store.keys())
