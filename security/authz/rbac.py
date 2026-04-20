def check_role(role: str, action: str) -> bool:
    if role == "admin":
        return True
    if role == "user" and action in ("read", "inspect"):
        return True
    return False
