import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit.syslog_export import format_syslog
from app.auth.dependencies import require_permission
from app.auth.schemas import CurrentSubject
from app.core.database import get_db
from app.models.audit import AuditEvent
from app.rbac.permissions import AUDIT_READ, SIEM_EXPORT

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


@router.get("/events.syslog", response_class=PlainTextResponse)
def export_audit_events_syslog(
    db: Session = Depends(get_db),
    limit: int = Query(default=200, le=1000),
    _current: CurrentSubject = Depends(require_permission(SIEM_EXPORT)),
) -> str:
    """ATLAS-034/035: one RFC 5424 line per event, newest last.

    No SIEM product is selected yet (open question). This is the export
    format a collector would tail or scrape; `app.audit.syslog_export.
    send_udp` performs the equivalent push once ATLAS_SYSLOG_HOST is set.
    """
    events: list[AuditEvent] = (
        db.query(AuditEvent).order_by(AuditEvent.occurred_at.asc()).limit(limit).all()
    )
    return "\n".join(format_syslog(event) for event in events)
