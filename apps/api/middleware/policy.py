from policies.engine import PolicyEngine

_engine = PolicyEngine()


def policy_middleware(action: str, context: dict) -> dict:
    return _engine.evaluate(action, context)
