def enforce_mutation_invariants(target_path: str) -> None:
    protected = ["control_plane/", "policies/", ".github/", "security/"]
    if any(target_path.startswith(p) for p in protected):
        raise ValueError("Mutation invariant violation: protected path")
