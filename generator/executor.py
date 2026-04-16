from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from generator.plan import BuildOperation, BuildPlan


@dataclass(frozen=True)
class BuildExecutionResult:
    target_repo: str
    operations_applied: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_repo": self.target_repo,
            "operations_applied": self.operations_applied,
        }


def _resolve_scoped_path(target: Path, relative_path: str) -> Path:
    candidate = (target / relative_path).resolve()
    if not str(candidate).startswith(str(target)):
        raise ValueError(f"Operation path escapes target repo: {relative_path}")
    return candidate


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _apply_operation(target: Path, op: BuildOperation) -> dict[str, str]:
    resolved = _resolve_scoped_path(target, op.path)

    if op.op == "create_dir":
        resolved.mkdir(parents=True, exist_ok=True)
        return {"op": op.op, "path": op.path, "status": "ok", "sha256": ""}

    if op.op == "write_file":
        if op.content is None:
            raise ValueError(f"write_file operation requires content: {op.path}")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(op.content, encoding="utf-8")
        return {"op": op.op, "path": op.path, "status": "ok", "sha256": _sha256(op.content)}

    if op.op == "update_file":
        if op.content is None:
            raise ValueError(f"update_file operation requires content: {op.path}")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        prior = resolved.read_text(encoding="utf-8") if resolved.exists() else ""
        next_content = f"{prior}{op.content}"
        resolved.write_text(next_content, encoding="utf-8")
        return {"op": op.op, "path": op.path, "status": "ok", "sha256": _sha256(next_content)}

    raise ValueError(f"Unsupported operation: {op.op}")


def apply_build_plan(plan: BuildPlan) -> BuildExecutionResult:
    target = Path(plan.target_repo).resolve()
    target.mkdir(parents=True, exist_ok=True)

    applied = [_apply_operation(target, operation) for operation in plan.operations]
    return BuildExecutionResult(target_repo=str(target), operations_applied=applied)
