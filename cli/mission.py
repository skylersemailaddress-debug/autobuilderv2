import argparse
import io
import json
import sys
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from typing import Dict, Optional

# Ensure top-level package imports work when executing cli/mission.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from cli.resume import resume_saved_run
from cli.run import perform_run
from state.json_store import JsonRunStore


def _mission_result_path(run_id: str) -> Path:
    return ROOT_DIR / "runs" / f"{run_id}.mission.json"


def _build_resume_hint(run_id: str) -> str:
    return (
        f"Approval required. Approve run in runs/{run_id}.json, then run "
        f"python cli/mission.py --resume {run_id} --approve"
    )


def build_mission_result(record: Dict, saved_path: str) -> Dict:
    summary = record.get("summary", {})
    approval_required = summary.get(
        "approval_required",
        record.get("policy", {}).get("approval_required", False),
    )
    awaiting_approval = record.get("awaiting_approval", False)

    result = {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status", summary.get("final_status")),
        "approval_required": approval_required,
        "awaiting_approval": awaiting_approval,
        "confidence": record.get("confidence", summary.get("confidence", 0.0)),
        "repair_count": record.get("repair_count", 0),
        "summary": summary,
        "saved_path": saved_path,
    }
    if awaiting_approval:
        result["resume_hint"] = _build_resume_hint(record["run_id"])
    return result


def _save_mission_result(result: Dict) -> str:
    path = _mission_result_path(result["run_id"])
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    return str(path)


def run_mission(goal: str) -> Dict:
    run_id = f"mission_{uuid.uuid4().hex}"
    with io.StringIO() as capture, redirect_stdout(capture):
        record, saved_path = perform_run(run_id=run_id, goal=goal, nexus_mode_enabled=True)
    result = build_mission_result(record, saved_path)
    result["mission_result_path"] = _save_mission_result(result)
    return result


def resume_mission(run_id: str, approve: bool = False) -> Dict:
    store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    record = store.load(run_id)
    if record is None:
        raise FileNotFoundError(f"Run record {run_id} not found")

    if approve and record.get("awaiting_approval"):
        approval_request = record.get("approval_request")
        if approval_request:
            approval_request["status"] = "approved"
            record["approval_request"] = approval_request
            store.save(run_id, record)

    with io.StringIO() as capture, redirect_stdout(capture):
        resumed_record, saved_path = resume_saved_run(run_id)
    if resumed_record is None:
        raise FileNotFoundError(f"Run record {run_id} not found")

    normalized_saved_path = saved_path or str(ROOT_DIR / "runs" / f"{run_id}.json")
    result = build_mission_result(resumed_record, normalized_saved_path)
    result["mission_result_path"] = _save_mission_result(result)
    return result


def _print_result(result: Dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"run_id={result['run_id']}")
    print(f"goal={result['goal']}")
    print(f"final_status={result['final_status']}")
    print(f"approval_required={result['approval_required']}")
    print(f"awaiting_approval={result['awaiting_approval']}")
    print(f"confidence={result['confidence']}")
    print(f"repair_count={result['repair_count']}")
    print(f"saved_path={result['saved_path']}")
    print(f"mission_result_path={result['mission_result_path']}")
    if result.get("resume_hint"):
        print(f"resume_hint={result['resume_hint']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or resume one-button Nexus missions")
    parser.add_argument("goal", nargs="?", help="Goal to execute as a Nexus mission")
    parser.add_argument("--resume", dest="resume_run_id", help="Run ID of a mission to resume")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Mark pending approval as approved before resume",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full mission result as JSON",
    )
    args = parser.parse_args()

    if args.resume_run_id:
        result = resume_mission(args.resume_run_id, approve=args.approve)
    elif args.goal:
        result = run_mission(args.goal)
    else:
        parser.error("Provide a goal or use --resume <run_id>.")

    _print_result(result, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())