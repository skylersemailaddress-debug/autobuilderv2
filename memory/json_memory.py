import json
from pathlib import Path
from typing import Dict


class JsonMemoryStore:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text("{}")

    def add_memory(self, key: str, value: Dict):
        data = self._load_data()
        data[key] = value
        self._save_data(data)

    def get_memory(self, key: str) -> Dict | None:
        data = self._load_data()
        return data.get(key)

    def list_keys(self) -> list[str]:
        data = self._load_data()
        return list(data.keys())

    def _load_data(self) -> Dict:
        try:
            return json.loads(self.file_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: Dict):
        self.file_path.write_text(json.dumps(data, indent=2))
