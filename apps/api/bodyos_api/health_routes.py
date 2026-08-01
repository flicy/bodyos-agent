from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bodyos_api.auth import DevicePrincipal, require_device
from bodyos_api.crypto import FieldCipher
from bodyos_api.db import get_session
from bodyos_api.health_service import (
    ConsentRequired,
    DeviceBindingRejected,
    HealthIngestionService,
)
from bodyos_api.models import DeviceBinding, HealthSample
from bodyos_api.runtime import get_field_cipher
from bodyos_api.schemas import HealthSyncBatchIn

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def sync_health(
    batch: HealthSyncBatchIn,
    principal: Annotated[DevicePrincipal, Depends(require_device)],
    session: Annotated[Session, Depends(get_session)],
    cipher: Annotated[FieldCipher, Depends(get_field_cipher)],
) -> dict[str, str | int | bool]:
    if str(batch.device_binding_id) != principal.device_binding_id:
        raise HTTPException(status_code=403, detail="device binding mismatch")
    try:
        result = HealthIngestionService(session, cipher).ingest(
            principal.fitcrew_user_id, batch
        )
    except ConsentRequired as error:
        raise HTTPException(status_code=403, detail="active consent required") from error
    except DeviceBindingRejected as error:
        raise HTTPException(status_code=403, detail="device binding rejected") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "batch_id": result.batch_id,
        "inserted_samples": result.inserted_samples,
        "replayed": result.replayed,
    }


@router.get("/status")
def health_status(
    principal: Annotated[DevicePrincipal, Depends(require_device)],
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, str | int | None]:
    binding = session.get(DeviceBinding, principal.device_binding_id)
    sample_count = session.scalar(
        select(func.count(HealthSample.id)).where(
            HealthSample.fitcrew_user_id == principal.fitcrew_user_id
        )
    )
    return {
        "device_binding_id": principal.device_binding_id,
        "sample_count": int(sample_count or 0),
        "last_sync_at": (
            binding.last_sync_at.isoformat() if binding and binding.last_sync_at else None
        ),
    }
