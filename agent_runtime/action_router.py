from __future__ import annotations

from typing import Callable, Dict, Any


class ActionRouter:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._handlers[action] = handler

    def route(self, action: str, payload: Dict[str, Any]) -> Any:
        if action not in self._handlers:
            raise KeyError(f"No handler for action: {action}")
        return self._handlers[action](payload)
