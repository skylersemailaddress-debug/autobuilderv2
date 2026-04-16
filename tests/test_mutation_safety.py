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
