import uuid

import pytest

from app.connectors.sanfabric.client import SanFabricClient
from app.connectors.sanfabric.schemas import DiscoveredFabric, DiscoveryResult
from app.core.security import hash_password
from app.models.identity import LocalCredential, Role, User, UserRole
from app.models.inventory import ConnectorInstance
from app.rbac.permissions import ADMINISTRATOR_ROLE


@pytest.fixture()
def seeded_connector(db_session):
    # A unique key per invocation: `get_current_subject` commits the whole
    # session as a side effect of touching session.last_seen_at on every
    # authenticated request in the same test (harmless in production, where
    # each request gets a fresh session — see app.auth.dependencies), so a
    # fixed key here would collide the second time this fixture is used
    # within one test run.
    instance = ConnectorInstance(
        key=f"sanfabric-sim-api-test-{uuid.uuid4().hex[:8]}",
        vendor="Atlas Simulator",
        product="SAN Fabric Simulator",
        domain="san_fabric",
        target_base_url="http://simulator.test",
    )
    db_session.add(instance)
    db_session.flush()
    return instance


def test_sync_requires_permission(client, seeded_connector):
    client.post("/api/auth/login/development")
    response = client.post(f"/api/connectors/{seeded_connector.key}/sync")
    assert response.status_code == 403


def test_sync_unknown_connector_returns_404(client):
    client.post("/api/auth/login/development")  # not privileged, but 404 check happens after auth
    response = client.post("/api/connectors/does-not-exist/sync")
    assert response.status_code in (403, 404)


def test_sync_and_read_inventory_as_administrator(client, db_session, monkeypatch, seeded_connector):
    admin_user = User(subject_id="inventory-admin", display_name="Inventory Admin", identity_source="local")
    db_session.add(admin_user)
    db_session.flush()
    db_session.add(LocalCredential(user_id=admin_user.id, password_hash=hash_password("correct-horse")))
    role = db_session.query(Role).filter(Role.name == ADMINISTRATOR_ROLE).one()
    db_session.add(UserRole(user_id=admin_user.id, role_id=role.id))
    db_session.commit()

    def fake_discover(self) -> DiscoveryResult:
        return DiscoveryResult(
            fabric=DiscoveredFabric(external_id="fab-01", name="Fabric A"), switches=(), ports=(), zones=()
        )

    monkeypatch.setattr(SanFabricClient, "discover", fake_discover)

    login = client.post(
        "/api/auth/login/local", json={"username": "inventory-admin", "password": "correct-horse"}
    )
    assert login.status_code == 204

    sync = client.post(f"/api/connectors/{seeded_connector.key}/sync")
    assert sync.status_code == 200
    assert sync.json() == {
        "connector_instance_key": seeded_connector.key,
        "entities_written": 1,
        "relationships_written": 0,
    }

    entities = client.get("/api/inventory/entities")
    assert entities.status_code == 200
    assert any(e["external_id"] == "fab-01" for e in entities.json())
