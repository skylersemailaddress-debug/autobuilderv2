from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from zipfile import ZIP_DEFLATED, ZipFile


def _write_frontend(root: Path, app_type: str, features: List[str], stack: List[str]) -> str:
    app_dir = root / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    package_json = {
        "name": "generated-app",
        "private": True,
        "version": "0.1.0",
        "scripts": {
            "dev": "python -m http.server 3000 -d app",
            "build": "echo build-ok",
            "start": "python -m http.server 3000 -d app"
        }
    }
    (root / "package.json").write_text(json.dumps(package_json, indent=2) + "\n", encoding="utf-8")
    (app_dir / "index.html").write_text(
        f"<html><body><h1>{app_type}</h1><p>Features: {', '.join(features)}</p><p>Stack: {', '.join(stack)}</p></body></html>\n",
        encoding="utf-8",
    )
    return str(app_dir / "index.html")


def _write_backend(root: Path) -> str:
    api_dir = root / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (root / "requirements.txt").write_text("fastapi==0.115.0\nuvicorn==0.30.6\n", encoding="utf-8")
    (api_dir / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    return str(api_dir / "main.py")


def validate_generated_output(root_dir: str) -> Dict[str, Any]:
    root = Path(root_dir)
    required = [root / "spec.json", root / "README.md", root / "package.json", root / "requirements.txt", root / "app" / "index.html", root / "api" / "main.py"]
    missing = [str(p) for p in required if not p.exists()]
    return {
        "valid": len(missing) == 0,
        "missing": missing,
    }


def package_generated_output(root_dir: str) -> str:
    root = Path(root_dir)
    zip_path = root.with_suffix(".zip")
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root))
    return str(zip_path)


def generate_app_from_spec(spec: Dict[str, Any], output_dir: str = "generated_apps/latest") -> Dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    app_type = spec.get("app", {}).get("type", "web_app")
    features = spec.get("app", {}).get("features", [])
    stack = spec.get("stack", [])

    (root / "spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"# Generated App\n\nType: {app_type}\n\nFeatures: {', '.join(features)}\n\nStack: {', '.join(stack)}\n",
        encoding="utf-8",
    )
    entrypoint = _write_frontend(root, app_type, features, stack)
    backend = _write_backend(root)
    validation = validate_generated_output(str(root))
    package_path = package_generated_output(str(root)) if validation["valid"] else None

    return {
        "root": str(root),
        "spec": str(root / "spec.json"),
        "readme": str(root / "README.md"),
        "entrypoint": entrypoint,
        "backend": backend,
        "validation": validation,
        "package": package_path,
    }
