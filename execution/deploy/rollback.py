def rollback(success: bool) -> str:
    return "rolled_back" if not success else "ok"
