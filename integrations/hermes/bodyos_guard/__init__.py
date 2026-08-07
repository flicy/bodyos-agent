"""Hermes middleware that replaces the complete LLM request with a safe envelope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def rewrite_llm_request(request: dict, sanitized_envelope: dict | None) -> dict:
    rewritten = {key: value for key, value in request.items() if key not in {"messages", "input"}}
    if sanitized_envelope is None:
        content = (
            "BODYOS_CONTEXT_UNAVAILABLE: reply that private coaching is temporarily "
            "unavailable."
        )
    else:
        content = "BODYOS_SANITIZED_ENVELOPE=" + json.dumps(
            sanitized_envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    rewritten["messages"] = [
        {
            "role": "system",
            "content": (
                "You are BodyOS. Use only the sanitized envelope. Never request or infer raw "
                "health data, identity, or other conversation history."
            ),
        },
        {"role": "user", "content": content},
    ]
    return {
        "request": rewritten,
        "plugin": "bodyos_guard",
        "decision": "rewrite",
    }


def cache_path(session_id: str) -> Path:
    directory = Path(os.environ.get("BODYOS_SANITIZED_CACHE_DIR", "/tmp/bodyos-sanitized"))
    digest = hashlib.sha256(session_id.encode()).hexdigest()
    return directory / f"{digest}.json"


def _load_envelope(session_id: str) -> dict | None:
    if not session_id:
        return None
    try:
        record = json.loads(cache_path(session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    envelope = record.get("envelope") if isinstance(record, dict) else None
    return envelope if isinstance(envelope, dict) else None


def _middleware(**kwargs):
    request = kwargs.get("request") or {}
    envelope = _load_envelope(str(kwargs.get("session_id") or ""))
    return rewrite_llm_request(request, envelope)


def register(ctx) -> None:
    ctx.register_middleware("llm_request", _middleware)
