from app.models.connector_health import ConnectorHealthCheck
from app.models.inventory import ConnectorInstance
from app.scheduler.health import check_instance


async def test_check_instance_records_healthy(db_session, sanfabric_simulator_url):
    instance = ConnectorInstance(
        key="health-check-target",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url=sanfabric_simulator_url,
    )
    db_session.add(instance)
    db_session.commit()

    await check_instance(instance)

    check = (
        db_session.query(ConnectorHealthCheck)
        .filter(ConnectorHealthCheck.connector_instance_id == instance.id)
        .one()
    )
    assert check.status == "healthy"
    assert check.detail["fabric_count"] == 1


async def test_check_instance_records_unhealthy_for_unreachable_target(db_session):
    instance = ConnectorInstance(
        key="health-check-unreachable",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url="http://127.0.0.1:1",  # nothing listens here
    )
    db_session.add(instance)
    db_session.commit()

    await check_instance(instance)

    check = (
        db_session.query(ConnectorHealthCheck)
        .filter(ConnectorHealthCheck.connector_instance_id == instance.id)
        .one()
    )
    assert check.status == "unhealthy"
