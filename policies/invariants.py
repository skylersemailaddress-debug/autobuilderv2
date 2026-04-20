def enforce_invariants(context: dict) -> None:
    if context.get("secrets_exposed"):
        raise ValueError("Invariant violation: secrets exposure")
