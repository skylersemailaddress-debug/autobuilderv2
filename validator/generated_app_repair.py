from __future__ import annotations

import json
from pathlib import Path

from generator.template_packs import GeneratedTemplate


def _fallback_file_content(path: str) -> str | None:
    fallback = {
        "docs/ENTERPRISE_POLISH.md": "# Enterprise Polish Coverage\n\nPending regeneration of enterprise polish details.\n",
        "docs/READINESS.md": "# Readiness\n\nPending readiness verification.\n",
        "docs/PROOF_OF_RUN.md": "# Proof of Run\n\nPending proof execution.\n",
        ".autobuilder/proof_report.json": json.dumps({"proof_status": "pending"}, indent=2, sort_keys=True) + "\n",
        ".autobuilder/readiness_report.json": (
            json.dumps(
                {
                    "readiness_status": "pending",
                    "readiness_reasons": ["run generated app validation"],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ),
        ".autobuilder/validation_summary.json": (
            json.dumps({"validation_status": "pending"}, indent=2, sort_keys=True) + "\n"
        ),
        ".autobuilder/determinism_signature.json": (
            json.dumps({"build_signature_sha256": "pending"}, indent=2, sort_keys=True) + "\n"
        ),
    }
    return fallback.get(path)


def _templates_by_path(templates: list[GeneratedTemplate] | None) -> dict[str, str]:
    if not templates:
        return {}
    return {template.path: template.content for template in templates}


def repair_generated_app(
    target_repo: str | Path,
    validation_report: dict[str, object],
    expected_templates: list[GeneratedTemplate] | None = None,
    max_repairs: int = 24,
) -> dict[str, object]:
    target = Path(target_repo).resolve()
    template_map = _templates_by_path(expected_templates)

    repaired_issues: list[dict[str, str]] = []
    unrepaired_blockers: list[dict[str, str]] = []
    repairs_applied = 0

    failed_items = validation_report.get("failed_items", [])
    if not isinstance(failed_items, list):
        failed_items = []

    for entry in failed_items:
        if repairs_applied >= max_repairs:
            unrepaired_blockers.append(
                {
                    "check": "repair_limit",
                    "item": "repair_limit",
                    "reason": f"repair limit reached ({max_repairs})",
                }
            )
            break

        if not isinstance(entry, dict):
            continue

        check_name = str(entry.get("check", "unknown_check"))
        item_path = str(entry.get("item", ""))
        if not item_path:
            continue

        destination = target / item_path
        details = str(entry.get("details", ""))

        replacement = template_map.get(item_path)
        if replacement is None:
            replacement = _fallback_file_content(item_path)

        if replacement is None:
            unrepaired_blockers.append(
                {
                    "check": check_name,
                    "item": item_path,
                    "reason": "no repair template available",
                }
            )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(replacement, encoding="utf-8")

        repaired_issues.append(
            {
                "check": check_name,
                "item": item_path,
                "repair": "restored_expected_content",
                "prior_details": details,
            }
        )
        repairs_applied += 1

    return {
        "repair_status": "repaired" if repaired_issues and not unrepaired_blockers else (
            "partial" if repaired_issues else "none"
        ),
        "repairs_applied": repairs_applied,
        "max_repairs": max_repairs,
        "repaired_issues": repaired_issues,
        "unrepaired_blockers": unrepaired_blockers,
    }
