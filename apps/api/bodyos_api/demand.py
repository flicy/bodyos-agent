from sqlalchemy.orm import Session

from bodyos_api.crypto import EncryptedValue, FieldCipher
from bodyos_api.models import DemandItem


class InvalidDemandTransition(ValueError):
    pass


_TRANSITIONS = {
    "new": {"clustered", "declined"},
    "clustered": {"validated", "declined"},
    "validated": {"planned", "declined"},
    "planned": {"shipped", "declined"},
    "shipped": {"measured"},
    "declined": set(),
    "measured": set(),
}


class DemandService:
    def __init__(self, session: Session, cipher: FieldCipher):
        self._session = session
        self._cipher = cipher

    def capture(
        self, *, fitcrew_user_id: str | None, source_type: str, description: str
    ) -> DemandItem:
        item = DemandItem(
            fitcrew_user_id=fitcrew_user_id,
            source_type=source_type,
            state="new",
            description_nonce=b"",
            description_ciphertext=b"",
        )
        self._session.add(item)
        self._session.flush()
        encrypted = self._cipher.encrypt_json({"description": description}, aad=f"demand:{item.id}")
        item.description_nonce = encrypted.nonce
        item.description_ciphertext = encrypted.ciphertext
        self._session.commit()
        return item

    def transition(self, demand_id: str, state: str, *, rationale: str) -> DemandItem:
        item = self._session.get(DemandItem, demand_id)
        if item is None:
            raise ValueError("demand item not found")
        if state not in _TRANSITIONS.get(item.state, set()):
            raise InvalidDemandTransition(f"cannot transition demand from {item.state} to {state}")
        item.state = state
        item.decision_rationale = rationale
        self._session.commit()
        return item

    def read_description(self, fitcrew_user_id: str, demand_id: str) -> str:
        item = self._session.get(DemandItem, demand_id)
        if item is None or item.fitcrew_user_id != fitcrew_user_id:
            raise PermissionError("demand item is unavailable for this user")
        return self._cipher.decrypt_json(
            EncryptedValue(item.description_nonce, item.description_ciphertext),
            aad=f"demand:{item.id}",
        )["description"]
