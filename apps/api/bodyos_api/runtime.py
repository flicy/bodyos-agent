from functools import lru_cache

from bodyos_api.config import get_settings
from bodyos_api.crypto import FieldCipher


@lru_cache
def get_field_cipher() -> FieldCipher:
    encoded_key = get_settings().encryption_key.get_secret_value()
    if not encoded_key:
        raise RuntimeError("BODYOS_ENCRYPTION_KEY is required")
    return FieldCipher.from_base64(encoded_key)
