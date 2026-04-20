from __future__ import annotations

import re
from typing import Any, Dict, List

_STACK_HINTS = {
    "next": "nextjs",
    "react": "react",
    "fastapi": "fastapi",
    "django": "django",
    "postgres": "postgres",
    "sqlite": "sqlite",
    "stripe": "stripe",
}

_FEATURE_HINTS = {
    "auth": "authentication",
    "login": "authentication",
    "dashboard": "dashboard",
    "admin": "admin_panel",
    "billing": "billing",
    "payments": "billing",
    "search": "search",
    "api": "api",
}


def parse_intake(message: str) -> dict:
    text = (message or "").strip()
    lowered = text.lower()
    tokens: List[str] = re.findall(r"[a-zA-Z0-9_+-]+", lowered)

    stack = sorted({value for key, value in _STACK_HINTS.items() if key in tokens or key in lowered})
    features = sorted({value for key, value in _FEATURE_HINTS.items() if key in tokens or key in lowered})

    app_type = "web_app"
    if "dashboard" in features:
        app_type = "dashboard_app"
    elif "api" in features:
        app_type = "api_app"

    return {
        "raw": text,
        "tokens": tokens,
        "app_type": app_type,
        "stack": stack,
        "features": features,
        "word_count": len(tokens),
    }
