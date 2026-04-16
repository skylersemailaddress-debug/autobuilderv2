from orchestrator.policy import RetryPolicy


def test_retry_policy_allows_until_max():
    policy = RetryPolicy(max_repairs=2)

    assert policy.can_retry(0) is True
    assert policy.can_retry(1) is True
    assert policy.can_retry(2) is False
