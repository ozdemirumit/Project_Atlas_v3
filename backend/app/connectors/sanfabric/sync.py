"""Reconcile one SAN fabric discovery result into inventory entities and
relationships.

This is the reference implementation of the discovery-to-inventory mapping
that was an open question in `docs/026_Graph_Engine.md` Section 33 and
`docs/020_MCP_Framework.md` Section 35: one connector's discovery output
becomes N normalized `InventoryEntity` rows plus `InventoryRelationship`
edges, keyed by (connector_instance_id, external_id) so re-running discovery
updates existing rows instead of duplicating them.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.connectors.sanfabric.schemas import DiscoveryResult
from app.models.inventory import ConnectorInstance, InventoryEntity, InventoryRelationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _upsert_entity(
    db: Session,
    *,
    instance: ConnectorInstance,
    entity_type: str,
    external_id: str,
    display_name: str,
    attributes: dict[str, object],
) -> InventoryEntity:
    entity = (
        db.query(InventoryEntity)
        .filter(
            InventoryEntity.connector_instance_id == instance.id,
            InventoryEntity.external_id == external_id,
        )
        .one_or_none()
    )
    now = _now()
    if entity is None:
        entity = InventoryEntity(
            connector_instance_id=instance.id,
            entity_type=entity_type,
            external_id=external_id,
            display_name=display_name,
            attributes=attributes,
            first_observed_at=now,
            last_observed_at=now,
        )
        db.add(entity)
        db.flush()
    else:
        entity.display_name = display_name
        entity.attributes = attributes
        entity.last_observed_at = now
    return entity


def _upsert_relationship(
    db: Session, *, from_entity: InventoryEntity, to_entity: InventoryEntity, relationship_type: str
) -> None:
    relationship = (
        db.query(InventoryRelationship)
        .filter(
            InventoryRelationship.from_entity_id == from_entity.id,
            InventoryRelationship.to_entity_id == to_entity.id,
            InventoryRelationship.relationship_type == relationship_type,
        )
        .one_or_none()
    )
    now = _now()
    if relationship is None:
        db.add(
            InventoryRelationship(
                from_entity_id=from_entity.id,
                to_entity_id=to_entity.id,
                relationship_type=relationship_type,
                first_observed_at=now,
                last_observed_at=now,
            )
        )
    else:
        relationship.last_observed_at = now


def reconcile(db: Session, *, instance: ConnectorInstance, result: DiscoveryResult) -> dict[str, int]:
    entities_written = 0
    relationships_written = 0

    fabric_entity = _upsert_entity(
        db,
        instance=instance,
        entity_type="fabric",
        external_id=result.fabric.external_id,
        display_name=result.fabric.name,
        attributes={},
    )
    entities_written += 1

    switch_entities: dict[str, InventoryEntity] = {}
    for switch in result.switches:
        entity = _upsert_entity(
            db,
            instance=instance,
            entity_type="switch",
            external_id=switch.external_id,
            display_name=switch.name,
            attributes={"wwn": switch.wwn, "status": switch.status},
        )
        entities_written += 1
        switch_entities[switch.external_id] = entity
        _upsert_relationship(
            db, from_entity=entity, to_entity=fabric_entity, relationship_type="managed_by"
        )
        relationships_written += 1

    port_entities: dict[str, InventoryEntity] = {}
    for port in result.ports:
        entity = _upsert_entity(
            db,
            instance=instance,
            entity_type="port",
            external_id=port.external_id,
            display_name=f"port {port.index}",
            attributes={"wwn": port.wwn, "status": port.status, "index": port.index},
        )
        entities_written += 1
        port_entities[port.external_id] = entity
        switch_entity = switch_entities.get(port.switch_external_id)
        if switch_entity is not None:
            _upsert_relationship(
                db, from_entity=entity, to_entity=switch_entity, relationship_type="managed_by"
            )
            relationships_written += 1

    for zone in result.zones:
        zone_entity = _upsert_entity(
            db,
            instance=instance,
            entity_type="zone",
            external_id=zone.external_id,
            display_name=zone.name,
            attributes={},
        )
        entities_written += 1
        for port_external_id in zone.member_port_external_ids:
            port_entity = port_entities.get(port_external_id)
            if port_entity is not None:
                _upsert_relationship(
                    db, from_entity=port_entity, to_entity=zone_entity, relationship_type="member_of"
                )
                relationships_written += 1

    return {"entities_written": entities_written, "relationships_written": relationships_written}
