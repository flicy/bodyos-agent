from datetime import UTC, datetime

from bodyos_api.crypto import FieldCipher
from bodyos_api.health_service import HealthIngestionService
from bodyos_api.models import Consent, DeviceBinding, User
from bodyos_api.schemas import HealthSyncBatchIn
from sqlalchemy.orm import Session


def seed(session: Session) -> tuple[str, str, str]:
    user_id = "11111111-1111-4111-8111-111111111111"
    device_id = "22222222-2222-4222-8222-222222222222"
    consent_id = "33333333-3333-4333-8333-333333333333"
    session.add(User(fitcrew_user_id=user_id))
    session.add(
        DeviceBinding(
            id=device_id,
            fitcrew_user_id=user_id,
            device_public_id="owner-iphone",
            token_hash="hash",
        )
    )
    session.add(
        Consent(
            id=consent_id,
            fitcrew_user_id=user_id,
            category="blood_glucose",
            purpose="private_coaching",
            granted=True,
            receipt_version="v1",
            granted_at=datetime(2026, 8, 1, tzinfo=UTC),
        )
    )
    session.commit()
    return user_id, device_id, consent_id


def batch(device_id: str, consent_id: str) -> HealthSyncBatchIn:
    return HealthSyncBatchIn.model_validate(
        {
            "batch_id": "44444444-4444-4444-8444-444444444444",
            "device_binding_id": device_id,
            "consent_id": consent_id,
            "source": "com.yuwell.anytime",
            "timezone": "Asia/Shanghai",
            "sent_at": "2026-08-01T12:00:00+08:00",
            "samples": [
                {
                    "sample_id": "55555555-5555-4555-8555-555555555555",
                    "kind": "blood_glucose",
                    "start_at": "2026-08-01T11:55:00+08:00",
                    "end_at": "2026-08-01T11:55:00+08:00",
                    "value": 100,
                    "unit": "mg/dL",
                    "source": "com.yuwell.anytime",
                }
            ],
        }
    )


def test_export_is_readable_and_deletion_removes_health_derivatives(
    session: Session, field_cipher: FieldCipher
) -> None:
    user_id, device_id, consent_id = seed(session)
    service = HealthIngestionService(session, field_cipher)
    service.ingest(user_id, batch(device_id, consent_id))

    exported = service.export_user_health(user_id)
    deleted = service.delete_user_health(user_id)

    assert exported["samples"][0]["value"] == 100
    assert exported["samples"][0]["source"] == "com.yuwell.anytime"
    assert deleted["health_samples"] == 1
    assert service.export_user_health(user_id)["samples"] == []


def test_withdrawal_stops_future_ingestion(session: Session, field_cipher: FieldCipher) -> None:
    user_id, device_id, consent_id = seed(session)
    service = HealthIngestionService(session, field_cipher)

    service.withdraw_consent(user_id, consent_id, at=datetime(2026, 8, 1, 1, tzinfo=UTC))

    try:
        service.ingest(user_id, batch(device_id, consent_id))
    except Exception as error:
        assert error.__class__.__name__ == "ConsentRequired"
    else:
        raise AssertionError("withdrawn consent unexpectedly allowed ingestion")
