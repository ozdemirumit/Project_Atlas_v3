"""Permission keys and seed roles for the MVP-001 Foundation slice.

ATLAS-031 owns the full RBAC model; this module seeds only the permissions
the current API surface enforces. New permissions are added here as new
capabilities ship — never inferred from a request.
"""

IDENTITY_SELF_READ = "identity.self.read"
AUDIT_READ = "audit.read"
RBAC_ADMIN = "rbac.admin"

ALL_PERMISSIONS: dict[str, str] = {
    IDENTITY_SELF_READ: "Read the caller's own identity and session context.",
    AUDIT_READ: "Read audit events.",
    RBAC_ADMIN: "Manage roles, permissions, and role assignments.",
}

# ADR-003: the development identity's default role grants only
# identity.self.read — it is not a bootstrap administrator.
DEVELOPMENT_OPERATOR_ROLE = "local_operator_dev"
ADMINISTRATOR_ROLE = "administrator"

SEED_ROLES: dict[str, list[str]] = {
    DEVELOPMENT_OPERATOR_ROLE: [IDENTITY_SELF_READ],
    ADMINISTRATOR_ROLE: [IDENTITY_SELF_READ, AUDIT_READ, RBAC_ADMIN],
}
