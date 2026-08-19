"""Connector instance and inventory schema (MVP-002 Data and Integration).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-13

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connector_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("vendor", sa.String(length=100), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("target_base_url", sa.String(length=500), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "inventory_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("connector_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("attributes", postgresql.JSON(), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connector_instance_id"], ["connector_instances.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("connector_instance_id", "external_id", name="uq_inventory_entity_source"),
    )
    op.create_index("ix_inventory_entities_entity_type", "inventory_entities", ["entity_type"])

    op.create_table(
        "inventory_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["from_entity_id"], ["inventory_entities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_entity_id"], ["inventory_entities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "from_entity_id", "to_entity_id", "relationship_type", name="uq_inventory_relationship"
        ),
    )
    op.create_index("ix_inventory_relationships_type", "inventory_relationships", ["relationship_type"])


def downgrade() -> None:
    op.drop_table("inventory_relationships")
    op.drop_table("inventory_entities")
    op.drop_table("connector_instances")
