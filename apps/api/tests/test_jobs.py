from datetime import UTC, date, datetime

from bodyos_api.jobs import run_once
from bodyos_api.models import DailyFeature, OutboxEvent, User
from sqlalchemy import func, select
from sqlalchemy.orm import Session

OWNER = "11111111-1111-4111-8111-111111111111"


def test_maintenance_enforces_aggregate_retention_and_idempotent_day16_event(
    session: Session,
) -> None:
    session.add(User(fitcrew_user_id=OWNER))
    session.add(
        DailyFeature(
            fitcrew_user_id=OWNER,
            feature_date="2025-06-30",
            feature_set="daily.v1",
            payload_nonce=b"nonce",
            payload_ciphertext=b"ciphertext",
            quality_status="partial",
            algorithm_version="features.v1",
        )
    )
    session.commit()
    now = datetime(2026, 8, 1, 8, tzinfo=UTC)

    first = run_once(session, now=now, study_start=date(2026, 7, 17))
    second = run_once(session, now=now, study_start=date(2026, 7, 17))

    assert first == {"raw_deleted": 0, "aggregates_deleted": 1, "checkpoint_events": 1}
    assert second == {"raw_deleted": 0, "aggregates_deleted": 0, "checkpoint_events": 0}
    event = session.scalar(select(OutboxEvent))
    assert event is not None
    assert event.destination == "ios_bridge"
    assert event.event_type == "owner_study_day_16_full_reconciliation"
    assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
