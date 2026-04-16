from execution.contracts import CONTRACTS


def validate_plan_artifact(artifact):
    evidence = CONTRACTS["plan"].validate(artifact)
    return evidence["passed"], evidence


def validate_task_result_artifact(artifact):
    evidence = CONTRACTS["task_result"].validate(artifact)
    return evidence["passed"], evidence


def validate_run_summary_contract(summary):
    evidence = CONTRACTS["run_summary"].validate(summary)
    return evidence["passed"], evidence