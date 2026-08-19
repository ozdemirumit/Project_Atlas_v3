"""Seed connector-health and knowledge permissions.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-18

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

NEW_PERMISSIONS = {
    "connector.health.read": "Read connector scheduled health-check history.",
    "knowledge.read": "Search governed knowledge sources.",
    "knowledge.admin": "Ingest and manage governed knowledge sources.",
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


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        role_permissions_table.delete().where(
            role_permissions_table.c.permission_id.in_(
                sa.select(permissions_table.c.id).where(permissions_table.c.key.in_(list(NEW_PERMISSIONS)))
            )
        )
    )
    connection.execute(permissions_table.delete().where(permissions_table.c.key.in_(list(NEW_PERMISSIONS))))
