import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConnectorHealthCheck(Base):
    """One scheduled health-check result for a connector instance.

    `docs/002_Product_Requirements.md` MVP-002 requires "one scheduled
    health check." This table records each run; `app.scheduler.health`
    performs them on an interval.
    """

    __tablename__ = "connector_health_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connector_instances.id", ondelete="CASCADE"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # healthy | unhealthy
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
