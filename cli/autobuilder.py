import argparse
import hashlib
import json
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

# Ensure top-level package imports work when executing cli/autobuilder.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from archetypes.catalog import ArchetypeResolutionError
from benchmarks.cases import BENCHMARK_CASES
from benchmarks.report import build_benchmark_report
from benchmarks.runner import run_benchmark_cases
from chat_builder.workflow import run_chat_first_workflow
from cli.inspect import inspect_run
from cli.mission import resume_mission, run_mission
from generator.executor import apply_build_plan
from generator.plan import prepare_build_plan
from ir.compiler import compile_specs_to_ir
from ir.model import AppIR
from platform_plugins.registry import PluginResolutionError, ResolvedPluginSet, get_plugin_registry
from readiness.checks import run_readiness_checks
from readiness.report import build_readiness_report
from stack_registry.registry import StackRegistryResolutionError
from specs.loader import SpecValidationError, load_spec_bundle
from universal_capability.agent_runtime import execute_computer_use_plan, model_computer_use_task
from universal_capability.self_extension import synthesize_missing_capabilities


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_first_class_lane(plugins: ResolvedPluginSet, ir: AppIR) -> None:
    unsupported: list[str] = []
    for category, entry in sorted(ir.stack_entries.items()):
        support_tier = str(entry.get("support_tier", "unknown"))
        if support_tier != "first_class":
            unsupported.append(f"{category}:{entry.get('name', 'unknown')} ({support_tier})")

    supported_lanes = {
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    }
    lane_id = plugins.generation.metadata.lane_id
    if lane_id not in supported_lanes:
        unsupported.append(f"lane:{lane_id}")

    if unsupported:
        raise RuntimeError(
            "Unsupported commercial lane stack selection. "
            "Only first_class stack entries and approved lanes are allowed in this tranche: "
            + ", ".join(unsupported)
        )


