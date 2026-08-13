import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    """Append-only audit record.

    ATLAS-032 governs the canonical audit contract; this table is the MVP
    durable store for it. Rows are never updated or deleted by application
    code. `detail` must never contain passwords, tokens, or secret values —
    see `app.audit.service.record_event`, which is the only writer.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # success | failure | denied

    subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    detail: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
