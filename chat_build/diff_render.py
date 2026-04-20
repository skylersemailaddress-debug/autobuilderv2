def render_diff(old: dict, new: dict) -> dict:
    return {"added": {k:v for k,v in new.items() if k not in old}, "removed": {k:v for k,v in old.items() if k not in new}}
