import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from bodyos_api.auth import hash_device_token, require_owner
from bodyos_api.config import Settings, get_settings
from bodyos_api.crypto import FieldCipher
from bodyos_api.db import get_session
from bodyos_api.models import Consent, DeviceBinding, IdentityBinding, User
from bodyos_api.runtime import get_field_cipher
from bodyos_api.schemas import HealthKind

router = APIRouter(prefix="/v1/owner", tags=["owner"])


class OwnerBootstrapIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feishu_subject: str = Field(min_length=3, max_length=200)
    device_public_id: str = Field(min_length=3, max_length=128)
    categories: set[HealthKind] = Field(min_length=1)


class OwnerIdentityRebindIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feishu_subject: str = Field(min_length=3, max_length=200)
    device_public_id: str = Field(min_length=3, max_length=128)


def _subject_hash(subject: str, pepper: str) -> str:
    if not pepper:
        raise RuntimeError("BODYOS_IDENTITY_PEPPER is required")
    return hmac.new(pepper.encode(), subject.encode(), hashlib.sha256).hexdigest()


def _pairing_url(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    return f"fitcrew-health://configure?{urlencode({'payload': encoded})}"


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap_owner_device(
    request: OwnerBootstrapIn,
    _: Annotated[None, Depends(require_owner)],
    session: Annotated[Session, Depends(get_session)],
    cipher: Annotated[FieldCipher, Depends(get_field_cipher)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    subject_hash = _subject_hash(
        request.feishu_subject, settings.identity_pepper.get_secret_value()
    )
    identity = session.scalar(
        select(IdentityBinding).where(
            IdentityBinding.provider == "feishu",
            IdentityBinding.subject_hash == subject_hash,
            IdentityBinding.revoked_at.is_(None),
        )
    )
    if identity is None:
        user = User()
        session.add(user)
        session.flush()
        identity = IdentityBinding(
            fitcrew_user_id=user.fitcrew_user_id,
            provider="feishu",
            subject_hash=subject_hash,
            encrypted_subject=b"",
            verified_at=datetime.now(UTC),
        )
        session.add(identity)
        session.flush()
        encrypted_subject = cipher.encrypt_json(
            {"subject": request.feishu_subject}, aad=f"identity:{identity.id}"
        )
        identity.encrypted_subject = encrypted_subject.nonce + encrypted_subject.ciphertext
    user_id = identity.fitcrew_user_id

    device_token = secrets.token_urlsafe(32)
    binding = session.scalar(
        select(DeviceBinding).where(DeviceBinding.device_public_id == request.device_public_id)
    )
    if binding is None:
        binding = DeviceBinding(
            fitcrew_user_id=user_id,
            device_public_id=request.device_public_id,
            token_hash=hash_device_token(device_token),
        )
        session.add(binding)
        session.flush()
    elif binding.fitcrew_user_id == user_id:
        binding.token_hash = hash_device_token(device_token)
        binding.revoked_at = None
    else:
        raise ValueError("device public identifier is already bound")

    consent_ids: dict[str, str] = {}
    for category in sorted(request.categories, key=lambda item: item.value):
        consent = Consent(
            fitcrew_user_id=user_id,
            category=category.value,
            purpose="private_coaching",
            granted=True,
            receipt_version="owner-alpha.v1",
            granted_at=datetime.now(UTC),
        )
        session.add(consent)
        session.flush()
        consent_ids[category.value] = consent.id
    session.commit()

    pairing_payload = {
        "baseURL": settings.public_base_url,
        "deviceBindingID": binding.id,
        "consentIDs": consent_ids,
        "deviceToken": device_token,
    }
    return {
        "fitcrew_user_id": user_id,
        "device_binding_id": binding.id,
        "consent_ids": consent_ids,
        "device_token": device_token,
        "pairing_url": _pairing_url(pairing_payload),
    }


@router.post("/identity/rebind")
def rebind_owner_identity(
    request: OwnerIdentityRebindIn,
    _: Annotated[None, Depends(require_owner)],
    session: Annotated[Session, Depends(get_session)],
    cipher: Annotated[FieldCipher, Depends(get_field_cipher)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    device = session.scalar(
        select(DeviceBinding).where(
            DeviceBinding.device_public_id == request.device_public_id,
            DeviceBinding.revoked_at.is_(None),
        )
    )
    if device is None:
        raise HTTPException(status_code=404, detail="active owner device not found")

    now = datetime.now(UTC)
    subject_hash = _subject_hash(
        request.feishu_subject, settings.identity_pepper.get_secret_value()
    )
    current = session.scalar(
        select(IdentityBinding).where(
            IdentityBinding.provider == "feishu",
            IdentityBinding.subject_hash == subject_hash,
        )
    )
    if current is not None and current.fitcrew_user_id != device.fitcrew_user_id:
        raise HTTPException(status_code=409, detail="identity is bound to another owner")

    active_identities = session.scalars(
        select(IdentityBinding).where(
            IdentityBinding.provider == "feishu",
            IdentityBinding.fitcrew_user_id == device.fitcrew_user_id,
            IdentityBinding.revoked_at.is_(None),
        )
    ).all()
    changed = current is None or current.revoked_at is not None or any(
        identity.id != current.id for identity in active_identities if current is not None
    )

    for identity in active_identities:
        if current is None or identity.id != current.id:
            identity.revoked_at = now

    if current is None:
        current = IdentityBinding(
            fitcrew_user_id=device.fitcrew_user_id,
            provider="feishu",
            subject_hash=subject_hash,
            encrypted_subject=b"",
            verified_at=now,
        )
        session.add(current)
        session.flush()

    encrypted_subject = cipher.encrypt_json(
        {"subject": request.feishu_subject}, aad=f"identity:{current.id}"
    )
    current.encrypted_subject = encrypted_subject.nonce + encrypted_subject.ciphertext
    current.verified_at = now
    current.revoked_at = None
    session.commit()
    return {"changed": changed}
