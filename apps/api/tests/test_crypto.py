import base64

import pytest
from bodyos_api.crypto import FieldCipher
from cryptography.exceptions import InvalidTag


def encryption_key() -> str:
    return base64.urlsafe_b64encode(bytes(range(32))).decode()


def test_field_cipher_round_trips_json_with_aad() -> None:
    cipher = FieldCipher.from_base64(encryption_key())

    encrypted = cipher.encrypt_json({"value": 5.6, "unit": "mmol/L"}, aad="user-1:sample-1")

    assert encrypted.ciphertext != b'{"value": 5.6, "unit": "mmol/L"}'
    assert cipher.decrypt_json(encrypted, aad="user-1:sample-1") == {
        "unit": "mmol/L",
        "value": 5.6,
    }


def test_field_cipher_rejects_wrong_owner_context() -> None:
    cipher = FieldCipher.from_base64(encryption_key())
    encrypted = cipher.encrypt_json({"value": 5.6}, aad="user-1:sample-1")

    with pytest.raises(InvalidTag):
        cipher.decrypt_json(encrypted, aad="user-2:sample-1")


def test_field_cipher_requires_256_bit_key() -> None:
    short_key = base64.urlsafe_b64encode(b"too-short").decode()

    with pytest.raises(ValueError, match="32 bytes"):
        FieldCipher.from_base64(short_key)
