from dataclasses import dataclass
from datetime import datetime
from statistics import mean, stdev
from typing import Any


@dataclass(frozen=True, slots=True)
class DecryptedSample:
    kind: str
    start_at: datetime
    end_at: datetime
    value_mg_dl: float


def compute_daily_features(
    samples: list[DecryptedSample], *, expected_glucose_interval_minutes: int = 5
) -> dict[str, Any]:
    glucose_samples = [sample for sample in samples if sample.kind == "blood_glucose"]
    seen: set[tuple[str, datetime, float]] = set()
    duplicate_count = 0
    unique_glucose: list[DecryptedSample] = []
    for sample in glucose_samples:
        key = (sample.kind, sample.start_at, sample.value_mg_dl)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        unique_glucose.append(sample)

    values = [sample.value_mg_dl for sample in unique_glucose]
    expected_points = max(1, (24 * 60) // expected_glucose_interval_minutes)
    glucose: dict[str, float | int | None] = {
        "count": len(values),
        "mean_mg_dl": mean(values) if values else None,
        "min_mg_dl": min(values) if values else None,
        "max_mg_dl": max(values) if values else None,
        "stdev_mg_dl": stdev(values) if len(values) > 1 else 0.0 if values else None,
        "coefficient_of_variation": None,
    }
    if values and glucose["mean_mg_dl"]:
        glucose["coefficient_of_variation"] = float(glucose["stdev_mg_dl"] or 0.0) / float(
            glucose["mean_mg_dl"]
        )

    return {
        "algorithm_version": "features.v1",
        "glucose": glucose,
        "data_quality": {
            "duplicate_count": duplicate_count,
            "expected_glucose_points": expected_points,
            "glucose_completeness": min(1.0, len(values) / expected_points),
        },
    }
