import pytest
from bodyos_api.crypto import FieldCipher
from bodyos_api.demand import DemandService, InvalidDemandTransition
from bodyos_api.models import User
from sqlalchemy.orm import Session

OWNER = "11111111-1111-4111-8111-111111111111"


def test_demand_follows_reviewed_state_machine(session: Session, field_cipher: FieldCipher) -> None:
    session.add(User(fitcrew_user_id=OWNER))
    session.commit()
    service = DemandService(session, field_cipher)

    demand = service.capture(
        fitcrew_user_id=OWNER,
        source_type="feishu_dm",
        description="希望支持非 Apple 设备",
    )
    service.transition(demand.id, "clustered", rationale="归入设备接入主题")
    service.transition(demand.id, "validated", rationale="多次出现并已核验")
    service.transition(demand.id, "planned", rationale="进入后续连接器计划")

    assert demand.state == "planned"
    assert service.read_description(OWNER, demand.id) == "希望支持非 Apple 设备"


def test_demand_cannot_skip_validation(session: Session, field_cipher: FieldCipher) -> None:
    session.add(User(fitcrew_user_id=OWNER))
    session.commit()
    service = DemandService(session, field_cipher)
    demand = service.capture(
        fitcrew_user_id=OWNER,
        source_type="feishu_group",
        description="想要一个新功能",
    )

    with pytest.raises(InvalidDemandTransition):
        service.transition(demand.id, "shipped", rationale="不能直接发布")


def test_demand_description_is_owner_only(session: Session, field_cipher: FieldCipher) -> None:
    session.add(User(fitcrew_user_id=OWNER))
    session.commit()
    service = DemandService(session, field_cipher)
    demand = service.capture(
        fitcrew_user_id=OWNER,
        source_type="feishu_dm",
        description="私人需求",
    )

    with pytest.raises(PermissionError):
        service.read_description("other-user", demand.id)
