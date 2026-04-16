import argparse
import json
import sys
from pathlib import Path

# Ensure top-level package imports work when executing cli/autobuilder.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from benchmarks.cases import BENCHMARK_CASES
from benchmarks.report import build_benchmark_report
from benchmarks.runner import run_benchmark_cases
from cli.inspect import inspect_run
from cli.mission import resume_mission, run_mission
from readiness.checks import run_readiness_checks
from readiness.report import build_readiness_report


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

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())