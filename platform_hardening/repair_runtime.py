from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from generator.template_packs import GeneratedTemplate
from validator.generated_app_repair import repair_generated_app


LANE_REPAIR_POLICY = {
    "first_class_commercial": 24,
    "first_class_mobile": 20,
    "first_class_game": 20,
    "first_class_realtime": 24,
    "first_class_enterprise_agent": 24,
}


LANE_RUNTIME_CHECKS = {
    "first_class_commercial": [
        "docker-compose.yml",
        "frontend/app/page.tsx",
        "backend/api/main.py",
        ".autobuilder/validation_summary.json",
    ],
    "first_class_mobile": [
        "pubspec.yaml",
        "lib/main.dart",
        "lib/navigation.dart",
        ".autobuilder/validation_summary.json",
    ],
    "first_class_game": [
        "project.godot",
        "scenes/Main.tscn",
        "scripts/main.gd",
        ".autobuilder/validation_summary.json",
    ],
    "first_class_realtime": [
        "frontend/app/page.tsx",
        "backend/api/main.py",
        "backend/realtime/world_state.py",
        ".autobuilder/validation_summary.json",
    ],
    "first_class_enterprise_agent": [
        "frontend/app/page.tsx",
        "backend/api/main.py",
        "backend/workflows/router.py",
        ".autobuilder/validation_summary.json",
    ],
}


@dataclass(frozen=True)
class FailureClassification:
    lane_id: str
    severity: str
    check: str
    item: str
    details: str
    category: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_validation_failures(
    lane_id: str,
    validation_report: dict[str, object],
) -> list[dict[str, object]]:
    failed_items = validation_report.get("failed_items", [])
    if not isinstance(failed_items, list):
        return []

    classifications: list[FailureClassification] = []
    for entry in failed_items:
        if not isinstance(entry, dict):
            continue
        item = str(entry.get("item", ""))
        details = str(entry.get("details", ""))
        check = str(entry.get("check", "unknown"))

        category = "content"
        severity = "high"
        if item.endswith(".json") or item.endswith(".md"):
            category = "artifact"
            severity = "medium"
        if "missing" in details:
            category = "missing_file"
        if "docker" in item or "compose" in item:
            category = "runtime"
            severity = "critical"

        classifications.append(
            FailureClassification(
                lane_id=lane_id,
                severity=severity,
                check=check,
                item=item,
                details=details,
                category=category,
            )
        )

    return [item.to_dict() for item in classifications]


def resolve_repair_policy(lane_id: str, requested_max_repairs: int) -> dict[str, object]:
    lane_cap = LANE_REPAIR_POLICY.get(lane_id, 16)
    effective = min(max(0, requested_max_repairs), lane_cap)
    return {
        "lane_id": lane_id,
        "requested_max_repairs": requested_max_repairs,
        "lane_max_repairs": lane_cap,
        "effective_max_repairs": effective,
    }


def repair_with_lane_policy(
    lane_id: str,
    target_repo: str | Path,
    validation_report: dict[str, object],
    expected_templates: list[GeneratedTemplate] | None,
    max_repairs: int,
) -> dict[str, object]:
    policy = resolve_repair_policy(lane_id, max_repairs)
    report = repair_generated_app(
        target_repo=target_repo,
        validation_report=validation_report,
        expected_templates=expected_templates,
        max_repairs=int(policy["effective_max_repairs"]),
    )
    report["failure_classification"] = classify_validation_failures(lane_id, validation_report)
    report["repair_policy"] = policy
    return report


def verify_runtime_startup(lane_id: str, target_repo: str | Path) -> dict[str, object]:
    target = Path(target_repo).resolve()
    checks = LANE_RUNTIME_CHECKS.get(lane_id, [])

    items: list[dict[str, object]] = []
    for rel in checks:
        exists = (target / rel).exists()
        items.append(
            {
                "name": rel,
                "passed": exists,
                "details": "present" if exists else "missing",
            }
        )

    passed_count = sum(1 for item in items if item["passed"])
    status = "passed" if passed_count == len(items) else "failed"
    return {
        "lane_id": lane_id,
        "runtime_status": status,
        "passed_count": passed_count,
        "total_checks": len(items),
        "failed_count": len(items) - passed_count,
        "checks": items,
    }
