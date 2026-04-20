from __future__ import annotations

import json
from typing import Any, Dict

from commerce.billing.webhook_verify import verify_webhook
from commerce.entitlements.service import grant_plan


def handle_webhook(payload: bytes, signature: str) -> Dict[str, Any]:
    verify_webhook(payload, signature)
    data = json.loads(payload.decode("utf-8"))

    user = data.get("user")
    plan = data.get("plan")

    if user and plan:
        grant_plan(user, plan)

    return {
        "processed": True,
        "user": user,
        "plan": plan,
    }
