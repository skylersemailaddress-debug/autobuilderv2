from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def generate_app_from_spec(spec: Dict[str, Any], output_dir: str = "generated_apps/latest") -> Dict[str, str]:
    root = Path(output_dir)
    app_dir = root / "app"
    api_dir = root / "api"
    app_dir.mkdir(parents=True, exist_ok=True)
    api_dir.mkdir(parents=True, exist_ok=True)

    app_type = spec.get("app", {}).get("type", "web_app")
    features = spec.get("app", {}).get("features", [])
    stack = spec.get("stack", [])

    (root / "spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"# Generated App\n\nType: {app_type}\n\nFeatures: {', '.join(features)}\n\nStack: {', '.join(stack)}\n",
        encoding="utf-8",
    )
    (app_dir / "index.html").write_text(
        "<html><body><h1>Generated App</h1><p>Output lane scaffold</p></body></html>\n",
        encoding="utf-8",
    )
    (api_dir / "health.json").write_text('{"status": "ok"}\n', encoding="utf-8")

    return {
        "root": str(root),
        "spec": str(root / "spec.json"),
        "readme": str(root / "README.md"),
        "entrypoint": str(app_dir / "index.html"),
        "health": str(api_dir / "health.json"),
    }
