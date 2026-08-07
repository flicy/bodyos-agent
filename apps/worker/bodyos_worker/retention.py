from datetime import UTC, datetime, timedelta

from bodyos_api.models import HealthSample
from sqlalchemy import delete
from sqlalchemy.orm import Session

RAW_RETENTION_DAYS = 30


def expire_raw_health(session: Session, *, now: datetime | None = None) -> int:
    current = now or datetime.now(UTC)
    cutoff = current - timedelta(days=RAW_RETENTION_DAYS)
    result = session.execute(delete(HealthSample).where(HealthSample.end_at < cutoff))
    session.commit()
    return int(result.rowcount or 0)
