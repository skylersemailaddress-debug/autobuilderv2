from __future__ import annotations

import json
from pathlib import Path

from archetypes.catalog import resolve_archetype
from generator.template_packs import GeneratedTemplate
from platform_hardening.proof_enrichment import enrich_proof_with_platform_hardening
from platform_hardening.repair_runtime import repair_with_lane_policy
from platform_plugins.contracts import PluginMetadata
from platform_plugins.registry import register_plugin
from stack_registry.registry import resolve_stack_bundle
from validator.generated_app_proof import emit_generated_app_proof_artifacts


def _json_pretty(payload: dict[str, object]) -> str:
    return f"{json.dumps(payload, indent=2, sort_keys=True)}\n"


def _check(name: str, items: list[dict[str, object]]) -> dict[str, object]:
    passed = all(bool(item["passed"]) for item in items)
    return {"name": name, "passed": passed, "items": items}


def _file_exists(target: Path, relative_path: str) -> dict[str, object]:
    exists = (target / relative_path).exists()
    return {"name": relative_path, "passed": exists, "details": "present" if exists else "missing"}


def _file_contains(target: Path, relative_path: str, markers: list[str]) -> dict[str, object]:
    path = target / relative_path
    if not path.exists():
        return {"name": relative_path, "passed": False, "details": "missing"}
    content = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in content]
    return {
        "name": relative_path,
        "passed": not missing,
        "details": "markers_present" if not missing else f"missing markers: {', '.join(missing)}",
    }


def _summarize(checks: list[dict[str, object]]) -> dict[str, object]:
    passed_count = sum(1 for check in checks if check["passed"])
    failed_checks = [check["name"] for check in checks if check["passed"] is not True]
    failed_items = [
        {"check": check["name"], "item": item["name"], "details": item["details"]}
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


def _shared_artifacts() -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_json_pretty({"proof_status": "pending"})),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_json_pretty({"readiness_status": "pending"})),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_json_pretty({"validation_status": "pending"})),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_json_pretty({"verified": False})),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_json_pretty({"packaging_status": "pending"})),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_json_pretty({"bundle_status": "pending"})),
        GeneratedTemplate(path="release/README.md", content="# Release Bundle\n\nLane release artifacts.\n"),
        GeneratedTemplate(path="release/deploy/DEPLOYMENT_NOTES.md", content="# Deployment Notes\n\nDocker Compose local + cloud contract placeholders.\n"),
        GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content="# Operator Runbook\n\nRun build, validate-app, and proof-app before handoff.\n"),
        GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content="# Proof Bundle\n\nProof/readiness and hardening artifacts are collected in .autobuilder.\n"),
        GeneratedTemplate(path="docs/DEPLOYMENT.md", content="# Deployment Notes\n\nLocal Docker and cloud expectation placeholders.\n"),
        GeneratedTemplate(path="docs/STARTUP_VALIDATION.md", content="# Startup and Validation\n\nRun lane startup checks and validation commands.\n"),
        GeneratedTemplate(path="docker-compose.yml", content=(
            "services:\n"
            "  backend:\n"
            "    image: python:3.12-slim\n"
            "    command: sh -c \"echo lane backend placeholder && sleep infinity\"\n"
            "  db:\n"
            "    image: postgres:16\n"
            "    environment:\n"
            "      POSTGRES_PASSWORD: postgres\n"
        )),
        GeneratedTemplate(path="backend/.env.example", content="APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\n"),
    ]


