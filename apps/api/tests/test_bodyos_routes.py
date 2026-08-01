import hashlib
import hmac

from bodyos_api.app import create_app
from bodyos_api.config import Settings, get_settings
from bodyos_api.crypto import FieldCipher
from bodyos_api.db import get_session
from bodyos_api.models import IdentityBinding, User
from bodyos_api.runtime import get_field_cipher, get_model_gateway
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

USER_ID = "11111111-1111-4111-8111-111111111111"
SUBJECT = "ou_private_owner"


class RecordingGateway:
    def __init__(self):
        self.envelopes: list[dict] = []

    def respond(self, envelope: dict):
        self.envelopes.append(envelope)
        return type("Reply", (), {"text": "安全建议", "route": "codex"})()


def client_for(session: Session, cipher: FieldCipher, gateway: RecordingGateway) -> TestClient:
    settings = Settings(
        internal_token="bodyos-internal-secret",
        model_proxy_token="model-proxy-secret",
        identity_pepper="identity-pepper",
    )
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_field_cipher] = lambda: cipher
    app.dependency_overrides[get_model_gateway] = lambda: gateway
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def seed_identity(session: Session, cipher: FieldCipher) -> None:
    session.add(User(fitcrew_user_id=USER_ID))
    subject_hash = hmac.new(
        b"identity-pepper", SUBJECT.encode(), hashlib.sha256
    ).hexdigest()
    encrypted = cipher.encrypt_json({"subject": SUBJECT}, aad="identity:binding-1")
    session.add(
        IdentityBinding(
            id="binding-1",
            fitcrew_user_id=USER_ID,
            provider="feishu",
            subject_hash=subject_hash,
            encrypted_subject=encrypted.nonce + encrypted.ciphertext,
        )
    )
    session.commit()


def test_envelope_endpoint_maps_feishu_identity_but_returns_no_identifier_or_raw_text(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_identity(session, field_cipher)
    raw_text = "我的鱼跃血糖是 10.2，我该怎么办？"

    response = client_for(session, field_cipher, RecordingGateway()).post(
        "/v1/bodyos/envelope",
        headers={"X-BodyOS-Token": "bodyos-internal-secret"},
        json={"provider": "feishu", "subject": SUBJECT, "channel": "dm", "text": raw_text},
    )

    assert response.status_code == 200
    rendered = response.text
    assert response.json()["mode"] == "model"
    assert response.json()["envelope"]["intent"] == "glucose_coaching"
    assert SUBJECT not in rendered
    assert USER_ID not in rendered
    assert raw_text not in rendered
    assert "10.2" not in rendered


def test_group_envelope_is_a_fixed_token_and_never_calls_gateway(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_identity(session, field_cipher)
    gateway = RecordingGateway()

    response = client_for(session, field_cipher, gateway).post(
        "/v1/bodyos/envelope",
        headers={"X-BodyOS-Token": "bodyos-internal-secret"},
        json={"provider": "feishu", "subject": SUBJECT, "channel": "group", "text": "血糖 10.2"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "mode": "deterministic",
        "reply": "个性化健康建议请私聊 BodyOS。",
        "envelope": {
            "schema_version": "bodyos-group.v1",
            "channel": "group",
            "behavior_token": "private_coaching",
        },
    }
    assert gateway.envelopes == []


def test_openai_compatible_proxy_routes_only_sanitized_dm_envelope(
    session: Session, field_cipher: FieldCipher
) -> None:
    gateway = RecordingGateway()
    envelope = {
        "schema_version": "bodyos-model.v1",
        "intent": "glucose_coaching",
        "channel": "dm",
        "features": {"status": "insufficient_data"},
        "knowledge": [],
        "constraints": ["not_medical_diagnosis"],
    }
    import json

    response = client_for(session, field_cipher, gateway).post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer model-proxy-secret"},
        json={
            "model": "bodyos-codex",
            "messages": [
                {
                    "role": "user",
                    "content": "BODYOS_SANITIZED_ENVELOPE=" + json.dumps(envelope),
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "安全建议"
    assert gateway.envelopes == [envelope]


def test_proxy_rejects_raw_chat_even_with_valid_proxy_token(
    session: Session, field_cipher: FieldCipher
) -> None:
    gateway = RecordingGateway()
    response = client_for(session, field_cipher, gateway).post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer model-proxy-secret"},
        json={"model": "bodyos-codex", "messages": [{"role": "user", "content": "血糖10.2"}]},
    )

    assert response.status_code == 403
    assert gateway.envelopes == []