def _write_json(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _emit_packaging_bundle(
    target_repo: str,
    files_created_summary: dict[str, object],
    validation_status: str,
    proof_artifacts: dict[str, object],
    determinism: dict[str, object],
) -> dict[str, object]:
    target = Path(target_repo)

    release_bundle_paths = [
        "release/README.md",
        "release/deploy/DEPLOYMENT_NOTES.md",
        "release/runbook/OPERATOR_RUNBOOK.md",
        "release/proof/PROOF_BUNDLE.md",
    ]
    release_bundle_missing = [rel for rel in release_bundle_paths if not (target / rel).exists()]

    deployment_docs = [
        "README.md",
        "docs/DEPLOYMENT.md",
        "docs/STARTUP_VALIDATION.md",
        "docker-compose.yml",
    ]
    deployment_docs_missing = [rel for rel in deployment_docs if not (target / rel).exists()]

    env_files = [".env.example", "backend/.env.example"]
    env_files_missing = [rel for rel in env_files if not (target / rel).exists()]

    proof_bundle_paths = [
        ".autobuilder/proof_report.json",
        ".autobuilder/readiness_report.json",
        ".autobuilder/validation_summary.json",
        ".autobuilder/determinism_signature.json",
    ]
    proof_bundle_missing = [rel for rel in proof_bundle_paths if not (target / rel).exists()]

    packaging_status = (
        "ready"
        if not release_bundle_missing and not deployment_docs_missing and not env_files_missing and not proof_bundle_missing
        else "incomplete"
    )

    package_summary = {
        "packaging_status": packaging_status,
        "files_generated_count": files_created_summary.get("count", 0),
        "release_bundle_paths": release_bundle_paths,
        "release_bundle_missing": release_bundle_missing,
        "deployment_docs": deployment_docs,
        "deployment_docs_missing": deployment_docs_missing,
        "env_files": env_files,
        "env_files_missing": env_files_missing,
    }

    proof_bundle = {
        "bundle_status": "complete" if not proof_bundle_missing else "incomplete",
        "proof_bundle_paths": proof_bundle_paths,
        "proof_bundle_missing": proof_bundle_missing,
        "proof_status": proof_artifacts.get("proof_status", "not_certified"),
        "readiness_status": proof_artifacts.get("readiness_status", "not_ready"),
        "validation_status": validation_status,
        "determinism_verified": determinism.get("verified", False),
    }

    _write_json(target / ".autobuilder" / "package_artifact_summary.json", package_summary)
    _write_json(target / ".autobuilder" / "proof_readiness_bundle.json", proof_bundle)

    return {
        "packaging_summary": package_summary,
        "deployment_readiness_summary": {
            "status": "ready" if not deployment_docs_missing and not env_files_missing else "not_ready",
            "deployment_docs_missing": deployment_docs_missing,
            "env_files_missing": env_files_missing,
            "docker_compose_present": (target / "docker-compose.yml").exists(),
        },
        "proof_summary": {
            "status": proof_artifacts.get("proof_status", "not_certified"),
            "readiness_status": proof_artifacts.get("readiness_status", "not_ready"),
            "bundle_status": proof_bundle["bundle_status"],
            "proof_bundle_missing": proof_bundle_missing,
        },
    }


def _assert_ship_artifacts(target_repo: str, proof_artifacts: dict[str, object]) -> dict[str, object]:
    paths = proof_artifacts.get("artifact_paths", {})
    required = {
        "proof_report": ".autobuilder/proof_report.json",
        "readiness_report": ".autobuilder/readiness_report.json",
        "validation_summary": ".autobuilder/validation_summary.json",
        "determinism_signature": ".autobuilder/determinism_signature.json",
        "package_summary": ".autobuilder/package_artifact_summary.json",
        "proof_bundle": ".autobuilder/proof_readiness_bundle.json",
    }

    missing: list[str] = []
    for key in required:
        candidate = str(paths.get(key, ""))
        if not candidate or not Path(candidate).exists():
            missing.append(required[key])
    if missing:
        raise RuntimeError("Missing proof artifacts: " + ", ".join(missing))

    readiness_payload = _read_json(Path(str(paths["readiness_report"])))
    proof_payload = _read_json(Path(str(paths["proof_report"])))
    validation_payload = _read_json(Path(str(paths["validation_summary"])))
    determinism_payload = _read_json(Path(str(paths["determinism_signature"])))
    package_payload = _read_json(Path(str(paths["package_summary"])))
    bundle_payload = _read_json(Path(str(paths["proof_bundle"])))

    if str(proof_payload.get("proof_status", "")) not in {"certified", "certified_with_repairs"}:
        raise RuntimeError("Proof certification failed")
    if str(readiness_payload.get("readiness_status", "")) != "ready":
        raise RuntimeError("Readiness result is not ready")
    if str(validation_payload.get("validation_status", "")) != "passed":
        raise RuntimeError("Validation summary is not passed")
    if bool(determinism_payload.get("verified", False)) is not True:
        raise RuntimeError("Determinism signature is not verified")
    if str(package_payload.get("packaging_status", "incomplete")) != "ready":
        raise RuntimeError("Packaging summary is not ready")
    if str(bundle_payload.get("bundle_status", "incomplete")) != "complete":
        raise RuntimeError("Proof/readiness bundle is incomplete")

    return {
        "target_repo": target_repo,
        "readiness_status": readiness_payload.get("readiness_status", "not_ready"),
        "proof_status": proof_payload.get("proof_status", "not_certified"),
        "packaging_status": package_payload.get("packaging_status", "incomplete"),
        "proof_bundle_status": bundle_payload.get("bundle_status", "incomplete"),
    }


def _print(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data, indent=2))


def _run_benchmarks(case_names: str | None = None) -> dict:
    selected = BENCHMARK_CASES
    if case_names:
        wanted = {name.strip() for name in case_names.split(",") if name.strip()}
        selected = [case for case in BENCHMARK_CASES if case.name in wanted]
    results = run_benchmark_cases(selected)
    return build_benchmark_report(results)


def run_proof_workflow() -> dict:
    low_risk = run_mission("Build an autonomous execution plan")
    approval_sensitive = run_mission("Delete production resources safely")
    inspected = inspect_run(approval_sensitive["run_id"])
    resumed = resume_mission(approval_sensitive["run_id"], approve=True)
    benchmark_summary = _run_benchmarks("simple_low_risk_mission")
    readiness_checks = run_readiness_checks()
    readiness_report = build_readiness_report(readiness_checks, benchmark_summary=benchmark_summary)

    return {
        "proof_status": "ok",
        "mission_started": bool(low_risk.get("run_id")),
        "approval_pause_detected": approval_sensitive.get("awaiting_approval", False),
        "inspect_reachable": bool(inspected.get("run_id")),
        "resume_path_exists": "resume_hint" in approval_sensitive,
        "resume_completed": resumed.get("final_status") == "complete",
        "benchmark_executed": benchmark_summary.get("total_cases", 0) > 0,
        "readiness_generated": bool(readiness_report.get("readiness_status")),
        "artifacts": {
            "low_risk_run_id": low_risk.get("run_id"),
            "approval_run_id": approval_sensitive.get("run_id"),
            "resumed_run_id": resumed.get("run_id"),
        },
    }


