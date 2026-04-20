from __future__ import annotations


def parse_intake(message: str) -> dict:
    return {"raw": message, "tokens": message.split()}
