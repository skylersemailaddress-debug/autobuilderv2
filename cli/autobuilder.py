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
from ir.compiler import compile_specs_to_ir
from readiness.checks import run_readiness_checks
from readiness.report import build_readiness_report
from stack_registry.registry import StackRegistryResolutionError
from specs.loader import SpecValidationError, load_spec_bundle
from validator.generated_app import validate_generated_app


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
    ) -> tuple[object, object, object, list[str], list[str], dict[str, object]]:
        plan = prepare_build_plan(ir, target_repo)
        execution = apply_build_plan(plan)
        generated_app_validation = validate_generated_app(target_repo)
        if generated_app_validation["all_passed"] is not True:
            failed_checks = [
                check["name"]
                for check in generated_app_validation["checks"]
                if check["passed"] is not True
            ]
            raise RuntimeError(
                "Generated app enterprise validation failed: " + ", ".join(failed_checks)
            )

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

    return {
        "status": "ok",
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
        "determinism": {
            "verified": True,
            "build_signature_sha256": primary_hash,
            "proof_signature_sha256": proof_signature,
            "repeat_build_match_required": True,
        },
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

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())