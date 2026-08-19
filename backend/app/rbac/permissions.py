"""Permission keys and seed roles for the MVP-001 through MVP-004 slice.

ATLAS-031 owns the full RBAC model; this module seeds only the permissions
the current API surface enforces. New permissions are added here as new
capabilities ship — never inferred from a request.
"""

IDENTITY_SELF_READ = "identity.self.read"
AUDIT_READ = "audit.read"
RBAC_ADMIN = "rbac.admin"
INVENTORY_READ = "inventory.read"
CONNECTOR_SYNC = "connector.sync"
CONNECTOR_HEALTH_READ = "connector.health.read"
KNOWLEDGE_READ = "knowledge.read"
KNOWLEDGE_ADMIN = "knowledge.admin"
INVESTIGATION_READ = "investigation.read"
INVESTIGATION_WRITE = "investigation.write"
APPROVAL_DECIDE = "approval.decide"
SIEM_EXPORT = "siem.export"

ALL_PERMISSIONS: dict[str, str] = {
    IDENTITY_SELF_READ: "Read the caller's own identity and session context.",
    AUDIT_READ: "Read audit events.",
    RBAC_ADMIN: "Manage roles, permissions, and role assignments.",
    INVENTORY_READ: "Read discovered inventory entities and relationships.",
    CONNECTOR_SYNC: "Trigger a connector discovery/reconciliation run.",
    CONNECTOR_HEALTH_READ: "Read connector scheduled health-check history.",
    KNOWLEDGE_READ: "Search governed knowledge sources.",
    KNOWLEDGE_ADMIN: "Ingest and manage governed knowledge sources.",
    INVESTIGATION_READ: "Read investigations, hypotheses, impact assessments, and recommendations.",
    INVESTIGATION_WRITE: "Open investigations and generate hypotheses, impact assessments, and recommendations.",
    APPROVAL_DECIDE: "Approve or reject a recommendation submitted for approval.",
    SIEM_EXPORT: "Export audit events in syslog format to a configured collector.",
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
        CONNECTOR_HEALTH_READ,
        KNOWLEDGE_READ,
        KNOWLEDGE_ADMIN,
        INVESTIGATION_READ,
        INVESTIGATION_WRITE,
        APPROVAL_DECIDE,
        SIEM_EXPORT,
    ],
}
