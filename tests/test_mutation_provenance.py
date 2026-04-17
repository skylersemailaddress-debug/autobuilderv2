"""
Tests for repo-targeted mutation provenance: scope envelopes,
critical file classification, mutation decisions, provenance records.
"""
import pytest
from mutation.provenance import (
    classify_critical_path,
    build_scope_envelope,
    build_mutation_decision,
    MutationProvenanceRecord,
)


# ---------------------------------------------------------------------------
# Critical path classification
# ---------------------------------------------------------------------------

def test_classify_db_schema_dangerous():
    cls, risk = classify_critical_path("db/schema.sql")
    assert risk == "DANGEROUS"
    assert cls == "database_schema"


def test_classify_security_dangerous():
    cls, risk = classify_critical_path("backend/security/auth.py")
    assert risk == "DANGEROUS"


def test_classify_env_file_dangerous():
    cls, risk = classify_critical_path(".env")
    assert risk == "DANGEROUS"
    assert cls == "secrets_config"


def test_classify_package_json_caution():
    cls, risk = classify_critical_path("pyproject.toml")
    assert risk == "CAUTION"


def test_classify_dockerfile_caution():
    cls, risk = classify_critical_path("Dockerfile")
    assert risk == "CAUTION"


def test_classify_readme_safe():
    cls, risk = classify_critical_path("README.md")
    assert risk == "SAFE"


def test_classify_tests_safe():
    cls, risk = classify_critical_path("tests/test_auth.py")
    assert risk == "SAFE"


def test_classify_autobuilder_state_caution():
    cls, risk = classify_critical_path(".autobuilder/state.json")
    assert risk == "CAUTION"


def test_classify_unknown_safe():
    cls, risk = classify_critical_path("some_random_module.py")
    assert risk == "SAFE"
    assert cls == "general_file"


# ---------------------------------------------------------------------------
# Scope envelope
# ---------------------------------------------------------------------------

def test_scope_envelope_basic(tmp_path):
    env = build_scope_envelope(str(tmp_path / "src/module.py"), str(tmp_path))
    assert env.repo_root == str(tmp_path.resolve())
    assert env.risk_level in ("SAFE", "CAUTION", "DANGEROUS")
    assert isinstance(env.excluded_paths, list)
    assert len(env.excluded_paths) > 0


def test_scope_envelope_critical_path_sets_checkpoint(tmp_path):
    env = build_scope_envelope(str(tmp_path / "db/schema.sql"), str(tmp_path))
    assert env.requires_checkpoint is True
    assert env.requires_approval is True
    assert env.risk_level == "DANGEROUS"


def test_scope_envelope_safe_path_no_checkpoint(tmp_path):
    env = build_scope_envelope(str(tmp_path / "README.md"), str(tmp_path))
    assert env.requires_checkpoint is False
    assert env.requires_approval is False


def test_scope_envelope_signature_deterministic(tmp_path):
    env1 = build_scope_envelope(str(tmp_path / "README.md"), str(tmp_path))
    env2 = build_scope_envelope(str(tmp_path / "README.md"), str(tmp_path))
    assert env1.envelope_signature == env2.envelope_signature


# ---------------------------------------------------------------------------
# Mutation decision
# ---------------------------------------------------------------------------

def test_mutation_decision_safe_create(tmp_path):
    env = build_scope_envelope(str(tmp_path / "src/app.py"), str(tmp_path))
    decision = build_mutation_decision("d1", "src/app.py", "create", env)
    assert decision.overwrite_allowed is True
    assert decision.risk_level in ("SAFE", "CAUTION")
    assert decision.rollback_strategy in ("none_needed", "checkpoint_preferred")


def test_mutation_decision_dangerous_requires_approval(tmp_path):
    env = build_scope_envelope(str(tmp_path / "db/schema.sql"), str(tmp_path))
    decision = build_mutation_decision("d2", "db/schema.sql", "delete", env, existing_file=True)
    assert decision.requires_approval is True
    assert decision.requires_checkpoint is True
    assert "checkpoint" in decision.rollback_strategy


def test_mutation_decision_caution_merge_required(tmp_path):
    env = build_scope_envelope(str(tmp_path / "pyproject.toml"), str(tmp_path))
    decision = build_mutation_decision("d3", "pyproject.toml", "update", env, existing_file=True)
    assert decision.merge_required is True
    assert decision.requires_checkpoint is True


def test_mutation_decision_provenance_has_envelope_sig(tmp_path):
    env = build_scope_envelope(str(tmp_path / "README.md"), str(tmp_path))
    decision = build_mutation_decision("d4", "README.md", "update", env)
    assert "envelope_signature" in decision.provenance
    assert decision.provenance["envelope_signature"] == env.envelope_signature


# ---------------------------------------------------------------------------
# Provenance record
# ---------------------------------------------------------------------------

def test_provenance_record_summary(tmp_path):
    record = MutationProvenanceRecord(run_id="prov-001")
    env = build_scope_envelope(str(tmp_path / "src/app.py"), str(tmp_path))
    for i, (path, op) in enumerate([
        ("src/app.py", "create"),
        ("README.md", "update"),
        ("db/schema.sql", "delete"),
    ]):
        env_i = build_scope_envelope(str(tmp_path / path), str(tmp_path))
        record.add_decision(build_mutation_decision(f"d{i}", path, op, env_i, existing_file=(op != "create")))

    summary = record.summary()
    assert summary["run_id"] == "prov-001"
    assert summary["total_decisions"] == 3
    assert summary["dangerous_count"] >= 1
    assert "decisions" in summary


def test_provenance_record_empty():
    record = MutationProvenanceRecord(run_id="empty-001")
    summary = record.summary()
    assert summary["total_decisions"] == 0
    assert summary["all_within_scope"] is True