def generate_realtime_templates() -> list[GeneratedTemplate]:
    templates = [
        GeneratedTemplate(
            path="README.md",
            content=(
                "# Realtime / Sensing Lane\n\n"
                "First-class realtime starter with stream ingestion, sensor connectors, alerts, and world-state updates.\n\n"
                "## Run\n\n"
                "1. docker compose up --build\n"
                "2. Start backend stream endpoints\n"
                "3. Open live dashboard\n"
            ),
        ),
        GeneratedTemplate(path="frontend/app/page.tsx", content=(
            "export default function RealtimePage() {\n"
            "  return (\n"
            "    <main data-testid=\"realtime-dashboard\">\n"
            "      <h1>Realtime Dashboard</h1>\n"
            "      <p>event_streams sensor_connectors world_state_updates alert_paths</p>\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )),
        GeneratedTemplate(path="frontend/lib/realtime-client.ts", content=(
            "export function startSubscription(baseUrl: string, onEvent: (payload: unknown) => void): EventSource {\n"
            "  const source = new EventSource(`${baseUrl}/api/realtime/subscribe`);\n"
            "  source.onmessage = (event) => onEvent(JSON.parse(event.data));\n"
            "  return source;\n"
            "}\n"
        )),
        GeneratedTemplate(path="backend/api/main.py", content=(
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/health')\n"
            "def health() -> dict[str, str]:\n"
            "    return {'status': 'ok'}\n\n"
            "@app.get('/api/realtime/poll')\n"
            "def poll() -> dict[str, object]:\n"
            "    return {'polling_inputs': True, 'sensors': ['temperature', 'occupancy']}\n\n"
            "@app.get('/api/realtime/subscribe')\n"
            "def subscribe() -> dict[str, object]:\n"
            "    return {'subscription_inputs': True, 'event_streams': ['ops.events', 'sensor.events']}\n"
        )),
        GeneratedTemplate(path="backend/connectors/sensors.py", content=(
            "def list_sensor_connectors() -> list[str]:\n"
            "    return ['temperature_connector', 'occupancy_connector', 'camera_metadata_connector']\n"
        )),
        GeneratedTemplate(path="backend/realtime/world_state.py", content=(
            "WORLD_STATE: dict[str, object] = {'version': 1, 'alerts': [], 'actions': []}\n\n"
            "def apply_event(event: dict[str, object]) -> dict[str, object]:\n"
            "    WORLD_STATE['last_event'] = event\n"
            "    return WORLD_STATE\n"
        )),
        GeneratedTemplate(path="docs/RUN.md", content="# Run\n\nUse docker compose for backend/db and connect dashboard subscriptions.\n"),
        GeneratedTemplate(path="docs/EXPORT.md", content="# Export Expectations\n\nPackage lane with proof artifacts and deployment notes.\n"),
        GeneratedTemplate(path=".env.example", content="API_BASE_URL=http://localhost:8000\nSTREAM_SOURCE=ops.events\nSENSOR_CONNECTORS=temperature,occupancy\n"),
    ]
    return templates + _shared_artifacts()


def generate_enterprise_agent_templates() -> list[GeneratedTemplate]:
    templates = [
        GeneratedTemplate(
            path="README.md",
            content=(
                "# Enterprise Agent / Workflow Lane\n\n"
                "First-class enterprise workflow starter for multi-role approvals, memory, routing, and operator reporting.\n\n"
                "## Run\n\n"
                "1. docker compose up --build\n"
                "2. Open operator surface\n"
                "3. Execute approval and task routing workflows\n"
            ),
        ),
        GeneratedTemplate(path="frontend/app/page.tsx", content=(
            "export default function EnterpriseAgentPage() {\n"
            "  return (\n"
            "    <main data-testid=\"enterprise-agent-surface\">\n"
            "      <h1>Enterprise Agent Console</h1>\n"
            "      <p>multi_role_workflows approvals task_routing reporting_briefings operator_surfaces</p>\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )),
        GeneratedTemplate(path="frontend/components/workflow-board.tsx", content=(
            "export type WorkflowTask = { id: string; role: string; status: string };\n\n"
            "export function WorkflowBoard({ tasks }: { tasks: WorkflowTask[] }) {\n"
            "  return <section data-testid=\"workflow-board\">{tasks.length} tasks</section>;\n"
            "}\n"
        )),
        GeneratedTemplate(path="backend/api/main.py", content=(
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/health')\n"
            "def health() -> dict[str, str]:\n"
            "    return {'status': 'ok'}\n\n"
            "@app.post('/api/workflows/route')\n"
            "def route_task() -> dict[str, object]:\n"
            "    return {'task_routing': 'queued', 'role': 'operator'}\n\n"
            "@app.post('/api/workflows/approve')\n"
            "def approve_task() -> dict[str, object]:\n"
            "    return {'approvals': 'recorded'}\n\n"
            "@app.get('/api/reports/briefing')\n"
            "def briefing() -> dict[str, object]:\n"
            "    return {'briefing_outputs': ['daily_summary', 'risk_items']}\n"
        )),
        GeneratedTemplate(path="backend/workflows/router.py", content=(
            "def route_by_role(task: dict[str, str]) -> str:\n"
            "    role = task.get('role', 'operator')\n"
            "    return f'routed:{role}'\n"
        )),
        GeneratedTemplate(path="backend/memory/state_store.py", content=(
            "WORKFLOW_MEMORY: dict[str, object] = {'tasks': [], 'approvals': []}\n\n"
            "def append_task(task: dict[str, object]) -> None:\n"
            "    WORKFLOW_MEMORY['tasks'].append(task)\n"
        )),
        GeneratedTemplate(path="docs/RUN.md", content="# Run\n\nStart operator workflow surfaces and backend routing APIs.\n"),
        GeneratedTemplate(path="docs/BRIEFING.md", content="# Briefing Outputs\n\nDaily/weekly reporting placeholders for operators and leadership.\n"),
        GeneratedTemplate(path=".env.example", content="APP_ENV=local\nROUTING_MODE=role_based\nAPPROVAL_POLICY=required\n"),
    ]
    return templates + _shared_artifacts()


def validate_realtime_generated_app(target_repo: str) -> dict[str, object]:
    target = Path(target_repo).resolve()
    checks = [
        _check(
            "realtime_structure",
            [
                _file_exists(target, "frontend/app/page.tsx"),
                _file_exists(target, "frontend/lib/realtime-client.ts"),
                _file_exists(target, "backend/api/main.py"),
                _file_exists(target, "backend/connectors/sensors.py"),
                _file_exists(target, "backend/realtime/world_state.py"),
            ],
        ),
        _check(
            "realtime_markers",
            [
                _file_contains(target, "frontend/app/page.tsx", ["event_streams", "sensor_connectors", "alert_paths"]),
                _file_contains(target, "backend/api/main.py", ["/api/realtime/poll", "/api/realtime/subscribe"]),
                _file_contains(target, "backend/realtime/world_state.py", ["WORLD_STATE", "apply_event"]),
            ],
        ),
        _check(
            "realtime_packaging",
            [
                _file_exists(target, "docs/RUN.md"),
                _file_exists(target, "docs/EXPORT.md"),
                _file_exists(target, "release/README.md"),
                _file_exists(target, ".autobuilder/proof_report.json"),
                _file_exists(target, ".autobuilder/readiness_report.json"),
                _file_exists(target, ".autobuilder/validation_summary.json"),
            ],
        ),
    ]
    return _summarize(checks)


def validate_enterprise_generated_app(target_repo: str) -> dict[str, object]:
    target = Path(target_repo).resolve()
    checks = [
        _check(
            "enterprise_structure",
            [
                _file_exists(target, "frontend/app/page.tsx"),
                _file_exists(target, "frontend/components/workflow-board.tsx"),
                _file_exists(target, "backend/api/main.py"),
                _file_exists(target, "backend/workflows/router.py"),
                _file_exists(target, "backend/memory/state_store.py"),
            ],
        ),
        _check(
            "enterprise_markers",
            [
                _file_contains(target, "frontend/app/page.tsx", ["multi_role_workflows", "approvals", "task_routing"]),
                _file_contains(target, "backend/api/main.py", ["/api/workflows/route", "/api/workflows/approve", "/api/reports/briefing"]),
                _file_contains(target, "backend/memory/state_store.py", ["WORKFLOW_MEMORY", "append_task"]),
            ],
        ),
        _check(
            "enterprise_packaging",
            [
                _file_exists(target, "docs/RUN.md"),
                _file_exists(target, "docs/BRIEFING.md"),
                _file_exists(target, "release/README.md"),
                _file_exists(target, ".autobuilder/proof_report.json"),
                _file_exists(target, ".autobuilder/readiness_report.json"),
                _file_exists(target, ".autobuilder/validation_summary.json"),
            ],
        ),
    ]
    return _summarize(checks)


class RealtimeArchetypePlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.archetype",
        plugin_type="archetype",
        lane_id="first_class_realtime",
        capabilities=["archetype_resolution"],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def resolve_archetype(self, app_type: str) -> object:
        return resolve_archetype(app_type)


class RealtimeStackPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.stack",
        plugin_type="stack",
        lane_id="first_class_realtime",
        capabilities=["stack_resolution"],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def resolve_stack_bundle(self, selection: dict[str, str]) -> dict[str, object]:
        return resolve_stack_bundle(selection)


class RealtimeGenerationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.generation",
        plugin_type="generation",
        lane_id="first_class_realtime",
        capabilities=["event_streams", "sensor_connectors", "world_state_updates"],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def generate_templates(self, ir) -> list[GeneratedTemplate]:
        return generate_realtime_templates()

    def validation_plan(self) -> list[str]:
        return ["realtime_structure", "realtime_markers", "realtime_packaging"]


class RealtimeValidationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.validation",
        plugin_type="validation",
        lane_id="first_class_realtime",
        capabilities=["realtime_validation"],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def validate_generated_app(self, target_repo: str) -> dict[str, object]:
        return validate_realtime_generated_app(target_repo)


class RealtimeRepairPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.repair",
        plugin_type="repair",
        lane_id="first_class_realtime",
        capabilities=["bounded_repair_policy", "failure_classification"],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def repair_generated_app(self, target_repo, validation_report, expected_templates, max_repairs):
        return repair_with_lane_policy(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            validation_report=validation_report,
            expected_templates=expected_templates,
            max_repairs=max_repairs,
        )


class RealtimePackagingPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_realtime.packaging",
        plugin_type="packaging",
        lane_id="first_class_realtime",
        capabilities=[
            "proof_artifacts",
            "packaging_targets",
            "runtime_verification",
            "pack_composition",
            "security_governance_contracts",
            "commerce_pack_contracts",
            "failure_corpus_logging",
            "deterministic_replay_harness",
        ],
        supported_archetypes=["realtime_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=40,
    )

    def emit_proof_artifacts(self, target_repo, build_status, validation_report, determinism, repair_report):
        base = emit_generated_app_proof_artifacts(
            target_repo,
            build_status,
            validation_report,
            determinism,
            repair_report,
        )
        return enrich_proof_with_platform_hardening(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            determinism=determinism,
            validation_report=validation_report,
            repair_report=repair_report,
            proof_artifacts=base,
        )


class EnterpriseArchetypePlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.archetype",
        plugin_type="archetype",
        lane_id="first_class_enterprise_agent",
        capabilities=["archetype_resolution"],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def resolve_archetype(self, app_type: str) -> object:
        return resolve_archetype(app_type)


class EnterpriseStackPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.stack",
        plugin_type="stack",
        lane_id="first_class_enterprise_agent",
        capabilities=["stack_resolution"],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def resolve_stack_bundle(self, selection: dict[str, str]) -> dict[str, object]:
        return resolve_stack_bundle(selection)


class EnterpriseGenerationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.generation",
        plugin_type="generation",
        lane_id="first_class_enterprise_agent",
        capabilities=["multi_role_workflows", "approvals", "memory_state", "task_routing", "briefings"],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def generate_templates(self, ir) -> list[GeneratedTemplate]:
        return generate_enterprise_agent_templates()

    def validation_plan(self) -> list[str]:
        return ["enterprise_structure", "enterprise_markers", "enterprise_packaging"]


class EnterpriseValidationPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.validation",
        plugin_type="validation",
        lane_id="first_class_enterprise_agent",
        capabilities=["enterprise_agent_validation"],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def validate_generated_app(self, target_repo: str) -> dict[str, object]:
        return validate_enterprise_generated_app(target_repo)


class EnterpriseRepairPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.repair",
        plugin_type="repair",
        lane_id="first_class_enterprise_agent",
        capabilities=["bounded_repair_policy", "failure_classification"],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def repair_generated_app(self, target_repo, validation_report, expected_templates, max_repairs):
        return repair_with_lane_policy(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            validation_report=validation_report,
            expected_templates=expected_templates,
            max_repairs=max_repairs,
        )


class EnterprisePackagingPlugin:
    metadata = PluginMetadata(
        plugin_id="first_class_enterprise_agent.packaging",
        plugin_type="packaging",
        lane_id="first_class_enterprise_agent",
        capabilities=[
            "proof_artifacts",
            "packaging_targets",
            "runtime_verification",
            "pack_composition",
            "security_governance_contracts",
            "commerce_pack_contracts",
            "failure_corpus_logging",
            "deterministic_replay_harness",
        ],
        supported_archetypes=["workflow_system", "enterprise_agent_system"],
        supported_stacks={
            "frontend": ["react_next"],
            "backend": ["fastapi"],
            "database": ["postgres"],
            "deployment": ["docker_compose"],
        },
        priority=50,
    )

    def emit_proof_artifacts(self, target_repo, build_status, validation_report, determinism, repair_report):
        base = emit_generated_app_proof_artifacts(
            target_repo,
            build_status,
            validation_report,
            determinism,
            repair_report,
        )
        return enrich_proof_with_platform_hardening(
            lane_id=self.metadata.lane_id,
            target_repo=target_repo,
            determinism=determinism,
            validation_report=validation_report,
            repair_report=repair_report,
            proof_artifacts=base,
        )


register_plugin(RealtimeArchetypePlugin())
register_plugin(RealtimeStackPlugin())
register_plugin(RealtimeGenerationPlugin())
register_plugin(RealtimeValidationPlugin())
register_plugin(RealtimeRepairPlugin())
register_plugin(RealtimePackagingPlugin())

register_plugin(EnterpriseArchetypePlugin())
register_plugin(EnterpriseStackPlugin())
register_plugin(EnterpriseGenerationPlugin())
register_plugin(EnterpriseValidationPlugin())
register_plugin(EnterpriseRepairPlugin())
register_plugin(EnterprisePackagingPlugin())
