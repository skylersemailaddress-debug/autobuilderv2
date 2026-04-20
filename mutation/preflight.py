def preflight_check(action: str, context: dict) -> dict:
    return {"action": action, "approved": context.get("approved", False)}
