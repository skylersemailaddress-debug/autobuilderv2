import json
from control_plane.control import derive_control_state


def inspect_run(record_path: str):
    with open(record_path, "r") as f:
        record = json.load(f)

    control = derive_control_state(record)

    print("=== RUN INSPECTION ===")
    print(f"Run ID: {record.get('id')}")
    print(f"Status: {record.get('status')}")
    print(f"Control State: {control.state}")
    print(f"Awaiting Approval: {control.awaiting_approval}")
    print(f"Resume Ready: {control.resume_ready}")


if __name__ == "__main__":
    import sys
    inspect_run(sys.argv[1])
