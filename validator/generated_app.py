from __future__ import annotations

from pathlib import Path


REPO_STRUCTURE_PATHS = [
    ".autobuilder",
    "frontend",
    "frontend/app",
    "frontend/components",
    "backend",
    "backend/api",
    "backend/tests",
    "db",
    "docs",
    "docker-compose.yml",
    "README.md",
]

FRONTEND_ESSENTIAL_FILES = {
    "frontend/app/page.tsx": [
        'data-testid="workspace-shell"',
        'data-testid="command-surface"',
        'data-testid="response-state-region"',
        "/api/workspace/execute",
    ],
    "frontend/components/enterprise-shell.tsx": [
        'data-testid="shell-navigation"',
        'data-testid="shell-header"',
        'data-testid="status-notification"',
    ],
    "frontend/components/enterprise-states.tsx": [
        'data-testid="loading-state"',
        'data-testid="empty-state"',
        'data-testid="error-state"',
    ],
}

BACKEND_ESSENTIAL_FILES = {
    "backend/api/main.py": [
        '@app.get("/health")',
        '@app.get("/ready")',
        '@app.get("/version")',
        '@app.post("/api/workspace/execute")',
    ],
    "backend/api/admin.py": ['prefix="/api/admin"'],
    "backend/api/operator.py": ['prefix="/api/operator"'],
    "backend/api/audit.py": ['prefix="/api/audit"'],
}

ENV_CONFIG_ESSENTIALS = {
    ".env.example": [
        "APP_ENV=",
        "APP_VERSION=",
        "DATABASE_URL=",
        "CORS_ORIGIN=",
        "NEXT_PUBLIC_API_BASE_URL=",
    ],
    "backend/.env.example": [
        "APP_ENV=",
        "APP_VERSION=",
        "DATABASE_URL=",
        "CORS_ORIGIN=",
    ],
    "backend/api/config.py": [
        "class Settings",
        "app_env",
        "app_version",
        "database_url",
        "cors_origin",
    ],
}

DEPLOYMENT_ESSENTIALS = {
    "docker-compose.yml": ["services:", "frontend:", "backend:", "db:", "postgres:16"],
}

PROOF_READINESS_FILES = [
    "docs/ENTERPRISE_POLISH.md",
    "docs/READINESS.md",
    "docs/PROOF_OF_RUN.md",
    ".autobuilder/proof_report.json",
    ".autobuilder/readiness_report.json",
    ".autobuilder/validation_summary.json",
    ".autobuilder/determinism_signature.json",
    ".autobuilder/generation_summary.json",
]

ENTERPRISE_POLISH_SURFACE_FILES = {
    "frontend/app/settings/page.tsx": ['data-testid="settings-surface"'],
    "frontend/app/admin/page.tsx": ['data-testid="admin-surface"'],
    "frontend/app/activity/page.tsx": ['data-testid="activity-surface"'],
    "docs/OPERATOR.md": [],
}


def _file_exists(target: Path, relative_path: str) -> dict[str, object]:
    exists = (target / relative_path).exists()
    return {
        "name": relative_path,
        "passed": exists,
        "details": "present" if exists else "missing",
    }


def _file_contains(target: Path, relative_path: str, markers: list[str]) -> dict[str, object]:
    path = target / relative_path
    if not path.exists():
        return {
            "name": relative_path,
            "passed": False,
            "details": "missing",
        }

    content = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in content]
    return {
        "name": relative_path,
        "passed": not missing,
        "details": "markers_present" if not missing else f"missing markers: {', '.join(missing)}",
    }


def _check(name: str, items: list[dict[str, object]]) -> dict[str, object]:
    passed = all(bool(item["passed"]) for item in items)
    return {
        "name": name,
        "passed": passed,
        "items": items,
    }


def _contains_checks(target: Path, markers_by_path: dict[str, list[str]]) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for relative_path, markers in markers_by_path.items():
        if markers:
            checks.append(_file_contains(target, relative_path, markers))
        else:
            checks.append(_file_exists(target, relative_path))
    return checks


def _exists_checks(target: Path, paths: list[str]) -> list[dict[str, object]]:
    return [_file_exists(target, relative_path) for relative_path in paths]


def validate_generated_app(target_repo: str | Path) -> dict[str, object]:
    target = Path(target_repo).resolve()
    checks = [
        _check(
            "required_repo_structure_present",
            _exists_checks(target, REPO_STRUCTURE_PATHS),
        ),
        _check(
            "frontend_shell_essentials_present",
            _contains_checks(target, FRONTEND_ESSENTIAL_FILES),
        ),
        _check(
            "backend_endpoint_essentials_present",
            _contains_checks(target, BACKEND_ESSENTIAL_FILES)
            + _exists_checks(
                target,
                [
                    "backend/api/responses.py",
                    "backend/api/logging.py",
                    "backend/tests/test_endpoints.py",
                ],
            ),
        ),
        _check(
            "env_config_essentials_present",
            _contains_checks(target, ENV_CONFIG_ESSENTIALS),
        ),
        _check(
            "docker_deployment_essentials_present",
            _contains_checks(target, DEPLOYMENT_ESSENTIALS),
        ),
        _check(
            "proof_readiness_artifacts_present",
            _exists_checks(target, PROOF_READINESS_FILES),
        ),
        _check(
            "enterprise_polish_surface_presence",
            _contains_checks(target, ENTERPRISE_POLISH_SURFACE_FILES),
        ),
    ]
    passed_count = sum(1 for check in checks if check["passed"])
    failed_checks = [check["name"] for check in checks if check["passed"] is not True]
    failed_items = [
        {
            "check": check["name"],
            "item": item["name"],
            "details": item["details"],
        }
        for check in checks
        for item in check["items"]
        if item["passed"] is not True
    ]
    return {
        "checks": checks,
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "total_checks": len(checks),
        "failed_checks": failed_checks,
        "failed_items": failed_items,
        "validation_status": "passed" if passed_count == len(checks) else "failed",
        "all_passed": passed_count == len(checks),
    }