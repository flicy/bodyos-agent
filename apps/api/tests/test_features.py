from datetime import UTC, datetime, timedelta

import pytest
from bodyos_api.features import DecryptedSample, compute_daily_features


def test_daily_features_are_aggregates_without_raw_series() -> None:
    start = datetime(2026, 8, 1, tzinfo=UTC)
    samples = [
        DecryptedSample(
            kind="blood_glucose",
            start_at=start + timedelta(minutes=index * 5),
            end_at=start + timedelta(minutes=index * 5),
            value_mg_dl=value,
        )
        for index, value in enumerate([90.0, 100.0, 110.0])
    ]

    features = compute_daily_features(samples, expected_glucose_interval_minutes=5)

    assert features["glucose"]["count"] == 3
    assert features["glucose"]["mean_mg_dl"] == pytest.approx(100.0)
    assert features["glucose"]["stdev_mg_dl"] == pytest.approx(10.0)
    assert features["glucose"]["coefficient_of_variation"] == pytest.approx(0.1)
    assert features["data_quality"]["duplicate_count"] == 0
    assert "raw_values" not in features["glucose"]


def test_daily_features_count_duplicate_timestamps() -> None:
    instant = datetime(2026, 8, 1, tzinfo=UTC)
    samples = [
        DecryptedSample("blood_glucose", instant, instant, 90.0),
        DecryptedSample("blood_glucose", instant, instant, 90.0),
    ]

    features = compute_daily_features(samples)

    assert features["data_quality"]["duplicate_count"] == 1
