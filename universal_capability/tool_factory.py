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

CAPABILITY_KIND_TO_TEMPLATE = {
    "tool": TOOL_TYPE_TEMPLATES["domain_utility"],
    "pack": "def register_pack() -> dict[str, object]:\n    return {'status': 'registered', 'kind': 'pack'}\n",
    "adapter": "def adapt(payload: dict[str, object]) -> dict[str, object]:\n    return {'status': 'adapted', 'payload': payload}\n",
    "validator": TOOL_TYPE_TEMPLATES["validator"],
    "contract": "def contract_schema() -> dict[str, object]:\n    return {'type': 'object', 'required': ['status']}\n",
}

FORBIDDEN_SNIPPETS = ["os.system", "subprocess.Popen", "eval(", "exec("]


def _signature(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value.lower()).strip("_")


def _kind_for_tool_type(tool_type: str) -> str:
    if tool_type == "validator":
        return "validator"
    if tool_type == "connector":
        return "adapter"
    return "tool"


def _module_template(kind: str, tool_type: str) -> str:
    if kind == "tool" and tool_type in TOOL_TYPE_TEMPLATES:
        return TOOL_TYPE_TEMPLATES[tool_type]
    return CAPABILITY_KIND_TO_TEMPLATE[kind]


def generate_capability_candidate(
    *,
    sandbox_root: str | Path,
    capability_name: str,
    capability_kind: str,
    purpose: str,
    lane_id: str,
    family: str,
    compatibility: dict[str, object] | None = None,
    generated_by: str = "self_extension",
) -> dict[str, object]:
    if capability_kind not in CAPABILITY_KIND_TO_TEMPLATE:
        raise ValueError(f"Unsupported capability_kind '{capability_kind}'")

    safe_name = _safe_name(capability_name)
    if not safe_name:
        raise ValueError("capability_name must contain letters or numbers")

    root = Path(sandbox_root).resolve()
    capability_root = root / "generated_capabilities" / capability_kind / safe_name
    module_root = capability_root / "src"
    test_root = capability_root / "tests"
    docs_root = capability_root / "docs"
    proof_root = capability_root / "proof"
    module_root.mkdir(parents=True, exist_ok=True)
    test_root.mkdir(parents=True, exist_ok=True)
    docs_root.mkdir(parents=True, exist_ok=True)
    proof_root.mkdir(parents=True, exist_ok=True)

    module_path = module_root / f"{safe_name}.py"
    module_content = (
        f'"""Generated capability candidate: {safe_name}"""\n\n'
        f"# purpose: {purpose}\n"
        f"# lane_id: {lane_id}\n"
        f"# capability_kind: {capability_kind}\n"
        + _module_template(capability_kind, "domain_utility")
    )
    module_path.write_text(module_content, encoding="utf-8")

    test_path = test_root / f"test_{safe_name}.py"
    test_path.write_text(
        (
            "from pathlib import Path\n\n\n"
            f"def test_{safe_name}_artifact_presence() -> None:\n"
            f"    root = Path(__file__).resolve().parents[1]\n"
            f"    assert (root / 'src' / '{safe_name}.py').exists()\n"
            f"    assert (root / 'metadata.json').exists()\n"
            f"    assert (root / 'proof' / 'expectations.json').exists()\n"
        ),
        encoding="utf-8",
    )

    proof_path = proof_root / "expectations.json"
    proof_payload = {
        "kind": capability_kind,
        "requires": [
            "machine_readable_validation_pass",
            "compatibility_verification_pass",
            "quarantine_or_promotion_decision_recorded",
        ],
        "deterministic": True,
    }
    proof_path.write_text(json.dumps(proof_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    docs_path = docs_root / "RUNBOOK.md"
    docs_path.write_text(
        (
            f"# Capability Runbook: {safe_name}\n\n"
            f"- Kind: {capability_kind}\n"
            f"- Lane: {lane_id}\n"
            f"- Family: {family}\n"
            "- Activation starts in quarantine unless governance thresholds are met.\n"
            "- Promotion requires explicit evidence and operator-visible trust metadata.\n"
        ),
        encoding="utf-8",
    )

    normalized_compatibility = compatibility or {
        "lanes": [lane_id],
        "runtimes": ["python"],
        "stacks": {"backend": ["fastapi"], "deployment": ["docker_compose"]},
        "composable_with": [],
    }

    candidate = {
        "tool_id": f"{capability_kind}::{lane_id}::{safe_name}",
        "capability_id": f"{capability_kind}::{lane_id}::{safe_name}",
        "tool_name": safe_name,
        "capability_name": safe_name,
        "tool_type": capability_kind,
        "capability_kind": capability_kind,
        "purpose": purpose,
        "lane_id": lane_id,
        "family": family,
        "module_path": str(module_path),
        "candidate_root": str(capability_root),
        "tests_path": str(test_path),
        "proof_expectations_path": str(proof_path),
        "runbook_path": str(docs_path),
        "quality_threshold": 85,
        "safety_tier": "standard",
        "validation_requirements": [
            "file_exists",
            "forbidden_calls_absent",
            "signature_present",
            "metadata_present",
            "tests_present",
            "proof_expectations_present",
            "runbook_present",
            "compatibility_declared",
        ],
        "compatibility": normalized_compatibility,
        "input_contract": {
            "type": "object",
            "required": ["request_id"],
            "additionalProperties": True,
        },
        "output_contract": {
            "type": "object",
            "required": ["status"],
            "additionalProperties": True,
        },
        "trust_notes": [
            "generated_in_sandbox",
            "requires_operator_review_before_core_use",
            "bounded_template_no_shell_exec",
        ],
        "trust": {
            "status": "candidate",
            "quarantine_default": True,
            "promotion_requires_evidence": True,
            "generated_by": generated_by,
        },
        "promotion_criteria": [
            "validation_pass_rate_ge_threshold",
            "compatibility_checks_pass",
            "proof_expectations_satisfied",
            "no_regression_signals",
        ],
        "demotion_criteria": [
            "compatibility_regression_detected",
            "validation_failure_repeat",
            "operator_reported_trust_issue",
        ],
        "rollback_reference": f"rollback::{capability_kind}::{lane_id}::{safe_name}",
        "lineage": {
            "source": "generated",
            "generated_by": generated_by,
            "purpose": purpose,
            "lane_id": lane_id,
        },
    }
    candidate["candidate_signature_sha256"] = _signature(candidate)

    metadata_path = capability_root / "metadata.json"
    metadata_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate["metadata_path"] = str(metadata_path)
    return candidate


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
    kind = _kind_for_tool_type(tool_type)
    candidate = generate_capability_candidate(
        sandbox_root=sandbox_root,
        capability_name=tool_name,
        capability_kind=kind,
        purpose=purpose,
        lane_id=lane_id,
        family="validation" if kind == "validator" else ("adapter" if kind == "adapter" else "domain"),
        generated_by="tool_factory",
    )
    candidate["tool_type"] = tool_type
    candidate["tool_id"] = f"tool::{lane_id}::{candidate['tool_name']}"
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
    checks.append(
        {
            "name": "input_contract_present",
            "passed": isinstance(candidate.get("input_contract"), dict),
        }
    )
    checks.append(
        {
            "name": "output_contract_present",
            "passed": isinstance(candidate.get("output_contract"), dict),
        }
    )
    checks.append(
        {
            "name": "sandbox_path_enforced",
            "passed": "/generated_capabilities/" in str(module_path).replace("\\", "/") or "/generated_tools/" in str(module_path).replace("\\", "/"),
        }
    )
    checks.append(
        {
            "name": "metadata_present",
            "passed": Path(str(candidate.get("metadata_path", ""))).exists(),
        }
    )
    checks.append(
        {
            "name": "tests_present",
            "passed": Path(str(candidate.get("tests_path", ""))).exists(),
        }
    )
    checks.append(
        {
            "name": "proof_expectations_present",
            "passed": Path(str(candidate.get("proof_expectations_path", ""))).exists(),
        }
    )
    checks.append(
        {
            "name": "runbook_present",
            "passed": Path(str(candidate.get("runbook_path", ""))).exists(),
        }
    )
    checks.append(
        {
            "name": "compatibility_declared",
            "passed": isinstance(candidate.get("compatibility"), dict),
        }
    )

    passed_count = sum(1 for item in checks if item["passed"])
    quality_score = int((passed_count / len(checks)) * 100) if checks else 0

    return {
        "tool_id": candidate.get("tool_id", ""),
        "checks": checks,
        "quality_score": quality_score,
        "is_valid": passed_count == len(checks),
        "safety_tier": candidate.get("safety_tier", "standard"),
    }