def run_build_workflow(spec_path: str, target_path: str) -> dict:
    def _hash_json(payload: object) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _build_once(
        plugins: ResolvedPluginSet,
        target_repo: str,
    ) -> tuple[
        object,
        object,
        object,
        list[str],
        list[str],
        dict[str, object],
        dict[str, object],
    ]:
        plugin_templates = plugins.generation.generate_templates(ir)
        plugin_validation_plan = plugins.generation.validation_plan()
        plan = prepare_build_plan(
            ir,
            target_repo,
            templates=plugin_templates,
            plugin_validation_plan=plugin_validation_plan,
        )
        execution = apply_build_plan(plan)

        generated_app_validation = plugins.validation.validate_generated_app(target_repo)
        repair_report: dict[str, object] = {
            "repair_status": "none",
            "repaired_issues": [],
            "unrepaired_blockers": [],
            "repairs_applied": 0,
            "max_repairs": 24,
        }
        if generated_app_validation["all_passed"] is not True:
            repair_report = plugins.repair.repair_generated_app(
                target_repo=target_repo,
                validation_report=generated_app_validation,
                expected_templates=plugin_templates,
                max_repairs=24,
            )
            generated_app_validation = plugins.validation.validate_generated_app(target_repo)

        unrepaired_blockers = list(repair_report.get("unrepaired_blockers", []))
        if generated_app_validation["all_passed"] is not True and not unrepaired_blockers:
            for failed_check in generated_app_validation.get("failed_checks", []):
                unrepaired_blockers.append(
                    {
                        "check": str(failed_check),
                        "item": str(failed_check),
                        "reason": "validation still failing after repair attempt",
                    }
                )
            repair_report["unrepaired_blockers"] = unrepaired_blockers
            repair_report["repair_status"] = "partial"

        files_created = sorted(
            {
                item["path"]
                for item in execution.operations_applied
                if item["op"] in {"write_file", "update_file"}
            }
        )
        validation_plan = sorted(plan.planned_validation_surface)
        return (
            plan,
            execution,
            execution.to_dict(),
            files_created,
            validation_plan,
            generated_app_validation,
            repair_report,
        )

    specs = load_spec_bundle(spec_path)
    plugins = get_plugin_registry().resolve_plugins(specs.app_type, specs.stack_selection)
    ir = compile_specs_to_ir(specs)
    _assert_first_class_lane(plugins, ir)
    (
        plan,
        execution,
        execution_payload,
        files_created,
        validation_plan,
        generated_app_validation,
        repair_report,
    ) = _build_once(plugins, target_path)
    primary_plan_payload = plan.to_dict()
    primary_plan_payload["target_repo"] = "__TARGET_REPO__"

    primary_signature = {
        "plan": primary_plan_payload,
        "files_created_summary": {
            "count": len(files_created),
            "paths": files_created,
        },
        "validation_plan": validation_plan,
        "generated_app_validation": generated_app_validation,
        "repair_report": repair_report,
        "output_hash": execution.output_hash,
        "output_files": execution.output_files,
    }
    primary_hash = _hash_json(primary_signature)

    with TemporaryDirectory(prefix="autobuilder_repeat_build_") as repeat_target:
        (
            repeat_plan,
            repeat_execution,
            _,
            repeat_files,
            repeat_validation,
            repeat_generated_app_validation,
            repeat_repair_report,
        ) = _build_once(plugins, repeat_target)
        repeat_plan_payload = repeat_plan.to_dict()
        repeat_plan_payload["target_repo"] = "__TARGET_REPO__"
        repeat_signature = {
            "plan": repeat_plan_payload,
            "files_created_summary": {
                "count": len(repeat_files),
                "paths": repeat_files,
            },
            "validation_plan": repeat_validation,
            "generated_app_validation": repeat_generated_app_validation,
            "repair_report": repeat_repair_report,
            "output_hash": repeat_execution.output_hash,
            "output_files": repeat_execution.output_files,
        }
        repeat_hash = _hash_json(repeat_signature)

    if primary_hash != repeat_hash:
        raise RuntimeError(
            "Determinism verification failed: repeat build output diverged from primary build"
        )

    proof_signature = _hash_json(
        {
            "validation_plan": validation_plan,
            "output_hash": execution.output_hash,
        }
    )

    determinism = {
        "verified": True,
        "build_signature_sha256": primary_hash,
        "proof_signature_sha256": proof_signature,
        "repeat_build_match_required": True,
    }

    proof_artifacts = plugins.packaging.emit_proof_artifacts(
        target_repo=plan.target_repo,
        build_status="ok",
        validation_report=generated_app_validation,
        determinism=determinism,
        repair_report=repair_report,
    )

    packaging_bundle = _emit_packaging_bundle(
        target_repo=plan.target_repo,
        files_created_summary={"count": len(files_created), "paths": files_created},
        validation_status=str(generated_app_validation.get("validation_status", "failed")),
        proof_artifacts=proof_artifacts,
        determinism=determinism,
    )
    proof_artifacts.setdefault("artifact_paths", {})
    proof_artifacts["artifact_paths"]["package_summary"] = str(
        Path(plan.target_repo) / ".autobuilder" / "package_artifact_summary.json"
    )
    proof_artifacts["artifact_paths"]["proof_bundle"] = str(
        Path(plan.target_repo) / ".autobuilder" / "proof_readiness_bundle.json"
    )

    unrepaired_blockers = list(repair_report.get("unrepaired_blockers", []))
    if unrepaired_blockers:
        raise RuntimeError(
            "Generated app validation failed after repair: "
            + ", ".join(str(item.get("check", "unknown")) for item in unrepaired_blockers)
        )

    validation_status = str(generated_app_validation.get("validation_status", "failed"))
    build_status = "ok" if validation_status == "passed" else "failed"

    return {
        "status": "ok",
        "build_status": build_status,
        "validation_status": validation_status,
        "proof_status": proof_artifacts["proof_status"],
        "spec_root": specs.spec_root,
        "target_repo": plan.target_repo,
        "ir": ir.to_dict(),
        "plan": plan.to_dict(),
        "execution": execution_payload,
        "files_created_summary": {
            "count": len(files_created),
            "paths": files_created,
        },
        "validation_plan": validation_plan,
        "generated_app_validation": generated_app_validation,
        "repair_report": repair_report,
        "repaired_issues": repair_report.get("repaired_issues", []),
        "unrepaired_blockers": repair_report.get("unrepaired_blockers", []),
        "proof_artifacts": proof_artifacts,
        "packaging_summary": packaging_bundle["packaging_summary"],
        "deployment_readiness_summary": packaging_bundle["deployment_readiness_summary"],
        "proof_summary": packaging_bundle["proof_summary"],
        "determinism": determinism,
    }


