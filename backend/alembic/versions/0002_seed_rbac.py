"""Seed the MVP-001 permissions and roles.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# Frozen at this migration's creation time — do NOT import from
# app.rbac.permissions here. That module has grown permissions in later
# migrations (0004, 0006, 0008, 0010); importing the *current* module state
# from this earlier migration would re-insert those later permissions too
# and collide with the migration that actually owns them. Every governed
# migration's seed data must be a frozen literal, not a live import.
ALL_PERMISSIONS: dict[str, str] = {
    "identity.self.read": "Read the caller's own identity and session context.",
    "audit.read": "Read audit events.",
    "rbac.admin": "Manage roles, permissions, and role assignments.",
}

SEED_ROLES: dict[str, list[str]] = {
    "local_operator_dev": ["identity.self.read"],
    "administrator": ["identity.self.read", "audit.read", "rbac.admin"],
}

permissions_table = sa.table(
    "permissions",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("key", sa.String),
    sa.column("description", sa.String),
)
roles_table = sa.table(
    "roles",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
)
role_permissions_table = sa.table(
    "role_permissions",
    sa.column("role_id", postgresql.UUID(as_uuid=True)),
    sa.column("permission_id", postgresql.UUID(as_uuid=True)),
)


def upgrade() -> None:
    permission_ids: dict[str, uuid.UUID] = {key: uuid.uuid4() for key in ALL_PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[key], "key": key, "description": description}
            for key, description in ALL_PERMISSIONS.items()
        ],
    )

    role_ids: dict[str, uuid.UUID] = {name: uuid.uuid4() for name in SEED_ROLES}
    op.bulk_insert(
        roles_table,
        [{"id": role_ids[name], "name": name, "description": ""} for name in SEED_ROLES],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[permission_key]}
            for role_name, permission_keys in SEED_ROLES.items()
            for permission_key in permission_keys
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(role_permissions_table.delete())
    connection.execute(
        roles_table.delete().where(roles_table.c.name.in_(list(SEED_ROLES)))
    )
    connection.execute(
        permissions_table.delete().where(permissions_table.c.key.in_(list(ALL_PERMISSIONS)))
    )
