from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConsentGrant:
    consent_id: str
    fitcrew_user_id: str
    category: str
    purpose: str
    granted_at: datetime
    withdrawn_at: datetime | None = None

    def allows(self, fitcrew_user_id: str, category: str, purpose: str) -> bool:
        return (
            self.withdrawn_at is None
            and self.fitcrew_user_id == fitcrew_user_id
            and self.category == category
            and self.purpose == purpose
        )

    def withdraw(self, withdrawn_at: datetime) -> "ConsentGrant":
        return replace(self, withdrawn_at=withdrawn_at)
