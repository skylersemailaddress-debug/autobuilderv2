from typing import Dict, Optional
from orchestrator.run_state_machine import RunState


def infer_next_stage(record: Dict) -> Optional[str]:
    """Infer the next actionable stage from a saved run record."""
    tasks = record.get("tasks", [])
    validation_result = record.get("validation_result")
    repair_count = record.get("repair_count", 0)
    max_repairs = 1  # This should match the retry policy
    
    # If no tasks, need to plan
    if not tasks:
        return "plan"
    
    # Check if all tasks are complete
    all_complete = all(task.get("status") == "complete" for task in tasks)
    if all_complete:
        # If validation passed, we're done
        if validation_result and isinstance(validation_result, dict) and validation_result.get("status") == "pass":
            return None  # Complete, no action needed
        # If validation failed and we can retry, need repair
        elif validation_result and repair_count < max_repairs:
            return "repair"
        # Otherwise, failed
        else:
            return None  # Failed, no action possible
    
    # If tasks are incomplete, need execution
    return "execute"


def resume_run(record: Dict) -> Dict:
    """Resume execution from the inferred next stage."""
    next_stage = infer_next_stage(record)
    
    if next_stage is None:
        # Run is either complete or failed, return as-is
        return record
    
    # Update the record to indicate resumption
    record["resumed"] = True
    record["resumed_from"] = next_stage
    
    return record
