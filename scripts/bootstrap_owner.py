#!/usr/bin/env python3
"""Create owner identity, consent, and a one-time private iOS pairing artifact."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import qrcode

CATEGORIES = [
    "blood_glucose",
    "sleep_asleep",
    "sleep_core",
    "sleep_deep",
    "sleep_rem",
    "heart_rate_variability",
    "resting_heart_rate",
    "workout",
    "active_energy",
    "step_count",
    "stand_hours",
    "activity_summary",
]


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"required environment variable is missing: {name}")
    return value


def main() -> None:
    owner_token = required("BODYOS_OWNER_TOKEN")
    subject = required("FEISHU_ALLOWED_USERS").split(",", maxsplit=1)[0]
    request = Request(
        "http://127.0.0.1:8000/v1/owner/bootstrap",
        data=json.dumps(
            {
                "feishu_subject": subject,
                "device_public_id": "owner-iphone-healthkit",
                "categories": CATEGORIES,
            }
        ).encode(),
        headers={"Content-Type": "application/json", "X-Owner-Token": owner_token},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed loopback URL
        payload = json.load(response)
    output_dir = Path("/owner-runtime")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    record = output_dir / "owner-bootstrap.json"
    record.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(record, 0o600)
    pairing = qrcode.make(payload["pairing_url"])
    qr_path = output_dir / "owner-pairing.png"
    pairing.save(qr_path)
    os.chmod(qr_path, 0o600)
    print("Owner bootstrap completed; private JSON and pairing QR stored outside Git.")


if __name__ == "__main__":
    main()
