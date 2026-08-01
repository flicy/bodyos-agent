"""Hermes gateway hook: send raw input only to BodyOS and persist only its safe envelope."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


def _cache_path(session_id: str) -> Path:
    directory = Path(os.environ.get("BODYOS_SANITIZED_CACHE_DIR", "/tmp/bodyos-sanitized"))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    digest = hashlib.sha256(session_id.encode()).hexdigest()
    return directory / f"{digest}.json"


def _write_record(session_id: str, record: dict) -> None:
    path = _cache_path(session_id)
    descriptor, temporary = tempfile.mkstemp(prefix="bodyos-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def handle(_event_type: str, context: dict) -> None:
    session_id = str(context.get("session_id") or "")
    if not session_id:
        return
    api_base = os.environ.get("BODYOS_API_BASE", "").rstrip("/")
    token = os.environ.get("BODYOS_INTERNAL_TOKEN", "")
    if not api_base or not token:
        _write_record(session_id, {"mode": "unavailable"})
        return
    payload = {
        "provider": "feishu",
        "subject": str(context.get("user_id") or ""),
        "channel": "group" if context.get("chat_type") == "group" else "dm",
        "text": str(context.get("message") or ""),
    }
    request = urllib.request.Request(
        f"{api_base}/v1/bodyos/envelope",
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={
            "Content-Type": "application/json",
            "X-BodyOS-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            record = json.loads(response.read())
        if not isinstance(record, dict) or not isinstance(record.get("envelope"), dict):
            record = {"mode": "unavailable"}
    except (OSError, ValueError, TypeError, urllib.error.URLError):
        record = {"mode": "unavailable"}
    _write_record(session_id, record)
