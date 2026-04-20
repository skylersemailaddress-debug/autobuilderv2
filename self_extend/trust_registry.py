from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class TrustRegistry:
    def __init__(self, path: str = "self_extend/trust_registry.json"):
        self.path = Path(path)
        self.registry = self._load()

    def _load(self) -> Dict[str, dict]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def register(self, name: str, status: str, provenance: str | None = None):
        self.registry[name] = {
            "status": status,
            "provenance": provenance,
        }
        self._save()

    def get(self, name: str):
        return self.registry.get(name)

    def promote(self, name: str) -> None:
        if name in self.registry:
            self.registry[name]["status"] = "promoted"
            self._save()

    def quarantine(self, name: str) -> None:
        if name in self.registry:
            self.registry[name]["status"] = "quarantined"
            self._save()

    def rollback(self, name: str) -> None:
        if name in self.registry:
            self.registry[name]["status"] = "rolled_back"
            self._save()