def run_ship_workflow(spec_path: str, target_path: str) -> dict:
    build_result = run_build_workflow(spec_path=spec_path, target_path=target_path)

    if build_result.get("status") != "ok":
        raise RuntimeError("Build status failed during ship")
    if build_result.get("build_status") != "ok":
        raise RuntimeError("Build status is not ok")
    if build_result.get("validation_status") != "passed":
        raise RuntimeError("Validation status is not passed")
    if str(build_result.get("proof_status", "")).startswith("certified") is not True:
        raise RuntimeError("Proof status is not certified")
    if build_result.get("unrepaired_blockers"):
        raise RuntimeError("Unrepairable validation blockers remain")

    target_repo = str(build_result.get("target_repo", ""))
    if not target_repo:
        raise RuntimeError("Final target path missing")

    proof_artifact_summary = _assert_ship_artifacts(
        target_repo=target_repo,
        proof_artifacts=dict(build_result.get("proof_artifacts", {})),
    )

    plan = dict(build_result.get("plan", {}))
    stack_chosen = dict(plan.get("stack_chosen", {}))
    stack = {
        "frontend": stack_chosen.get("frontend", {}).get("name"),
        "backend": stack_chosen.get("backend", {}).get("name"),
        "database": stack_chosen.get("database", {}).get("name"),
        "deployment": stack_chosen.get("deployment", {}).get("name"),
    }

    return {
        "status": "ok",
        "build_status": build_result.get("build_status", "failed"),
        "archetype": plan.get("archetype_chosen", {}).get("name"),
        "stack": stack,
        "files_generated": build_result.get("files_created_summary", {}),
        "validation_result": {
            "status": build_result.get("validation_status", "failed"),
            "summary": build_result.get("generated_app_validation", {}),
        },
        "repair_actions_taken": build_result.get("repair_report", {}),
        "proof_result": {
            "status": proof_artifact_summary.get("proof_status", "not_certified"),
            "artifacts": build_result.get("proof_artifacts", {}),
        },
        "readiness_result": {
            "status": proof_artifact_summary.get("readiness_status", "not_ready"),
        },
        "packaged_app_artifact_summary": build_result.get("packaging_summary", {}),
        "deployment_readiness_summary": build_result.get("deployment_readiness_summary", {}),
        "proof_summary": build_result.get("proof_summary", {}),
        "final_target_path": target_repo,
        "determinism": build_result.get("determinism", {}),
    }


