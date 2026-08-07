import base64
import json
import os
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True, slots=True)
class EncryptedValue:
    nonce: bytes
    ciphertext: bytes


class FieldCipher:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("field encryption key must be exactly 32 bytes")
        self._cipher = AESGCM(key)

    @classmethod
    def from_base64(cls, encoded_key: str) -> "FieldCipher":
        try:
            key = base64.urlsafe_b64decode(encoded_key.encode())
        except (ValueError, TypeError) as exc:
            raise ValueError("field encryption key must be URL-safe base64") from exc
        return cls(key)

    def encrypt_json(self, value: Any, *, aad: str) -> EncryptedValue:
        nonce = os.urandom(12)
        plaintext = json.dumps(
            value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
        ciphertext = self._cipher.encrypt(nonce, plaintext, aad.encode())
        return EncryptedValue(nonce=nonce, ciphertext=ciphertext)

    def decrypt_json(self, value: EncryptedValue, *, aad: str) -> Any:
        plaintext = self._cipher.decrypt(value.nonce, value.ciphertext, aad.encode())
        return json.loads(plaintext)
