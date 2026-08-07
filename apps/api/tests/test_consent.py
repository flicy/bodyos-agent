from datetime import UTC, datetime

from bodyos_api.consent import ConsentGrant


def test_consent_is_bound_to_category_and_purpose() -> None:
    consent = ConsentGrant(
        consent_id="consent-1",
        fitcrew_user_id="user-1",
        category="blood_glucose",
        purpose="private_coaching",
        granted_at=datetime(2026, 8, 1, tzinfo=UTC),
    )

    assert consent.allows("user-1", "blood_glucose", "private_coaching") is True
    assert consent.allows("user-1", "sleep", "private_coaching") is False
    assert consent.allows("user-1", "blood_glucose", "group_sharing") is False
    assert consent.allows("user-2", "blood_glucose", "private_coaching") is False


def test_withdrawal_stops_processing_immediately() -> None:
    consent = ConsentGrant(
        consent_id="consent-1",
        fitcrew_user_id="user-1",
        category="blood_glucose",
        purpose="private_coaching",
        granted_at=datetime(2026, 8, 1, tzinfo=UTC),
    )

    withdrawn = consent.withdraw(datetime(2026, 8, 1, 1, tzinfo=UTC))

    assert withdrawn.allows("user-1", "blood_glucose", "private_coaching") is False
    assert withdrawn.withdrawn_at == datetime(2026, 8, 1, 1, tzinfo=UTC)
