from __future__ import annotations

import hashlib
import json
from pathlib import Path

from chat_builder.models import ChatMemorySnapshot


class ChatProjectMemoryStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def derive_session_id(prompt: str) -> str:
        return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def derive_project_id(target_path: str) -> str:
        return hashlib.sha256(target_path.strip().encode("utf-8")).hexdigest()[:12]

    def load_or_create(self, session_id: str, project_id: str) -> ChatMemorySnapshot:
        path = self._path_for(session_id, project_id)
        if not path.exists():
            return ChatMemorySnapshot(session_id=session_id, project_id=project_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ChatMemorySnapshot(
            session_id=session_id,
            project_id=project_id,
            conversation_turns=list(payload.get("conversation_turns", [])),
            decisions=list(payload.get("decisions", [])),
            accepted_defaults=list(payload.get("accepted_defaults", [])),
            tradeoffs=list(payload.get("tradeoffs", [])),
            failures=list(payload.get("failures", [])),
            fixes=list(payload.get("fixes", [])),
            generated_components=list(payload.get("generated_components", [])),
        )

    def save(self, snapshot: ChatMemorySnapshot) -> str:
        path = self._path_for(snapshot.session_id, snapshot.project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return str(path)

    def _path_for(self, session_id: str, project_id: str) -> Path:
        return self.root / f"chat_{session_id}_{project_id}.json"
