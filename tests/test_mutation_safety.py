from mutation.safety import CAUTION, DANGEROUS, SAFE, MutationSafetyPolicy


def test_mutation_safety_classification_safe():
    policy = MutationSafetyPolicy()
    assert policy.classify("create", "docs/new-file.md") == SAFE
    assert policy.requires_checkpoint("create", "docs/new-file.md") is False


def test_mutation_safety_classification_caution():
    policy = MutationSafetyPolicy()
    assert policy.classify("update", "README.md") == CAUTION
    assert policy.requires_checkpoint("update", "README.md") is False


def test_mutation_safety_classification_dangerous():
    policy = MutationSafetyPolicy()
    assert policy.classify("delete", "production/config.yaml") == DANGEROUS
    assert policy.requires_checkpoint("delete", "production/config.yaml") is True


def test_mutation_safety_uses_structured_context_for_governance_targets():
    policy = MutationSafetyPolicy()
    decision = policy.evaluate(
        "update approval workflow",
        "control_plane/approvals.py",
        lane_id="first_class_enterprise_agent",
        stack_id="langgraph_agents",
        irreversible_operation=True,
    )

    assert decision.risk_level == DANGEROUS
    assert decision.target_type == "governance_state"
    assert decision.approval_required is True
    assert decision.checkpoint_required is True
    assert decision.environment_sensitivity == "governance"
    assert decision.failure_mode == "halt_before_mutation"
    assert "lane:first_class_enterprise_agent" in decision.policy_basis
