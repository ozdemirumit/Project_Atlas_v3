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


def _seed_recommendation(client, db_session, sanfabric_simulator_url, investigation_key: str) -> str:
    connector = ConnectorInstance(
        key=f"sanfabric-governance-{investigation_key}",
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

    client.post("/api/investigations", json={"key": investigation_key, "title": "Governance test"})
    hyp = client.post(
        f"/api/investigations/{investigation_key}/hypotheses/generate",
        json={"target_entity_id": str(offline_port.id)},
    )
    hypothesis_id = hyp.json()[0]["id"]
    rec = client.post(
        f"/api/investigations/{investigation_key}/recommendations", json={"hypothesis_id": hypothesis_id}
    )
    return rec.json()["id"]


def test_dlp_guardrail_blocks_secret_in_event_description(client, db_session):
    _login_as_administrator(client, db_session, "dlp-tester")
    client.post("/api/investigations", json={"key": "inv-dlp", "title": "DLP test"})
    response = client.post(
        "/api/investigations/inv-dlp/events",
        json={"event_type": "note", "description": "api_key=sk-abcdef0123456789verylongsecret"},
    )
    assert response.status_code == 422


def test_investigation_opener_cannot_self_approve(client, db_session, sanfabric_simulator_url):
    _login_as_administrator(client, db_session, "opener")
    recommendation_id = _seed_recommendation(client, db_session, sanfabric_simulator_url, "inv-self-approve")

    client.post(f"/api/investigations/inv-self-approve/recommendations/{recommendation_id}/submit")
    decision = client.post(
        f"/api/investigations/inv-self-approve/recommendations/{recommendation_id}/decide",
        json={"decision": "approved", "comment": "looks fine"},
    )
    assert decision.status_code == 403


def test_second_administrator_can_approve(client, db_session, sanfabric_simulator_url):
    _login_as_administrator(client, db_session, "opener-2")
    recommendation_id = _seed_recommendation(client, db_session, sanfabric_simulator_url, "inv-approve-ok")
    client.post(f"/api/investigations/inv-approve-ok/recommendations/{recommendation_id}/submit")
    client.post("/api/auth/logout")

    _login_as_administrator(client, db_session, "approver-2")
    decision = client.post(
        f"/api/investigations/inv-approve-ok/recommendations/{recommendation_id}/decide",
        json={"decision": "approved", "comment": "confirmed rollback plan is safe"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"

    approvals = client.get(
        f"/api/investigations/inv-approve-ok/recommendations/{recommendation_id}/approvals"
    )
    assert approvals.status_code == 200
    assert approvals.json()[0]["approver_subject_id"] == "approver-2"


def test_syslog_export_requires_permission(client):
    client.post("/api/auth/login/development")
    response = client.get("/api/audit/events.syslog")
    assert response.status_code == 403


def test_syslog_export_format(client, db_session):
    _login_as_administrator(client, db_session, "siem-exporter")
    response = client.get("/api/audit/events.syslog")
    assert response.status_code == 200
    lines = [line for line in response.text.splitlines() if line]
    assert lines
    assert lines[0].startswith("<")
    assert "atlas@0" in lines[0]
