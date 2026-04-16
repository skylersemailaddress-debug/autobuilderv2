from __future__ import annotations

import hashlib
import json
from pathlib import Path


TOOL_TYPE_TEMPLATES = {
    "validator": "def validate(payload: dict[str, object]) -> bool:\n    return bool(payload)\n",
    "connector": "def connect(config: dict[str, object]) -> dict[str, object]:\n    return {'status': 'connected', 'config': config}\n",
    "helper": "def helper(value: str) -> str:\n    return value.strip()\n",
    "domain_utility": "def run_domain_rule(entity: dict[str, object]) -> dict[str, object]:\n    return {'entity': entity, 'status': 'processed'}\n",
}

FORBIDDEN_SNIPPETS = ["os.system", "subprocess.Popen", "eval(", "exec("]


def _signature(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def generate_tool_candidate(
    *,
    sandbox_root: str | Path,
    tool_name: str,
    tool_type: str,
    purpose: str,
    lane_id: str,
) -> dict[str, object]:
    if tool_type not in TOOL_TYPE_TEMPLATES:
        raise ValueError(f"Unsupported tool_type '{tool_type}'")

    safe_name = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in tool_name.lower()).strip("_")
    if not safe_name:
        raise ValueError("tool_name must contain letters or numbers")

    root = Path(sandbox_root).resolve()
    tool_dir = root / "generated_tools"
    tool_dir.mkdir(parents=True, exist_ok=True)

    module_path = tool_dir / f"{safe_name}.py"
    content = (
        f"\"\"Auto-generated tool: {safe_name}\"\"\"\n\n"
        f"# purpose: {purpose}\n"
        f"# lane_id: {lane_id}\n"
        + TOOL_TYPE_TEMPLATES[tool_type]
    )
    module_path.write_text(content, encoding="utf-8")

    candidate = {
        "tool_id": f"tool::{lane_id}::{safe_name}",
        "tool_name": safe_name,
        "tool_type": tool_type,
        "purpose": purpose,
        "lane_id": lane_id,
        "module_path": str(module_path),
        "quality_threshold": 80,
        "safety_tier": "standard",
        "validation_requirements": ["file_exists", "forbidden_calls_absent", "signature_present"],
    }
    candidate["candidate_signature_sha256"] = _signature(candidate)
    return candidate


def validate_tool_candidate(candidate: dict[str, object]) -> dict[str, object]:
    module_path = Path(str(candidate.get("module_path", "")))
    checks: list[dict[str, object]] = []

    exists = module_path.exists()
    checks.append({"name": "file_exists", "passed": exists})

    content = module_path.read_text(encoding="utf-8") if exists else ""
    checks.append({
        "name": "forbidden_calls_absent",
        "passed": all(snippet not in content for snippet in FORBIDDEN_SNIPPETS),
    })
    checks.append({
        "name": "signature_present",
        "passed": bool(candidate.get("candidate_signature_sha256")),
    })

    passed_count = sum(1 for item in checks if item["passed"])
    quality_score = int((passed_count / len(checks)) * 100) if checks else 0

    return {
        "tool_id": candidate.get("tool_id", ""),
        "checks": checks,
        "quality_score": quality_score,
        "is_valid": passed_count == len(checks),
        "safety_tier": candidate.get("safety_tier", "standard"),
    }
