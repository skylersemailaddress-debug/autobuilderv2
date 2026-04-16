if __name__ == "inspect":
    # This file name can shadow stdlib inspect when other CLI scripts are executed
    # from the cli directory. Mirror stdlib inspect in that import context.
    import importlib.util
    import os
    import sysconfig

    _inspect_path = os.path.join(sysconfig.get_paths()["stdlib"], "inspect.py")
    _spec = importlib.util.spec_from_file_location("_stdlib_inspect", _inspect_path)
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    globals().update({name: getattr(_module, name) for name in dir(_module)})
else:
    import argparse
    import json
    import sys
    from pathlib import Path
    from typing import Dict

    # Ensure top-level package imports work when executing cli/inspect.py directly.
    ROOT_DIR = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT_DIR))

    from state.json_store import JsonRunStore


    def build_inspection_payload(record: Dict) -> Dict:
        summary = record.get("summary", {})
        failures = record.get("failures", [])

        payload = {
            "run_id": record.get("run_id"),
            "goal": record.get("goal"),
            "final_status": record.get("status", summary.get("final_status")),
            "confidence": record.get("confidence", summary.get("confidence", 0.0)),
            "repair_count": record.get("repair_count", 0),
            "approval_required": summary.get(
                "approval_required",
                record.get("policy", {}).get("approval_required", False),
            ),
            "event_count": summary.get("event_count", len(record.get("events", []))),
            "summary": summary,
        }

        if failures:
            payload["failure_info"] = {
                "count": len(failures),
                "types": list({failure.get("failure_type", "unknown") for failure in failures}),
                "latest": failures[-1],
            }

        return payload


    def inspect_run(run_id: str) -> Dict:
        store = JsonRunStore(base_dir=ROOT_DIR / "runs")
        record = store.load(run_id)
        if record is None:
            raise FileNotFoundError(f"Run record {run_id} not found")
        return build_inspection_payload(record)


    def main() -> int:
        parser = argparse.ArgumentParser(description="Inspect a saved AutobuilderV2 run")
        parser.add_argument("run_id", help="Run ID of the saved record to inspect")
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print full inspection payload as JSON",
        )
        args = parser.parse_args()

        try:
            payload = inspect_run(args.run_id)
        except FileNotFoundError as exc:
            print(str(exc))
            return 1

        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"run_id={payload['run_id']}")
            print(f"goal={payload['goal']}")
            print(f"final_status={payload['final_status']}")
            print(f"confidence={payload['confidence']}")
            print(f"repair_count={payload['repair_count']}")
            print(f"approval_required={payload['approval_required']}")
            print(f"event_count={payload['event_count']}")
            print(f"summary={json.dumps(payload['summary'])}")
            if "failure_info" in payload:
                print(f"failure_info={json.dumps(payload['failure_info'])}")

        return 0


    if __name__ == "__main__":
        raise SystemExit(main())
