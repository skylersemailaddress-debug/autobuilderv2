from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from platform_hardening.composition import evaluate_composition_request
from platform_hardening.packs import get_pack_registry

CapabilityMaturity = Literal["first_class", "bounded_prototype", "structural_only", "future"]
TrustLabel = Literal["built_in", "candidate", "quarantined", "trusted_internal", "retired"]
GapClass = Literal["safely_generatable", "bounded_only", "unsupported", "approval_gated"]
AcquisitionAction = Literal[
    "use_existing",
    "compose_existing",
    "generate_pack",
    "generate_tool",
    "generate_adapter",
    "generate_validator",
    "generate_contract",
    "defer",
    "refuse",
    "require_approval",
]


@dataclass(frozen=True)
class CapabilityIdentity:
    capability_id: str
    family: str
    capability_type: str
    version: str = "1.0.0"


@dataclass(frozen=True)
class CompatibilityScope:
    lanes: list[str] = field(default_factory=list)
    runtimes: list[str] = field(default_factory=list)
    stacks: dict[str, list[str]] = field(default_factory=dict)
    composable_with: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityDescriptor:
    identity: CapabilityIdentity
    maturity: CapabilityMaturity
    trust_label: TrustLabel
    compatibility: CompatibilityScope
    prerequisites: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    validation_rules: list[str] = field(default_factory=list)
    proof_requirements: list[str] = field(default_factory=list)
    promotion_criteria: list[str] = field(default_factory=list)
    demotion_criteria: list[str] = field(default_factory=list)
    retirement_criteria: list[str] = field(default_factory=list)
    operator_trust_metadata: dict[str, object] = field(default_factory=dict)
    lineage_metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityGap:
    requirement: str
    family: str
    status: Literal["supported", "composable", "missing"]
    gap_class: GapClass | None
    reason: str
    supporting_capabilities: list[str] = field(default_factory=list)
    composition_patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityAcquisitionDecision:
    requirement: str
    action: AcquisitionAction
    reason: str
    confidence: float
    evidence: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _norm(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _detect_family(requirement: str) -> str:
    text = _norm(requirement)
    if any(token in text for token in ("payment", "billing", "entitlement", "commerce")):
        return "commerce"
    if any(token in text for token in ("auth", "security", "rbac", "policy")):
        return "security"
    if any(token in text for token in ("realtime", "stream", "event", "sensor")):
        return "realtime"
    if any(token in text for token in ("agent", "assistant", "workflow")):
        return "agent-runtime"
    if any(token in text for token in ("validate", "proof", "contract", "check")):
        return "validation"
    if any(token in text for token in ("adapter", "connect", "bridge")):
        return "adapter"
    return "domain"


def _required_patterns_for_family(family: str) -> list[str]:
    mapping = {
        "commerce": ["app_plus_payment_layer"],
        "agent-runtime": ["app_plus_agent"],
        "realtime": ["app_plus_realtime"],
        "ops-governance": ["app_plus_ops_governance"],
    }
    return list(mapping.get(family, []))


def _load_json(path: Path, default: dict[str, object]) -> dict[str, object]:
    if not path.exists():
        return dict(default)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return dict(default)
    return loaded


def _save_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CapabilityRegistry:
    """Deterministic capability registry with trust + governance state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.payload = _load_json(
            self.path,
            {
                "version": "v2",
                "built_in": [],
                "generated_candidates": [],
                "quarantined": [],
                "trusted_internal": [],
                "retired": [],
                "history": [],
                "learning": {"success": [], "failure": [], "composition": []},
            },
        )

    def save(self) -> None:
        _save_json(self.path, self.payload)

    def _bucket(self, trust_label: TrustLabel) -> str:
        return {
            "built_in": "built_in",
            "candidate": "generated_candidates",
            "quarantined": "quarantined",
            "trusted_internal": "trusted_internal",
            "retired": "retired",
        }[trust_label]

    def _all_entries(self) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        for key in ("built_in", "generated_candidates", "quarantined", "trusted_internal", "retired"):
            section = self.payload.get(key, [])
            if isinstance(section, list):
                entries.extend([item for item in section if isinstance(item, dict)])
        return entries

    def add_capability(self, descriptor: CapabilityDescriptor) -> dict[str, object]:
        issues = validate_capability_descriptor(descriptor)
        entry = descriptor.to_dict()
        bucket = self._bucket(descriptor.trust_label)

        if issues:
            entry["validation_issues"] = issues
            self.payload.setdefault("quarantined", []).append(entry)
            self.payload.setdefault("history", []).append(
                {
                    "event": "quarantined_on_insert",
                    "capability_id": descriptor.identity.capability_id,
                    "issues": issues,
                }
            )
            self.save()
            return {"status": "quarantined", "issues": issues, "bucket": "quarantined"}

        self.payload.setdefault(bucket, []).append(entry)
        self.payload.setdefault("history", []).append(
            {
                "event": "added",
                "capability_id": descriptor.identity.capability_id,
                "bucket": bucket,
            }
        )
        self.save()
        return {"status": "added", "issues": [], "bucket": bucket}

    def list_capabilities(
        self,
        *,
        lane_id: str | None = None,
        runtime: str | None = None,
        stack: dict[str, str] | None = None,
        include_quarantined: bool = False,
    ) -> list[dict[str, object]]:
        stack = stack or {}
        items = []
        allowed_buckets = {"built_in", "generated_candidates", "trusted_internal"}
        if include_quarantined:
            allowed_buckets.add("quarantined")

        for bucket in sorted(allowed_buckets):
            section = self.payload.get(bucket, [])
            if not isinstance(section, list):
                continue
            for entry in section:
                if not isinstance(entry, dict):
                    continue
                compatibility = entry.get("compatibility", {})
                if not isinstance(compatibility, dict):
                    compatibility = {}
                if lane_id and compatibility.get("lanes") and lane_id not in compatibility.get("lanes", []):
                    continue
                if runtime and compatibility.get("runtimes") and runtime not in compatibility.get("runtimes", []):
                    continue
                stacks = compatibility.get("stacks", {})
                if isinstance(stacks, dict) and stack:
                    invalid = False
                    for category, selected in stack.items():
                        allowed = stacks.get(category, [])
                        if allowed and selected not in allowed:
                            invalid = True
                            break
                    if invalid:
                        continue
                items.append(entry)

        return sorted(items, key=lambda item: str(item.get("identity", {}).get("capability_id", "")))

    def lookup_by_requirement(
        self,
        *,
        requirement: str,
        lane_id: str,
        runtime: str,
        stack: dict[str, str],
    ) -> dict[str, object]:
        family = _detect_family(requirement)
        requirement_norm = _norm(requirement)
        candidates = self.list_capabilities(lane_id=lane_id, runtime=runtime, stack=stack)

        supporting = []
        for item in candidates:
            identity = item.get("identity", {})
            capability_id = _norm(str(identity.get("capability_id", "")))
            capability_family = _norm(str(identity.get("family", "")))
            if requirement_norm in capability_id or requirement_norm == capability_family or family == capability_family:
                supporting.append(item)

        return {
            "requirement": requirement,
            "family": family,
            "supported": len(supporting) > 0,
            "supporting": supporting,
        }

    def promote(self, capability_id: str, reason: str) -> dict[str, object]:
        moved = _move_entry(
            payload=self.payload,
            capability_id=capability_id,
            source_key="quarantined",
            target_key="trusted_internal",
            trust_label="trusted_internal",
        )
        self.payload.setdefault("history", []).append(
            {"event": "promoted", "capability_id": capability_id, "reason": reason, "changed": moved}
        )
        self.save()
        return {"status": "promoted" if moved else "not_found", "capability_id": capability_id}

    def demote(self, capability_id: str, reason: str) -> dict[str, object]:
        moved = _move_entry(
            payload=self.payload,
            capability_id=capability_id,
            source_key="trusted_internal",
            target_key="quarantined",
            trust_label="quarantined",
        )
        self.payload.setdefault("history", []).append(
            {"event": "demoted", "capability_id": capability_id, "reason": reason, "changed": moved}
        )
        self.save()
        return {"status": "demoted" if moved else "not_found", "capability_id": capability_id}

    def retire(self, capability_id: str, reason: str) -> dict[str, object]:
        moved_any = False
        for source in ("trusted_internal", "generated_candidates", "built_in"):
            moved_any = _move_entry(
                payload=self.payload,
                capability_id=capability_id,
                source_key=source,
                target_key="retired",
                trust_label="retired",
            ) or moved_any
        self.payload.setdefault("history", []).append(
            {"event": "retired", "capability_id": capability_id, "reason": reason, "changed": moved_any}
        )
        self.save()
        return {"status": "retired" if moved_any else "not_found", "capability_id": capability_id}

    def rollback(self, capability_id: str) -> dict[str, object]:
        return self.demote(capability_id, reason="rollback requested")

    def record_learning(self, event: dict[str, object]) -> None:
        learning = self.payload.setdefault("learning", {})
        if not isinstance(learning, dict):
            learning = {"success": [], "failure": [], "composition": []}
            self.payload["learning"] = learning

        category = str(event.get("category", "failure"))
        if category not in {"success", "failure", "composition"}:
            category = "failure"
        bucket = learning.setdefault(category, [])
        if isinstance(bucket, list):
            bucket.append(event)

        self.payload.setdefault("history", []).append(
            {
                "event": "learning_recorded",
                "category": category,
                "requirement": event.get("requirement", ""),
            }
        )
        self.save()


def _move_entry(
    *,
    payload: dict[str, object],
    capability_id: str,
    source_key: str,
    target_key: str,
    trust_label: TrustLabel,
) -> bool:
    source = payload.get(source_key, [])
    if not isinstance(source, list):
        return False

    for index, entry in enumerate(source):
        if not isinstance(entry, dict):
            continue
        identity = entry.get("identity", {})
        if str(identity.get("capability_id", "")) != capability_id:
            continue
        source.pop(index)
        entry["trust_label"] = trust_label
        payload.setdefault(target_key, []).append(entry)
        return True

    return False


def validate_capability_descriptor(descriptor: CapabilityDescriptor) -> list[str]:
    issues: list[str] = []
    identity = descriptor.identity

    if not identity.capability_id.strip():
        issues.append("identity.capability_id required")
    if not identity.family.strip():
        issues.append("identity.family required")
    if not descriptor.validation_rules:
        issues.append("validation_rules required")
    if not descriptor.proof_requirements:
        issues.append("proof_requirements required")
    if not descriptor.promotion_criteria:
        issues.append("promotion_criteria required")
    if not descriptor.demotion_criteria:
        issues.append("demotion_criteria required")
    if not descriptor.retirement_criteria:
        issues.append("retirement_criteria required")
    if not descriptor.operator_trust_metadata:
        issues.append("operator_trust_metadata required")
    if not descriptor.lineage_metadata:
        issues.append("lineage_metadata required")

    return sorted(issues)


def build_builtin_capabilities_for_lane(
    *, lane_id: str, runtime: str, stack: dict[str, str]
) -> list[CapabilityDescriptor]:
    profile = get_pack_registry().compose_lane_profile(lane_id)
    descriptors: list[CapabilityDescriptor] = []

    for pack in profile.get("packs", []):
        if not isinstance(pack, dict):
            continue
        pack_capabilities = pack.get("capabilities", [])
        if not isinstance(pack_capabilities, list):
            continue
        pack_id = str(pack.get("pack_id", ""))
        family = str(pack.get("pack_type", "domain"))
        for capability in sorted({_norm(str(item)) for item in pack_capabilities if str(item).strip()}):
            descriptors.append(
                CapabilityDescriptor(
                    identity=CapabilityIdentity(
                        capability_id=f"builtin::{lane_id}::{capability}",
                        family=family,
                        capability_type="pack_capability",
                    ),
                    maturity="first_class" if family not in {"security", "commerce", "research"} else "bounded_prototype",
                    trust_label="built_in",
                    compatibility=CompatibilityScope(
                        lanes=[lane_id],
                        runtimes=[runtime],
                        stacks={k: [v] for k, v in sorted(stack.items())},
                        composable_with=sorted(_required_patterns_for_family(family)),
                    ),
                    prerequisites=[],
                    dependencies=[pack_id],
                    validation_rules=["pack_registered", "lane_profile_consistent"],
                    proof_requirements=["proof_bundle_present", "support_honesty_declared"],
                    promotion_criteria=["builtin_always_trusted"],
                    demotion_criteria=["pack_removed_from_lane"],
                    retirement_criteria=["lane_retired"],
                    operator_trust_metadata={"source": "pack_registry", "operator_visible": True},
                    lineage_metadata={"source": "pack_registry", "pack_id": pack_id},
                )
            )

    return descriptors


def detect_capability_gaps(
    *,
    lane_id: str,
    runtime: str,
    stack: dict[str, str],
    required_capabilities: list[str],
    registry: CapabilityRegistry,
) -> dict[str, object]:
    requirements = sorted({_norm(item) for item in required_capabilities if str(item).strip()})
    required_families = sorted({_detect_family(item) for item in requirements})

    gap_entries: list[CapabilityGap] = []
    supported: list[str] = []
    composable: list[str] = []
    missing: list[str] = []

    for requirement in requirements:
        lookup = registry.lookup_by_requirement(
            requirement=requirement,
            lane_id=lane_id,
            runtime=runtime,
            stack=stack,
        )
        family = str(lookup.get("family", "domain"))
        if lookup.get("supported", False):
            support_ids = [
                str(item.get("identity", {}).get("capability_id", ""))
                for item in lookup.get("supporting", [])
                if isinstance(item, dict)
            ]
            gap_entries.append(
                CapabilityGap(
                    requirement=requirement,
                    family=family,
                    status="supported",
                    gap_class=None,
                    reason="already_supported",
                    supporting_capabilities=sorted([sid for sid in support_ids if sid]),
                )
            )
            supported.append(requirement)
            continue

        patterns = _required_patterns_for_family(family)
        composable_pattern_hits = []
        for pattern_id in patterns:
            secondary = {
                "app_plus_payment_layer": "commerce",
                "app_plus_agent": "agent-runtime",
                "app_plus_realtime": "first_class_realtime",
                "app_plus_ops_governance": "enterprise-readiness",
            }.get(pattern_id, family)
            composition = evaluate_composition_request(lane_id, secondary)
            if composition.get("accepted", False):
                composable_pattern_hits.append(pattern_id)

        if composable_pattern_hits:
            gap_entries.append(
                CapabilityGap(
                    requirement=requirement,
                    family=family,
                    status="composable",
                    gap_class="bounded_only",
                    reason="can_be_composed_from_registered_pattern",
                    composition_patterns=sorted(composable_pattern_hits),
                )
            )
            composable.append(requirement)
            continue

        if "core" in requirement or family in {"security", "commerce"}:
            gap_class: GapClass = "approval_gated"
            reason = "core_or_regulated_capability_requires_approval"
        elif family in {"validation", "adapter", "domain"}:
            gap_class = "safely_generatable"
            reason = "bounded_generation_supported"
        elif family in {"realtime", "agent-runtime"}:
            gap_class = "bounded_only"
            reason = "bounded_generation_or_composition_only"
        else:
            gap_class = "unsupported"
            reason = "unsupported_capability_family"

        gap_entries.append(
            CapabilityGap(
                requirement=requirement,
                family=family,
                status="missing",
                gap_class=gap_class,
                reason=reason,
            )
        )
        missing.append(requirement)

    return {
        "lane_id": lane_id,
        "runtime": runtime,
        "stack": dict(sorted(stack.items())),
        "required_capabilities": requirements,
        "required_families": required_families,
        "supported": sorted(supported),
        "composable": sorted(composable),
        "missing": sorted(missing),
        "gaps": [gap.to_dict() for gap in gap_entries],
    }


def evaluate_create_compose_refuse_policy(
    *,
    gap: dict[str, object],
    has_composition_path: bool,
    approvals_enabled: bool,
    approved: bool,
    learning_preference: str | None,
) -> dict[str, object]:
    gap_class = str(gap.get("gap_class", "unsupported"))
    family = str(gap.get("family", "domain"))
    requirement = str(gap.get("requirement", ""))

    if gap_class == "unsupported":
        return {
            "requirement": requirement,
            "decision": "refuse",
            "reason": "unsupported_family",
            "approval_required": False,
        }

    if has_composition_path and learning_preference != "generate":
        return {
            "requirement": requirement,
            "decision": "compose_existing",
            "reason": "registered_composition_pattern_available",
            "approval_required": False,
        }

    if gap_class == "approval_gated":
        if approvals_enabled and not approved:
            return {
                "requirement": requirement,
                "decision": "require_approval",
                "reason": "core_or_regulated_gap_requires_approval",
                "approval_required": True,
            }
        return {
            "requirement": requirement,
            "decision": "generate_validator" if family == "security" else "generate_contract",
            "reason": "approval_satisfied_for_regulated_gap",
            "approval_required": approvals_enabled,
        }

    if gap_class == "bounded_only":
        if family == "adapter":
            decision = "generate_adapter"
        elif family == "validation":
            decision = "generate_validator"
        else:
            decision = "generate_tool"
        return {
            "requirement": requirement,
            "decision": decision,
            "reason": "bounded_generation_policy",
            "approval_required": False,
        }

    if learning_preference == "compose" and has_composition_path:
        decision = "compose_existing"
    elif family == "adapter":
        decision = "generate_adapter"
    elif family == "validation":
        decision = "generate_validator"
    elif "pack" in requirement:
        decision = "generate_pack"
    elif "contract" in requirement:
        decision = "generate_contract"
    else:
        decision = "generate_tool"

    return {
        "requirement": requirement,
        "decision": decision,
        "reason": "safely_generatable_policy",
        "approval_required": False,
    }


def _learning_preference(registry: CapabilityRegistry, family: str) -> str | None:
    learning = registry.payload.get("learning", {})
    if not isinstance(learning, dict):
        return None

    success_entries = [item for item in learning.get("success", []) if isinstance(item, dict)]
    failure_entries = [item for item in learning.get("failure", []) if isinstance(item, dict)]
    composition_entries = [item for item in learning.get("composition", []) if isinstance(item, dict)]

    family_success = sum(1 for item in success_entries if _detect_family(str(item.get("requirement", ""))) == family)
    family_failure = sum(1 for item in failure_entries if _detect_family(str(item.get("requirement", ""))) == family)
    family_composition = sum(
        1 for item in composition_entries if _detect_family(str(item.get("requirement", ""))) == family
    )

    if family_composition > family_success:
        return "compose"
    if family_success > family_failure:
        return "generate"
    return None


def build_capability_acquisition_plan(
    *,
    gap_report: dict[str, object],
    approvals_enabled: bool,
    approved: bool,
    registry: CapabilityRegistry,
) -> dict[str, object]:
    decisions: list[CapabilityAcquisitionDecision] = []

    for gap in gap_report.get("gaps", []):
        if not isinstance(gap, dict):
            continue
        status = str(gap.get("status", "missing"))
        requirement = str(gap.get("requirement", ""))
        family = str(gap.get("family", "domain"))
        if status == "supported":
            decisions.append(
                CapabilityAcquisitionDecision(
                    requirement=requirement,
                    action="use_existing",
                    reason="already_supported_in_registry",
                    confidence=1.0,
                    evidence={"supporting_capabilities": gap.get("supporting_capabilities", [])},
                )
            )
            continue

        has_composition_path = bool(gap.get("composition_patterns"))
        policy = evaluate_create_compose_refuse_policy(
            gap=gap,
            has_composition_path=has_composition_path,
            approvals_enabled=approvals_enabled,
            approved=approved,
            learning_preference=_learning_preference(registry, family),
        )
        decision = str(policy.get("decision", "refuse"))
        action: AcquisitionAction = "refuse"
        if decision in {
            "use_existing",
            "compose_existing",
            "generate_pack",
            "generate_tool",
            "generate_adapter",
            "generate_validator",
            "generate_contract",
            "defer",
            "refuse",
            "require_approval",
        }:
            action = decision

        confidence = 0.9 if action in {"use_existing", "compose_existing"} else 0.75
        if action in {"refuse", "require_approval"}:
            confidence = 1.0

        decisions.append(
            CapabilityAcquisitionDecision(
                requirement=requirement,
                action=action,
                reason=str(policy.get("reason", "policy_decision")),
                confidence=confidence,
                evidence={
                    "gap_class": gap.get("gap_class"),
                    "composition_patterns": gap.get("composition_patterns", []),
                    "approval_required": policy.get("approval_required", False),
                },
            )
        )

    action_summary: dict[str, int] = {}
    for item in decisions:
        action_summary[item.action] = action_summary.get(item.action, 0) + 1

    return {
        "decisions": [item.to_dict() for item in decisions],
        "action_summary": dict(sorted(action_summary.items())),
        "deterministic": True,
    }


def summarize_learning(registry: CapabilityRegistry) -> dict[str, object]:
    learning = registry.payload.get("learning", {})
    if not isinstance(learning, dict):
        learning = {}

    success = [item for item in learning.get("success", []) if isinstance(item, dict)]
    failure = [item for item in learning.get("failure", []) if isinstance(item, dict)]
    composition = [item for item in learning.get("composition", []) if isinstance(item, dict)]

    strategy_scores: dict[str, dict[str, int]] = {}
    for bucket_name, entries in (("success", success), ("failure", failure), ("composition", composition)):
        for item in entries:
            strategy = str(item.get("strategy", "unknown"))
            agg = strategy_scores.setdefault(strategy, {"success": 0, "failure": 0, "composition": 0})
            agg[bucket_name] += 1

    return {
        "counts": {
            "success": len(success),
            "failure": len(failure),
            "composition": len(composition),
        },
        "strategy_scores": dict(sorted(strategy_scores.items())),
        "deterministic": True,
    }


def prime_registry_with_builtins(
    *,
    registry: CapabilityRegistry,
    lane_id: str,
    runtime: str,
    stack: dict[str, str],
) -> dict[str, object]:
    existing_ids = {
        str(item.get("identity", {}).get("capability_id", ""))
        for item in registry.payload.get("built_in", [])
        if isinstance(item, dict)
    }

    added = 0
    for descriptor in build_builtin_capabilities_for_lane(lane_id=lane_id, runtime=runtime, stack=stack):
        cap_id = descriptor.identity.capability_id
        if cap_id in existing_ids:
            continue
        result = registry.add_capability(descriptor)
        if result.get("status") == "added":
            added += 1
            existing_ids.add(cap_id)

    return {"added": added, "total_builtins": len(existing_ids)}
