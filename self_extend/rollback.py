def rollback(candidate: dict) -> dict:
    candidate["status"] = "rolled_back"
    return candidate
