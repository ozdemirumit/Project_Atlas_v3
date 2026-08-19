import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.investigation import Recommendation


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RecommendationApproval(Base):
    """ATLAS-037: an exact human approval decision on one recommendation.

    Recommendations never execute anything by themselves (no connector in
    this codebase can write to infrastructure) — this table exists to
    demonstrate the approval gate itself, per MVP-004's "exact human
    approval flow demonstrated without AI execution." `approver_subject_id`
    must differ from the investigation's `created_by` (separation of
    duties, enforced in `app.api.routes.investigations`), and a
    `generated_by=rule_engine` recommendation can never approve itself.
    """

    __tablename__ = "recommendation_approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False
    )
    approver_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # approved | rejected
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    recommendation: Mapped[Recommendation] = relationship()
