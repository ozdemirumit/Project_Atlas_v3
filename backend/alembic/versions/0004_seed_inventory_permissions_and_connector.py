"""Seed inventory/connector permissions and the sanfabric-sim connector instance.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-13

"""
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

NEW_PERMISSIONS = {
    "inventory.read": "Read discovered inventory entities and relationships.",
    "connector.sync": "Trigger a connector discovery/reconciliation run.",
}

permissions_table = sa.table(
    "permissions",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("key", sa.String),
    sa.column("description", sa.String),
)
roles_table = sa.table("roles", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String))
role_permissions_table = sa.table(
    "role_permissions",
    sa.column("role_id", postgresql.UUID(as_uuid=True)),
    sa.column("permission_id", postgresql.UUID(as_uuid=True)),
)
connector_instances_table = sa.table(
    "connector_instances",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("key", sa.String),
    sa.column("vendor", sa.String),
    sa.column("product", sa.String),
    sa.column("domain", sa.String),
    sa.column("target_base_url", sa.String),
    sa.column("is_enabled", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)


def upgrade() -> None:
    connection = op.get_bind()

    permission_ids = {key: uuid.uuid4() for key in NEW_PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [{"id": permission_ids[key], "key": key, "description": desc} for key, desc in NEW_PERMISSIONS.items()],
    )

    admin_role_id = connection.execute(
        sa.select(roles_table.c.id).where(roles_table.c.name == "administrator")
    ).scalar_one()
    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": admin_role_id, "permission_id": permission_id}
            for permission_id in permission_ids.values()
        ],
    )

    op.bulk_insert(
        connector_instances_table,
        [
            {
                "id": uuid.uuid4(),
                "key": "sanfabric-sim",
                "vendor": "Atlas Simulator",
                "product": "SAN Fabric Simulator",
                "domain": "san_fabric",
                "target_base_url": "http://localhost:9101",
                "is_enabled": True,
                "created_at": datetime.now(timezone.utc),
            }
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        connector_instances_table.delete().where(connector_instances_table.c.key == "sanfabric-sim")
    )
    connection.execute(role_permissions_table.delete().where(
        role_permissions_table.c.permission_id.in_(
            sa.select(permissions_table.c.id).where(permissions_table.c.key.in_(list(NEW_PERMISSIONS)))
        )
    ))
    connection.execute(permissions_table.delete().where(permissions_table.c.key.in_(list(NEW_PERMISSIONS))))
