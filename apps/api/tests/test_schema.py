import json
from pathlib import Path

import jsonschema
import pytest

CONTRACT = Path("packages/contracts/health-sync-v1.schema.json")


def valid_batch() -> dict:
    return {
        "schema_version": "health-sync.v1",
        "batch_id": "11111111-1111-4111-8111-111111111111",
        "device_binding_id": "22222222-2222-4222-8222-222222222222",
        "consent_id": "33333333-3333-4333-8333-333333333333",
        "source": "com.yuwell.anytime",
        "timezone": "Asia/Shanghai",
        "sent_at": "2026-08-01T12:00:00+08:00",
        "samples": [
            {
                "sample_id": "44444444-4444-4444-8444-444444444444",
                "kind": "blood_glucose",
                "start_at": "2026-08-01T11:55:00+08:00",
                "end_at": "2026-08-01T11:55:00+08:00",
                "value": 5.6,
                "unit": "mmol/L",
                "source": "com.yuwell.anytime",
            }
        ],
    }


def test_health_sync_contract_accepts_complete_batch() -> None:
    schema = json.loads(CONTRACT.read_text())

    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(
        valid_batch()
    )


def test_health_sync_contract_rejects_unknown_health_kind() -> None:
    schema = json.loads(CONTRACT.read_text())
    batch = valid_batch()
    batch["samples"][0]["kind"] = "precise_location"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(batch)


def test_health_sync_contract_rejects_unexpected_identity_field() -> None:
    schema = json.loads(CONTRACT.read_text())
    batch = valid_batch()
    batch["feishu_open_id"] = "ou_private"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(batch)
