from policies.action_policy import ActionPolicy


def test_low_risk_classification():
    policy = ActionPolicy()
    result = policy.classify_action("Build an autonomous execution plan", [])
    
    assert result["risk_level"] == "low"
    assert result["approval_required"] is False


def test_high_risk_classification():
    policy = ActionPolicy()
    result = policy.classify_action("Delete production database", [])
    
    assert result["risk_level"] == "high"
    assert result["approval_required"] is True


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
