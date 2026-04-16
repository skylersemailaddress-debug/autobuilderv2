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
from cli.inspect import inspect_run
from cli.mission import resume_mission, run_mission
from generator.executor import apply_build_plan
from generator.plan import prepare_build_plan
from generator.template_packs import generate_first_class_templates
from ir.compiler import compile_specs_to_ir
from ir.model import AppIR
from readiness.checks import run_readiness_checks
from readiness.report import build_readiness_report
from stack_registry.registry import StackRegistryResolutionError
from specs.loader import SpecValidationError, load_spec_bundle
from validator.generated_app import validate_generated_app
from validator.generated_app_proof import emit_generated_app_proof_artifacts
from validator.generated_app_repair import repair_generated_app


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
        plan = prepare_build_plan(ir, target_repo)
        execution = apply_build_plan(plan)

        generated_app_validation = validate_generated_app(target_repo)
        repair_report: dict[str, object] = {
            "repair_status": "none",
            "repaired_issues": [],
            "unrepaired_blockers": [],
            "repairs_applied": 0,
            "max_repairs": 24,
        }
        if generated_app_validation["all_passed"] is not True:
            repair_report = repair_generated_app(
                target_repo=target_repo,
                validation_report=generated_app_validation,
                expected_templates=generate_first_class_templates(ir),
                max_repairs=24,
            )
            generated_app_validation = validate_generated_app(target_repo)

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
    ir = compile_specs_to_ir(specs)
    (
        plan,
        execution,
        execution_payload,
        files_created,
        validation_plan,
        generated_app_validation,
        repair_report,
    ) = _build_once(target_path)
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
        ) = _build_once(repeat_target)
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

    proof_artifacts = emit_generated_app_proof_artifacts(
        target_repo=plan.target_repo,
        build_status="ok",
        validation_report=generated_app_validation,
        determinism=determinism,
        repair_report=repair_report,
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
        "determinism": determinism,
    }


def run_generated_app_validation_workflow(target_path: str, repair: bool = False) -> dict:
    target = Path(target_path).resolve()
    validation = validate_generated_app(target)

    repair_report: dict[str, object] = {
        "repair_status": "none",
        "repaired_issues": [],
        "unrepaired_blockers": [],
        "repairs_applied": 0,
        "max_repairs": 24,
    }

    repair_templates = None
    ir_path = target / ".autobuilder" / "ir.json"
    if ir_path.exists():
        ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
        repair_templates = generate_first_class_templates(AppIR(**ir_payload))

    if repair and validation["all_passed"] is not True:
        repair_report = repair_generated_app(
            target_repo=target,
            validation_report=validation,
            expected_templates=repair_templates,
            max_repairs=24,
        )
        validation = validate_generated_app(target)

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

    determinism_payload = {
        "verified": False,
        "build_signature_sha256": "",
        "proof_signature_sha256": "",
        "repeat_build_match_required": True,
    }
    proof_artifacts = emit_generated_app_proof_artifacts(
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
        except (SpecValidationError, ArchetypeResolutionError, StackRegistryResolutionError, RuntimeError) as exc:
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

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())