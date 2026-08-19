import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConnectorInstance(Base):
    """ATLAS-020: a configured, running connector.

    This is an intentionally simplified MVP-002 slice of the full governed
    connector lifecycle in ADR-028 through ADR-041 (registration, package
    installation, instance creation, target/credential binding, capability
    governance, runtime trust, and invocation authorization as separate
    human-gated steps). Those contracts remain the target model for
    production connectors; this table exists so MVP-002 can prove one real
    end-to-end discovery → inventory slice without first building the full
    fourteen-step approval chain.
    """

    __tablename__ = "connector_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    vendor: Mapped[str] = mapped_column(String(100), nullable=False)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "san_fabric"
    target_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class InventoryEntity(Base):
    """A normalized inventory record produced by reconciling one connector's
    discovery output. ATLAS-026 Section 7 lists `switch`, `port`, `zone`,
    `fabric` among the initial entity types this maps onto.
    """

    __tablename__ = "inventory_entities"
    __table_args__ = (
        UniqueConstraint("connector_instance_id", "external_id", name="uq_inventory_entity_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connector_instances.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class InventoryRelationship(Base):
    """A directed edge between two inventory entities.

    ATLAS-026 Section 8 relationship types include `managed_by`,
    `connected_to`, and `provides_path_to`; this MVP slice implements
    `managed_by` (port → switch) and `connected_to` (port → zone).
    """

    __tablename__ = "inventory_relationships"
    __table_args__ = (
        UniqueConstraint(
            "from_entity_id", "to_entity_id", "relationship_type", name="uq_inventory_relationship"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_entities.id", ondelete="CASCADE"), nullable=False
    )
    to_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_entities.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
