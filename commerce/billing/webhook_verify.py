from __future__ import annotations

import hmac
import hashlib
import os


class WebhookVerificationError(Exception):
    pass


def verify_webhook(payload: bytes, signature: str) -> bool:
    secret = os.getenv("AUTOBUILDER_WEBHOOK_SECRET", "")
    if not secret:
        raise WebhookVerificationError("Missing webhook secret")

    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise WebhookVerificationError("Invalid webhook signature")

    return True
