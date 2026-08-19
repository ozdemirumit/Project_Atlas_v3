import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Investigation(Base):
    """A bounded investigation case (ATLAS-042 Root Cause Analysis).

    MVP-003 proves one end-to-end scenario: a SAN switch port/fabric
    failure with a zoning conflict (docs/002_Product_Requirements.md
    Section 10, resolved in Section 16). This is a versioned case, not a
    live/mutable status board: hypotheses, impact assessments, and
    recommendations are children of one investigation and are never
    deleted, only added to, so the case's evidence trail stays intact.
    """

    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")  # open | closed
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list["InvestigationEvent"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan", order_by="InvestigationEvent.occurred_at"
    )
    hypotheses: Mapped[list["RcaHypothesis"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    impact_assessments: Mapped[list["ChangeImpactAssessment"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )


class InvestigationEvent(Base):
    """One timeline entry (ATLAS-042: incident scope, timeline, evidence)."""

    __tablename__ = "investigation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_entities.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # manual | connector_health | audit

    investigation: Mapped[Investigation] = relationship(back_populates="events")


class RcaHypothesis(Base):
    """A root-cause hypothesis (ATLAS-042: hypothesis ledger, evidence, confidence).

    `generated_by` records how the hypothesis was produced. MVP-003 has no
    AI reasoning engine configured yet (ATLAS-041 is not implemented) so the
    only generator today is `rule_engine` — a deterministic, documented
    fault-family matcher (`app.decision.rca`) standing in for it. A human
    or a future AI generator are both first-class values of this field so
    the schema does not need to change when ATLAS-041 lands.
    """

    __tablename__ = "rca_hypotheses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    fault_family: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)  # low | medium | high
    supporting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    contradicting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="rule_engine")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    investigation: Mapped[Investigation] = relationship(back_populates="hypotheses")


class ChangeImpactAssessment(Base):
    """ATLAS-044: direct/transitive impact from one target entity.

    MVP must describe this as dependency and scenario analysis, not a
    validated digital twin (docs/002_Product_Requirements.md Section 10) —
    `affected_entity_ids` is a graph-reachability result, not a prediction.
    """

    __tablename__ = "change_impact_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_entities.id", ondelete="CASCADE"), nullable=False
    )
    affected_entity_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    graph_gaps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    investigation: Mapped[Investigation] = relationship(back_populates="impact_assessments")


class Recommendation(Base):
    """ATLAS-043: recommendation with evidence, risk, and recovery.

    Per AGENTS.md Section 7, every recommendation involving operational
    change must carry summary, risk, impact, duration, preconditions, and a
    rollback plan — the fields below are that fixed contract, not free text.
    """

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low | medium | high
    estimated_duration_minutes: Mapped[int] = mapped_column(nullable=False)
    preconditions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rollback_plan: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="rule_engine")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    investigation: Mapped[Investigation] = relationship(back_populates="recommendations")
