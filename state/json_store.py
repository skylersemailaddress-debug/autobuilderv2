import json
from pathlib import Path


class JsonRunStore:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parents[1] / "runs"
        else:
            self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run_id, data):
        path = self.base_dir / f"{run_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        return path

    def load(self, run_id):
        path = self.base_dir / f"{run_id}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
