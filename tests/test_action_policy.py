from policies.action_policy import ActionPolicy


def test_low_risk_classification():
    policy = ActionPolicy()
    result = policy.classify_action("Build an autonomous execution plan", [])
    
    assert result["risk_level"] == "low"
    assert result["approval_required"] is False
    assert result["checkpoint_required"] is False
    assert result["action_class"] == "creation"


def test_high_risk_classification():
    policy = ActionPolicy()
    result = policy.classify_action("Delete production database", [])
    
    assert result["risk_level"] == "high"
    assert result["approval_required"] is True
    assert result["checkpoint_required"] is True
    assert result["environment_sensitivity"] == "production"


def test_high_risk_keywords():
    policy = ActionPolicy()
    
    # Test various high-risk keywords
    high_risk_goals = [
        "delete all files",
        "destroy the system",
        "production deployment",
        "migrate database",
    ]
    
    for goal in high_risk_goals:
        result = policy.classify_action(goal, [])
        assert result["risk_level"] == "high"
        assert result["approval_required"] is True


def test_medium_risk_classification_exposes_restore_strategy():
    policy = ActionPolicy()
    result = policy.classify_action("Update application settings", [])

    assert result["risk_level"] == "medium"
    assert result["approval_required"] is False
    assert result["restore_strategy"] == "not_required"
    assert result["destructive_potential"] == "medium"
