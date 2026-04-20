def map_to_spec(parsed: dict) -> dict:
    return {"spec": parsed.get("tokens", [])}
