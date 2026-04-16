from typing import Any


def calculate_confidence(tasks: list[Any], validation_result: Any, repair_count: int) -> float:
    score = 1.0

    if repair_count > 0:
        score -= 0.1 * repair_count

    if validation_result and isinstance(validation_result, dict):
        if validation_result.get("status") != "pass":
            score -= 0.2

    return max(0.0, min(1.0, score))
