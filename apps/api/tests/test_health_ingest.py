from datetime import UTC, datetime

import pytest
from bodyos_api.crypto import EncryptedValue, FieldCipher
from bodyos_api.health_service import (
    ConsentRequired,
    DeviceBindingRejected,
    HealthIngestionService,
)
from bodyos_api.models import Consent, DailyFeature, DeviceBinding, HealthSample, User
from bodyos_api.schemas import HealthSyncBatchIn
from sqlalchemy import select
from sqlalchemy.orm import Session

USER_ID = "11111111-1111-4111-8111-111111111111"
DEVICE_ID = "22222222-2222-4222-8222-222222222222"
CONSENT_ID = "33333333-3333-4333-8333-333333333333"
BATCH_ID = "44444444-4444-4444-8444-444444444444"
SAMPLE_ID = "55555555-5555-4555-8555-555555555555"


def seed_authorized_owner(session: Session, *, granted: bool = True) -> None:
    session.add(User(fitcrew_user_id=USER_ID))
    session.add(
        DeviceBinding(
            id=DEVICE_ID,
            fitcrew_user_id=USER_ID,
            device_public_id="owner-iphone",
            token_hash="hashed-token",
        )
    )
    session.add(
        Consent(
            id=CONSENT_ID,
            fitcrew_user_id=USER_ID,
            category="blood_glucose",
            purpose="private_coaching",
            granted=granted,
            receipt_version="v1",
            granted_at=datetime(2026, 8, 1, tzinfo=UTC) if granted else None,
        )
    )
    session.commit()


def glucose_batch(*, value: float = 5.6, unit: str = "mmol/L") -> HealthSyncBatchIn:
    return HealthSyncBatchIn.model_validate(
        {
            "batch_id": BATCH_ID,
            "device_binding_id": DEVICE_ID,
            "consent_id": CONSENT_ID,
            "source": "com.yuwell.anytime",
            "timezone": "Asia/Shanghai",
            "sent_at": "2026-08-01T12:00:00+08:00",
            "samples": [
                {
                    "sample_id": SAMPLE_ID,
                    "kind": "blood_glucose",
                    "start_at": "2026-08-01T11:55:00+08:00",
                    "end_at": "2026-08-01T11:55:00+08:00",
                    "value": value,
                    "unit": unit,
                    "source": "com.yuwell.anytime",
                }
            ],
        }
    )


def test_ingest_encrypts_value_and_normalizes_glucose_unit(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_authorized_owner(session)
    service = HealthIngestionService(session, field_cipher)

    result = service.ingest(USER_ID, glucose_batch())

    assert result.inserted_samples == 1
    assert result.replayed is False
    stored = session.scalar(select(HealthSample))
    assert stored is not None
    assert stored.original_unit == "mmol/L"
    assert stored.normalized_unit == "mg/dL"
    assert b"5.6" not in stored.value_ciphertext
    value = field_cipher.decrypt_json(
        EncryptedValue(stored.value_nonce, stored.value_ciphertext),
        aad=f"{USER_ID}:{SAMPLE_ID}",
    )
    assert value["value"] == pytest.approx(100.90192)

    daily = session.scalar(select(DailyFeature))
    assert daily is not None
    assert daily.feature_date == "2026-08-01"
    assert b"100.90192" not in daily.payload_ciphertext
    payload = field_cipher.decrypt_json(
        EncryptedValue(daily.payload_nonce, daily.payload_ciphertext),
        aad=f"feature:{USER_ID}:2026-08-01:daily.v1",
    )
    assert payload["glucose"]["mean_mg_dl"] == pytest.approx(100.90192)


def test_replaying_same_batch_is_idempotent(session: Session, field_cipher: FieldCipher) -> None:
    seed_authorized_owner(session)
    service = HealthIngestionService(session, field_cipher)

    first = service.ingest(USER_ID, glucose_batch())
    replay = service.ingest(USER_ID, glucose_batch())

    assert first.inserted_samples == 1
    assert replay.inserted_samples == 0
    assert replay.replayed is True
    assert len(session.scalars(select(HealthSample)).all()) == 1


def test_ingest_rejects_withdrawn_or_missing_consent(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_authorized_owner(session, granted=False)

    with pytest.raises(ConsentRequired):
        HealthIngestionService(session, field_cipher).ingest(USER_ID, glucose_batch())


def test_ingest_rejects_device_bound_to_another_user(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_authorized_owner(session)

    with pytest.raises(DeviceBindingRejected):
        HealthIngestionService(session, field_cipher).ingest(
            "99999999-9999-4999-8999-999999999999", glucose_batch()
        )
