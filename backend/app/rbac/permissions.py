"""Permission keys and seed roles for the MVP-001/MVP-002 slice.

ATLAS-031 owns the full RBAC model; this module seeds only the permissions
the current API surface enforces. New permissions are added here as new
capabilities ship — never inferred from a request.
"""

IDENTITY_SELF_READ = "identity.self.read"
AUDIT_READ = "audit.read"
RBAC_ADMIN = "rbac.admin"
INVENTORY_READ = "inventory.read"
CONNECTOR_SYNC = "connector.sync"

ALL_PERMISSIONS: dict[str, str] = {
    IDENTITY_SELF_READ: "Read the caller's own identity and session context.",
    AUDIT_READ: "Read audit events.",
    RBAC_ADMIN: "Manage roles, permissions, and role assignments.",
    INVENTORY_READ: "Read discovered inventory entities and relationships.",
    CONNECTOR_SYNC: "Trigger a connector discovery/reconciliation run.",
}

# ADR-003: the development identity's default role grants only
# identity.self.read — it is not a bootstrap administrator.
DEVELOPMENT_OPERATOR_ROLE = "local_operator_dev"
ADMINISTRATOR_ROLE = "administrator"

SEED_ROLES: dict[str, list[str]] = {
    DEVELOPMENT_OPERATOR_ROLE: [IDENTITY_SELF_READ],
    ADMINISTRATOR_ROLE: [
        IDENTITY_SELF_READ,
        AUDIT_READ,
        RBAC_ADMIN,
        INVENTORY_READ,
        CONNECTOR_SYNC,
    ],
}
