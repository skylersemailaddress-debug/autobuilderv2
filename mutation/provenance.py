"""
Mutation provenance tracking: scope envelopes, critical file awareness,
artifact lineage, and machine-readable mutation decisions.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Critical file classification
# ---------------------------------------------------------------------------

_CRITICAL_PATTERNS: list[tuple[list[str], str, str]] = [
    (["db/schema", "migrations/", "alembic/", ".sql"], "database_schema", "DANGEROUS"),
    (["security/", "auth/", "billing/", "payment/"], "security_or_billing", "DANGEROUS"),
    ([".env", "secrets.", "credentials."], "secrets_config", "DANGEROUS"),
    (["pyproject.toml", "package.json", "requirements.txt", "go.mod"], "dependency_manifest", "CAUTION"),
    (["docker-compose", "dockerfile", "kubernetes/", ".k8s/"], "deployment_config", "CAUTION"),
    ([".autobuilder/", "runs/", "state/", "memory/"], "autobuilder_state", "CAUTION"),
    (["README", "CHANGELOG", "LICENSE", "docs/"], "documentation", "SAFE"),
    (["tests/", "test_", "_test.py", "spec."], "test_surface", "SAFE"),
    (["frontend/", "backend/api/", "src/"], "application_source", "CAUTION"),
]


def classify_critical_path(file_path: str) -> tuple[str, str]:
    """Return (classification, risk_level) for a file path."""
    norm = file_path.lower().replace("\\", "/")
    for patterns, classification, risk in _CRITICAL_PATTERNS:
        if any(p in norm for p in patterns):
            return classification, risk
    return "general_file", "SAFE"


# ---------------------------------------------------------------------------
# Scope Envelope
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScopeEnvelope:
    """Defines the safe mutation boundary for a repo operation."""
    repo_root: str
    allowed_paths: list[str]
    excluded_paths: list[str]
    critical_paths: list[str]
    risk_level: str
    requires_checkpoint: bool
    requires_approval: bool
    envelope_signature: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_scope_envelope(
    target_path: str,
    repo_root: str,
    extra_exclusions: Optional[list[str]] = None,
) -> ScopeEnvelope:
    """Build a safe scope envelope for mutation within a repo."""
    norm_root = Path(repo_root).resolve()
    norm_target = Path(target_path)

    # Prevent path traversal
    try:
        norm_target.resolve().relative_to(norm_root)
        within_repo = True
    except ValueError:
        within_repo = False

    classification, risk_level = classify_critical_path(target_path)

    excluded = [
        ".git/",
        "runs/",
        "state/",
        "memory/",
        ".autobuilder/",
        "db/schema.sql",
        "migrations/",
        "security/",
        ".env",
        "secrets.",
    ]
    if extra_exclusions:
        excluded.extend(extra_exclusions)

    critical = [p for p, cls, _ in _CRITICAL_PATTERNS if classification == cls for p in p]

    signature_data = json.dumps(
        {"repo_root": str(norm_root), "target_path": target_path, "risk_level": risk_level},
        sort_keys=True,
    )
    env_sig = hashlib.sha256(signature_data.encode()).hexdigest()[:16]

    return ScopeEnvelope(
        repo_root=str(norm_root),
        allowed_paths=[target_path] if within_repo else [],
        excluded_paths=excluded,
        critical_paths=[target_path] if risk_level in ("DANGEROUS", "CAUTION") else [],
        risk_level=risk_level,
        requires_checkpoint=risk_level in ("DANGEROUS", "CAUTION"),
        requires_approval=risk_level == "DANGEROUS",
        envelope_signature=env_sig,
    )


# ---------------------------------------------------------------------------
# Mutation Decision
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MutationDecision:
    """Machine-readable record of a single mutation decision."""
    decision_id: str
    file_path: str
    operation: str  # create | update | delete | overwrite
    classification: str
    risk_level: str
    scope_within_envelope: bool
    requires_checkpoint: bool
    requires_approval: bool
    overwrite_allowed: bool
    merge_required: bool
    rollback_strategy: str
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def build_mutation_decision(
    decision_id: str,
    file_path: str,
    operation: str,
    scope_envelope: ScopeEnvelope,
    existing_file: bool = False,
) -> MutationDecision:
    """Build a machine-readable mutation decision for a file operation."""
    classification, risk_level = classify_critical_path(file_path)

    # Resolve overwrite safety
    overwrite_allowed = (
        operation == "create" or
        (operation in ("update", "overwrite") and risk_level == "SAFE") or
        (operation == "overwrite" and risk_level == "CAUTION" and scope_envelope.requires_checkpoint)
    )
    merge_required = (
        existing_file and risk_level == "CAUTION" and operation in ("update", "overwrite")
    )

    rollback = (
        "checkpoint_and_restore" if risk_level == "DANGEROUS"
        else ("checkpoint_preferred" if risk_level == "CAUTION" else "none_needed")
    )

    norm_path = file_path.lower().replace("\\", "/")
    scope_safe = any(
        norm_path.startswith(ap.lower()) for ap in scope_envelope.allowed_paths
    ) or bool(scope_envelope.allowed_paths)
    scope_in_exclusion = any(
        ep in norm_path for ep in scope_envelope.excluded_paths
    )
    within_scope = scope_safe and not scope_in_exclusion

    return MutationDecision(
        decision_id=decision_id,
        file_path=file_path,
        operation=operation,
        classification=classification,
        risk_level=risk_level,
        scope_within_envelope=within_scope,
        requires_checkpoint=risk_level in ("DANGEROUS", "CAUTION"),
        requires_approval=risk_level == "DANGEROUS",
        overwrite_allowed=overwrite_allowed,
        merge_required=merge_required,
        rollback_strategy=rollback,
        provenance={
            "envelope_signature": scope_envelope.envelope_signature,
            "scope_risk_level": scope_envelope.risk_level,
            "existing_file": existing_file,
        },
    )


# ---------------------------------------------------------------------------
# Provenance Record (run-level)
# ---------------------------------------------------------------------------

@dataclass
class MutationProvenanceRecord:
    """Tracks all mutation decisions made during a run."""
    run_id: str
    decisions: list[MutationDecision] = field(default_factory=list)

    def add_decision(self, decision: MutationDecision) -> None:
        self.decisions.append(decision)

    def summary(self) -> dict:
        total = len(self.decisions)
        dangerous = sum(1 for d in self.decisions if d.risk_level == "DANGEROUS")
        caution = sum(1 for d in self.decisions if d.risk_level == "CAUTION")
        safe = total - dangerous - caution
        blocked = sum(1 for d in self.decisions if not d.scope_within_envelope)
        return {
            "run_id": self.run_id,
            "total_decisions": total,
            "dangerous_count": dangerous,
            "caution_count": caution,
            "safe_count": safe,
            "out_of_scope_blocked": blocked,
            "all_within_scope": blocked == 0,
            "decisions": [d.to_dict() for d in self.decisions],
        }
