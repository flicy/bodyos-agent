from functools import lru_cache

from bodyos_api.config import get_settings
from bodyos_api.crypto import FieldCipher
from bodyos_api.model_gateway import CodexCLIHarness, HermesCLIHarness, RoutedModelGateway


@lru_cache
def get_field_cipher() -> FieldCipher:
    encoded_key = get_settings().encryption_key.get_secret_value()
    if not encoded_key:
        raise RuntimeError("BODYOS_ENCRYPTION_KEY is required")
    return FieldCipher.from_base64(encoded_key)


@lru_cache
def get_model_gateway() -> RoutedModelGateway:
    settings = get_settings()
    return RoutedModelGateway(
        CodexCLIHarness(
            settings.codex_command,
            timeout_seconds=settings.model_timeout_seconds,
        ),
        HermesCLIHarness(
            settings.hermes_command,
            model=settings.hermes_model,
            timeout_seconds=settings.model_timeout_seconds,
        ),
    )
