#!/usr/bin/env python3
"""Fail CI when XcodeGen strips FitCrew's HealthKit configuration."""

from __future__ import annotations

import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "apps" / "ios-bridge" / "FitCrewHealthBridge"


def load_plist(path: Path) -> dict:
    with path.open("rb") as handle:
        return plistlib.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    info = load_plist(BRIDGE / "Info.plist")
    entitlements = load_plist(BRIDGE / "FitCrewHealthBridge.entitlements")

    require(
        bool(info.get("NSHealthShareUsageDescription")),
        "generated Info.plist is missing NSHealthShareUsageDescription",
    )
    require(
        "processing" in info.get("UIBackgroundModes", []),
        "generated Info.plist is missing background processing mode",
    )
    require(
        "com.fitcrew.healthbridge.daily-sync"
        in info.get("BGTaskSchedulerPermittedIdentifiers", []),
        "generated Info.plist is missing the daily sync task identifier",
    )
    url_schemes = {
        scheme
        for item in info.get("CFBundleURLTypes", [])
        for scheme in item.get("CFBundleURLSchemes", [])
    }
    require(
        "fitcrew-health" in url_schemes,
        "generated Info.plist is missing the private pairing URL scheme",
    )
    require(
        entitlements.get("com.apple.developer.healthkit") is True,
        "generated entitlements are missing HealthKit",
    )

    print("Generated iOS configuration preserves HealthKit and pairing metadata.")


if __name__ == "__main__":
    main()