def run_generated_app_validation_workflow(target_path: str, repair: bool = False) -> dict:
    target = Path(target_path).resolve()
    plugins: ResolvedPluginSet | None = None
    validation: dict[str, object]

    ir_path = target / ".autobuilder" / "ir.json"
    if ir_path.exists():
        ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
        app_type = str(ir_payload.get("app_type", ""))
        stack_selection = dict(ir_payload.get("stack_selection", {}))
        if app_type and stack_selection:
            plugins = get_plugin_registry().resolve_plugins(app_type, stack_selection)

    if plugins is not None:
        validation = plugins.validation.validate_generated_app(str(target))
    else:
        # Defensive fallback when invoked on repositories not generated by current flow.
        validation = get_plugin_registry().resolve_plugins(
            "saas_web_app",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        ).validation.validate_generated_app(str(target))

    repair_report: dict[str, object] = {
        "repair_status": "none",
        "repaired_issues": [],
        "unrepaired_blockers": [],
        "repairs_applied": 0,
        "max_repairs": 24,
    }

    repair_templates = None
    if ir_path.exists():
        ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
        if plugins is None:
            plugins = get_plugin_registry().resolve_plugins(
                str(ir_payload.get("app_type", "")),
                dict(ir_payload.get("stack_selection", {})),
            )
        repair_templates = plugins.generation.generate_templates(AppIR(**ir_payload))

    if repair and validation["all_passed"] is not True:
        plugin_for_repair = plugins or get_plugin_registry().resolve_plugins(
            "saas_web_app",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        )
        repair_report = plugin_for_repair.repair.repair_generated_app(
            target_repo=target,
            validation_report=validation,
            expected_templates=repair_templates,
            max_repairs=24,
        )
        validation = plugin_for_repair.validation.validate_generated_app(str(target))

    validation_status = str(validation.get("validation_status", "failed"))
    return {
        "status": "ok",
        "target_repo": str(target),
        "validation_status": validation_status,
        "build_status": "ok" if validation_status == "passed" else "failed",
        "proof_status": "pending",
        "generated_app_validation": validation,
        "repair_report": repair_report,
        "repaired_issues": repair_report.get("repaired_issues", []),
        "unrepaired_blockers": repair_report.get("unrepaired_blockers", []),
    }


