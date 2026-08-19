import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.schemas import CurrentSubject
from app.core.database import get_db
from app.models.audit import AuditEvent
from app.rbac.permissions import AUDIT_READ

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    event_type: str
    outcome: str
    subject_id: str | None
    correlation_id: str

    model_config = {"from_attributes": True}


@router.get("/events", response_model=list[AuditEventResponse])
def list_audit_events(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
    _current: CurrentSubject = Depends(require_permission(AUDIT_READ)),
) -> list[AuditEvent]:
    events: list[AuditEvent] = (
        db.query(AuditEvent)
        .order_by(AuditEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return events
