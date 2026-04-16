from enum import Enum


class RunState(Enum):
    INTAKE = "intake"
    PLAN = "plan"
    EXECUTE = "execute"
    VALIDATE = "validate"
    REPAIR = "repair"
    COMPLETE = "complete"
    FAILED = "failed"


class RunStateMachine:
    def __init__(self):
        self.state = RunState.INTAKE

    def transition(self, success=True):
        if self.state == RunState.INTAKE:
            self.state = RunState.PLAN
        elif self.state == RunState.PLAN:
            self.state = RunState.EXECUTE
        elif self.state == RunState.EXECUTE:
            self.state = RunState.VALIDATE
        elif self.state == RunState.VALIDATE:
            self.state = RunState.COMPLETE if success else RunState.REPAIR
        elif self.state == RunState.REPAIR:
            self.state = RunState.EXECUTE
        return self.state
