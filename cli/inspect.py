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

    from execution.lineage import summarize_artifact_lineage
    from state.json_store import JsonRunStore
    from state.restore import latest_restore_payload


    def build_inspection_payload(record: Dict) -> Dict:
        summary = record.get("summary", {})
        failures = record.get("failures", [])
        change_sets = record.get("change_sets", [])
        mutation_risk = record.get("mutation_risk", "safe")
        checkpoint_required = any(item.get("requires_checkpoint", False) for item in change_sets)
        restore_payload = record.get("restore_payload") or latest_restore_payload(record)
        artifact_lineage_summary = summarize_artifact_lineage(
            record.get("run_id"),
            record.get("artifacts", []),
            record.get("checkpoints", []),
        )

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
            "change_sets": change_sets,
            "mutation_risk_summary": {
                "risk_level": mutation_risk,
                "checkpoint_required": checkpoint_required,
                "change_set_count": len(change_sets),
            },
            "checkpoint_restore": restore_payload,
            "audit_record": record.get("audit_record"),
            "audit_event_count": len(record.get("audit_trail", [])),
            "artifact_lineage_summary": artifact_lineage_summary,
            "benchmark_summary": record.get("benchmark_summary"),
            "quality_report": record.get("quality_report"),
            "memory_policy_summary": record.get("memory_policy_summary", {}),
            "selected_memory_usage": {
                "keys": record.get("selected_memory_keys", []),
                "count": len(record.get("selected_memory_keys", [])),
                "memory_context_keys": list(record.get("memory_context", {}).keys()),
            },
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
            print(f"change_sets={json.dumps(payload['change_sets'])}")
            print(f"mutation_risk_summary={json.dumps(payload['mutation_risk_summary'])}")
            print(f"checkpoint_restore={json.dumps(payload['checkpoint_restore'])}")
            print(f"audit_record={json.dumps(payload['audit_record'])}")
            print(f"audit_event_count={payload['audit_event_count']}")
            print(f"artifact_lineage_summary={json.dumps(payload['artifact_lineage_summary'])}")
            print(f"benchmark_summary={json.dumps(payload['benchmark_summary'])}")
            print(f"quality_report={json.dumps(payload['quality_report'])}")
            print(f"memory_policy_summary={json.dumps(payload['memory_policy_summary'])}")
            print(f"selected_memory_usage={json.dumps(payload['selected_memory_usage'])}")
            if "failure_info" in payload:
                print(f"failure_info={json.dumps(payload['failure_info'])}")

        return 0


    if __name__ == "__main__":
        raise SystemExit(main())
