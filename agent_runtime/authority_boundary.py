def enforce_authority(role: str, action: str) -> bool:
    if role == "admin":
        return True
    if role == "operator" and action not in ("self_extend", "admin_override"):
        return True
    return False
