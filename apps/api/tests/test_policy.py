import pytest
from bodyos_api.policy import (
    BehaviorToken,
    PolicyDenied,
    PolicyEngine,
    RequestContext,
    Scope,
    ToolCapability,
)


@pytest.mark.parametrize(
    "capability",
    [
        ToolCapability.HEALTH,
        ToolCapability.PRIVATE_MEMORY,
        ToolCapability.PRIVATE_KNOWLEDGE,
    ],
)
def test_group_scope_cannot_access_private_capability(capability: ToolCapability) -> None:
    context = RequestContext(
        fitcrew_user_id="user-1",
        scope=Scope.GROUP,
        purpose="group_support",
        consent_id=None,
    )

    with pytest.raises(PolicyDenied) as denied:
        PolicyEngine().require(context, capability)

    assert denied.value.status_code == 403


def test_private_scope_can_access_health_only_with_matching_consent() -> None:
    context = RequestContext(
        fitcrew_user_id="user-1",
        scope=Scope.PRIVATE,
        purpose="private_coaching",
        consent_id="consent-1",
        consent_categories=frozenset({"blood_glucose"}),
    )

    PolicyEngine().require(context, ToolCapability.HEALTH, category="blood_glucose")

    with pytest.raises(PolicyDenied):
        PolicyEngine().require(context, ToolCapability.HEALTH, category="sleep")


@pytest.mark.parametrize("token", list(BehaviorToken))
def test_group_behavior_tokens_require_user_confirmation(token: BehaviorToken) -> None:
    with pytest.raises(PolicyDenied):
        PolicyEngine().render_group_token(token, confirmed=False)

    rendered = PolicyEngine().render_group_token(token, confirmed=True)
    assert rendered == token.message
