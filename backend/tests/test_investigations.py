from app.connectors.sanfabric.client import SanFabricClient
from app.connectors.sanfabric.sync import reconcile
from app.core.security import hash_password
from app.models.identity import LocalCredential, Role, User, UserRole
from app.models.inventory import ConnectorInstance, InventoryEntity
from app.rbac.permissions import ADMINISTRATOR_ROLE


def _login_as_administrator(client, db_session, subject_id: str) -> None:
    user = User(subject_id=subject_id, display_name=subject_id, identity_source="local")
    db_session.add(user)
    db_session.flush()
    db_session.add(LocalCredential(user_id=user.id, password_hash=hash_password("correct-horse")))
    role = db_session.query(Role).filter(Role.name == ADMINISTRATOR_ROLE).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    login = client.post("/api/auth/login/local", json={"username": subject_id, "password": "correct-horse"})
    assert login.status_code == 204


def test_investigations_requires_permission(client):
    client.post("/api/auth/login/development")
    response = client.post("/api/investigations", json={"key": "inv-1", "title": "Test"})
    assert response.status_code == 403


def test_full_investigation_workflow(client, db_session, sanfabric_simulator_url):
    _login_as_administrator(client, db_session, "investigator")

    # Seed real inventory via the real connector + simulator, then take an
    # offline port down a zone path, matching the selected MVP fault family.
    connector = ConnectorInstance(
        key="sanfabric-investigation-test",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url=sanfabric_simulator_url,
    )
    db_session.add(connector)
    db_session.flush()
    result = SanFabricClient(base_url=sanfabric_simulator_url).discover()
    reconcile(db_session, instance=connector, result=result)
    db_session.commit()

    offline_port = (
        db_session.query(InventoryEntity)
        .filter(
            InventoryEntity.connector_instance_id == connector.id,
            InventoryEntity.entity_type == "port",
            InventoryEntity.external_id == "sw-01-p3",
        )
        .one()
    )
    assert offline_port.attributes["status"] == "offline"

    create = client.post("/api/investigations", json={"key": "inv-san-01", "title": "Port down"})
    assert create.status_code == 201

    hypotheses = client.post(
        "/api/investigations/inv-san-01/hypotheses/generate",
        json={"target_entity_id": str(offline_port.id)},
    )
    assert hypotheses.status_code == 201
    hypothesis_list = hypotheses.json()
    assert len(hypothesis_list) == 1
    assert hypothesis_list[0]["fault_family"] == "san_port_offline"
    hypothesis_id = hypothesis_list[0]["id"]

    confirm = client.patch(
        f"/api/investigations/inv-san-01/hypotheses/{hypothesis_id}", json={"status": "confirmed"}
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"

    impact = client.post(
        "/api/investigations/inv-san-01/impact", json={"target_entity_id": str(offline_port.id)}
    )
    assert impact.status_code == 201
    assert impact.json()["summary"]

    recommendation = client.post(
        "/api/investigations/inv-san-01/recommendations", json={"hypothesis_id": hypothesis_id}
    )
    assert recommendation.status_code == 201
    assert recommendation.json()["rollback_plan"]

    report = client.get("/api/investigations/inv-san-01/report")
    assert report.status_code == 200
    body = report.json()
    assert body["investigation"]["key"] == "inv-san-01"
    assert len(body["hypotheses"]) == 1
    assert len(body["impact_assessments"]) == 1
    assert len(body["recommendations"]) == 1
