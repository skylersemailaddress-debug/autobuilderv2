from orchestrator.run_state_machine import RunStateMachine, RunState

def test_flow():
    sm = RunStateMachine()
    assert sm.transition().value == "plan"
    assert sm.transition().value == "execute"
    assert sm.transition().value == "validate"
    assert sm.transition(True).value == "complete"
