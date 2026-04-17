from typing import Any


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 4)))


def calculate_confidence_details(
    tasks: list[Any],
    validation_result: Any,
    repair_count: int,
    *,
    contract_validation_passed: bool = True,
    rollback_available: bool = False,
    unsupported_feature_count: int = 0,
    reproducible: bool = True,
    determinism_verified: bool = False,
    reliability_score: float | None = None,
) -> dict[str, Any]:
    total_tasks = len(tasks)
    completed_tasks = 0
    for task in tasks:
        status = getattr(task, "status", None)
        if status is None and isinstance(task, dict):
            status = task.get("status")
        if status == "complete":
            completed_tasks += 1

    task_completion = 1.0 if total_tasks == 0 else completed_tasks / total_tasks

    validation_score = 0.65
    if validation_result and isinstance(validation_result, dict):
        validation_score = 1.0 if validation_result.get("status") == "pass" else 0.25

    repair_adjustment = max(0.45, 1.0 - (repair_count * 0.12))
    contract_score = 1.0 if contract_validation_passed else 0.55
    rollback_score = 1.0 if rollback_available else 0.75
    unsupported_score = max(0.0, 1.0 - (unsupported_feature_count * 0.35))
    reproducibility_score = 1.0 if reproducible else 0.6
    determinism_score = 1.0 if determinism_verified else 0.7
    reliability_input_score = 0.8 if reliability_score is None else _clamp(reliability_score)

    weights = {
        "task_completion": 0.24,
        "validation": 0.22,
        "repair_adjustment": 0.13,
        "contract_validation": 0.1,
        "rollback": 0.08,
        "unsupported_handling": 0.06,
        "reproducibility": 0.07,
        "determinism": 0.06,
        "reliability_alignment": 0.04,
    }
    components = {
        "task_completion": _clamp(task_completion),
        "validation": _clamp(validation_score),
        "repair_adjustment": _clamp(repair_adjustment),
        "contract_validation": _clamp(contract_score),
        "rollback": _clamp(rollback_score),
        "unsupported_handling": _clamp(unsupported_score),
        "reproducibility": _clamp(reproducibility_score),
        "determinism": _clamp(determinism_score),
        "reliability_alignment": _clamp(reliability_input_score),
    }
    score = _clamp(sum(components[name] * weights[name] for name in weights))

    return {
        "score": score,
        "weights": weights,
        "components": components,
        "derived_from": {
            "model_version": "v2",
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "repair_count": repair_count,
            "validation_status": validation_result.get("status") if isinstance(validation_result, dict) else None,
            "contract_validation_passed": contract_validation_passed,
            "rollback_available": rollback_available,
            "unsupported_feature_count": unsupported_feature_count,
            "reproducible": reproducible,
            "determinism_verified": determinism_verified,
            "reliability_score": reliability_score,
        },
        "formula": "sum(component_i * weight_i) where components are bounded in [0,1]",
        "explanation": (
            "Confidence is calibrated from measurable factors: task completion, validation outcome, "
            "repair usage, contract validation, rollback availability, unsupported feature handling, "
            "reproducibility, determinism verification, and reliability alignment evidence."
        ),
    }


def calculate_confidence(
    tasks: list[Any],
    validation_result: Any,
    repair_count: int,
    *,
    contract_validation_passed: bool = True,
    rollback_available: bool = False,
    unsupported_feature_count: int = 0,
    reproducible: bool = True,
    determinism_verified: bool = False,
    reliability_score: float | None = None,
) -> float:
    return calculate_confidence_details(
        tasks,
        validation_result,
        repair_count,
        contract_validation_passed=contract_validation_passed,
        rollback_available=rollback_available,
        unsupported_feature_count=unsupported_feature_count,
        reproducible=reproducible,
        determinism_verified=determinism_verified,
        reliability_score=reliability_score,
    )["score"]
