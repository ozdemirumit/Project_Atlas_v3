from app.connectors.sanfabric.client import SanFabricClient
from app.connectors.sanfabric.sync import reconcile
from app.models.inventory import ConnectorInstance, InventoryEntity, InventoryRelationship


def test_client_discovers_fixture_topology(sanfabric_simulator_url):
    result = SanFabricClient(base_url=sanfabric_simulator_url).discover()

    assert result.fabric.external_id == "fab-01"
    assert {s.external_id for s in result.switches} == {"sw-01", "sw-02"}
    assert len(result.ports) == 5
    assert {z.external_id for z in result.zones} == {"zone-prod-storage-01", "zone-backup-01"}


def test_reconcile_creates_entities_and_relationships(db_session, sanfabric_simulator_url):
    instance = ConnectorInstance(
        key="sanfabric-sim-test",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url=sanfabric_simulator_url,
    )
    db_session.add(instance)
    db_session.flush()

    result = SanFabricClient(base_url=sanfabric_simulator_url).discover()
    counts = reconcile(db_session, instance=instance, result=result)
    db_session.commit()

    # 1 fabric + 2 switches + 5 ports + 2 zones
    assert counts["entities_written"] == 10
    entities = (
        db_session.query(InventoryEntity)
        .filter(InventoryEntity.connector_instance_id == instance.id)
        .all()
    )
    assert len(entities) == 10
    assert {e.entity_type for e in entities} == {"fabric", "switch", "port", "zone"}

    relationships = (
        db_session.query(InventoryRelationship)
        .join(InventoryEntity, InventoryRelationship.from_entity_id == InventoryEntity.id)
        .filter(InventoryEntity.connector_instance_id == instance.id)
        .all()
    )
    assert {r.relationship_type for r in relationships} == {"managed_by", "member_of"}


def test_reconcile_is_idempotent(db_session, sanfabric_simulator_url):
    instance = ConnectorInstance(
        key="sanfabric-sim-idempotent",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url=sanfabric_simulator_url,
    )
    db_session.add(instance)
    db_session.flush()

    client = SanFabricClient(base_url=sanfabric_simulator_url)
    reconcile(db_session, instance=instance, result=client.discover())
    db_session.commit()
    counts_second_run = reconcile(db_session, instance=instance, result=client.discover())
    db_session.commit()

    entities = (
        db_session.query(InventoryEntity)
        .filter(InventoryEntity.connector_instance_id == instance.id)
        .count()
    )
    assert entities == 10  # re-running discovery updates rows, does not duplicate them
    assert counts_second_run["entities_written"] == 10
