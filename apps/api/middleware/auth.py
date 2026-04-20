from security.auth.providers import validate_token


def auth_middleware(token: str) -> bool:
    return validate_token(token)