def run_generated_app_proof_workflow(target_path: str, repair: bool = True) -> dict:
    validation_result = run_generated_app_validation_workflow(target_path=target_path, repair=repair)
    target = validation_result["target_repo"]

    ir_path = Path(target) / ".autobuilder" / "ir.json"
    if ir_path.exists():
        ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
        plugins = get_plugin_registry().resolve_plugins(
            str(ir_payload.get("app_type", "")),
            dict(ir_payload.get("stack_selection", {})),
        )
    else:
        plugins = get_plugin_registry().resolve_plugins(
            "saas_web_app",
            {
                "frontend": "react_next",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        )

    determinism_payload = {
        "verified": False,
        "build_signature_sha256": "",
        "proof_signature_sha256": "",
        "repeat_build_match_required": True,
    }
    proof_artifacts = plugins.packaging.emit_proof_artifacts(
        target_repo=target,
        build_status=validation_result["build_status"],
        validation_report=validation_result["generated_app_validation"],
        determinism=determinism_payload,
        repair_report=validation_result["repair_report"],
    )

    return {
        "status": "ok",
        "target_repo": target,
        "build_status": validation_result["build_status"],
        "validation_status": validation_result["validation_status"],
        "proof_status": proof_artifacts["proof_status"],
        "generated_app_validation": validation_result["generated_app_validation"],
        "repair_report": validation_result["repair_report"],
        "repaired_issues": validation_result["repaired_issues"],
        "unrepaired_blockers": validation_result["unrepaired_blockers"],
        "proof_artifacts": proof_artifacts,
        "determinism": determinism_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AutobuilderV2 top-level CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mission_parser = subparsers.add_parser("mission", help="Start a Nexus mission")
    mission_parser.add_argument("goal", help="Mission goal")
    mission_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    resume_parser = subparsers.add_parser("resume", help="Resume a mission")
    resume_parser.add_argument("run_id", help="Run ID")
    resume_parser.add_argument("--approve", action="store_true", help="Approve pending mission before resume")
    resume_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a saved run")
    inspect_parser.add_argument("run_id", help="Run ID")
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark harness")
    benchmark_parser.add_argument(
        "--cases",
        help="Comma-separated benchmark case names to run (default: all)",
    )
    benchmark_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    readiness_parser = subparsers.add_parser("readiness", help="Generate readiness report")
    readiness_parser.add_argument(
        "--with-benchmarks",
        action="store_true",
        help="Run benchmarks before generating readiness report",
    )
    readiness_parser.add_argument(
        "--cases",
        help="Optional comma-separated benchmark case names when using --with-benchmarks",
    )
    readiness_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    proof_parser = subparsers.add_parser("proof", help="Run end-to-end proof workflow")
    proof_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    build_parser = subparsers.add_parser("build", help="Compile canonical specs into target repo scaffold")
    build_parser.add_argument(
        "--spec",
        default="specs",
        help="Path to canonical spec bundle directory (default: specs)",
    )
    build_parser.add_argument(
        "--target",
        required=True,
        help="Target repository path for scaffold output",
    )
    build_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    validate_app_parser = subparsers.add_parser(
        "validate-app", help="Validate generated app essentials and optionally repair defects"
    )
    validate_app_parser.add_argument("--target", required=True, help="Target generated app path")
    validate_app_parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt bounded repairs for missing generated-app essentials",
    )
    validate_app_parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON output"
    )

    proof_app_parser = subparsers.add_parser(
        "proof-app", help="Emit generated-app proof artifacts and certification status"
    )
    proof_app_parser.add_argument("--target", required=True, help="Target generated app path")
    proof_app_parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt bounded repairs before proof certification",
    )
    proof_app_parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON output"
    )

    ship_parser = subparsers.add_parser(
        "ship", help="One-command commercial ship mode: specs in -> app -> validate/repair -> proof"
    )
    ship_parser.add_argument(
        "--spec",
        default="specs",
        help="Path to canonical spec bundle directory (default: specs)",
    )
    ship_parser.add_argument(
        "--target",
        required=True,
        help="Target repository path for shipped app output",
    )
    ship_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    chat_build_parser = subparsers.add_parser(
        "chat-build",
        help="Chat-first preview and build flow: plain language -> guided preview -> approved build/proof",
    )
    chat_build_parser.add_argument(
        "--prompt",
        required=True,
        help="Plain-language app request from user conversation",
    )
    chat_build_parser.add_argument(
        "--target",
        required=True,
        help="Target repository path for generated output",
    )
    chat_build_parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve preview and execute build/proof flow",
    )
    chat_build_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    agent_runtime_parser = subparsers.add_parser(
        "agent-runtime",
        help="Model and execute bounded computer-use workflows with approval gating and replay",
    )
    agent_runtime_parser.add_argument("--task", required=True, help="Plain-language computer-use task")
    agent_runtime_parser.add_argument(
        "--world-state-json",
        default="{}",
        help="Optional JSON world-state payload for task modeling",
    )
    agent_runtime_parser.add_argument(
        "--approvals-json",
        default="{}",
        help="Optional JSON map of approved sensitive actions by step_id/action_type",
    )
    agent_runtime_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    self_extend_parser = subparsers.add_parser(
        "self-extend",
        help="Detect capability gaps and synthesize candidate tools in sandbox with safe registration",
    )
    self_extend_parser.add_argument("--lane", required=True, help="Lane id to extend")
    self_extend_parser.add_argument(
        "--needs",
        required=True,
        help="Comma-separated capability needs",
    )
    self_extend_parser.add_argument(
        "--sandbox",
        required=True,
        help="Sandbox directory for generated candidate tools",
    )
    self_extend_parser.add_argument(
        "--approve-core",
        action="store_true",
        help="Approve core-impact candidates if required",
    )
    self_extend_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    args = parser.parse_args()

    if args.command == "mission":
        result = run_mission(args.goal)
        _print(result, args.json)
        return 0

    if args.command == "resume":
        result = resume_mission(args.run_id, approve=args.approve)
        _print(result, args.json)
        return 0

    if args.command == "inspect":
        result = inspect_run(args.run_id)
        _print(result, args.json)
        return 0

    if args.command == "benchmark":
        report = _run_benchmarks(args.cases)
        _print(report, args.json)
        return 0

    if args.command == "readiness":
        benchmark_summary = _run_benchmarks(args.cases) if args.with_benchmarks else None
        checks = run_readiness_checks()
        report = build_readiness_report(checks, benchmark_summary=benchmark_summary)
        _print(report, args.json)
        return 0

    if args.command == "proof":
        proof = run_proof_workflow()
        _print(proof, args.json)
        return 0

    if args.command == "build":
        try:
            result = run_build_workflow(args.spec, args.target)
        except (
            SpecValidationError,
            ArchetypeResolutionError,
            StackRegistryResolutionError,
            PluginResolutionError,
            RuntimeError,
        ) as exc:
            _print({"status": "error", "error": str(exc)}, args.json)
            return 2
        _print(result, args.json)
        return 0

    if args.command == "validate-app":
        result = run_generated_app_validation_workflow(target_path=args.target, repair=args.repair)
        _print(result, args.json)
        return 0 if result["validation_status"] == "passed" else 2

    if args.command == "proof-app":
        result = run_generated_app_proof_workflow(target_path=args.target, repair=args.repair)
        _print(result, args.json)
        return 0 if str(result["proof_status"]).startswith("certified") else 2

    if args.command == "ship":
        try:
            result = run_ship_workflow(spec_path=args.spec, target_path=args.target)
        except (
            SpecValidationError,
            ArchetypeResolutionError,
            StackRegistryResolutionError,
            PluginResolutionError,
            RuntimeError,
        ) as exc:
            _print({"status": "error", "error": str(exc)}, args.json)
            return 2
        _print(result, args.json)
        return 0

    if args.command == "chat-build":
        try:
            result = run_chat_first_workflow(
                prompt=args.prompt,
                target_path=args.target,
                approve=args.approve,
                project_memory_root=ROOT_DIR / "state" / "chat_memory",
                ship_runner=run_ship_workflow,
            )
        except (
            SpecValidationError,
            ArchetypeResolutionError,
            StackRegistryResolutionError,
            PluginResolutionError,
            RuntimeError,
        ) as exc:
            _print({"status": "error", "error": str(exc)}, args.json)
            return 2

        _print(result, args.json)
        status = str(result.get("status", ""))
        if status in {"preview_ready", "needs_clarification", "built"}:
            return 0
        if status == "unsupported":
            return 2
        if status == "build_failed":
            return 2
        return 0

    if args.command == "agent-runtime":
        try:
            world_state = json.loads(args.world_state_json)
            approvals = json.loads(args.approvals_json)
            if not isinstance(world_state, dict):
                raise ValueError("world-state-json must decode to an object")
            if not isinstance(approvals, dict):
                raise ValueError("approvals-json must decode to an object")
            plan = model_computer_use_task(args.task, world_state)
            execution = execute_computer_use_plan(plan, approvals=approvals)
            result = {"status": "ok", "plan": plan, "execution": execution}
        except (ValueError, json.JSONDecodeError) as exc:
            _print({"status": "error", "error": str(exc)}, args.json)
            return 2

        _print(result, args.json)
        return 0 if execution.get("overall_status") in {"completed", "blocked"} else 2

    if args.command == "self-extend":
        needs = [item.strip() for item in args.needs.split(",") if item.strip()]
        if not needs:
            _print({"status": "error", "error": "--needs must include at least one capability"}, args.json)
            return 2
        result = synthesize_missing_capabilities(
            lane_id=args.lane,
            requested_capabilities=needs,
            sandbox_root=args.sandbox,
            registry_path=ROOT_DIR / "state" / "generated_capabilities_registry.json",
            quarantine_path=ROOT_DIR / "state" / "generated_capabilities_quarantine.json",
            require_approval_for_core=True,
            approved=args.approve_core,
            failure_intelligence_root=ROOT_DIR / "state" / "capability_failure_intelligence",
        )
        _print(result, args.json)
        return 0 if result.get("status") in {"extended", "no_gap"} else 2

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())