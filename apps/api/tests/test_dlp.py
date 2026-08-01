import pytest
from bodyos_api.dlp import SensitiveOutput, assert_group_safe
from bodyos_api.policy import BehaviorToken


@pytest.mark.parametrize(
    "text",
    [
        "我的血糖是 5.6 mmol/L",
        "昨晚睡了 6.5 小时",
        "HRV 42 ms",
        "体重 68 kg",
        "正在使用二甲双胍",
        "open_id 是 ou_abcdef123456",
        "今天走了 8500 步",
    ],
)
def test_group_dlp_rejects_health_and_raw_behavior_details(text: str) -> None:
    with pytest.raises(SensitiveOutput):
        assert_group_safe(text)


@pytest.mark.parametrize("token", list(BehaviorToken))
def test_group_dlp_allows_only_canonical_behavior_messages(token: BehaviorToken) -> None:
    assert assert_group_safe(token.message) == token.message
