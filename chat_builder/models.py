from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ParsedIntent:
    prompt: str
    app_name: str
    app_type: str
    lane_id: str
    stack: dict[str, str]
    core_outcome: str
    requested_features: list[str]
    unsupported_requests: list[str]
    risky_requests: list[str]
    inferred_defaults: list[str]
    missing_info: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SteeringDecision:
    simple_summary: str
    critical_questions: list[str]
    tradeoffs: list[str]
    warnings: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SynthesizedSpecBundle:
    product: dict[str, object]
    architecture: dict[str, object]
    ui: dict[str, object]
    acceptance: dict[str, object]
    stack: dict[str, object]
    explanations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ChatMemorySnapshot:
    session_id: str
    project_id: str
    conversation_turns: list[dict[str, object]] = field(default_factory=list)
    decisions: list[dict[str, object]] = field(default_factory=list)
    accepted_defaults: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    failures: list[dict[str, object]] = field(default_factory=list)
    fixes: list[dict[str, object]] = field(default_factory=list)
    generated_components: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
