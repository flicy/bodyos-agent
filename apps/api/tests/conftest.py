import base64

import pytest
from bodyos_api.crypto import FieldCipher
from bodyos_api.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database_session:
        yield database_session


@pytest.fixture
def field_cipher() -> FieldCipher:
    key = base64.urlsafe_b64encode(bytes(range(32))).decode()
    return FieldCipher.from_base64(key)
