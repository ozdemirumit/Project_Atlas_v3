"""Deterministic RCA hypothesis generation for the SAN fabric fault family.

`docs/002_Product_Requirements.md` Section 10 selects "SAN switch port/
fabric failure with a zoning conflict" as MVP-003's proving fault family.
ATLAS-041 (Reasoning / AI hypothesis generation) is not implemented — no
local/private model is configured yet (open question, Section 16). This
rule engine is an explicit, documented placeholder standing in for it: it
inspects inventory entity status and recent connector health checks and
proposes hypotheses a human reviews and confirms or rejects, preserving the
"AI assists, humans decide" boundary even though there is no AI here yet.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.connector_health import ConnectorHealthCheck
from app.models.inventory import InventoryEntity, InventoryRelationship


def generate_hypotheses(
    db: Session, *, target_entity_id: uuid.UUID
) -> list[dict[str, object]]:
    target = db.get(InventoryEntity, target_entity_id)
    if target is None:
        return []

    hypotheses: list[dict[str, object]] = []

    if target.entity_type == "port" and target.attributes.get("status") == "offline":
        zone_edges = (
            db.query(InventoryRelationship)
            .filter(
                InventoryRelationship.from_entity_id == target.id,
                InventoryRelationship.relationship_type == "member_of",
            )
            .all()
        )
        zone_names = []
        for edge in zone_edges:
            zone = db.get(InventoryEntity, edge.to_entity_id)
            if zone is not None:
                zone_names.append(zone.display_name)

        evidence = [f"Port {target.display_name} ({target.external_id}) reports status=offline."]
        if zone_names:
            evidence.append(f"Port is a member of zone(s): {', '.join(zone_names)}.")

        hypotheses.append(
            {
                "fault_family": "san_port_offline",
                "description": (
                    f"Port {target.display_name} on its switch appears down, which may isolate "
                    f"any zone it belongs to ({', '.join(zone_names) or 'none observed'}) from its "
                    "paired storage or host ports."
                ),
                "confidence": "medium" if zone_names else "low",
                "supporting_evidence": evidence,
                "contradicting_evidence": [],
            }
        )

    if target.entity_type == "switch":
        recent_checks = (
            db.query(ConnectorHealthCheck)
            .filter(ConnectorHealthCheck.connector_instance_id == target.connector_instance_id)
            .order_by(ConnectorHealthCheck.checked_at.desc())
            .limit(3)
            .all()
        )
        unhealthy = [c for c in recent_checks if c.status == "unhealthy"]
        if unhealthy:
            hypotheses.append(
                {
                    "fault_family": "san_fabric_unreachable",
                    "description": (
                        f"The connector for {target.display_name}'s fabric has reported "
                        f"{len(unhealthy)} of its last {len(recent_checks)} scheduled health checks "
                        "as unhealthy, suggesting the fabric manager or its network path is degraded."
                    ),
                    "confidence": "high" if len(unhealthy) == len(recent_checks) else "medium",
                    "supporting_evidence": [
                        f"Health check at {c.checked_at.isoformat()}: {c.detail}" for c in unhealthy
                    ],
                    "contradicting_evidence": [],
                }
            )

    if not hypotheses:
        hypotheses.append(
            {
                "fault_family": "unclassified",
                "description": (
                    f"No known SAN fabric fault pattern matched {target.entity_type} "
                    f"{target.display_name}'s current observed state; manual investigation required."
                ),
                "confidence": "low",
                "supporting_evidence": [f"Attributes: {target.attributes}"],
                "contradicting_evidence": [],
            }
        )

    return hypotheses
