import hashlib
import hmac
import json
import time
import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from bodyos_api.auth import require_internal, require_model_proxy
from bodyos_api.bodyos import BodyOSService, classify_group_token
from bodyos_api.config import Settings, get_settings
from bodyos_api.crypto import FieldCipher
from bodyos_api.db import get_session
from bodyos_api.model_gateway import HarnessFailure, validate_model_envelope
from bodyos_api.models import IdentityBinding
from bodyos_api.policy import BehaviorToken
from bodyos_api.runtime import get_field_cipher, get_model_gateway

router = APIRouter(tags=["bodyos"])


class EnvelopeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["feishu"]
    subject: str = Field(min_length=3, max_length=200)
    channel: Literal["dm", "group"]
    text: str = Field(min_length=1, max_length=4_000)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model: str = "bodyos-codex"
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    stream: bool = False


def _identity_user(session: Session, request: EnvelopeRequest, settings: Settings) -> str:
    pepper = settings.identity_pepper.get_secret_value()
    if not pepper:
        raise HTTPException(status_code=503, detail="identity mapping unavailable")
    subject_hash = hmac.new(
        pepper.encode(), request.subject.encode(), hashlib.sha256
    ).hexdigest()
    identity = session.scalar(
        select(IdentityBinding).where(
            IdentityBinding.provider == request.provider,
            IdentityBinding.subject_hash == subject_hash,
            IdentityBinding.revoked_at.is_(None),
        )
    )
    if identity is None:
        raise HTTPException(status_code=403, detail="identity is not bound")
    return identity.fitcrew_user_id


@router.post("/v1/bodyos/envelope")
def create_bodyos_envelope(
    request: EnvelopeRequest,
    _: Annotated[None, Depends(require_internal)],
    session: Annotated[Session, Depends(get_session)],
    cipher: Annotated[FieldCipher, Depends(get_field_cipher)],
    settings: Annotated[Settings, Depends(get_settings)],
    gateway: Annotated[Any, Depends(get_model_gateway)],
) -> dict:
    if request.channel == "group":
        token = classify_group_token(request.text)
        return {
            "mode": "deterministic",
            "reply": token.message,
            "envelope": {
                "schema_version": "bodyos-group.v1",
                "channel": "group",
                "behavior_token": token.value,
            },
        }
    user_id = _identity_user(session, request, settings)
    envelope = BodyOSService(session, cipher, gateway).build_envelope(user_id, request.text)
    return {"mode": "model", "envelope": envelope}


def _extract_envelope(request: ChatCompletionRequest) -> dict:
    prefix = "BODYOS_SANITIZED_ENVELOPE="
    content = request.messages[-1].content
    if not content.startswith(prefix):
        raise HTTPException(status_code=403, detail="sanitized envelope required")
    try:
        envelope = json.loads(content[len(prefix) :])
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=403, detail="invalid sanitized envelope") from error
    if not isinstance(envelope, dict):
        raise HTTPException(status_code=403, detail="invalid sanitized envelope")
    return envelope


@router.post("/v1/chat/completions")
def chat_completions(
    request: ChatCompletionRequest,
    _: Annotated[None, Depends(require_model_proxy)],
    gateway: Annotated[Any, Depends(get_model_gateway)],
) -> dict:
    if request.stream:
        raise HTTPException(status_code=422, detail="streaming is disabled for BodyOS")
    envelope = _extract_envelope(request)
    if envelope.get("schema_version") == "bodyos-group.v1":
        try:
            token = BehaviorToken(envelope.get("behavior_token"))
        except (TypeError, ValueError) as error:
            raise HTTPException(status_code=403, detail="invalid group token") from error
        if envelope != {
            "schema_version": "bodyos-group.v1",
            "channel": "group",
            "behavior_token": token.value,
        }:
            raise HTTPException(status_code=403, detail="invalid group token")
        text = token.message
        route = "deterministic"
    else:
        try:
            validate_model_envelope(envelope)
            result = gateway.respond(envelope)
        except (HarnessFailure, ValueError) as error:
            raise HTTPException(status_code=503, detail="private coaching unavailable") from error
        text = result.text
        route = result.route
    return {
        "id": f"bodyos-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "bodyos_route": route,
    }
