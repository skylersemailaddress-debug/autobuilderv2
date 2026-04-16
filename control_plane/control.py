from dataclasses import dataclass


@dataclass
class ControlState:
    state: str
    awaiting_approval: bool = False
    resume_ready: bool = False


def derive_control_state(record: dict) -> ControlState:
    status = record.get("status", "unknown")
    approval = record.get("approval") or {}
    awaiting = approval.get("status") == "pending" or record.get("awaiting_approval", False)

    if awaiting:
        return ControlState(state="awaiting_approval", awaiting_approval=True, resume_ready=True)
    if status == "complete":
        return ControlState(state="complete", awaiting_approval=False, resume_ready=False)
    if status == "failed":
        return ControlState(state="failed", awaiting_approval=False, resume_ready=False)
    if record.get("tasks"):
        return ControlState(state="resumable", awaiting_approval=False, resume_ready=True)
    return ControlState(state="running", awaiting_approval=False, resume_ready=False)
