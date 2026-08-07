from bodyos_api.policy import BehaviorToken


class SensitiveOutput(ValueError):
    pass


_CANONICAL_GROUP_MESSAGES = frozenset(token.message for token in BehaviorToken)


def assert_group_safe(text: str) -> str:
    """Accept only canonical, pre-reviewed low-sensitivity group messages."""
    normalized = text.strip()
    if normalized not in _CANONICAL_GROUP_MESSAGES:
        raise SensitiveOutput("group output must be a canonical confirmed behavior token")
    return normalized
