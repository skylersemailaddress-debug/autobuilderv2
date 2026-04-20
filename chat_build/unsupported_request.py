def is_unsupported(message: str) -> bool:
    banned = ["hack", "exploit", "malware"]
    lower = message.lower()
    return any(term in lower for term in banned)
